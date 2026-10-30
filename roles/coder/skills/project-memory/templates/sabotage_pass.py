"""Sabotage pass: break each guard SEPARATELY, name what fails.

Copy into the project root, edit TESTS and SABOTAGES, run, then DELETE it.
Throwaway by design — it is a verification instrument, not project code.

Why a script and not an interpreter session: a kernel killed by a timeout
mid-iteration leaves an injected break sitting in the source. Originals are held
in memory and restored in `finally`, twice.

Read alongside references/sabotage-verification.md.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")   # or sys.executable

# Scope to the relevant files while iterating; run the full suite at the end.
TESTS = ["tests/test_the_feature.py"]

TARGETS = [ROOT / "src" / "pkg" / "cli.py", ROOT / "src" / "pkg" / "store.py"]
ORIG = {p: p.read_text(encoding="utf-8") for p in TARGETS}

# (label, file, exact text to find, replacement)
# One guard per entry. Break each guard TWO ways across entries: delete it, and
# make it vacuously true (`if False:`, an off-by-one threshold).
SABOTAGES = [
    ("the last-item guard is removed",
     TARGETS[0], "    if remaining <= 1:", "    if False:"),
    ("the guard is off by one",
     TARGETS[0], "    if remaining <= 1:", "    if remaining <= 0:"),
    ("the plan no longer names the subject",
     TARGETS[0], 'print(f"  id {ref_id}  belongs to  {subject}")',
     'print(f"  id {ref_id}")'),
]


def run() -> list[str]:
    """Tests that did not pass. ERRORS COUNT, and so does a collection crash.

    Counting only `FAILED` lines is how a non-compiling sabotage reads as a
    clean one: every test ERRORs, no line says FAILED, and the report announces
    that nothing broke.
    """
    r = subprocess.run([PY, "-m", "pytest", "-q", "--tb=no", *TESTS],
                       cwd=ROOT, capture_output=True, text=True)
    bad = set(re.findall(r"FAILED \S+::(\S+)", r.stdout))
    bad |= {f"ERROR {n}" for n in re.findall(r"ERROR \S+::(\S+)", r.stdout)}
    if r.returncode not in (0, 1) and not bad:
        bad.add(f"<pytest exited {r.returncode} without naming a test>")
    return sorted(bad)


def main() -> int:
    baseline = run()
    if baseline:
        print("BASELINE IS NOT GREEN:", baseline)
        return 1
    print("baseline: green\n")

    vacuous = []
    try:
        for label, path, old, new in SABOTAGES:
            text = ORIG[path]
            if old not in text:
                print(f"### {label}\n    !!! TEXT NOT FOUND — not applied\n")
                vacuous.append(label)
                continue
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            try:
                fails = run()
            finally:
                path.write_text(ORIG[path], encoding="utf-8")

            print(f"### {label}   [{path.name}]")
            if not fails:
                print("    !!! NOTHING FAILED — the sabotage sabotaged nothing")
                vacuous.append(label)
            for f in fails:
                print(f"    {f}")
            print()
    finally:
        for p, t in ORIG.items():
            p.write_text(t, encoding="utf-8")

    print("all files restored from memory — now check `git status --porcelain`")
    if vacuous:
        print("\nVACUOUS SABOTAGES. Four suspects, in order:")
        print("  1. ordering — the injection reads rows already gone")
        print("  2. the fixture makes two values coincide")
        print("  3. the fixture leaks the value through another channel")
        print("  4. the sabotage did not compile")
        for v in vacuous:
            print("  -", v)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
