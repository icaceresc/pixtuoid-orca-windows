# Dungeons & Agents v1.0.1: team banners and a QA of the look

Objective: replace the original Pixtuoid caps that mark a subagent's team with a medieval banner the adventurer carries, QA the rest of the look for what still reads as the original office, and ship it as fork release v1.0.1 and plugin 3.0.1 for the owner's work PC.

status: completed
commits: authorized
coordination: Punky coordinates and reports to the owner (Spanish); the owner chose variant B (hanging banner) and asked for it integrated with the figure.
delegation: none; one worker did the whole mission (claude-sonnet-5-5).
authorized: branches, commits, pushes, PRs and squash merges on icaceresc repos; the fork release v1.0.1; plugin tag v3.0.1; updating the owner's installed plugin to 3.0.1 in dungeon mode.
not authorized: anything on upstream pixtuoid/pixtuoid; classes, monsters or other features; engine changes beyond the marker and the board text.

## Steps
- [x] Research: the cap is a procedural effect (`EffectKind::SubagentCap`), not a sprite, drawn in the classic 1x look, the 4x look and the list portrait; the lead wears no marker; ink = hash of the lead's id
- [x] Variants A pennant, B gonfalon, C shield shown at real size in every pose; owner picked B
- [x] Banner implemented and integrated: pole beside the head's west clear of every hair and helm (pinned per pose), strap at the shoulder, cloth in three ramp steps, iron tip, pack wood; heraldic inks held by contrast and distinctness tests; portrait draws none (one-size rows)
- [x] QA of the look: wood name plates, tooltips and panels with parchment ink, muted source hues, moon for the sleeper's z, carved exclamation for the ?, wall board reads Dungeons & Agents and its star opens the fork (`STAR_URL`); before/after captures reviewed and approved by Punky
- [x] Checks: scene 1521, core 1199 and every other crate pass; clippy `-D warnings` clean; `gen-art --check` and `--selftest` OK under Python 3.14 (457 sprites); release build OK; `pixtuoid` crate per process: only `floating::gpu::tests::gpu_*` (no usable Vulkan device) and `a_job_runs_as_handed_then_reads_the_rows` (finds this machine's real CLIs) fail
- [x] Fork: PR https://github.com/icaceresc/dungeons-and-agents/pull/4 squashed into main at 04df56b79acd4b610e1fcb0740bb96ecd52fc7b9, branch deleted; release https://github.com/icaceresc/dungeons-and-agents/releases/tag/v1.0.1, zip dungeons-and-agents-v1.0.1-x86_64-pc-windows-msvc.zip, 6,473,437 bytes, SHA-256 be69b42c7aa399b5ffecd5f41f185a941324d4a852dd9176bf432a86cc17596f; a public download without auth matched it
- [x] Plugin: PR https://github.com/icaceresc/pixtuoid-orca-windows/pull/14 (pin and SHA-256 moved to v1.0.1, manifest 3.0.1; 109 tests OK, `orca plugin validate` ok, CI green) squashed into main at ade28bcf0e8c5d2de102acf068a764f3df7ddd9a; annotated tag v3.0.1 on it
- [x] Catalog: the community catalog (stablyai/orca-community-plugins, the source of orca.dev) lists icaceresc.pixtuoid-office 3.0.1 at ade28bcf (its bot refreshed at 04:52 UTC); the orca.dev plugin page still showed 3.0.0 at about 05:30 UTC, so the site's own refresh is pending and outside this mission's DONE
- [x] Owner's install: `orca plugin update icaceresc.pixtuoid-office` -> 3.0.1 (nothing new asked); app reinstalled in dungeon mode from the v1.0.1 release (SHA verified); the window opened with the installed app showed a real Codex worker carrying a purple banner; the clone C:\Dev\Personalization\pixtuoid-orca-windows was put back on the pinned v1.0.1 in dungeon mode
- [x] Close: both repos have only main, git clean, no workspaces left

## Proposals for v1.1 (not done)
- Footer: the R/A/I tally hues and the `[p]ause [t]heme` hints still read as the office.
- Light parchment plates with dark ink need per-theme badge plate and inks in the theme model (7 themes).
- Tab panel: red title and `[cc]` brackets keep the terminal look.
- Crash reports, doctor links and the version popup still use `REPO_URL`, the upstream repository from Cargo.toml.
- The coffee machine opens the upstream author's tip jar (`COFFEE_URL`).
