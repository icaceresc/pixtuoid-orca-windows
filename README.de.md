<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md">English</a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md">Español</a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md"><b>Deutsch</b></a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md">日本語</a>
</p>

# Pixtuoid für Orca unter Windows

Ein schwebendes Pixel-Art-Büro, das deine lokalen Orca-Agenten, ihre Worker und ihre Subagenten als Kollegen zeigt, jeweils mit Anbieter, Rolle und Projekt beschriftet. Es läuft aus einem Klon dieses Repositorys.

![Demo-Arbeitsbereiche: zwei Orchestratoren mit Codex-, Antigravity- und Claude-Code-Workern und einem Explore-Subagenten](docs/office-roles.png)

## Was es zeigt

Eine Figur pro Agent, den Orca auf diesem Rechner erkennt. Kinder tragen eine Mütze in der Farbe ihres Teams und gehen mit ihrem Elternagenten. Mit `Tab` erscheint der Agentenbaum.

![Der Agentenbaum: jeder Orchestrator mit seinen Workern und Subagenten, ihren Werkzeugen und Zuständen](docs/office-dashboard.png)

| In Orca | Name im Büro |
|---|---|
| Agent der obersten Ebene | `cc·my-repo` |
| Agent, der Worker gestartet hat | `cc·my-repo · orchestrator` |
| Orchestrierungs-Worker, in jeder Tiefe | `cx·worker · my-repo` |
| Worker eines anderen Anbieters als sein Elternagent | `cx·claude worker · my-repo` |
| Subagent, den Orca in einer Sitzung beobachtet | `cc·Explore subagent · my-repo` |
| Worker eines Antigravity-Agenten | `cx·worker of antigravity · my-repo` |
| Hintergrundbefehl, Monitor oder Werkzeugaufruf | Keine Figur |

Das Präfix ist der Anbieter (`cc` Claude Code, `cx` Codex, `oc` OpenCode, `ag` Antigravity), das Projekt ist der Ordner des Orca-Arbeitsbereichs. Der Schreibtisch zeigt die ersten Zeichen des Namens; fahre mit dem Mauszeiger über eine Figur oder drücke `Tab` für den vollen Namen, den Elternagenten und das aktuelle Werkzeug.

Live gesehen mit Pixtuoid v0.23.0 unter Orca 1.4.266, oder unter 1.4.263, wo angegeben. Alle vier Anbieter werden außerdem gegen das echte Pixtuoid mit aufgezeichneten Orca-Antworten geprüft.

| Anbieter | Als Agent | Als Worker | Native Subagenten |
|---|---|---|---|
| Claude Code | Ja | Ja | Ja |
| Codex | Ja (1.4.263) | Ja | Nicht geprüft |
| OpenCode | Ja (1.4.263) | Ja (1.4.263) | Nicht geprüft |
| Antigravity | Ja (1.4.263) | Ja | Orca meldet keine |

## Voraussetzungen

- Windows x64 mit DirectX 12
- Python 3.11+ (64 Bit) mit dem Starter `py`
- Orca 1.4.263 oder neuer, gestartet, mit mindestens einem unterstützten Agenten. Geprüft bis 1.4.266; ein neueres Orca zeigt einmalig einen Hinweis und sollte weiter funktionieren.
- `claude`, `codex` oder `agy` im `PATH` für die Quellen Claude Code, Codex oder Antigravity

