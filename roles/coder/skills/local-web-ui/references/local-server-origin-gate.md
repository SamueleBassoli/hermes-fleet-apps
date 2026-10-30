# The origin gate: making a loopback server actually local

A page served on `127.0.0.1` is reachable by **every program and every browser tab on
that machine**. The bind is not the security boundary it looks like.

## What the loopback bind does and does not stop

| Threat | Stopped by the bind? |
|---|---|
| Another host on the LAN reaching the port | **yes** — it never reaches the socket |
| A page in another tab POSTing to the port | no |
| DNS rebinding: a hostile name resolved to 127.0.0.1 | **no** |

**DNS rebinding is the attack the bind does not touch.** A page at `evil.example` whose
name resolves to `127.0.0.1` makes the browser connect *from this machine*, so the client
address looks perfectly ordinary. Same-origin policy stops the attacker **reading** the
reply — and a write-capable endpoint does not need to be read. A blind POST that files,
deletes, or moves something succeeds silently. An ephemeral port is a ~16k guess, which
is a spray, not a wall.

The giveaway is the **name the request asked for**: a rebound request carries
`Host: evil.example`, which the human never typed.

## The three checks

Run them before choosing a route, cheapest first:

| Check | Refuses |
|---|---|
| client address is loopback | anything reaching a wider bind, if one is ever added |
| `Host:` hostname in `{127.0.0.1, localhost, ::1}` **and** the port matches | DNS rebinding |
| `Sec-Fetch-Site` in `{same-origin, none}` when present | a cross-site form POST |

Details that matter:

- **Check the port too.** `localhost:9999` is a different program on the same machine;
  honouring it accepts a request aimed at something else.
- **Parse the `Host` header with `urlsplit(f"//{raw}")`**, not a manual `rsplit(":")` —
  a bare split mangles the bracketed IPv6 form `[::1]:8080`. A non-numeric port raises
  `ValueError` from `.port`; treat that as a refusal, not a crash.
- **A missing `Host` is a refusal.** HTTP/1.1 requires it; a client that omits it is not
  a browser.
- **A missing `Sec-Fetch-Site` is ALLOWED.** That is curl, a test, or an agent — never a
  browser driven by another site, which always sets it. Refusing it breaks tooling to
  defend against nobody.
- **Keep the loopback assertion even though the bind makes it redundant today.** The bind
  is one line; a future `--host` flag, a reverse proxy, or a port forward each remove the
  guarantee silently. A currently-redundant check is what stops it becoming wrong later.
- **Refuse POSTs through the same drain-then-close path as any other refusal**, or the
  403 reaches the client as a connection reset instead of a status.

## Do NOT build this on the `Origin` header

`Origin` is the header everyone reaches for, and here it breaks the page while stopping
no attacker.

Measured against Chrome on a page whose responses carry `Referrer-Policy: no-referrer`,
submitting its own plain form:

```
Origin:         null          <- an Origin allowlist refuses YOUR OWN form
Sec-Fetch-Site: same-origin   <- correctly identifies it
```

MDN's `Referrer-Policy` page states it directly: for requests that are neither GET nor
HEAD and are not made in `cors` mode — which includes **HTML form submissions** — a
policy of `no-referrer` makes the user agent set `Origin` to `null`. `strict-origin` and
`strict-origin-when-cross-origin` do the same on an https→http downgrade. A `fetch()`
POST defaults to `cors` mode and so keeps its real Origin, which is why advice written
for APIs does not transfer to a no-JavaScript form page.

So an Origin allowlist refuses every real answer, while a hostile page nulls its own
Origin just as easily by declaring the same policy. `Sec-Fetch-Site` is attached by the
browser and cannot be forged or suppressed by the page that made the request.

**Encode this as a build check**, because the wrong choice looks more correct than the
right one: fail the build if the server module ever reads `Origin`. Match the lookup
(`headers.get("Origin"`), not the word — the module's own docstring has to explain the
rule and will contain it.

## Proving it with a real browser

Unit tests cannot show what a browser actually sends. Two staged attacks, both worth
running once:

**Cross-site POST.** Serve a throwaway page on a second local port that auto-submits a
form at the real server, then load it headless. Expect the refusal text, and assert the
write path was never invoked.

**True DNS rebinding.** No hosts-file edit needed — Chrome will do the mapping:

```bash
chrome --headless=new --disable-gpu --user-data-dir=<empty dir> \
  --host-resolver-rules="MAP evil.example 127.0.0.1" \
  --screenshot=<out.png> http://evil.example:<port>/
```

Then **look at the screenshot**: the refusal must be there and no item name or media may
appear in it.

Traps when driving these:

- **`--dump-dom` hangs on a page that is mid-navigation**, such as a form auto-submitting
  on load. It blocks until timeout and can starve a background helper you started for
  the same test, producing empty results that look like a failed attack but are a failed
  measurement. Use `--screenshot` for those pages.
- **Chrome's DevTools `/json/list` returns extension targets first.** Filter for
  `type == "page"` with a URL that is not `chrome-extension://`, or you attach to an
  extension background page and see an empty document with zero forms.
- **Give a helper server a generous lifetime.** A short window plus one slow browser
  launch means it exits before the browser arrives, and the empty result reads as a
  passing test when nothing was exercised.

## Stopping it

A foreground `ThreadingHTTPServer` whose handler threads are daemons returns promptly
from `shutdown()` even with a request in flight, so Ctrl-C does not hang on a stalled
client. Assert that directly: park a connection mid-request, time `shutdown()` +
`server_close()`, and confirm a later connection to the port is refused. "Nothing is left
listening" is a promise worth a test, not a comment.
