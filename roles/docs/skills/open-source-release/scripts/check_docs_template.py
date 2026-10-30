#!/usr/bin/env python3
"""Project notes consistency checker — TEMPLATE.

Copy into the project's private notes directory (e.g. `_private/notes/check.py`)
and adjust the CONFIGURE block. Run before ending any session that changed
something:

    python _private/notes/check.py

Exit 0 = code and docs agree. Exit 1 = fix before you stop.

Catches the failure mode that rots a multi-session project: the code says one
thing, the notes say another, and a fresh agent trusts whichever it reads first.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# ============================== CONFIGURE ===================================

ROOT = Path(__file__).resolve().parents[2]      # project root from notes/check.py
NOTES = ROOT / "_private" / "notes"             # the private notes directory
CONFIG = ROOT / "src" / "<package>" / "config.py"   # module holding constants
SRC = ROOT / "src"                              # source tree to police

# Public + private docs that may quote a constant. All are kept in agreement.
DOC_FILES = [ROOT / "AGENTS.md", ROOT / "README.md"]

# Claims the notes make that the source must keep true:
#   (claim as written in the notes, file to check, regex that must be present)
CODE_CLAIMS: list[tuple[str, Path, str]] = [
    # ("actions.py is the only module that writes to disk",
    #  SRC / "<package>" / "actions.py", r"shutil\.move"),
]

# Things the notes forbid. A hit anywhere in SRC fails the run.
FORBIDDEN_IN_CODE: list[tuple[str, str]] = [
    # (r"CUDAExecutionProvider", "GPU provider found — notes say CPU only"),
    # (r"chromadb|qdrant|faiss", "vector DB import — notes say SQLite+numpy"),
]

# Enforce a single-writer module, if the architecture claims one.
SINGLE_WRITER: str | None = None                # e.g. "actions.py", or None
WRITE_CALLS = re.compile(
    r"shutil\.(move|copy|copy2|rmtree)|\.rename\(|\.unlink\(|\.rmdir\(|\.write_text\("
)

# Identifier shapes of real personal source material that must never reach a
# doc. Extend with the prefixes the project's own sample data actually used.
PERSONAL_DATA_PATTERNS = [
    r"\bFB_IMG_\d{10,}\b",        # platform export prefix
    r"\bIMG_\d{8}_\d{6}\b",       # camera filename
    r"[A-Za-z]:\\\\Users\\\\[A-Za-z]",  # absolute Windows user path
    r"/home/[a-z][a-z0-9_-]*/",   # absolute Linux home path
]

REQUIRED_FRONTMATTER = ["title", "created", "updated", "type", "tags", "status"]
MIN_OUTBOUND_LINKS = 2

# ============================================================================

problems: list[str] = []
checked = 0


def fail(msg: str) -> None:
    problems.append(msg)


def note_pages() -> list[Path]:
    return sorted(
        p for p in NOTES.rglob("*.md")
        if p.name not in {"index.md", "log.md", "SCHEMA.md"}
    )


def all_docs() -> dict[Path, str]:
    out: dict[Path, str] = {}
    for p in list(NOTES.rglob("*.md")) + DOC_FILES:
        if p.exists():
            out[p] = p.read_text(encoding="utf-8")
    return out


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


# --- 1. constants in code must match constants in every doc -----------------

def check_constants() -> None:
    """Highest-value check by far: this is where drift happens most."""
    global checked
    if not CONFIG.exists():
        fail(f"config module not found at {rel(CONFIG)}")
        return
    consts = dict(
        re.findall(r"^([A-Z_]{2,})\s*=\s*([0-9]+\.?[0-9]*)", 
                   CONFIG.read_text(encoding="utf-8"), re.MULTILINE)
    )
    if not consts:
        fail("no constants parsed from the config module — restructured?")
        return

    for path, text in all_docs().items():
        for name, value in consts.items():
            if name not in text:
                continue
            checked += 1
            for line in text.splitlines():
                if name in line and re.search(r"[0-9]+\.[0-9]+", line):
                    nums = re.findall(r"[0-9]+\.[0-9]+", line)
                    if value not in nums:
                        fail(f"{rel(path)}: {name} documented as {nums} "
                             f"but config says {value}")


# --- 2. architecture claims must still hold ---------------------------------

def check_claims() -> None:
    global checked
    for claim, path, pattern in CODE_CLAIMS:
        checked += 1
        if not path.exists():
            fail(f"claim '{claim}': {rel(path)} is missing")
        elif not re.search(pattern, path.read_text(encoding="utf-8")):
            fail(f"claim no longer holds: '{claim}' (looked in {path.name})")

    for src in SRC.rglob("*.py"):
        text = src.read_text(encoding="utf-8")
        for pattern, msg in FORBIDDEN_IN_CODE:
            checked += 1
            if re.search(pattern, text, re.IGNORECASE):
                fail(f"{rel(src)}: {msg}")

    if SINGLE_WRITER:
        for src in SRC.rglob("*.py"):
            checked += 1
            if src.name == SINGLE_WRITER:
                continue
            for i, line in enumerate(text_lines(src), 1):
                if WRITE_CALLS.search(line) and not line.strip().startswith("#"):
                    fail(f"{rel(src)}:{i} writes to the filesystem outside "
                         f"{SINGLE_WRITER} — violates the architecture rule")


def text_lines(p: Path) -> list[str]:
    return p.read_text(encoding="utf-8").splitlines()


# --- 3. notes hygiene --------------------------------------------------------

def check_notes() -> None:
    global checked
    pages = note_pages()
    if not pages:
        fail(f"no note pages found under {rel(NOTES)}")
        return
    slugs = {p.stem for p in pages}
    index_path = NOTES / "index.md"
    index = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    if not index:
        fail(f"{rel(index_path)} missing or empty")

    for p in pages:
        text = p.read_text(encoding="utf-8")

        checked += 1
        if not text.startswith("---"):
            fail(f"{rel(p)}: missing frontmatter")
            continue
        fm = text.split("---", 2)[1]
        for field in REQUIRED_FRONTMATTER:
            if f"{field}:" not in fm:
                fail(f"{rel(p)}: frontmatter missing '{field}'")

        checked += 1
        if "status: superseded" in fm and "superseded_by:" not in fm:
            fail(f"{rel(p)}: superseded but no 'superseded_by:' pointer")

        links = set(re.findall(r"\[\[([^\]]+)\]\]", text))
        for link in links:
            checked += 1
            if link not in slugs:
                fail(f"{rel(p)}: broken link [[{link}]]")

        checked += 1
        if len(links) < MIN_OUTBOUND_LINKS:
            fail(f"{rel(p)}: fewer than {MIN_OUTBOUND_LINKS} outbound links "
                 f"({len(links)}) — an unlinked page is invisible")

        checked += 1
        if f"[[{p.stem}]]" not in index:
            fail(f"{rel(p)}: not listed in index.md")


# --- 4. personal data must not reach any doc --------------------------------

def check_no_personal_data() -> None:
    global checked
    for path, text in all_docs().items():
        for pattern in PERSONAL_DATA_PATTERNS:
            checked += 1
            hit = re.search(pattern, text)
            if hit:
                fail(f"{rel(path)}: personal data pattern found "
                     f"({hit.group(0)[:40]!r})")


def main() -> int:
    check_constants()
    check_claims()
    check_notes()
    check_no_personal_data()

    if problems:
        print(f"DOCS INCONSISTENT — {len(problems)} problem(s), "
              f"{checked} checks run\n")
        for p in problems:
            print(f"  ! {p}")
        print("\nFix these, or the next session will build on a false claim.")
        return 1

    print(f"docs consistent — {checked} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