## Schnellinstallation

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py
py -3 -m unittest -v test_oficina
```

`instalar.py` lädt Pixtuoid v0.23.0 in den Klon, prüft die SHA-256 und verbindet die Agenten, die Orca meldet. Quellen begrenzen: `py -3 instalar.py --sources claude-code codex`.

**Aktualisierungen.** Ein täglicher Workflow in diesem Repository sucht nach einer neuen stabilen Pixtuoid-Version, prüft ihre SHA-256, führt die Tests aus und schlägt die neue Version zur Prüfung vor; er führt nie selbst zusammen. Nach dem Holen einer Aktualisierung das Büro schließen und `py -3 instalar.py` erneut ausführen.

Das Orca-Plugin (v2.0.0) ist pausiert: Es lässt sich noch installieren und öffnet das Büro, aber ohne die Funktionen oben. Nutze den Klon.

## Büro öffnen

Doppelklick auf **`Abrir oficina.lnk`**. Schließen mit `Q` oder mit `py -3 oficina.py --stop`.

Das Fenster schwebt außerhalb von Orca, du kannst es also auf einem zweiten Monitor lassen. Pro Ordner läuft nur ein Büro. Alles, was es startet, läuft mit niedrigerer Priorität als normal und liest Orca mit einem einzigen CLI-Aufruf pro Zyklus, damit dein PC Vorrang behält. `py -3 oficina.py --evidence` protokolliert die Zustände in `actividad/`.

## Bedienung

| Aktion | Eingabe |
|---|---|
| Verschieben | Leere Fläche ziehen |
| Größe ändern | Untere rechte Ecke ziehen |
| Zoom | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| Agentenbaum | `Tab` |
| Name, Elternagent, Ordner und Werkzeug eines Agenten | Mauszeiger darüber |
| Hilfe · Pause · Thema | `?` · `P` · `T` |
| Schließen und Größe und Position speichern | `Q`, oder `py -3 oficina.py --stop` |

## Sichtbare Zustände

| Orca-Zustand | Im Büro |
|---|---|
| `working` | Am Schreibtisch; das von Orca gemeldete Werkzeug (etwa `Bash`, `Edit`, `shell`) auf dem Monitor, im Tooltip und in der Zählung der Fußzeile |
| `waiting` / `blocked` | Bittet um Erlaubnis (`!`), gezählt als „braucht dich“ |
| `done` / `idle` | Ruht oder läuft herum |
| Sitzung geschlossen, Subagent fertig oder abgebrochen | Geht durch die Tür; seine Kinder gehen zuerst |

## Einschränkungen

- Pixtuoid verknüpft ein Kind nur mit einem Elternagenten desselben Anbieters. Ein Worker eines anderen Anbieters sitzt unter seinem Elternagenten mit dessen Präfix und Farbe, und sein Name nennt seinen eigenen Anbieter (`cx·claude worker`). In einem Claude-Code-Baum ist auch das Präfix das des Workers.
- Pixtuoid kann unter einem Antigravity-Agenten der obersten Ebene keine Kinder zeichnen: Seine Worker erscheinen als eigene Kollegen namens `worker of antigravity`.
- Die Rolle ist die, die Orca beim ersten Erscheinen des Agenten zeigt. Ein Agent, der erst später Worker startet, behält seinen Namen; seine Worker erscheinen trotzdem unter ihm.
- Orca meldet den Namen des Werkzeugs, aber weder Modell, Aufwand noch Token-Verbrauch, daher zeigt das Büro kein Modell, keinen Aufwand und keine Token-Anzeige. Die Eingabe des Werkzeugs wird nie gelesen, daher erscheint daneben keine Datei und kein Befehl.
- Ein Klick auf eine Figur fokussiert nicht ihr Terminal: Orca legt keinen Agentenprozess offen, und Pixtuoids Fokus unter Windows deckt nur seine eigene Antigravity-Integration ab.
- Das Büro wartet zwischen zwei Abfragen von Orca 1,5 bis 10 Sekunden, länger, solange PC oder Orca ausgelastet sind; sehr kurze Runden und Werkzeuge können daher fehlen. Solange Orca ausgelastet ist, kann ein neues Kind kurz erscheinen, bevor es unter seinen Elternagenten wechselt.
- Es erscheinen nur Subagenten, die Orca selbst beobachtet. Agenten, die beim Öffnen des Büros schon fertig sind, werden nicht gezeigt.
- Nur der lokale Orca-Host. Entfernte Orca-Umgebungen werden ignoriert.

## Datenschutz

- Das Büro liest nur IDs, Elternverknüpfungen, Anbieter, Subagententyp, Zustand, Werkzeugname und Arbeitsbereichsordner aus `orca worktree ps` (und `orca agent list` als Rückfall). Prompts, Antworten und Werkzeugeingaben werden nie weitergegeben oder gespeichert.
- Der einzige Netzwerkzugriff des Adapters ist der Download der festgelegten Pixtuoid-Version von GitHub.
- Die App, das isolierte Agentenprofil und die Protokolle bleiben im Klon (`app/`, `perfil/`, `actividad/`). Um den Anbieter eines Workers zu benennen, schreibt das Büro eine einzeilige Karte (Name und Ordner) in das isolierte Profil und löscht sie, wenn der Worker geht oder das Büro schließt.
- Globale Einstellungen der Agenten und von Orca werden nicht verändert.

## Deinstallation

Das Büro schließen und den Klon-Ordner löschen. Sonst wird nichts installiert. Wer das pausierte Plugin installiert hat, führt **Pixtuoid: Remove downloaded app and local data** aus und deinstalliert es in Orca unter Settings → Plugins.

## Danksagung und Lizenz

- Dieser Adapter: [MIT-Lizenz](LICENSE).
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid) von Ivan Wang, MIT-Lizenz. Wird bei der Installation heruntergeladen, nicht weiterverteilt.
- Flaggen-Icons: [lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3, [MIT-Lizenz](docs/flags/LICENSE).
- Orca ist ein eigenständiges Produkt und nicht enthalten. Dies ist ein unabhängiger Adapter, kein offizielles Projekt von Pixtuoid oder Orca.
