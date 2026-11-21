<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md"><b>English</b></a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md">Español</a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md">Deutsch</a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md">日本語</a> &nbsp;·&nbsp;
  <a href="README.zh.md"><img src="docs/flags/cn.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.zh.md">中文</a> &nbsp;·&nbsp;
  <a href="README.ru.md"><img src="docs/flags/ru.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ru.md">Русский</a>
</p>

# Pixtuoid for Orca on Windows

A floating pixel-art office that shows your local Orca agents, their workers and their subagents as coworkers, each labelled with its provider, role and project. It runs from a clone of this repository.

![Demo workspaces: two orchestrators with Codex, Antigravity and Claude Code workers and an Explore subagent](docs/office-roles.png)

## What it shows

One character per agent that Orca identifies on this machine. Children wear a cap in their team's color and leave with their parent. Press `Tab` for the agent tree.

![The agent tree: each orchestrator with its workers and subagents, their tools and states](docs/office-dashboard.png)

| In Orca | Name in the office |
|---|---|
| Top-level agent | `cc·my-repo` |
| Agent that dispatched workers | `cc·my-repo · orchestrator` |
| Orchestration worker, any depth | `cx·worker · my-repo` |
| Worker of another provider than its parent | `cx·claude worker · my-repo` |
| Subagent Orca observes inside a session | `cc·Explore subagent · my-repo` |
| Worker of an Antigravity agent | `cx·worker of antigravity · my-repo` |
| Background command, monitor or tool call | No character |

The prefix is the provider (`cc` Claude Code, `cx` Codex, `oc` OpenCode, `ag` Antigravity) and the project is the Orca workspace folder. A desk shows the first characters of the name; hover a character or press `Tab` for the whole name, its parent and its current tool.

Seen live with Pixtuoid v0.23.0 on Orca 1.4.266, or on 1.4.263 where noted. All four providers are also checked against the real Pixtuoid with recorded Orca answers.

| Provider | As agent | As worker | Native subagents |
|---|---|---|---|
| Claude Code | Yes | Yes | Yes |
| Codex | Yes (1.4.263) | Yes | Not verified |
| OpenCode | Yes (1.4.263) | Yes (1.4.263) | Not verified |
| Antigravity | Yes (1.4.263) | Yes | Orca reports none |

## Requirements

- Windows x64 with DirectX 12
- Python 3.11+ (64-bit) with the `py` launcher
- Orca 1.4.263 or later, running, with at least one supported agent installed. Verified up to 1.4.266; a newer Orca shows a one-time notice and should keep working.
- `claude`, `codex` or `agy` in `PATH` for the Claude Code, Codex or Antigravity sources

## Quick install

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py
py -3 -m unittest -v test_oficina test_instalar
```

`instalar.py` downloads Pixtuoid v0.23.0 into the clone, verifies its SHA-256 and connects the agents Orca reports. To limit sources: `py -3 instalar.py --sources claude-code codex`.

**Your own build.** With the office closed, `py -3 instalar.py --local C:\path\to\pixtuoid\target\release` installs `pixtuoid.exe` and `pixtuoid-hook.exe` from a local build, plus the `LICENSE` found beside them or at the root of their repository. `py -3 instalar.py --url https://... --sha256 <64 hex>` installs a zip you released with the same layout as Pixtuoid's Windows zip; the SHA-256 is mandatory. `app/origen.json` records what is installed: a later plain `py -3 instalar.py` keeps your build and says so, and `py -3 instalar.py --pinned` goes back to v0.23.0.

**Updating.** A daily workflow in this repository looks for a new stable Pixtuoid release, verifies its SHA-256, runs the tests and proposes the new pin for review; it never merges by itself. After you pull an update, close the office and run `py -3 instalar.py` again.

The Orca plugin (v2.0.0) is paused: it still installs and opens the office, but without the features above. Use the clone.

## Open the office

Double-click **`Abrir oficina.lnk`**. Close it with `Q`, or run `py -3 oficina.py --stop`.

The window floats outside Orca, so you can keep it on a second monitor. Only one office runs per folder. Everything it starts runs below normal priority and reads Orca with a single CLI call per cycle, so your PC keeps priority. `py -3 oficina.py --evidence` logs states to `actividad/`.

## Controls

| Action | Input |
|---|---|
| Move | Drag an empty area |
| Resize | Drag the bottom-right corner |
| Zoom | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| Agent tree | `Tab` |
| Name, parent, folder and tool of an agent | Hover it |
| Help · Pause · Theme | `?` · `P` · `T` |
| Close and save size and position | `Q`, or `py -3 oficina.py --stop` |

## Visible states

| Orca state | In the office |
|---|---|
| `working` | At the desk; the tool Orca reports (such as `Bash`, `Edit`, `shell`) on the monitor, in the tooltip and in the footer tally |
| `waiting` / `blocked` | Asking for permission (`!`), counted as "need you" |
| `done` / `idle` | Resting or wandering |
| Session closed, subagent finished or cancelled | Leaves through the door; its children leave first |

## Limitations

- Pixtuoid links a child only to a parent of the same provider. A worker of another provider sits under its parent with the parent's prefix and color, and its name says its own provider (`cx·claude worker`). In a Claude Code tree the prefix too is the worker's own.
- Pixtuoid cannot draw children under a top-level Antigravity agent: its workers appear as separate coworkers named `worker of antigravity`.
- The role is the one Orca shows when the agent first appears. An agent that starts dispatching later keeps its name; its workers still appear under it.
- Orca reports a tool name, not model, effort or token use, so the office shows no model, effort or token meter. The tool's input is never read, so no file or command appears next to it.
- Clicking a character does not focus its terminal: Orca exposes no agent process, and Pixtuoid's Windows focus covers only its own Antigravity integration.
- The office waits 1.5 to 10 seconds between reads of Orca, longer while the PC or Orca is busy, so very short turns and tools may be missed. While Orca is busy, a new child may appear for a moment before it moves under its parent.
- Only subagents that Orca itself observes appear. Agents already finished when the office opens are not shown.
- Local Orca host only. Remote Orca environments are ignored.

## Privacy

- The office reads only IDs, parent links, provider, subagent type, state, tool name and workspace folder from `orca worktree ps` (and `orca agent list` as a fallback). Prompts, replies and tool inputs are never forwarded or stored.
- The adapter's only network access is the download of the pinned Pixtuoid release from GitHub.
- The app, the isolated agent profile and the logs stay in the clone (`app/`, `perfil/`, `actividad/`). To name a worker's provider, the office writes a one-line card (name and folder) to the isolated profile and deletes it when the worker leaves or the office closes.
- Global agent and Orca settings are not modified.

## Uninstall

Close the office and delete the clone folder. Nothing else is installed. If you installed the paused plugin, run **Pixtuoid: Remove downloaded app and local data** and uninstall it in Orca under Settings → Plugins.

## Credits and license

- This adapter: [MIT License](LICENSE).
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid) by Ivan Wang, MIT License. Downloaded at install time, not redistributed.
- Flag icons: [lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3, [MIT License](docs/flags/LICENSE).
- Orca is a separate product and is not included. This is an independent adapter, not an official Pixtuoid or Orca project.
