"""Verify a FACTS ledger against the repo it cites.

Usage: python verify_facts_ledger.py <FACTS.md> <repo_root> [--stop-at "## Private"]

Each markdown table row whose first cell starts with 'F' must contain a cell
`path:line` or `path:line-line` followed by a quote cell. Every backticked or
double-quoted fragment (>= 6 chars) of the quote must appear, whitespace
normalised, within +-2 lines of the cited range. Exit 1 if any row misses.
"""
import re, sys

facts, root = sys.argv[1], sys.argv[2].rstrip("/\\") + "/"
stop = sys.argv[sys.argv.index("--stop-at") + 1] if "--stop-at" in sys.argv else None
text = open(facts, encoding="utf-8").read()
if stop and stop in text:
    text = text.split(stop)[0]
norm = lambda s: re.sub(r"\s+", " ", s.replace('\\"', '"')).strip()
src_re = re.compile(r"^([\w./\\-]+):(\d+)(?:-(\d+))?")
rows = bad = 0
for line in text.splitlines():
    if not re.match(r"\|\s*F", line):
        continue
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    idx = next((i for i, c in enumerate(cells) if src_re.match(c.strip("`"))), None)
    if idx is None or idx + 1 >= len(cells):
        print("UNPARSED:", line[:120]); bad += 1; continue
    rows += 1
    m = src_re.match(cells[idx].strip("`"))
    a, b = int(m.group(2)), int(m.group(3) or m.group(2))
    try:
        src = open(root + m.group(1), encoding="utf-8").read().splitlines()
    except OSError as e:
        print(cells[0], "MISSING FILE:", e); bad += 1; continue
    window = norm(" ".join(src[max(0, a - 3):b + 2]))
    quote = cells[idx + 1]
    frags = re.findall(r'[`"]([^`"]{6,})[`"]', quote) or [quote]
    miss = [f for f in frags if norm(f) not in window and norm(f.replace("\\", "")) not in window]
    if miss:
        bad += 1; print(cells[0], cells[idx], "NOT FOUND:", miss[:2])
print(f"{rows} rows checked, {bad} problems")
sys.exit(1 if bad else 0)
