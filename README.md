<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md"><b>English</b></a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md">Español</a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md">Deutsch</a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md">日本語</a>
</p>

# Pixtuoid for Orca on Windows

A floating pixel-art office that shows your local Orca agents, their workers and their subagents as coworkers. It installs as an Orca plugin or runs from a clone.

## What it shows

One character per agent that Orca identifies on this machine. Children wear a cap in their team's color and leave with their parent.

| In Orca | In the office |
|---|---|
| Agent session (Claude Code, Codex, OpenCode, Antigravity) | Its own character |
| Worker started through Orca orchestration, at any depth | A child of the agent that dispatched it |
| Subagent Orca observes inside a session | A child of that session |
| Background command, monitor or tool call | No character |

Verified with live sessions on Orca 1.4.263:

| Provider | As agent | As worker child | Native subagents |
|---|---|---|---|
| Claude Code | Yes | Yes | Yes |
| Codex | Yes | Yes | Not verified |
| OpenCode | Yes | Yes | Not verified |
| Antigravity | Yes | Yes | Orca reports none |

## Requirements

- Windows x64 with DirectX 12
- Python 3.11+ (64-bit) with the `py` launcher
- Orca 1.4.263 or later, running, with at least one supported agent installed
- `claude`, `codex` or `agy` in `PATH` for the Claude Code, Codex or Antigravity sources

## Quick install

**As an Orca plugin**

```powershell
orca plugin install icaceresc/pixtuoid-orca-windows
```

Orca shows what the plugin may do and asks you to approve it: it runs its own code and requests no Orca permissions. Then run **Pixtuoid: Install or update the office app** from the command palette. It downloads Pixtuoid v0.23.0 to `%LOCALAPPDATA%\PixtuoidOrca`, verifies its SHA-256 and connects the agents Orca reports.

**From a clone**

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py
py -3 -m unittest -v test_oficina
```

To limit sources: `py -3 instalar.py --sources claude-code codex`.

## Open the office

- Plugin: **Pixtuoid: Open office window** and **Pixtuoid: Close office window** in the command palette.
- Clone: double-click **`Abrir oficina.lnk`**. Close it with `Q`, or run `py -3 oficina.py --stop`.

The window floats outside Orca, so you can keep it on a second monitor. Only one office runs per installation. `py -3 oficina.py --evidence` logs states to `actividad/`.

## Controls

| Action | Input |
|---|---|
| Move | Drag an empty area |
| Resize | Drag the bottom-right corner |
| Zoom | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| Help · Pause · Theme | `?` · `P` · `T` |
| Close and save size and position | `Q`, or the close command |

## Visible states

| Orca state | In the office |
|---|---|
| `working` | Character at the desk, active |
| `waiting` / `blocked` | Character asking for permission |
| `done` / `idle` | Character resting |
| Session closed, subagent finished or cancelled | Character leaves; its children leave first |

## Limitations

- Pixtuoid v0.23.0 links a child only to a parent of the same provider. A worker of another provider is drawn under its parent, with the cap and the parent's provider label.
- Pixtuoid cannot draw children under a top-level Antigravity session: its workers appear as separate coworkers in the same team color. An Antigravity worker that is itself a child can have children.
- A worker whose dispatcher closes first leaves with it, then returns as a separate coworker.
- Only subagents that Orca itself observes appear. The hierarchy comes from `orca worktree ps`, the only Orca interface that exposes it.
- Agents already finished when the office opens are not shown.
- States mirror Orca's turn state, not tools, tokens or reasoning.
- Orca is polled about every 1.25 seconds, so very short turns may be missed. While Orca is busy, a new child may appear for a moment before it moves under its parent.
- `waiting` / `blocked` have not been verified with live sessions yet.
- Local Orca host only. Remote Orca environments are ignored.

## Privacy

- The office reads only IDs, parent links, provider, agent type, state and folder from `orca agent list` and `orca worktree ps`. Prompts, replies and tool inputs are never forwarded or stored.
- The adapter's only network access is the download of the pinned Pixtuoid release from GitHub.
- The app, the isolated agent profile and the logs stay in the clone or in `%LOCALAPPDATA%\PixtuoidOrca` (`app/`, `perfil/`, `actividad/`).
- Global agent and Orca settings are not modified.

## Uninstall

- Plugin: run **Pixtuoid: Remove downloaded app and local data**, then uninstall the plugin in Orca under Settings → Plugins.
- Clone: close the office and delete the clone folder.

Nothing else is installed.

## Credits and license

- This adapter: [MIT License](LICENSE).
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid) by Ivan Wang, MIT License. Downloaded at install time, not redistributed.
- Flag icons: [lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3, [MIT License](docs/flags/LICENSE).
- Orca is a separate product and is not included. This is an independent adapter, not an official Pixtuoid or Orca project.
