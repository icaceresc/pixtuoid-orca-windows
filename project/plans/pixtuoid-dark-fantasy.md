# Pixtuoid dark fantasy, as an Orca plugin

Objective: an original dark fantasy / medieval reskin of the Pixtuoid office (knights with
per-agent tabards, hooded mages, helmets and hoods, grimoire tables, alchemist shelf, braziers,
raven and wolf, stone and torchlight theme), built from the owner's fork and delivered through a
revived Orca plugin that is more integrated with Orca than upstream Pixtuoid.

status: active
commits: authorized
coordination: Punky coordinates this mission's Orchestrator and reports to the owner (Spanish).
delegation: the Orchestrator dispatches Orca workers and chooses their models and effort.
authorized: install Rust toolchain and MSVC Build Tools; fork pixtuoid/pixtuoid into icaceresc; branches, commits, pushes and PRs on icaceresc repos only.
not authorized: issues or PRs on pixtuoid/pixtuoid upstream; merge; release; repo rename; touching the running install at C:\Dev\Personalization\pixtuoid-orca-windows.
gates: owner approves the prototype look (phase 2) before phase 3; owner approves phase 3 and the integration ideas before phase 4.
originality: original designs only, no characters, art, logos or names from Dark Souls, Berserk, D&D, Baldur's Gate 3 or Tolkien.

## Layout
- Fork: https://github.com/icaceresc/pixtuoid, clone C:\Dev\Personalization\pixtuoid (remote `upstream` = pixtuoid/pixtuoid, `gh` default repo = the fork), Orca repo id b86f3755-0b74-4dde-93e0-6f2d7bcbf74b.
- Base branch `dark-fantasy` in the fork = upstream tag v0.23.0 (a89eebac), the version this adapter pins. Fantasy work branches from it and PRs target it.
- Release build: `cargo build --release --locked -p pixtuoid --bin pixtuoid -p pixtuoid-hook --bin pixtuoid-hook` (release-plz.yml), toolchain 1.99.1 (rust-toolchain.toml).

## Steps
- [x] Fork created and cloned, upstream remote and tags fetched, registered in Orca: icaceresc/pixtuoid, parent pixtuoid/pixtuoid
- [ ] Phase 1: Rust toolchain and MSVC Build Tools installed
- [ ] Phase 1: upstream v0.23.0 builds on Windows from the fork
- [ ] Phase 1: adapter option to install a local or owner-released binary (SHA-256 kept for downloads, tests green), PR in this repo
- [ ] Phase 1: the built pixtuoid.exe runs the office through the adapter
- [ ] Phase 2: dark fantasy theme, palette pass and one knight in the fork, built and running; screenshots of the office and the knight
- [ ] Phase 2: report to Punky and wait for the owner's approval of the look
- [ ] Phase 3: full reskin (all poses, helmets and hoods, furniture, pets, icons)
- [ ] Phase 4: propose Orca integration ideas, then revive the plugin with the fantasy build
