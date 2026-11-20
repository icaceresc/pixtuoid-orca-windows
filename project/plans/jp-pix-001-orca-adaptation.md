# JP-PIX-001: Pixtuoid fully adapted to Orca

Objective: every local Orca agent identifiable in the office (provider, role, parent, project),
every native Pixtuoid feature fed wherever Orca supplies the data, no PC freeze under real load,
and current with both upstreams plus an automatic Pixtuoid release check. Launch stays from the
clone; the Orca plugin is paused (not extended, still valid).

status: completed
commits: authorized
branch: feat/jp-pix-001-orca-adaptation (one PR to main; merge, tag and release stay with the Human)
delegation: Workers chosen by routing (any provider, model, effort) for research and independent review; temporary test agents in Orca, closed by their own handle.

## Findings

Performance (measured on the Human's PC, 12 logical CPUs, the office launched inside a Job
Object that accounts for every process it starts; 120 s windows; script kept in scratch):

| Metric | Before (f613b8d) | After |
|---|---|---|
| Office CPU time per 120 s | 75.6 s | 45.4 s (37.4 s on a second run) |
| Processes started per 120 s | 180 | 94 |
| Launch to Pixtuoid ready | 6.0 s | 2.3 s (1.4 to 3.7 s over runs) |
| Launch to first agent | 13.0 s | 5.3 s (3.4 to 7.7 s) |
| Peak memory of the office | 425 MB | 401 MB |

- Cause: every `orca` CLI call starts an Electron/Node runtime (~1 s CPU, 1 to 18 s wall under
  load); the bridge made two per 1.25 s cycle at normal priority, so a CLI ran almost nonstop,
  and the 10 s timeout killed slow reads under load only to start them again. Orca's own app
  spends only ~0.03 to 0.1 s per request. Killing the launcher also ends its Node child (no orphans).
- Fix: one `orca worktree ps` per cycle (it carries provider, state, tool, parent pane and
  children; `agent list` only when `ps` fails, is truncated or lacks provider/state), wait
  max(1.5 s, 2 x last read) capped at 10 s, 30 s timeout, everything below normal priority,
  `_pid` passed to the hook so it skips its process-table walk, `orca-slow-read` logged above 5 s.
- Remaining office CPU: Pixtuoid's own rendering ~7.5 s and the bridge ~0.5 s per 120 s; the rest
  is CLI reads (duty at most ~1/3, below normal priority).

Orca 1.4.266: `worktree ps` agent rows carry `agentType`, `state`, `toolName` (name only),
`workingMode`, `mainAgent`, `interrupted`, `paneKey`/`parentPaneKey`, `children`,
`subagentObservation`, plus prompt/reply/tool-input text that the office never reads or forwards.
No model, effort, token usage or agent process id anywhere in `ps`, `agent list` or `agent show`.
No streaming/watch command exists in the CLI.

Pixtuoid v0.23.0 (source read at the tag; inventory by a Worker, key points re-verified):
names are the source prefix, a middle dot and the cwd basename; `agent_type` is never shown; only Claude Code has a
relabel path (`attributionAgent`); Codex children showed no work (their PreToolUse is pending
only); Antigravity has no end hook (only the `_pid` exit watch); a silent agent is swept after
5 to 60 min while Orca may still list it; focus-on-click works on Windows only for Antigravity.

Feature matrix (W works, L works with limitation, X impossible: Orca does not expose the data):

