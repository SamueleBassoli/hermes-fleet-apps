# Vetting community skill repos

Quick check per repo via the GitHub API. Anonymous quota is ~60 req/h and a
batch of 12 repos exhausts it — run description + tree + README in ONE loop
and fall back to `hermes skills inspect <id>` for hub-listed entries.
If your web tool cannot fetch raw API JSON, use curl.

```bash
r=owner/repo
curl -s https://api.github.com/repos/$r | python -c "import json,sys;d=json.load(sys.stdin);print(d['description'],'| stars',d['stargazers_count'],'| lic',(d.get('license') or {}).get('spdx_id'),'| pushed',d['pushed_at'][:10])"
curl -s "https://api.github.com/repos/$r/git/trees/HEAD?recursive=1" | python -c "import json,sys;t=json.load(sys.stdin)['tree'];print('\n'.join(x['path'] for x in t if x['path'].endswith('SKILL.md')))"
curl -sL https://raw.githubusercontent.com/$r/HEAD/README.md | head -c 2000
```

## Decision table

| finding | verdict |
|---|---|
| no `SKILL.md` anywhere | DROP — app, paper, or tool, not a skill |
| shells out to a paid/cloud CLI (hosted inference) | DROP (local-first) |
| persona repo | DROP — SOUL-level; steal one idea at most |
| overlaps a skill already on that agent | keep one, read both; record the pick in the plan |
| 100+ skills pack | OPEN LATER — only the role folders, when that profile is built |
| no licence file | REF ONLY — read, do not vendor |
| platform mismatch (iOS skill, Android project) | DROP, note where it lives |
| orchestrator / multi-agent desktop app | DROP — overlaps the coordinator |
| a single principles file | not a skill — bake into the seed SOUL |

## Assignment

Split a multi-role repo by sub-skill: spec/tickets/domain-modeling → product;
review/triage/diagnosing → qa; implement/pr/debugging/git → coder;
launch/shipping → docs; diagrams/brand → designer; ffmpeg/motion → media.
Skip the author's self-referential skills (`ask-<author>`, `setup-<author>-skills`,
`in-progress/`). Vendor via git clone + copy `skills/<name>/` only — never
`npx skills add`, which writes to Claude Code/Codex dirs, not Hermes.

## Report shape

One screen: ✅ take (with per-agent split) / ❌ overlaps (name the winner) /
❌ off-role. One line of reason each. Then "recorded in the plan" and stop.
