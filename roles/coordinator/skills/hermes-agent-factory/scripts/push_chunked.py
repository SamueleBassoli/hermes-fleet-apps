#!/usr/bin/env python
"""Chunked, checksum-verified file upload over ssh.

For links where `scp` resets on bulk transfer but ssh command execution works.
Sends the file as base64 chunks through separate ssh invocations, retries each
chunk, then compares md5 on both sides.

    python push_chunked.py <local-file> <remote-path> user@host [chunk-bytes]

Exit 0 = checksums match. Exit 1 = mismatch. Never trust a transfer over a
flaky link without the checksum step.
"""
import base64
import hashlib
import pathlib
import subprocess
import sys

SRC = pathlib.Path(sys.argv[1])
DST = sys.argv[2]
HOST = sys.argv[3]
CHUNK = int(sys.argv[4]) if len(sys.argv) > 4 else 16384

data = SRC.read_bytes()
digest = hashlib.md5(data).hexdigest()
chunks = [data[i:i + CHUNK] for i in range(0, len(data), CHUNK)]
print(f"{SRC.name}: {len(data)} bytes, {len(chunks)} chunks, md5 {digest}")


def ssh(cmd, stdin=None):
    return subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", HOST, cmd],
        input=stdin, capture_output=True, timeout=120)


ssh(f"rm -f {DST} {DST}.part")

for n, c in enumerate(chunks):
    b64 = base64.b64encode(c)
    for attempt in range(4):
        r = ssh(f"base64 -d >> {DST}.part", stdin=b64)
        if r.returncode == 0:
            break
        print(f"  chunk {n} retry {attempt + 1}: {r.stderr.decode()[:80]}")
    else:
        sys.exit(f"chunk {n} failed permanently")
    if n % 10 == 0 or n == len(chunks) - 1:
        print(f"  {n + 1}/{len(chunks)}")

remote = ssh(f"md5sum {DST}.part | cut -d' ' -f1").stdout.decode().strip()
print(f"remote md5 {remote}")
if remote != digest:
    sys.exit("MISMATCH — left as .part, nothing renamed")
ssh(f"mv {DST}.part {DST}")
print("MATCH")