| Pixtuoid feature | Status | Evidence |
|---|---|---|
| One character per agent, 4 providers | W | live 1.4.266 (Claude Code, Codex, Antigravity); harness all 4; OpenCode live blocked by its usage limit |
| Parent link, team cap, `Tab` tree, "under" tooltip | L | live + dashboard capture; Antigravity cannot parent (Pixtuoid) -> `worker of antigravity` |
| Provider, role, project in the name | L | live labels (`cc·WORKSPACE · orchestrator`, `cx·worker · jp-pix-001`, `ag·worker · ...`, `cc·Explore subagent · ...`); desk badge shows ~10 chars; role fixed at first sight |
| Issue #5: provider of a cross-provider child in Codex/OpenCode trees | L | harness: `cx·claude worker · api`, `oc·claude worker · ...`; prefix and badge color stay the parent's (Pixtuoid has no relabel path for codex/opencode) |
| Working at the desk (incl. Codex children) | W | harness `cx·worker · web-app` running; live |
| Tool name on monitor, tooltip, footer tally, call counter | L | live `running(Bash)`, `running(shell)`, `running(execute)`; subagents get no tool name from Orca; tools shorter than a poll are missed |
| Monitor glow per tool kind | W | follows the real tool name (Edit/Read/Bash/Search) |
| Delegating pose | L | Orca's `Agent` tool is shown as `Orca: Agent`; Pixtuoid's Task pose ends children on its own clock, which would remove Orca workers early |
| Requires action (`!`, need-you count) | W | harness all 4 (`requires_action`); no live prompt observed |
| Idle / rest / wander / chitchat | W | live and harness |
| Leaving, subtree first | W | live: Codex and Antigravity workers left 0 to 6 s after Orca closed them; subagent left when done |
| Stays while Orca lists it (stale sweep) | W | heartbeat: harness idle 414 s kept Codex/OpenCode (control without it: 2 swept), busy 691 s kept all 3 |
| Model and effort tooltip | X | Orca exposes no model/effort per agent |
| Token meter, usage, today counter | X | Orca exposes no token usage |
| Click to focus the agent's terminal | X | Orca exposes no agent process; Pixtuoid's Windows probes cover only its own Antigravity hooks |
| Session age, running meter, label disambiguation | W | computed by Pixtuoid from the fed states |
| Orca version notice | W | unit tests (newer, same, older, once per version) |
| Native controls (move, resize, zoom, close) | W | live in v2.0.0; unchanged |
| `Tab` dashboard | W | capture docs/office-dashboard.png |
| `?` help, `P` pause, `T` theme, `M` sound, `S` sources, `V` version | L | Pixtuoid-native, independent of the connector; not exercised in this mission (posted key messages do not drive them) |
| Weather, day/night, pets, holidays, sound band and door chime | W | Pixtuoid-native, driven by the fed states; sound starts muted |
| Remote `serve`/`pair` | not used | would stream labels to other devices; outside the adapter |
| Demo mode, compaction, error state | n/a | not in Pixtuoid v0.23.0 |

Updates: Pixtuoid v0.23.0 is the latest stable release (2026-11-13); the pinned SHA-256 equals
the digest GitHub publishes for the asset. The repository does not let Actions create pull
requests (`can_approve_pull_request_reviews: false`); the release workflow then opens an issue
with the compare link. Allowing Actions to open pull requests is a repository setting for the Human.

## Steps
- [x] Close the previous mission plan: status completed; orca.dev check moved to prose as a pending Human action
- [x] Diagnosis: inventory scratch report by a Claude Worker (a first Codex attempt failed on API access); Orca 1.4.266 fields above; baseline measured
- [x] Performance: one read per cycle, adaptive wait, below normal priority; after-numbers above with the same method
- [x] Identification: role, provider and project in each name; issue #5 resolved as far as Pixtuoid allows; harness + live
- [x] Native features fed where Orca supplies the data: tool names, Codex child work, Antigravity leave, heartbeat; matrix above
- [x] Updates: pin verified against GitHub's digest; Orca 1.4.266 verified live; release workflow and bump script with fixture tests; Orca version notice
- [x] READMEs EN/ES/DE/JA rewritten together; structure parity checked by script
- [x] Live validation in Orca: the dispatching orchestrator, this Claude worker, Codex and Antigravity test workers, native Explore subagent; OpenCode test agent stopped by its usage limit
- [x] Independent review of the final diff by another Worker (Codex, high effort): no blocker; fixed both medium findings (PR and dry runs now run in a read-only job; a subagent's `name` never stands in for its type) and the low one (placeholder used only when the kill-on-close job holds it, else none); 58 tests pass
- [x] Push, PR to main, CI green (including the release workflow's dry run): https://github.com/icaceresc/pixtuoid-orca-windows/pull/7; unit (58 tests) and read-only dry-run jobs pass, release job skipped on pull requests; mergeable

Pending Human actions, outside this mission's DONE:
- Review and merge PR #7 (merge, tag and release are the Human's decisions).
- Optional: allow GitHub Actions to create pull requests (Settings, Actions, General) so the
  release check opens a pull request instead of an issue with the compare link.
- Decide whether issue #5 closes with this change (provider now in the child's name; the prefix
  and badge color cannot change without modifying Pixtuoid).
- Check OpenCode live on Orca 1.4.266 once its usage limit allows; it is covered by unit tests
  and the real Pixtuoid harness.
- From the previous mission: verify the orca.dev listing page from another workstation when the
  plugin is resumed.
