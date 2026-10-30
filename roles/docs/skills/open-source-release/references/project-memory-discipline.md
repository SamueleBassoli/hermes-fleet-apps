# Project memory that stays true

For a project built across many sessions, where each session starts with no memory of the
last. The private orientation notes are the handover. A fresh agent trusts them
completely — which is exactly what makes a stale page dangerous: confidence plus
staleness is how a project rots from one wrong sentence.

## Shape

Project-scoped markdown in the ignored private directory, not a profile-wide memory
store. The user can read and edit it, it travels with the repo, and one project's facts
stay out of unrelated work.

```
  _private/notes/
    SCHEMA.md      the rules these notes follow, incl. the update policy
    index.md       catalogue of pages
    log.md         append-only, what changed and why
    concepts/      current-state (READ FIRST), how-it-works, architecture
    decisions/     settled, rejected
    measurements/  the numbers and what produced them
    check.py       the enforcement script
```

One page is the entry point and says: what works, what is broken, what is next, where
the data lives. Point the private agent-instruction file at it as the first thing to
read every session.

Separate `settled` decisions from `rejected` ones. Recording what was turned down, with
the reason, is what stops a later session re-proposing it.

## The roadmap is a fourth file, not a notes page

The notes describe what the thing **is**. They must not carry the step list of what is
left to build — the two answer different questions and rot at different speeds. Keep a
separate private `ROADMAP.md` beside the notes directory:

```
  notes/        what it IS        architecture, settled decisions, measured numbers
  ROADMAP.md    what is LEFT      ordered phases, small steps, ticked as they land
  log.md        what HAPPENED     dated, append-only
```

Have the entry-point page point at the roadmap instead of restating the plan; one list in
one place, or a fresh session trusts whichever copy it opens first. Give it no
frontmatter and keep it out of the index — it is not a wiki page, and a checker that
requires frontmatter and inbound links will otherwise flag it forever.

Every step carries a **Verify** line naming what must be run to call it done; a step with
no Verify line is a wish, not a step. Tick a step only once that line actually passed, and
mark a dropped step as dropped with its reason rather than deleting it, so a later session
does not re-propose it. When a step completes, record in place the things the work forced
— a refactor it required, a non-obvious constraint it exposed — because those are the
reasons the next step's shape is what it is.

## The update policy

A change is not done when the code works. It is done when the notes, the agent
instruction file, and the README all agree with the code.

Updating on new features only is the common half-measure. These also force an update:

| Trigger | Action |
|---|---|
| A better method found | supersede the old page, record why the old one lost |
| The user changes their mind about an implemented choice | supersede, keep **both** reasonings |
| A measurement re-run with different numbers | replace the number everywhere it appears |
| A conclusion turns out wrong | mark superseded, write the correction, leave the wrong reasoning visible |
| A constant or default changes | update the notes **and** the code comment **and** the agent file |

## Supersede, never silently overwrite

1. Old page: `status: superseded`, add `superseded_by:`.
2. New page: add `supersedes:`. Link both ways.
3. State why the old answer lost. "The user changed their mind" is a complete reason.
4. Append to the log.
5. Grep the whole project for the old claim.

The reasoning that was wrong is worth as much as the reasoning that was right — it is
what stops the same idea returning in six months.

**A correction that lands in one file and not the others IS the contradiction.** A fresh
session reads whichever copy it opens first. Sweep for the old number or old claim
across notes, agent file, README, code comments and docstrings before ending the
session.

## Make the rule mechanical

A documentation rule with no detector is a good intention that survives about three
sessions. Write a checker script in the private directory and run it before ending any
session that changed something. Exit 0 = code and docs agree; exit 1 = fix before you
stop.

`scripts/check_docs_template.py` in this skill is a working starting point — copy it in
and fill the CONFIGURE block rather than writing one from scratch.

Worth checking, in rough order of value:

- **Every constant in the config module against every doc that mentions it.** Parse the
  assignments, then for each doc line naming the constant, confirm the current value
  appears on that line. This catches the highest-frequency drift by far.
- **Architecture claims against the source.** If the notes say one module is the only
  one that writes to disk, grep the others for write calls and fail on a hit. If they
  say CPU-only or no-vector-DB, grep for the forbidden provider or import.
- **Cross-link integrity** — broken links, pages missing from the index, pages with
  fewer than two outbound links (an unlinked page is invisible to the next session).
- **Frontmatter completeness**, and that anything marked superseded carries a pointer.
- **Personal data in public files** — real sample filenames, usernames, absolute paths.

## Verify the checker by breaking things

A checker that has only ever printed "all good" is untested. Deliberately introduce each
class of drift it claims to catch, confirm it fires with a useful message, then restore
and confirm it goes quiet:

- change a constant in the code and leave the docs alone
- add a forbidden call or import to a module
- point a link at a page that does not exist

Do the restore in the same command as the break, so an interrupted run cannot leave the
project modified.

**Expect the first real run to find something.** The checks encode rules that were being
followed by hand until then, and hand-following leaks — a genuine finding on run one is
the normal outcome, not a sign the script is too strict.

**A constant's value can share a documented line with unrelated numbers.** A table row
naming the constant alongside its supporting evidence ("raised recall 72.7% to 80.0%")
yields several decimals; require the current value to appear *among* them rather than to
be the only one, or every evidence-bearing row reports a false failure.

**Grow the checker with the architecture it guards.** A rule introduced this session — a
new single-source-of-truth function every caller must use, a new lookup every module must
go through — is only a rule if something fails when it is broken. Add the check in the
same pass that adds the rule, while the mechanism is still in mind.

## Verify before you trust the notes

The standing verify-before-asserting rule applies to these notes too. Do not take a
sentence as true because it is written down here. When a page makes a load-bearing
claim and checking is cheap, check it. When checking is not cheap, say so to the user
rather than building on it.
