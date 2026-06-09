# Codex Workflow For This Repo

This repo uses small repo-scoped skills instead of an enterprise agent framework.

## Why This Shape

Current Codex guidance supports:

- `AGENTS.md` for durable repository instructions.
- `.agents/skills/<name>/SKILL.md` for reusable task workflows.
- subagents for explicitly requested parallel work.
- sandbox/approval boundaries for network, filesystem, and secret-sensitive actions.

So this project uses:

- one root `AGENTS.md`
- five role skills under `.agents/skills`
- docs for requirements and cloud setup
- conservative project settings

## Practical Role Flow

For new work:

1. `$TVU_User` clarifies what users need from the corpus or chat agent.
2. `$TVU_Architect` decides the smallest safe phase and data contract.
3. `$TVU_Developer` implements the change.
4. `$TVU_Tester` validates fixtures, extraction quality, and acceptance criteria.
5. `$TVU_Security_Analyser` checks crawl scope, secrets, IAM, and cost risk.

For small coding tasks, use only `$TVU_Developer` and `$TVU_Tester`.

For cloud setup or scraping expansion, include `$TVU_Architect` and `$TVU_Security_Analyser`.

For retrieval quality or Tamil answer behavior, include `$TVU_User`.

## Parallel Agents

Use parallel subagents only when explicitly requested. Good split:

- architect: scope and design risks
- developer: implementation plan/diff
- tester: acceptance checks and fixture strategy
- security: permissions, secrets, crawl safety
- user: Tamil use cases and answer quality

The main thread should receive summaries, not raw logs.

## Sources Used

- OpenAI Codex manual, sections: Agent Skills, Custom instructions with `AGENTS.md`, Agent approvals & security, Sandbox, Subagents, Hooks.
- [Introducing Codex](https://openai.com/index/introducing-codex/) for the cloud-agent and parallel-tasking direction.
- [Codex is now generally available](https://openai.com/index/codex-now-generally-available/) for the current multi-surface Codex shape.
- [Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/) for the agent loop and harness framing.
- [How OpenAI uses Codex](https://cdn.openai.com/pdf/6a2631dc-783e-479b-b1a4-af0cfbd38630/how-openai-uses-codex.pdf) for practical patterns: code understanding, refactoring, tests, staying in flow, exploration, and `AGENTS.md` as persistent repo context.
