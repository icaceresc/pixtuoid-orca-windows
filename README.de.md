<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md">English</a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md">Español</a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md"><b>Deutsch</b></a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md">日本語</a>
</p>

# Pixtuoid für Orca unter Windows

Ein schwebendes Pixel-Art-Büro, das deine lokalen Orca-Agenten, ihre Worker und ihre Subagenten als Kollegen zeigt. Es lässt sich als Orca-Plugin installieren oder aus einem Klon starten.

## Was es zeigt

Eine Figur pro Agent, den Orca auf diesem Rechner erkennt. Kinder tragen eine Mütze in der Farbe ihres Teams und gehen mit ihrem Elternagenten.

| In Orca | Im Büro |
|---|---|
| Agentensitzung (Claude Code, Codex, OpenCode, Antigravity) | Eigene Figur |
| Über Orca-Orchestrierung gestarteter Worker, in jeder Tiefe | Kind des Agenten, der ihn gestartet hat |
| Subagent, den Orca in einer Sitzung beobachtet | Kind dieser Sitzung |
| Hintergrundbefehl, Monitor oder Tool-Aufruf | Keine Figur |

Mit echten Sitzungen unter Orca 1.4.263 geprüft:

| Anbieter | Als Agent | Als Worker-Kind | Native Subagenten |
|---|---|---|---|
| Claude Code | Ja | Ja | Ja |
| Codex | Ja | Ja | Nicht geprüft |
| OpenCode | Ja | Ja | Nicht geprüft |
| Antigravity | Ja | Ja | Orca meldet keine |

## Voraussetzungen

- Windows x64 mit DirectX 12
- Python 3.11+ (64 Bit) mit dem Starter `py`
- Orca 1.4.263 oder neuer, gestartet, mit mindestens einem unterstützten Agenten
- `claude`, `codex` oder `agy` im `PATH` für die Quellen Claude Code, Codex oder Antigravity

## Schnellinstallation

**Als Orca-Plugin**

```powershell
orca plugin install icaceresc/pixtuoid-orca-windows
```

Orca zeigt, was das Plugin darf, und bittet um deine Freigabe: Es führt eigenen Code aus und verlangt keine Orca-Berechtigungen. Führe danach **Pixtuoid: Install or update the office app** in der Befehlspalette aus. Es lädt Pixtuoid v0.23.0 nach `%LOCALAPPDATA%\PixtuoidOrca`, prüft die SHA-256 und verbindet die Agenten, die Orca meldet.

**Aus einem Klon**

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py
py -3 -m unittest -v test_oficina
```

Quellen einschränken: `py -3 instalar.py --sources claude-code codex`.

## Büro öffnen

- Plugin: **Pixtuoid: Open office window** und **Pixtuoid: Close office window** in der Befehlspalette.
- Klon: Doppelklick auf **`Abrir oficina.lnk`**. Schließen mit `Q` oder `py -3 oficina.py --stop`.

Das Fenster schwebt außerhalb von Orca und passt so gut auf einen zweiten Monitor. Pro Installation läuft nur ein Büro. `py -3 oficina.py --evidence` protokolliert die Zustände in `actividad/`.

## Steuerung

| Aktion | Eingabe |
|---|---|
| Verschieben | Freie Fläche ziehen |
| Größe ändern | Untere rechte Ecke ziehen |
| Zoom | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| Hilfe · Pause · Design | `?` · `P` · `T` |
| Schließen, Größe und Position speichern | `Q` oder der Schließen-Befehl |

## Sichtbare Zustände

| Orca-Zustand | Im Büro |
|---|---|
| `working` | Figur am Schreibtisch, aktiv |
| `waiting` / `blocked` | Figur bittet um Erlaubnis |
| `done` / `idle` | Figur ruht |
| Sitzung geschlossen, Subagent fertig oder abgebrochen | Figur geht; ihre Kinder gehen zuerst |

## Einschränkungen

- Pixtuoid v0.23.0 verknüpft ein Kind nur mit einem Elternagenten desselben Anbieters. Ein Worker eines anderen Anbieters erscheint unter seinem Elternagenten, mit Mütze und dem Anbieter-Label des Elternagenten.
- Unter einer Antigravity-Sitzung der obersten Ebene kann Pixtuoid keine Kinder zeichnen: Ihre Worker erscheinen als eigene Kollegen in derselben Teamfarbe. Ein Antigravity-Worker, der selbst ein Kind ist, kann Kinder haben.
- Es erscheinen nur Subagenten, die Orca selbst beobachtet. Die Hierarchie stammt aus `orca worktree ps`, der einzigen Orca-Schnittstelle, die sie liefert.
- Agenten, die beim Öffnen des Büros schon fertig sind, werden nicht gezeigt.
- Die Zustände spiegeln Orcas Turn-Status, nicht Tools, Tokens oder Reasoning.
- Orca wird etwa alle 1,25 Sekunden abgefragt, sehr kurze Turns können also fehlen. Ist Orca ausgelastet, kann ein neues Kind kurz erscheinen, bevor es unter seinen Elternagenten wechselt.
- `waiting` / `blocked` wurden noch nicht mit echten Sitzungen geprüft.
- Nur der lokale Orca-Host. Entfernte Orca-Umgebungen werden ignoriert.

## Datenschutz

- Aus `orca agent list` und `orca worktree ps` liest das Büro nur IDs, Eltern-Kind-Verknüpfungen, Anbieter, Agententyp, Zustand und Ordner. Prompts, Antworten und Tool-Eingaben werden nie weitergegeben oder gespeichert.
- Der einzige Netzwerkzugriff des Adapters ist der Download der festgelegten Pixtuoid-Version von GitHub.
- App, isoliertes Agentenprofil und Logs bleiben im Klon oder in `%LOCALAPPDATA%\PixtuoidOrca` (`app/`, `perfil/`, `actividad/`).
- Globale Agenten- und Orca-Einstellungen werden nicht geändert.

## Deinstallation

- Plugin: **Pixtuoid: Remove downloaded app and local data** ausführen, dann das Plugin in Orca unter Settings → Plugins deinstallieren.
- Klon: Büro schließen und den Klon-Ordner löschen.

Sonst wird nichts installiert.

## Credits und Lizenz

- Dieser Adapter: [MIT-Lizenz](LICENSE).
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid) von Ivan Wang, MIT-Lizenz. Wird bei der Installation geladen, nicht weiterverteilt.
- Flaggen-Icons: [lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3, [MIT-Lizenz](docs/flags/LICENSE).
- Orca ist ein separates Produkt und nicht enthalten. Dies ist ein unabhängiger Adapter, kein offizielles Pixtuoid- oder Orca-Projekt.
