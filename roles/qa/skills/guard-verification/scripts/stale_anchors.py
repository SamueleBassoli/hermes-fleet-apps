"""Which permanent sabotage cases no longer apply, and did this change break them?

Usage: python stale_anchors.py <repo> <harness.py relative to repo>
Assumes the harness defines CASES / TEST_CASES lists of (label, Path, find, ...)
and a ROOT Path. Line endings are normalised before matching.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

repo, harness = Path(sys.argv[1]), sys.argv[2]
spec = importlib.util.spec_from_file_location("harness", repo / harness)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
cases = list(getattr(h, "CASES", [])) + list(getattr(h, "TEST_CASES", []))
for label, path, find, *_ in cases:
    rel = Path(path).resolve().relative_to(repo.resolve()).as_posix()
    now = Path(path).read_bytes().decode("utf-8").replace("\r\n", "\n")
    head = subprocess.run(["git", "-C", str(repo), "show", f"HEAD:{rel}"],
                          capture_output=True, text=True, encoding="utf-8").stdout
    f = find.replace("\r\n", "\n")
    if f not in now:
        print(f"{'STALE AT HEAD TOO' if f not in head else 'BROKEN BY ME    '}  {label}")
