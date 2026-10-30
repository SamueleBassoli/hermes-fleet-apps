# Python stdlib http.server, for a one-command local UI

Patterns that survived a real build. `ThreadingHTTPServer` + `BaseHTTPRequestHandler`,
no framework.

## Handler built around one immutable snapshot

Build the handler class inside a factory so it closes over the data, and take a **copy**
of the caller's list. Nothing can be appended to it after the server is listening, so an
index means the same item for the whole session.

```python
def _handler_for(items, *, quiet: bool, resolver=None):
    queue = list(items)                  # private copy
    style_css = page.stylesheet().encode("utf-8")
    resolved: dict[int, Outcome] = {}    # answers live BESIDE the queue
    lock = Lock()

    def render_index() -> bytes:
        with lock:
            snapshot = dict(resolved)
        return page.index_page(queue, snapshot, can_resolve=resolver is not None).encode()

    class Handler(BaseHTTPRequestHandler):
        server_version = "toolname"
        sys_version = ""                 # do not advertise the Python version
        protocol_version = "HTTP/1.1"
    ...
    return Handler
```

Re-render the index per GET; pre-render the static CSS once. Never mutate `queue` to mark
progress — renumbering is what makes an index unsafe.

## One header helper, so no response can forget the policy

Split "send headers" from "send body" — a 303 needs the headers with a zero-length body
and an extra `Location`.

```python
def _headers(self, code, length, content_type):
    self.send_response(code)
    self.send_header("Content-Type", content_type)
    self.send_header("Content-Length", str(length))
    self.send_header("Cache-Control", "no-store")
    self.send_header("X-Content-Type-Options", "nosniff")
    self.send_header("Content-Security-Policy", CSP)
    self.send_header("Referrer-Policy", "no-referrer")

def _send(self, code, body, content_type):
    self._headers(code, len(body), content_type)
    self.end_headers()
    if self.command != "HEAD":          # HEAD shares the GET path
        self.wfile.write(body)
```

`protocol_version = "HTTP/1.1"` means keep-alive, which means **every** response needs an
accurate `Content-Length` or the client hangs waiting for more body.

## Refusing a POST without poisoning the connection

On a keep-alive connection an unread request body stays in the socket. The server then
parses those leftover bytes as the next request line, and the client reports a connection
abort instead of the 400 it was actually sent — on Windows a close with unread data sends
an RST, so the status never arrives at all.

Read the length once, refuse through one helper that drains and closes:

```python
MAX_POST_BYTES = 4096        # a decision is a few hundred bytes
DRAIN_LIMIT = 1 << 20        # read-and-discard budget, purely to deliver the refusal

def _refuse_post(self, code, message, *, drain=0):
    if 0 < drain <= DRAIN_LIMIT:
        try:
            self.rfile.read(drain)
        except OSError:
            pass
    self.close_connection = True
    self._text(code, message)

def _body_length(self) -> int:
    try:
        return int(self.headers.get("Content-Length", "0"))
    except ValueError:
        return -1
```

Every refusal path — wrong route, no writer, oversized, bad index, empty field — goes
through that helper. Two limits, two jobs: `MAX_POST_BYTES` decides what counts as a
valid action, `DRAIN_LIMIT` decides how much junk is worth swallowing to answer politely.

## A vanished client is not an error

Closing a tab mid-response raises inside the stdlib and prints a traceback into the
terminal the user is watching:

```python
def handle_one_request(self) -> None:
    try:
        super().handle_one_request()
    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
        self.close_connection = True
```

Also route `log_message` through a `quiet` flag so the tool owns its own output.

## POST an index, answer with 303

```python
def do_POST(self):
    length = self._body_length()
    if urlparse(self.path).path != RESOLVE_PATH:
        self._refuse_post(404, "not found", drain=length); return
    if resolver is None:
        self._refuse_post(403, "this server cannot write", drain=length); return
    if length <= 0 or length > MAX_POST_BYTES:
        self._refuse_post(400, "bad request", drain=length); return

    form = parse_qs(self.rfile.read(length).decode("utf-8", "replace"),
                    keep_blank_values=True)
    raw = form.get(FIELD_INDEX, [""])[0]
    if not raw.isdigit():                       # rejects paths, floats, negatives, ""
        self._refuse_post(400, "id must be a number"); return
    n = int(raw)
    if n >= len(queue):
        self._refuse_post(404, "no such item"); return

    with lock:
        if n in resolved:                       # double-click or stale form
            self._redirect_home(); return
    outcome = resolver(n, queue[n], value)
    with lock:
        resolved.setdefault(n, outcome)
    self._redirect_home()
```

`str.isdigit()` is the whole input validation for an index — it rejects `../x`,
`C:\x`, `0.jpg`, `-1`, `1e0` and the empty string in one call. Check membership in the
answered map *before* calling the writer, or a double-click tries to act twice.

The redirect helper sends headers with a zero-length body:

```python
def _redirect_home(self):
    self._headers(303, 0, "text/plain; charset=utf-8")
    self.send_header("Location", "/")
    self.end_headers()
```

## Keep the writer out, mechanically

The server receives a callable; it must not import the writing module even transitively.
Type-only imports are free:

```python
if TYPE_CHECKING:            # never executes, so the boundary holds
    from .resolve import Resolution
Resolver = Callable[[int, Item, str], "Resolution"]
```

Prove it with a test that parses the module's own AST. **`ast.walk` yields the children
of an `if TYPE_CHECKING:` node whether or not you skip the `If` itself** — collect the
ids of everything inside the block first, then filter:

```python
type_only = set()
for node in ast.walk(tree):
    if isinstance(node, ast.If) and "TYPE_CHECKING" in ast.dump(node.test):
        type_only.update(id(c) for c in ast.walk(node))

runtime = set()
for node in ast.walk(tree):
    if id(node) in type_only:
        continue
    ...collect ImportFrom/Import names...

assert "actions" not in runtime
assert type_only, "the type-only import is gone — this test now proves nothing"
```

That last assertion matters: without it the test passes trivially once the import it was
watching disappears.

## Testing a live server

Run it on an ephemeral port in a daemon thread, and always tear down in `finally`:
`httpd.shutdown()`, `httpd.server_close()`, `thread.join(timeout=5)`.

To assert on a redirect rather than follow it, build an opener whose
`HTTPRedirectHandler.redirect_request` returns `None`, then read `status` and `Location`.
Wrap the call and catch `urllib.error.HTTPError` so 4xx responses return a status instead
of raising.

To prove a mid-request disconnect is handled, send a request then close the socket with
`SO_LINGER` set to `(1, 0)` to force an RST rather than a clean FIN, and assert the
server still answers the next request and printed no traceback (`capfd`).
