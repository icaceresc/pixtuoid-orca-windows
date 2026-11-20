# Pixtuoid 2.0: native Orca plugin and nested agents

Objective: install Pixtuoid as an Orca community plugin (open/close the independent floating
window from Orca commands, safe install/update/uninstall) and show real nested agents
(Orca orchestration workers and provider subagents) as their own characters.

status: completed
commits: authorized
branch: feat/orca-plugin-subagents (merged as 55edb64; release v2.0.0)
delegation: Workers for API research and independent review are authorized when they add net value.
publication: authorized by the Human (merge PR #4, tag v2.0.0, `orca-plugin` topic, orca.dev/plugins).

## Findings
- Orca 1.4.263 exposes nesting only through `orca worktree ps --json`: agent rows carry
  `parentPaneKey` (orchestration parent) and `children` (AgentChildWorkView; kind `agent` is a
  real subagent, `command`/`monitor`/`workflow` are tool work) or `subagents` (hook roster),
  gated by `subagentObservation: live`. `agent list`, `agent show`, `worktree show/list`,
  `status` and the plugin API (`agents.list`, `agent.status.changed`) expose no subagents.
- Pixtuoid v0.23.0 links a child only to a parent of the same source (SubagentStart for
  claude-code/codex, `parentID` for opencode); Antigravity has no parent link. Cross-provider
  children are drawn in the parent's source. In a Claude Code tree a one-line subagent
  transcript ("name card", `attributionAgent`) relabels them with their real provider; Codex and
  OpenCode trees have no label path (issue #5).
- Orca starts plugin workers without APPDATA, which the Orca CLI needs; the worker restores the
  per-user folders.

## Steps
- [x] Research Orca and Pixtuoid subagent interfaces: findings above, verified against v1.4.263 / v0.23.0 sources and live `worktree ps` output
- [x] Hierarchical projection in oficina.py (Agent/Office), stop event, data folder split: 36 unit tests pass
- [x] Plugin manifest and worker (plugin/worker.mjs): `orca plugin validate .` ok, 0 capabilities, dev load approved
- [x] Live validation through the plugin worker commands (install 21 s, open, close, reopen): Claude parent with two simultaneous subagents; short one left first (6 -> 5 characters); cancelled subagent left ~4 s after stop; Codex -> Claude, OpenCode -> Codex and Antigravity -> OpenCode two-level workers (three levels under the Claude root); office matched Orca's 5 live sessions with no ghosts; reopened at saved 960x640 @ 300,200
- [x] Real screenshots: docs/office.png is public (private repo label pixelated); other captures stay local
- [x] READMEs (EN/ES/DE/JA) and CI (Python tests + `node --check` of the worker)
- [x] Independent review of the diff: 2 medium + 5 low findings; fixed M1 (remove-data retry), M2 (re-entry id), L1 (Antigravity-owned subagents), L2/L3 (stop waits for exit, install rollback), L4 (marker only in new/empty folder); L5 (repeated start after a failed hook) accepted; remove-data verified in scratch with and without marker
- [x] Push branch, open PR, CI green: https://github.com/icaceresc/pixtuoid-orca-windows/pull/4
- [x] Palette commands run from Orca's real palette: Close (office-exit:0), Remove Data (data folder removed, marker-guarded), Install (failed first: no APPDATA in the worker; fixed, then 4 sources prepared), Open (office read Orca inside the worker), Close again with final code (0 cards, 0 folders left); geometry backed up and restored
- [x] Real provider names for cross-provider children: Codex and Antigravity workers under a Claude root labelled "codex"/"antigravity" live, same character, no duplicate; Codex/OpenCode trees documented and registered as issue #5
- [x] Second independent review (release delta): no blockers; fixed card I/O resilience, orca_json on odd answers, empty-folder cleanup, cards cleared at close, README root wording
- [x] Merge PR #4 after CI passes on the final commit: squash-merged as 55edb64 after CI success on 959a0fe
- [x] Tag v2.0.0 and add the `orca-plugin` topic: annotated tag v2.0.0 -> 55edb64 pushed; topic set; `gh search repos --topic orca-plugin` lists the repo
- [x] Sync local main; replace the development load with the published plugin; reopen the office: main == origin/main at 55edb64; `orca plugin install icaceresc/pixtuoid-orca-windows` resolved v2.0.0 (55edb64, 0 capabilities); dev folder unloaded; Open from the palette started the office from the published plugin and it read Orca

Pending Human action, outside this mission's DONE: verify the listing page
https://orca.dev/plugins/icaceresc/pixtuoid-orca-windows from another workstation (this one cannot:
Kaspersky Endpoint Security re-signs TLS with a local CA certificate that expired on 2025-12-31,
curl SEC_E_CERT_EXPIRED; TLS verification is not bypassed), when the plugin is resumed. The plugin
is paused from 2026-11-20 (mission JP-PIX-001); launch is from the clone.

Not live-verified: native (non-orchestration) subagents of Codex and OpenCode; a top-level
Antigravity session as parent (covered by unit tests only).
