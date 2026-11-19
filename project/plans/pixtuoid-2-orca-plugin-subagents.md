# Pixtuoid 2.0: native Orca plugin and nested agents

Objective: install Pixtuoid as an Orca community plugin (open/close the independent floating
window from Orca commands, safe install/update/uninstall) and show real nested agents
(Orca orchestration workers and provider subagents) as their own characters.

status: active
commits: authorized
branch: feat/orca-plugin-subagents
delegation: Workers for API research and independent review are authorized when they add net value.

## Findings
- Orca 1.4.263 exposes nesting only through `orca worktree ps --json`: agent rows carry
  `parentPaneKey` (orchestration parent) and `children` (AgentChildWorkView; kind `agent` is a
  real subagent, `command`/`monitor`/`workflow` are tool work) or `subagents` (hook roster),
  gated by `subagentObservation: live`. `agent list`, `agent show`, `worktree show/list`,
  `status` and the plugin API (`agents.list`, `agent.status.changed`) expose no subagents.
- Pixtuoid v0.23.0 links a child only to a parent of the same source (SubagentStart for
  claude-code/codex, `parentID` for opencode); Antigravity has no parent link. Cross-provider
  children are drawn in the parent's source (correct tree and cap, parent's provider label).

## Steps
- [x] Research Orca and Pixtuoid subagent interfaces: findings above, verified against v1.4.263 / v0.23.0 sources and live `worktree ps` output
- [x] Hierarchical projection in oficina.py (Agent/Office), stop event, data folder split: 27 unit tests pass
- [x] Plugin manifest and worker (plugin/worker.mjs): `orca plugin validate .` ok, 0 capabilities, dev load approved
- [x] Live validation through the plugin worker commands (install 21 s, open, close, reopen): Claude parent with two simultaneous subagents; short one left first (6 -> 5 characters); cancelled subagent left ~4 s after stop; Codex -> Claude, OpenCode -> Codex two-level workers; office matched Orca's 5 live sessions with no ghosts; reopened at saved 960x640 @ 300,200
- [x] Real screenshots of parents and children (local, not committed: they show private folder names)
- [x] READMEs (EN/ES/DE/JA) and CI (Python tests + `node --check` of the worker)
- [ ] Independent review of the diff
- [ ] Push branch, open PR, CI green
- [ ] Palette commands run by the Human inside Orca (no CLI runs palette commands; GUI driving was stopped to avoid typing into the Human's draft)

Open, outside this mission's DONE: merge to main, then tag `v2.0.0` and add the `orca-plugin` topic
for orca.dev/plugins (Human decision; listing publishes under the owner's GitHub identity).
Not live-verified: native (non-orchestration) subagents of Codex and OpenCode; Antigravity as a
parent (its level-1 worker never dispatched its child).
