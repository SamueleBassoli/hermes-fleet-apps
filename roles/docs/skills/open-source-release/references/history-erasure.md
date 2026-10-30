# Erasing something from a history that has already been pushed

Applies when content — a leaked address, a wording the user rejects, a real path — is
already in commits that exist on a hosting service. The local side is easy; the hosting
side is where the wrong mental model costs a publication.

## The rule that decides everything

**A force-push unlinks commits from a branch. It does not delete them from the host.**
GitHub keeps the objects and continues to serve them by direct SHA: the commit no longer
appears in the branch's history list, and
`gh api repos/<owner>/<repo>/commits/<old-sha>` still returns it in full. Making that
repo public makes those orphaned commits publicly fetchable by anyone holding the sha.

So there are exactly two outcomes, and they are not the same:

```
  rewrite + force-push   →  hidden from the branch, still readable by sha
  delete the repository  →  object store gone, sha returns 404/422
```

**Never report an erasure as done on the strength of the force-push.** Fetch an old sha
from the host afterwards and read what comes back. That single call is the difference
between "cleaned" and "still there".

```
gh api repos/<owner>/<repo>/commits/<old-full-sha> --jq '.sha'
gh api 'repos/<owner>/<repo>/contents/<file>?ref=<old-full-sha>' --jq '.content' \
  | base64 -d | sed -n '<lines>p'        # the actual content, not just reachability
```

Run it BEFORE the destructive step as well. Proving the content is still readable is
what justifies deleting the repository; assuming it is turns a reversible situation into
an unnecessary delete.

## Scope the fix to the whole history, not the quoted line

A sentence introduced in the first commit lives in every commit after it. Locate every
commit that carries the string before choosing a method — the answer changes the method:

```
git log --format='%h' --all -S'<string>' -- <file>      # commits that added/removed it
git grep -lniE '<pattern>' $(git rev-list --all) -- .    # every commit still carrying it
git log --all --pretty=format: --name-only --diff-filter=A | sort -u   # files that ever existed
```

`git grep` over `git rev-list --all` is the history-wide search; a grep of the working
tree answers a different question and will report clean while 27 commits carry the
string. Use the same two commands to audit for identity leaks and for private files that
may have been committed once and removed.

## The three options, and the one the user must choose

Put the cost of each in front of the user and let them pick. This is their call, not an
engineering optimum.

| Option | What it costs |
|---|---|
| Scrub the string from every commit (`git-filter-repo`) | every hash changes again; history survives |
| Squash everything to one commit | `git blame` and `git bisect` answer nothing about anything written before today; a "0.1.0 plus N commits" version convention collapses; a mature tree with one commit reads as dumped code |
| Leave it | fine while private with no forks; unfixable once public |

State the blame/bisect loss explicitly — the agent is the party that loses most by it,
and a non-developer cannot be expected to know that a squash is what makes "when did this
line appear, and why" unanswerable. Then do what they choose without relitigating.

`git-filter-repo` is not bundled with git; `uvx git-filter-repo` runs it without
installing anything.

## Squash to a single commit, safely

```
cp -r <repo> "$TMPDIR/<name>-prebackup-$(date +%Y%m%d-%H%M%S)"   # whole folder, .git included
cd <repo>
git checkout --orphan <tmp-branch>     # no parent, so no history is inherited
git add -A
git commit -m "<project> <version> — <what it does>"
git branch -D main && git branch -m main
diff -r --exclude=.git . "$BACKUP"     # MUST print nothing
```

**Prove the tree survived before pushing.** `diff -r --exclude=.git` against the backup
is the only evidence that a squash moved zero bytes of content; the commit succeeding
proves nothing about what it contains. The backup keeps the old `.git` too, which is the
only remaining copy of the discarded history — tell the user its path and that a scratch
directory is pruned on a timer, so they can move it if they want the record.

## Purge the local side too, or the string is still on the user's disk

The orphaned commits stay reachable locally through the reflog **and through the
`origin/<branch>` remote-tracking ref**, so a local grep over `--all` still finds them
after the rewrite. After the remote is settled:

```
git reflog expire --expire=now --all
git gc --prune=now
git rev-list --all | wc -l                               # expect the new count
git grep -lniE '<pattern>' $(git rev-list --all) -- .     # expect nothing
git fsck --unreachable                                   # expect nothing
```

## Delete and recreate, when the objects must actually go

Cheapest while the repo is private with no forks, no collaborators, no issues and no
other clones — the local repo is then the sole source of truth and nothing is at risk.
After it has been public or forked, deleting achieves nothing: every fork holds a full
copy.

The default `gh` token deliberately lacks the scope. `gh repo delete` answers
`HTTP 403: Must have admin rights` **and exits 0**, so read the message.

```
gh auth refresh -h github.com -s delete_repo     # the USER runs this; browser approval
gh auth status | grep -i 'token scopes'          # confirm delete_repo on the right account
gh repo delete <owner>/<repo> --yes
gh repo view <owner>/<repo> --json name          # expect: could not resolve
git remote remove origin                         # stale remote survives the delete
```

Then recreate and push exactly as in `first-push-verification.md`, and close with the
proof:

```
for s in <old-sha> <old-sha> ; do gh api repos/<owner>/<repo>/commits/$s --jq '.sha' ; done
# every one must answer 422 "No commit found for SHA"
```

## The browser decides which account gets the scope

`gh auth login` and `gh auth refresh` authorise whichever account the **browser** is
signed into, not the one named on the command line. On a machine holding several
accounts this silently puts the token — or the new scope — on the wrong account.
Tell the user to approve in a private window signed into the
publishing account only, and confirm afterwards with `gh api user --jq '.id'` against
the numeric id in the commit address.

Never read, type, or ask for the device code. Hand over the command and wait.
