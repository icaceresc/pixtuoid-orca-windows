# Pixtuoid dark fantasy, as an Orca plugin

Objective: an original dark fantasy campaign rework of the Pixtuoid office (adventurer classes fighting monsters in dungeon floors, resting in a camp on floor 0), built from the owner's fork and delivered through a revived Orca plugin that is more integrated with Orca than upstream Pixtuoid.

status: active
commits: authorized
coordination: Punky coordinates this mission's Orchestrator and reports to the owner (Spanish).
delegation: the Orchestrator dispatches Orca workers and chooses their models and effort.
authorized: install Rust toolchain and MSVC Build Tools; fork pixtuoid/pixtuoid into icaceresc; branches, commits, pushes and PRs on icaceresc repos only.
not authorized: issues or PRs on pixtuoid/pixtuoid upstream; merge; release; repo rename; touching the running install at C:\Dev\Personalization\pixtuoid-orca-windows.
gates: owner approves the campaign vertical slice before the full rework; owner approves the full rework and the integration ideas before the plugin.
originality: original designs only; nothing from Dark Souls, Berserk, D&D / Baldur's Gate 3 or Tolkien in names, characters, logos, art or UI (generic monsters such as orc, goblin, skeleton are fine).

## Layout
- Fork: https://github.com/icaceresc/pixtuoid, clone C:\Dev\Personalization\pixtuoid (remote `upstream` = pixtuoid/pixtuoid, `gh` default repo = the fork), Orca repo id b86f3755-0b74-4dde-93e0-6f2d7bcbf74b.
- Base branch `dark-fantasy` in the fork = upstream tag v0.23.0 (a89eebac), the version this adapter pins. Fantasy work branches from it and PRs target it.
- Release build: `cargo build --release --locked -p pixtuoid --bin pixtuoid -p pixtuoid-hook --bin pixtuoid-hook` (release-plz.yml), toolchain 1.99.1 (rust-toolchain.toml).

## Steps
- [x] Fork created and cloned, upstream remote and tags fetched, registered in Orca: icaceresc/pixtuoid, parent pixtuoid/pixtuoid
- [x] Phase 1: Rust toolchain and MSVC Build Tools installed: rustup 1.29.3, rustc/cargo 1.99.1, VS Build Tools 17.14 VCTools (winget, no UAC prompt)
- [x] Phase 1: upstream v0.23.0 builds on Windows from the fork: release build 4m48s, `pixtuoid 0.23.0`, pixtuoid-scene tests 1493 passed
- [x] Phase 1: adapter option to install a local or owner-released binary: `instalar.py --local | --url --sha256 | --pinned`, app/origen.json, tests 58 -> 78, CI green, PR https://github.com/icaceresc/pixtuoid-orca-windows/pull/9 (open, not merged)
- [x] Phase 1: the built pixtuoid.exe runs the office through the adapter: `instalar.py --local <fork>/target/release` in the PR #9 workspace, office opened and read 7 live Orca agents, then stopped with `oficina.py --stop`
- [x] Phase 2: dark fantasy theme, palette pass and one knight in the fork, built and running: fork PR https://github.com/icaceresc/pixtuoid/pull/1 (fantasy/prototype @ 931f106e, base dark-fantasy, open, not merged; theme id `dark-fantasy`, default; 21 material colours retuned; every agent a knight: tabard in B, mail, `knight_helm` with H plume); pixtuoid-scene 1493 passed, clippy clean, gen-art --check ok; installed with `instalar.py --local` and the real office showed 3 live Orca agents as knights; screenshots in this workspace's scratch/shots (fase2-oficina-fantasia.png, fase2-caballeros-primer-plano.png, untracked)
- [x] Phase 2: report sent to Punky with screenshot paths
- [x] Phase 2: owner's review of the look (2026-11-20): not approved as planned; the owner redirected the mission to a fantasy campaign (below). The knights are reused.

## Direction change (2026-11-20): fantasy campaign
Agents are adventurers of four original classes (mage, knight, ranger, berserker) who fight generic monsters (orcs, goblins, spiders, skeletons) instead of working in an office. Floor 0 is a camp (campfire, tents, bedrolls) where idle or finished agents rest; floors 1..N are dungeon levels where working agents fight. Pets: an original owlbear (owl and bear mix), a raven and a wolf. Hard constraint: nothing from BG3, Tolkien or Berserk in names, characters, logos, art or UI; only the genre. Proposed Orca mapping (to validate): working = combat with a class attack instead of typing; current tool = the combat action; waiting/blocked = horn or banner with `!`; idle/done = camp; arrive/leave = camp road, elevator = dungeon stairs; orchestrator + workers + subagents = a party (leader, members, familiars), team colour kept.

- [x] Campaign 1: feasibility map: project/plans/pixtuoid-campaign-feasibility.md (studied on fantasy/prototype @ 931f106e): art only ~25 items mostly M (stand-ins on existing canvases: desk = monster lair or bedroll, phone_booth = tent, side_table/floor_lamp = campfire/torch, door = stairs, cat = owlbear, dog = wolf); engine ~25 agent-hours (B1 role packs, B2 campaign seating, B3 camp layout, B4 per-role look, B5 class attack); not worth it: new furniture kinds, camp generator, per-class bodies, per-tool animations, split view
- Slice work in flight (fork branches from fantasy/prototype, no PRs): campaign/classes (A1 four class hairstyle layers), campaign/pets (owlbear, wolf, raven), campaign/seating (B2 + eviction fix + B7 auto-follow), campaign/rolepacks (B1, B3, B4, B6; overlay contract camp.toml/dungeon.toml with camp_/dungeon_ sprites), campaign/dungeon-art (A3 attack, A4 lairs, A5-A7, A13, A16, A18). Still to dispatch: camp art (A8-A11, A14, A15) and B5 + A19 per-class attacks. Working choices pending the owner: class by stable hash, tools as colour, one fight zone.
- [ ] Campaign 2: vertical slice in the fork: camp floor 0 with real resting agents, one dungeon floor with an active agent fighting a monster, the four classes drawn, the owlbear; built, installed with `instalar.py --local`, real office screenshots and close-ups
- [ ] Campaign 3: report to Punky (feasibility, screenshots, open decisions as options: class criterion, tool mapping) and stop for the owner's approval
- [ ] Campaign 4: full rework (after approval)
- [ ] Campaign 5: Orca plugin with the campaign build; propose the integration ideas first (after approval)
