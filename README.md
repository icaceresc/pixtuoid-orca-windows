<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md"><b>English</b></a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md">Español</a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md">Deutsch</a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md">日本語</a> &nbsp;·&nbsp;
  <a href="README.zh.md"><img src="docs/flags/cn.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.zh.md">中文</a> &nbsp;·&nbsp;
  <a href="README.ru.md"><img src="docs/flags/ru.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ru.md">Русский</a>
</p>

# Pixtuoid para Orca

An Orca plugin for Windows. It opens a floating pixel-art window where your local Orca agents, their workers and their subagents appear as characters, each labelled with its provider, role and project. You choose what the window shows:

- **The official office** (`oficina`, the default): [Pixtuoid](https://github.com/pixtuoid/pixtuoid) v0.23.0 by Ivan Wang, as released.
- **Dungeons & Agents** (`dungeon`): [Dungeons & Agents](https://github.com/icaceresc/dungeons-and-agents), a fantasy mod of Pixtuoid. The office becomes a camp and dungeon floors, each agent an adventurer whose class shows its role, and clicking an adventurer opens its session in Orca.

![Demo workspaces: two orchestrators with Codex, Antigravity and Claude Code workers and an Explore subagent](docs/office-roles.png)

## What each mode has

| Feature | Official office | Dungeons & Agents |
|---|---|---|
| Agents, workers and subagents as characters, with provider, role and project | Yes | Yes |
| Notice and status bar count when an agent needs you | Yes | Yes |
| Commands in Orca's palette; install and update from Orca | Yes | Yes |
| Reads Orca when Orca reports an agent change, not on a fast timer | Yes | Yes |
| Team color | By project | By party: an orchestrator, its workers and their subagents |
| Class that shows the role (companion, orchestrator, worker, subagent) | No | Yes |
| Tools shown as skills; an Orca CLI call as `Hechizo (Orca)` | No (shown as the tool `Orca`) | Yes |
| Click an agent, or `Enter` on it in the `Tab` tree, to open its session in Orca | No | Yes |

## Requirements

- Windows x64 with DirectX 12
- Python 3.11+ (64-bit) with the `py` launcher
- Orca 1.4.265 or later, with at least one supported agent installed. A newer Orca than the one verified shows a one-time notice and should keep working.
- `claude`, `codex` or `agy` in `PATH` for the Claude Code, Codex or Antigravity sources

## Install from Orca

1. In Orca, open **Settings → Plugins**, choose **From a Git URL…** and enter `https://github.com/icaceresc/pixtuoid-orca-windows`, or run `orca plugin install icaceresc/pixtuoid-orca-windows`. Orca shows the access the plugin asks for (below) before it installs.
2. In the command palette, run **Pixtuoid: Install or update the office app** for the official office, or **Pixtuoid: Use Dungeons & Agents**. It downloads the build, checks its pinned SHA-256 and connects the agents Orca reports.
3. Run **Pixtuoid: Open office window**, or click **Pixtuoid** in Orca's status bar.

Until the Dungeons & Agents release is published and pinned in this plugin, **Use Dungeons & Agents** says so and changes nothing; install a build of it from a clone (see [Run from a clone](#run-from-a-clone)).

| Command | What it does |
|---|---|
| Pixtuoid: Open office window | Opens the window; only one runs at a time |
| Pixtuoid: Close office window | Closes it, keeping its size and position |
| Pixtuoid: Install or update the office app | Installs or updates the build of the mode chosen last |
| Pixtuoid: Use the official Pixtuoid office | Switches to the official office |
| Pixtuoid: Use Dungeons & Agents | Switches to Dungeons & Agents |
| Pixtuoid: Remove downloaded app and local data | Deletes the app, the isolated agent profile and the logs |

| Access the plugin asks for | Why |
|---|---|
| `agent:read` | Hear when an agent's status changes: the office reads Orca then, and the notice and the status bar count follow it |
| `workspace:read` | Find the workspace of a clicked agent by its folder |
| `workspace:write` | Bring that agent's session forward |
| `notifications:show` | Say when an agent needs you |

**Updating.** Orca updates the plugin (**Settings → Plugins**, or `orca plugin update icaceresc.pixtuoid-office`). **Pixtuoid: Install or update the office app** brings the office app to the build the plugin pins for its mode, and reopens the window if it was open. A daily workflow in this repository looks for a new stable Pixtuoid release, checks its SHA-256, runs the tests and proposes the new pin for review; it never merges by itself.

## What it shows

One character per agent that Orca identifies on this machine. Children wear their team's color and leave with their parent. Press `Tab` for the agent tree.

![The agent tree: each orchestrator with its workers and subagents, their tools and states](docs/office-dashboard.png)

| In Orca | Name in the office |
|---|---|
| An Orca bot's own session (its Strategic Companion) | `cc·punky · companion` |
| Top-level agent | `cc·my-repo · agent` |
| Agent that dispatches workers, a worker included | `cc·my-repo · orchestrator` |
| Orchestration worker, any depth | `cx·worker · my-repo` |
| Worker of another provider than its parent | `cx·claude worker · my-repo` |
| Subagent Orca observes inside a session | `cc·Explore subagent · my-repo` |
| Worker of an Antigravity agent | `cx·worker of antigravity · my-repo` |
| Background command, monitor or tool call | No character |

The prefix is the provider (`cc` Claude Code, `cx` Codex, `oc` OpenCode, `ag` Antigravity) and the project is the Orca workspace folder. A desk shows the first characters of the name; hover a character or press `Tab` for the whole name, its parent and its current tool.

| Provider | As agent | As worker | Native subagents |
|---|---|---|---|
| Claude Code | Yes | Yes | Yes |
| Codex | Yes (1.4.263) | Yes | Not verified |
| OpenCode | Yes (1.4.263) | Yes (1.4.263) | Not verified |
| Antigravity | Yes (1.4.263) | Yes | Orca reports none |

Seen live on Orca 1.4.265 and 1.4.266, or on 1.4.263 where noted. All four providers are also checked against the real Pixtuoid with recorded Orca answers.

## Controls

| Action | Input |
|---|---|
| Move | Drag an empty area |
| Resize | Drag the bottom-right corner |
| Zoom | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| Agent tree | `Tab` |
| Name, parent, folder and tool of an agent | Hover it |
| Open an agent's session in Orca (Dungeons & Agents) | Click it, or `Enter` on it in the `Tab` tree |
| Help · Pause · Theme | `?` · `P` · `T` |
| Close and save size and position | `Q`, or **Pixtuoid: Close office window** |

## Visible states

| Orca state | In the office |
|---|---|
| `working` | At the desk; the tool Orca reports (such as `Bash`, `Edit`, `shell`) on the monitor, in the tooltip and in the footer tally |
| `waiting` / `blocked` | Asking for permission (`!`), counted as "need you"; a desktop notice says so while the office is open, and Orca's status bar counts it |
| `done` / `idle` | Resting or wandering |
| Session closed, subagent finished or cancelled | Leaves through the door; its children leave first |

## Limitations

- **Clicking an agent** opens its session only in Dungeons & Agents. A terminal agent's pane is focused. An Orca chat has no terminal, so its workspace is shown: when one workspace holds several chats (a bot's home, for example), Orca shows the one last open there, not necessarily the clicked one. A subagent opens the session it runs in.
- Pixtuoid links a child only to a parent of the same provider. A worker of another provider sits under its parent with the parent's prefix, and its name says its own provider (`cx·claude worker`). In a Claude Code tree the prefix too is the worker's own.
- Pixtuoid cannot draw children under a top-level Antigravity agent: its workers appear as separate coworkers named `worker of antigravity`.
- Pixtuoid keeps the name a coworker first appears with, so an agent that starts dispatching later leaves and comes back as an orchestrator. The role is never taken back.
- Orca reports a tool name, not model, effort or token use, so the office shows no model, effort or token meter.
- With the plugin, the office reads Orca as soon as Orca reports an agent change, and otherwise every 6 seconds while an agent works and every 30 seconds while none does, so a subagent can take that long to appear and very short tools may be missed. Run from a clone, it reads every 1.5 to 10 seconds.
- The notice and the status bar count follow the status changes Orca reports after the plugin starts.
- Only subagents that Orca itself observes appear. Agents already finished when the office opens are not shown.
- Local Orca host only. Remote Orca environments are ignored.

## Privacy

- The office reads only IDs, parent links, provider, subagent type, state, tool name, workspace folder and whether the workspace is a bot's home from `orca worktree ps` (and `orca agent list` as a fallback). It looks at a shell tool's command only to tell whether it runs the Orca CLI; prompts, replies and tool inputs are never forwarded or stored.
- The plugin keeps each agent's status, pane, terminal and workspace IDs in memory while it runs. The notice shows the session's title from Orca on this computer only.
- The adapter's only network access is the download of the pinned build from GitHub.
- The app, the isolated agent profile and the logs stay in `%LOCALAPPDATA%\PixtuoidOrca` (in the clone when run from one). To name a worker's provider, the office writes a one-line card (name and folder) to the isolated profile and deletes it when the worker leaves or the office closes. A click writes the clicked session's IDs there for the plugin to read.
- Global agent and Orca settings are not modified.

## Run from a clone

The plugin is the supported way. To work on the adapter, or to install a build of your own:

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py                     # official office; --modo dungeon for Dungeons & Agents
py -3 -m unittest -v test_oficina test_instalar
```

Open the office with **`Abrir oficina.lnk`** and close it with `Q` or `py -3 oficina.py --stop`. A click on an agent needs the plugin. To limit sources: `py -3 instalar.py --sources claude-code codex`.

**Your own build.** With the office closed, `py -3 instalar.py --modo dungeon --local C:\path\to\dungeons-and-agents\target\release` installs `pixtuoid.exe` and `pixtuoid-hook.exe` from a local build, plus the `LICENSE` found beside them or at the root of their repository. `--url https://... --sha256 <64 hex>` installs a zip with the same layout as Pixtuoid's Windows zip. `app/origen.json` records what is installed and its mode: a later plain run keeps your build and says so, `--pinned` goes back to the mode's pinned build, and `--modo` switches mode. The plugin's commands do the same in `%LOCALAPPDATA%\PixtuoidOrca`.

## Uninstall

Run **Pixtuoid: Remove downloaded app and local data**, then uninstall the plugin in **Settings → Plugins**. A clone needs only its folder deleted.

## Credits and license

- This plugin: [MIT License](LICENSE).
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid) by Ivan Wang, MIT License. Downloaded at install time, not redistributed.
- [Dungeons & Agents](https://github.com/icaceresc/dungeons-and-agents), a mod of Pixtuoid, MIT License. Downloaded at install time, not redistributed.
- Flag icons: [lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3, [MIT License](docs/flags/LICENSE).
- Orca is a separate product and is not included. This is an independent plugin, not an official Pixtuoid or Orca project.
