"""Screenshot a local page in real headless Chrome over CDP, stdlib only.

usage: python cdp_shot.py <chrome.exe> <empty profile dir> <url> <out.png> [js-to-run]
env:   CDP_WAIT=<seconds after navigate, default 1.5>
       CDP_SIZE=<w,h window size, default 1400,1000>
       CDP_FLAGS=<extra Chrome flags, space-separated, e.g.
                  --force-prefers-reduced-motion  or  --force-dark-mode>

Navigates, optionally runs one JS expression (e.g. a button click, for a real
POST + 303), waits, prints {"y": scrollY, "hash": location.hash}, saves a PNG.
Use instead of `chrome --screenshot`, which renders blank for '#fragment' URLs
and captures loading overlays (e.g. Lavish's "Checking layout": use CDP_WAIT=30).
The JS runs from OUTSIDE the page, so a no-JS page stays no-JS.
To read state back, have the JS write it into location.hash (URL-encoded).
"""
import base64, json, os, socket, struct, subprocess, sys, time, urllib.request

chrome, prof, url, out = sys.argv[1:5]
js = sys.argv[5] if len(sys.argv) > 5 else None
WAIT = float(os.environ.get("CDP_WAIT", "1.5"))
SIZE = os.environ.get("CDP_SIZE", "1400,1000")
FLAGS = os.environ.get("CDP_FLAGS", "").split()
PORT = 9344
proc = subprocess.Popen(
    [chrome, "--headless=new", f"--remote-debugging-port={PORT}",
     f"--user-data-dir={prof}", f"--window-size={SIZE}", "--hide-scrollbars",
     *FLAGS, "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
buf = b""
try:
    for _ in range(50):
        try:
            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
            break
        except Exception:
            time.sleep(0.2)
    ws = [t for t in tabs if t["type"] == "page"][0]["webSocketDebuggerUrl"]
    host, path = ws[5:].split("/", 1)
    h, p = host.split(":")
    s = socket.create_connection((h, int(p)))
    key = base64.b64encode(os.urandom(16)).decode()
    s.send((f"GET /{path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n").encode())
    while b"\r\n\r\n" not in buf:
        buf += s.recv(4096)
    buf = buf.split(b"\r\n\r\n", 1)[1]

    def recvn(n):
        global buf
        while len(buf) < n:
            buf += s.recv(65536)
        r, buf = buf[:n], buf[n:]
        return r

    def frame():
        _, b2 = recvn(2)
        n = b2 & 127
        if n == 126:
            n = struct.unpack(">H", recvn(2))[0]
        elif n == 127:
            n = struct.unpack(">Q", recvn(8))[0]
        return recvn(n)

    mid = [0]

    def call(method, **params):
        mid[0] += 1
        data = json.dumps({"id": mid[0], "method": method, "params": params}).encode()
        mask, n = os.urandom(4), len(data)
        hdr = b"\x81" + (bytes([0x80 | n]) if n < 126 else
                         bytes([0x80 | 126]) + struct.pack(">H", n) if n < 65536 else
                         bytes([0x80 | 127]) + struct.pack(">Q", n))
        s.send(hdr + mask + bytes(c ^ mask[i % 4] for i, c in enumerate(data)))
        while True:
            m = json.loads(frame())
            if m.get("id") == mid[0]:
                return m.get("result", {})

    def ev(expr):
        return call("Runtime.evaluate", expression=expr,
                    returnByValue=True)["result"].get("value")

    call("Page.enable")
    call("Page.navigate", url=url)
    time.sleep(WAIT)
    if js:
        ev(js)
        time.sleep(1.5)
    print(json.dumps({"y": ev("scrollY"), "hash": ev("location.hash")}))
    shot = call("Page.captureScreenshot", format="png")
    with open(out, "wb") as f:
        f.write(base64.b64decode(shot["data"]))
finally:
    proc.kill()
