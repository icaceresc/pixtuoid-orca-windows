<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md"><b>English</b></a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md">Español</a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md">Deutsch</a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md">日本語</a>
</p>

# Pixtuoid for Orca on Windows

A floating pixel-art office that shows your local Orca agent sessions as coworkers.

## What it shows

One character per agent session that Orca identifies on this machine: **Claude Code, Codex, OpenCode and Antigravity**. Characters work while their agent runs a turn, rest when it finishes, and leave when the session closes.

## Requirements

- Windows x64 with DirectX 12
- Python 3.11+ (64-bit)
- Orca running, with at least one supported agent installed
- `claude`, `codex` or `agy` in `PATH` for the Claude Code, Codex or Antigravity sources

## Quick install

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py
py -3 -m unittest -v test_oficina
```

The installer downloads Pixtuoid v0.23.0, verifies its SHA-256 and connects the agents Orca reports. To limit sources: `py -3 instalar.py --sources claude-code codex`.

## Open the office

Double-click **`Abrir oficina.lnk`** in the clone. Only one office runs at a time. Run `py -3 oficina.py --evidence` to log states to `actividad/`.

## Controls

| Action | Input |
|---|---|
| Move | Drag an empty area |
| Resize | Drag the bottom-right corner |
| Zoom | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| Help · Pause · Theme | `?` · `P` · `T` |
| Close and save size and position | `Q` |

## Visible states

| Orca state | In the office |
|---|---|
| `working` | Character at the desk, active |
| `waiting` / `blocked` | Character asking for permission |
| `done` | Character resting |
| Session closed | Character leaves |

## Limitations

- Main agent sessions only. Subagents have no character of their own.
- Sessions already finished when the office opens are not shown.
- States mirror Orca's turn state, not tools, tokens or reasoning.
- Orca is polled about every 2 seconds, so very short turns may be missed.
- `waiting` / `blocked` have not been verified with live sessions yet.
- Local Orca host only. Remote Orca environments are ignored.

## Privacy

- From `orca agent list` the office uses only the session ID, provider, state and folder. Prompts and replies are never forwarded or stored.
- The adapter's only network access is the installer's download of the pinned release from GitHub.
- The app, the isolated agent profile and the logs stay inside the clone (`app/`, `perfil/`, `actividad/`). Git ignores them.
- Global agent and Orca settings are not modified.

## Uninstall

Close the office with `Q` and delete the clone folder. Nothing is installed outside it.

## Credits and license

- This adapter: [MIT License](LICENSE).
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid) by Ivan Wang, MIT License. Downloaded at install time, not redistributed.
- Flag icons: [lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3, [MIT License](docs/flags/LICENSE).
- Orca is a separate product and is not included. This is an independent adapter, not an official Pixtuoid or Orca project.
