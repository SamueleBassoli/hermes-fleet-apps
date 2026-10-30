# Rewriting a CLI tool's README around its window

When a CLI tool gains a desktop window, the README's readers become people with the
problem the tool solves, not terminal users. The README is restructured around the window,
and the command line moves to its own page. Nothing is deleted, only moved.

## Shape

```
README.md (short)            docs/cli.md (depth)
  name and one line            intro: same data, same rules, same undo
  problem it solves            the steps WITH commands (verbatim from the old README)
  what it will not do          Commands table
  Install (window extra +      For scripts and agents (--json)
    how to open it)            Letting an assistant drive it
  Use = steps in the window    Privacy, from the command line
    + one line linking cli.md
  How it decides
  Privacy (window actions)
  Licence
```

The link line sits at the top of Use ("Prefer the command line, or letting an assistant
drive it?" -> docs/cli.md). Links run both ways; check the anchors match the GitHub slugs
of the real headings.

## Procedure

1. Map the window before writing a word: read the Api class the page calls and grep the
   page for button, tab and label texts. Those texts are the README's words: quote the
   window's own labels, never paraphrase.
2. For every old step, mark it window / CLI / both from that map. A step the window cannot
   do stays a command with a link, labelled "command line only for now". Never describe a
   window step the code does not have.
3. Split with a script, not by hand: cut the CLI sections verbatim by heading into
   docs/cli.md, then write the new README sections.
4. Prove nothing was lost: every non-blank line of the old README appears in the new README
   or cli.md; list the misses and confirm each was rewritten on purpose.
5. Gate (tests + project checks), render the whole README as GitHub would and look at it
   (below), then show the owner.
6. Report a step table: step | window | command line, plus the CLI-only list. It is also
   the to-do list for the window.
7. Commit separately from any art or logo work.

## Render the full README before commit

An unpushed repo cannot be previewed on GitHub. One-shot, nothing installed:
`uv run --no-project --with markdown==<pinned> python render.py`, where render.py runs
`markdown.markdown(text, extensions=["tables", "fenced_code"])`, rewrites relative image
paths to `file:///` URIs and wraps it in GitHub-like CSS. Screenshot with headless Chrome
(`--allow-file-access-from-files`), look at it, save the PNG outside the repo's public
tree and give the owner the path, saying it is a local GitHub-styled render.

## Pitfall

Run gates through the terminal tool, not a `bash` subprocess from a code-execution tool: on
Windows that `bash` can resolve to WSL, where the Windows paths and the venv do not exist,
and the errors look like a broken project.
