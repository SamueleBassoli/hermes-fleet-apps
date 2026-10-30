# Guards that enforce themselves

A rules document, a skill and a `CLAUDE.md` are **instructions**: an agent may not
read them, and a script never does. When a rule is load-bearing — a commit signed
with the wrong email ends up public, a dirty commit ends up public — ship it
also as a guard the tool itself enforces.

Full example: a global git hook that refuses a commit signed with the wrong
email for the folder it lives in.

## Installation

A global `core.hooksPath` applies to **every repo, including future ones**, and
to anyone committing from that machine: the owner, you, other Hermes profiles,
Claude Code, any script.

    mkdir -p ~/.config/git-identity-hooks
    # write the pre-commit below
    chmod +x ~/.config/git-identity-hooks/pre-commit
    git config --global core.hooksPath ~/.config/git-identity-hooks

⚠️ `core.hooksPath` **replaces** every repo's `.git/hooks/`: existing local hooks
stop running. Check there are none before enabling it.

## The script

The rule is **per folder, not per project**: a repo moved into a mapped folder
is covered without touching the hook.

```sh
#!/bin/sh
email=$(git config user.email)
name=$(git config user.name)
dir=$(git rev-parse --show-toplevel 2>/dev/null)

die() {
	echo ""
	echo "  COMMIT BLOCKED - wrong email"
	echo "  folder:    $dir"
	echo "  signature: ${name:-<empty>} <${email:-<empty>}>"
	echo "  expected:  $1"
	echo ""
	echo "  Check for a local override that beats the global setting:"
	echo "      git config --local --get-regexp '^user\\.'"
	echo "      git config --local --unset-all user.email"
	echo ""
	exit 1
}

case "$dir" in
	*/GitHub/<user>/*|*/github/<user>/*)
		[ "$email" = "<id>+<user>@users.noreply.github.com" ] \
			|| die "<id>+<user>@users.noreply.github.com" ;;
	*)
		# Outside the mapped folders: fail closed.
		if [ -z "$email" ]; then
			echo "  COMMIT BLOCKED - no email set for: $dir"
			exit 1
		fi ;;
esac

# Addresses that must NEVER appear in a commit.
for banned in <personal-email> <old-email>; do
	case "$email$name" in
		*"$banned"*)
			echo "  COMMIT BLOCKED - banned address: $banned"
			exit 1 ;;
	esac
done
exit 0
```

Upper/lower-case double patterns (`*/GitHub/*|*/github/*`) because the same
folders are written differently on Windows and on Linux.

The error message must say **what is wrong and how to fix it**: the reader is
often an agent that has read no documentation.

## Test it for real

An untested guard is worse than no guard: it gives false confidence. Test **both**
directions, every time.

    # must PASS
    git commit --allow-empty -m test && git reset --hard HEAD~1

    # must BLOCK
    git -c user.email="<old-email>" -c user.name="test" \
        commit --allow-empty -m test

`git -c` is the clean way to try a wrong signature: it writes nothing and leaves
no residue when the hook fails.

## After every edit to the script: `sh -n`

    sh -n ~/.config/git-identity-hooks/pre-commit

A programmatic edit (patch, sed) can join two lines and merge a `;;` into the
next `case` branch: the syntax breaks, the hook exits with an error and **blocks
every commit on the machine**. `sh -n` catches it in a second. This holds for any
script edited by a tool, not only hooks.

## A second environment on the same machine

If git also runs in a second environment with its own `~` (a VM, a container, WSL),
install the guard there too. A copy from Windows carries CRLF line endings, which
make the script unrunnable on Linux: strip them (`sed -i "s/\r$//"`), `chmod +x`,
run `sh -n`, and set `core.hooksPath` in that environment as well.

## What such a guard does NOT cover

The hook blocks commits, not pushes: a repo created under the wrong account still
gets through. Server-side checks remain a separate step.

The guard does not replace the documents — it makes them impossible to bypass.
Both are needed: the document explains why, the guard prevents the mistake.
