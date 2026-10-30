# The first push, and proving it landed under the right identity

The first publication of a repo is the one irreversible git act. Visibility and
authorship are both permanent from the moment code reaches a hosting URL. This is the
exact order, with the checks that make each step provable rather than assumed.

Everything below is `gh`. Placeholders: `<owner>` the account, `<repo>` the project.

## 0 — Point the shell at the right account

A machine can hold several logins. `gh auth status` shows all of them; only one is
**active**, and `gh repo create` and the git credential helper both silently use the
active one.

```
gh auth status                       # who is logged in, who is active
gh auth switch --user <owner>        # do this even if status already says active
gh api user --jq '{login:.login,id:.id}'
```

The id from `gh api user` must equal the numeric id in the commits'
`<id>+<owner>@users.noreply.github.com` address. Matching the *login* is not enough —
the id is what binds a commit to an account.

If the intended account is absent, `gh auth switch` answers `no accounts matched that
criteria` **with exit code 0**. Read the message, never the exit status. Stop there and
hand the login command to the user; never authenticate on their behalf.

## 1 — Pre-publication scan, before anything is created

Run all of it. A failure here stops the publication; there is no partial push.

```
git log --format='%ae' | sort -u        # authors   — exactly one, the right one
git log --format='%ce' | sort -u        # committers — checked SEPARATELY
git grep -lniE '<other identities>' -- .
git ls-files | grep -iE '(^|/)\.env$|\.pem$|\.key$|id_rsa|credentials'
git ls-files | grep -iE '_private|AGENTS\.md|_sample|\.db$'
git grep -lniE '[A-Z]:\\\\Users\\\\<user>|/home/<user>'   # absolute-path leaks
grep -i '^copyright' LICENSE            # the publishing identity, not a real name
git ls-files | cut -d/ -f1 | sort -u    # what will ship, top level
git ls-files | wc -l                    # the number the remote must match
```

Authors and committers are different fields and a rewrite can fix one and miss the
other, so query both — `%ae` clean while `%ce` still carries the old address publishes
the old address.

The identity grep takes every string that must not be public: other usernames, names,
and **numeric account ids**. An id is as linking as a name and survives a rename.

## 2 — Create, then verify, then push. Never in one step.

```
gh repo create <owner>/<repo> --private --source=. --remote=origin
```

**Do not pass `--push`.** Creation and publication are separated on purpose: visibility
is the one property that cannot be taken back, so it is confirmed from the API before
any object leaves the disk.

```
gh repo view <owner>/<repo> --json isPrivate,owner,name,visibility
git remote -v
```

`isPrivate: true` and the owner login correct — then, and only then:

```
git push -u origin main
git status -sb                       # '## main...origin/main', no ahead/behind
```

## 3 — Verify from the hosting side, not from the local clone

A push reporting success proves the transfer, not the result. Ask the host what it
thinks it received.

```
gh repo view <owner>/<repo> --json name,isPrivate,defaultBranchRef,url

# attribution of EVERY commit, not just the tip
gh api 'repos/<owner>/<repo>/commits?per_page=100' --jq 'length'
gh api 'repos/<owner>/<repo>/commits?per_page=100' \
  --jq '[.[] | select(.author.login != "<owner>")] | length'      # must be 0
gh api 'repos/<owner>/<repo>/commits?per_page=100' \
  --jq '[.[].commit.author.email] | unique'                       # must be one address
```

**Carrying the right email is not the same as being attributed to the account.** The
`commit.author` block is inert git metadata; `author.login` / `author.id` is the host's
resolution of it. An address the account does not own yields `author: null` — the commit
shows as an unknown author forever. Check both blocks.

Checking only the tip commit proves only the tip commit. Query the whole list and count
the non-matching ones.

## 4 — Prove the private side is absent from the remote

```
gh api 'repos/<owner>/<repo>/git/trees/main?recursive=1' --jq '.tree[].path' > remote.txt
grep -iE '_private|AGENTS|_sample|[.]db$|[.]env$|[.]pem$|[.]key$' remote.txt
git ls-files | sort > local.txt
grep -v '/$' remote.txt | sort | comm -3 local.txt -    # only tree entries may differ
```

The remote blob count must equal `git ls-files | wc -l`. The recursive tree also lists
directory entries, which the local list does not — those are the only permitted
difference.

**Backslash escapes break inside a `--jq` expression**: `test("\.db$")` fails with
`invalid escape sequence "\."` because the shell and jq both consume the backslash. Use a
character class — `[.]db$` — or pipe the paths out and grep them, as above.

## 5 — The public surface, which is not the file list

A private repo still exposes metadata through its owner's profile and through anyone
later granted access. Confirm none of it describes the author or the project's origin.

```
gh api repos/<owner>/<repo> \
  --jq '{description,homepage,topics,has_pages,has_wiki,has_issues,fork}'
gh api repos/<owner>/<repo>/collaborators --jq '[.[].login]'
```

Description, homepage and topics stay `null`/empty unless the
user dictates the wording: each is free text that commonly names where a project came
from. Collaborators must be the owner alone.

**Do not add a CI workflow as part of publishing.** Actions minutes on a private repo
are billed against the user's quota; adding one uninvited spends their money on a step they
did not ask for. Propose it separately.

## 6 — The publication is not the deliverable

A push closes a *step*, not the task. The backup chore is finished when the roadmap tick,
the project-memory entry and the version/commit counts are updated too. Report the push,
then name what is still open rather than declaring the chore closed.

## Report shape

URL · private/public · branch · remote commit count · every pre-publication check with
its result · the attribution answer. Flat lines, no prose. The user needs to see which
checks actually ran, because the value of the scan is entirely in it having been run.
