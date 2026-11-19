<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md">English</a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md">Español</a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md"><b>Deutsch</b></a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md">日本語</a>
</p>

# Pixtuoid für Orca unter Windows

Ein schwebendes Pixel-Art-Büro, das deine lokalen Orca-Agentensitzungen als Kollegen zeigt.

## Was angezeigt wird

Eine Figur pro Agentensitzung, die Orca auf diesem Rechner erkennt: **Claude Code, Codex, OpenCode und Antigravity**. Die Figur arbeitet, solange ihr Agent einen Turn ausführt, ruht, wenn er fertig ist, und geht, wenn die Sitzung geschlossen wird.

## Voraussetzungen

- Windows x64 mit DirectX 12
- Python 3.11 oder neuer (64 Bit)
- Orca läuft, mit mindestens einem unterstützten Agenten
- `claude`, `codex` oder `agy` im `PATH` für die Quellen Claude Code, Codex oder Antigravity

## Schnellinstallation

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py
py -3 -m unittest -v test_oficina
```

Der Installer lädt Pixtuoid v0.23.0 herunter, prüft die SHA-256-Prüfsumme und verbindet die Agenten, die Orca meldet. Quellen einschränken: `py -3 instalar.py --sources claude-code codex`.

## Büro öffnen

Doppelklick auf **`Abrir oficina.lnk`** im Klon. Es läuft immer nur ein Büro. Mit `py -3 oficina.py --evidence` werden die Zustände in `actividad/` protokolliert.

## Steuerung

| Aktion | Eingabe |
|---|---|
| Verschieben | Leere Fläche ziehen |
| Größe ändern | Untere rechte Ecke ziehen |
| Zoom | `Strg` `+` / `Strg` `-` / `Strg` `0` |
| Hilfe · Pause · Theme | `?` · `P` · `T` |
| Schließen, Größe und Position speichern | `Q` |

## Sichtbare Zustände

| Orca-Zustand | Im Büro |
|---|---|
| `working` | Figur am Schreibtisch, aktiv |
| `waiting` / `blocked` | Figur bittet um Erlaubnis |
| `done` | Figur ruht |
| Sitzung geschlossen | Figur geht |

## Einschränkungen

- Nur Hauptsitzungen von Agenten. Subagenten haben keine eigene Figur.
- Sitzungen, die beim Öffnen des Büros schon beendet waren, werden nicht angezeigt.
- Die Zustände spiegeln Orcas Turn-Status, nicht Tools, Tokens oder Reasoning.
- Orca wird etwa alle 2 Sekunden abgefragt, sehr kurze Turns können daher fehlen.
- `waiting` / `blocked` sind noch nicht mit echten Sitzungen verifiziert.
- Nur der lokale Orca-Host. Entfernte Orca-Umgebungen werden ignoriert.

## Datenschutz

- Aus `orca agent list` nutzt das Büro nur Sitzungs-ID, Anbieter, Zustand und Ordner. Prompts und Antworten werden nie weitergegeben oder gespeichert.
- Der einzige Netzwerkzugriff des Adapters ist der Download des festgelegten Releases von GitHub durch den Installer.
- App, isoliertes Agentenprofil und Logs bleiben im Klon (`app/`, `perfil/`, `actividad/`). Git ignoriert sie.
- Globale Agenten- und Orca-Einstellungen bleiben unverändert.

## Deinstallation

Büro mit `Q` schließen und den Klon-Ordner löschen. Außerhalb davon wird nichts installiert.

## Credits und Lizenz

- Dieser Adapter: [MIT-Lizenz](LICENSE).
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid) von Ivan Wang, MIT-Lizenz. Wird bei der Installation heruntergeladen, nicht weiterverbreitet.
- Flaggen-Icons: [lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3, [MIT-Lizenz](docs/flags/LICENSE).
- Orca ist ein eigenständiges Produkt und nicht enthalten. Unabhängiger Adapter, kein offizielles Pixtuoid- oder Orca-Projekt.
