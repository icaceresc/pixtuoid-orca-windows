<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md">English</a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md">Español</a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md"><b>Deutsch</b></a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md">日本語</a> &nbsp;·&nbsp;
  <a href="README.zh.md"><img src="docs/flags/cn.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.zh.md">中文</a> &nbsp;·&nbsp;
  <a href="README.ru.md"><img src="docs/flags/ru.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ru.md">Русский</a>
</p>

# Pixtuoid para Orca

Ein Orca-Plugin für Windows. Es öffnet ein schwebendes Pixel-Art-Fenster, in dem deine lokalen Orca-Agenten, ihre Worker und ihre Subagenten als Figuren erscheinen, jeweils mit Anbieter, Rolle und Projekt beschriftet. Du wählst, was das Fenster zeigt:

- **Das offizielle Büro** (`oficina`, die Voreinstellung): [Pixtuoid](https://github.com/pixtuoid/pixtuoid) v0.23.0 von Ivan Wang, wie veröffentlicht.
- **Dungeons & Agents** (`dungeon`): [Dungeons & Agents](https://github.com/icaceresc/dungeons-and-agents), ein Fantasy-Mod von Pixtuoid. Das Büro wird zu einem Lager und Dungeon-Etagen, jeder Agent zu einem Abenteurer, dessen Klasse seine Rolle zeigt, und ein Klick auf einen Abenteurer öffnet seine Sitzung in Orca.

![Demo-Arbeitsbereiche: zwei Orchestratoren mit Codex-, Antigravity- und Claude-Code-Workern und einem Explore-Subagenten](docs/office-roles.png)

## Was jeder Modus bietet

| Funktion | Offizielles Büro | Dungeons & Agents |
|---|---|---|
| Agenten, Worker und Subagenten als Figuren, mit Anbieter, Rolle und Projekt | Ja | Ja |
| Hinweis und Zähler in der Statusleiste, wenn ein Agent dich braucht | Ja | Ja |
| Befehle in Orcas Palette; Installation und Update aus Orca | Ja | Ja |
| Liest Orca, wenn Orca eine Änderung eines Agenten meldet, nicht in schnellem Takt | Ja | Ja |
| Teamfarbe | Nach Projekt | Nach Gruppe: ein Orchestrator, seine Worker und ihre Subagenten |
| Klasse, die die Rolle zeigt (companion, orchestrator, worker, subagent) | Nein | Ja |
| Werkzeuge als Fähigkeiten (`Spell (Bash)`, `Scry (Grep)`…); ein Aufruf der Orca-CLI als `Sending (Orca)` | Nein (als Werkzeug `Orca` angezeigt) | Ja |
| Klick auf einen Agenten, oder `Enter` auf ihm im `Tab`-Baum, öffnet seine Sitzung in Orca | Nein | Ja |

## Voraussetzungen

- Windows x64 mit DirectX 12
- Python 3.11+ (64 Bit) mit dem Starter `py`
- Orca 1.4.265 oder neuer, mit mindestens einem unterstützten Agenten. Ein neueres Orca als das geprüfte zeigt einmalig einen Hinweis und sollte weiter funktionieren.
- `claude`, `codex` oder `agy` im `PATH` für die Quellen Claude Code, Codex oder Antigravity

## Installation aus Orca

1. Öffne in Orca **Settings → Plugins**, wähle **From a Git URL…** und gib `https://github.com/icaceresc/pixtuoid-orca-windows` ein, oder führe `orca plugin install icaceresc/pixtuoid-orca-windows` aus. Vor der Installation zeigt Orca die Zugriffe, die das Plugin anfordert (unten).
2. Führe in der Befehlspalette **Pixtuoid: Install or update the office app** für das offizielle Büro aus, oder **Pixtuoid: Use Dungeons & Agents**. Der Befehl lädt den Build herunter, prüft seinen festgelegten SHA-256 und verbindet die Agenten, die Orca meldet.
3. Führe **Pixtuoid: Open office window** aus, oder klicke in Orcas Statusleiste auf **Pixtuoid**.

| Befehl | Was er tut |
|---|---|
| Pixtuoid: Open office window | Öffnet das Fenster; es läuft immer nur eines |
| Pixtuoid: Close office window | Schließt es und behält Größe und Position |
| Pixtuoid: Install or update the office app | Installiert oder aktualisiert den Build des zuletzt gewählten Modus |
| Pixtuoid: Use the official Pixtuoid office | Wechselt zum offiziellen Büro |
| Pixtuoid: Use Dungeons & Agents | Wechselt zu Dungeons & Agents |
| Pixtuoid: Remove downloaded app and local data | Löscht die App, das isolierte Agentenprofil und die Protokolle |

| Zugriff, den das Plugin anfordert | Wozu |
|---|---|
| `agent:read` | Erfahren, wann sich der Zustand eines Agenten ändert: Dann liest das Büro Orca, und Hinweis und Zähler folgen dem |
| `workspace:read` | Den Arbeitsbereich eines angeklickten Agenten über seinen Ordner finden |
| `workspace:write` | Die Sitzung dieses Agenten in den Vordergrund holen |
| `notifications:show` | Melden, wenn ein Agent dich braucht |

**Aktualisieren.** Orca aktualisiert das Plugin (**Settings → Plugins**, oder `orca plugin update icaceresc.pixtuoid-office`). **Pixtuoid: Install or update the office app** bringt die Büro-App auf den Build, den das Plugin für ihren Modus festlegt, und öffnet das Fenster wieder, wenn es offen war. Ein täglicher Workflow in diesem Repository sucht nach einer neuen stabilen Pixtuoid-Version, prüft ihren SHA-256, führt die Tests aus und schlägt den neuen Pin zur Prüfung vor; er führt nie selbst zusammen.

## Was es zeigt

Eine Figur pro Agent, den Orca auf diesem Rechner erkennt. Kinder tragen die Farbe ihres Teams und gehen mit ihrem Elternagenten. Mit `Tab` erscheint der Agentenbaum.

![Der Agentenbaum: jeder Orchestrator mit seinen Workern und Subagenten, ihren Werkzeugen und Zuständen](docs/office-dashboard.png)

| In Orca | Name im Büro |
|---|---|
| Die eigene Sitzung eines Orca-Bots (sein Strategic Companion) | `cc·punky · companion` |
| Agent der obersten Ebene | `cc·my-repo · agent` |
| Agent, der Worker startet, auch ein Worker | `cc·my-repo · orchestrator` |
| Orchestrierungs-Worker, beliebige Tiefe | `cx·worker · my-repo` |
| Worker eines anderen Anbieters als sein Elternagent | `cx·claude worker · my-repo` |
| Subagent, den Orca in einer Sitzung beobachtet | `cc·Explore subagent · my-repo` |
| Worker eines Antigravity-Agenten | `cx·worker of antigravity · my-repo` |
| Hintergrundbefehl, Monitor oder Werkzeugaufruf | Keine Figur |

Das Präfix ist der Anbieter (`cc` Claude Code, `cx` Codex, `oc` OpenCode, `ag` Antigravity), das Projekt ist der Ordner des Orca-Arbeitsbereichs. Ein Schreibtisch zeigt die ersten Zeichen des Namens; fahre über eine Figur oder drücke `Tab` für den ganzen Namen, den Elternagenten und das aktuelle Werkzeug.

| Anbieter | Als Agent | Als Worker | Native Subagenten |
|---|---|---|---|
| Claude Code | Ja | Ja | Ja |
| Codex | Ja (1.4.263) | Ja | Nicht geprüft |
| OpenCode | Ja (1.4.263) | Ja (1.4.263) | Nicht geprüft |
| Antigravity | Ja (1.4.263) | Ja | Orca meldet keine |

Live gesehen mit Orca 1.4.265 und 1.4.266, oder mit 1.4.263, wo angegeben. Alle vier Anbieter werden außerdem mit aufgezeichneten Orca-Antworten gegen das echte Pixtuoid geprüft.

## Bedienung

| Aktion | Eingabe |
|---|---|
| Verschieben | Einen leeren Bereich ziehen |
| Größe ändern | Die rechte untere Ecke ziehen |
| Zoom | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| Agentenbaum | `Tab` |
| Name, Elternagent, Ordner und Werkzeug eines Agenten | Mit der Maus darüberfahren |
| Die Sitzung eines Agenten in Orca öffnen (Dungeons & Agents) | Ihn anklicken, oder `Enter` auf ihm im `Tab`-Baum |
| Hilfe · Pause · Thema | `?` · `P` · `T` |
| Schließen und Größe und Position speichern | `Q`, oder **Pixtuoid: Close office window** |

## Sichtbare Zustände

| Orca-Zustand | Im Büro |
|---|---|
| `working` | Am Schreibtisch; das von Orca gemeldete Werkzeug (etwa `Bash`, `Edit`, `shell`) auf dem Monitor, im Tooltip und in der Zählung der Fußzeile |
| `waiting` / `blocked` | Bittet um Erlaubnis (`!`), gezählt als „braucht dich“; ein Desktop-Hinweis meldet es, solange das Büro offen ist, und Orcas Statusleiste zählt es |
| `done` / `idle` | Ruht oder läuft herum |
| Sitzung geschlossen, Subagent fertig oder abgebrochen | Geht durch die Tür; seine Kinder gehen zuerst |

## Einschränkungen

- **Ein Klick auf einen Agenten** öffnet seine Sitzung nur in Dungeons & Agents. Der Bereich eines Terminal-Agenten erhält den Fokus. Ein Orca-Chat hat kein Terminal, daher wird sein Arbeitsbereich gezeigt: Enthält ein Arbeitsbereich mehrere Chats (etwa das Zuhause eines Bots), zeigt Orca den dort zuletzt offenen, nicht unbedingt den angeklickten. Ein Subagent öffnet die Sitzung, in der er läuft.
- Pixtuoid verknüpft ein Kind nur mit einem Elternagenten desselben Anbieters. Ein Worker eines anderen Anbieters sitzt unter seinem Elternagenten mit dessen Präfix, und sein Name nennt seinen eigenen Anbieter (`cx·claude worker`). In einem Claude-Code-Baum ist auch das Präfix das des Workers.
- Pixtuoid kann unter einem Antigravity-Agenten der obersten Ebene keine Kinder zeichnen: Seine Worker erscheinen als eigene Kollegen namens `worker of antigravity`.
- Pixtuoid behält den Namen, mit dem ein Kollege zuerst erscheint; ein Agent, der erst später Worker startet, geht daher und kommt als orchestrator zurück. Die Rolle wird nie zurückgenommen.
- Orca meldet den Namen des Werkzeugs, aber weder Modell, Aufwand noch Token-Verbrauch, daher zeigt das Büro kein Modell, keinen Aufwand und keine Token-Anzeige.
- Mit dem Plugin liest das Büro Orca, sobald Orca eine Änderung eines Agenten meldet, sonst alle 6 Sekunden, solange ein Agent arbeitet, und alle 30 Sekunden, solange keiner arbeitet; ein Subagent kann daher so lange brauchen, bis er erscheint, und sehr kurze Werkzeuge können fehlen. Aus einem Klon liest es alle 1,5 bis 10 Sekunden.
- Hinweis und Zähler folgen den Zustandsänderungen, die Orca nach dem Start des Plugins meldet.
- Es erscheinen nur Subagenten, die Orca selbst beobachtet. Agenten, die beim Öffnen des Büros schon fertig sind, werden nicht gezeigt.
- Nur der lokale Orca-Host. Entfernte Orca-Umgebungen werden ignoriert.

## Datenschutz

- Das Büro liest aus `orca worktree ps` (und als Ausweichlösung aus `orca agent list`) nur IDs, Elternverknüpfungen, Anbieter, Subagententyp, Zustand, Werkzeugname, Ordner des Arbeitsbereichs und ob der Arbeitsbereich das Zuhause eines Bots ist. Den Befehl eines Shell-Werkzeugs sieht es sich nur an, um zu erkennen, ob er die Orca-CLI ausführt; Prompts, Antworten und Werkzeugeingaben werden nie weitergegeben oder gespeichert.
- Das Plugin hält den Zustand jedes Agenten und die IDs seines Bereichs, Terminals und Arbeitsbereichs im Speicher, solange es läuft. Der Hinweis zeigt den Sitzungstitel aus Orca, nur auf diesem Rechner.
- Der einzige Netzwerkzugriff des Adapters ist der Download des festgelegten Builds von GitHub.
- App, isoliertes Agentenprofil und Protokolle bleiben in `%LOCALAPPDATA%\PixtuoidOrca` (im Klon, wenn aus einem gestartet). Um den Anbieter eines Workers zu nennen, schreibt das Büro eine einzeilige Karte (Name und Ordner) ins isolierte Profil und löscht sie, wenn der Worker geht oder das Büro schließt. Ein Klick schreibt dort die IDs der angeklickten Sitzung, die das Plugin liest.
- Globale Einstellungen der Agenten und von Orca werden nicht verändert.

## Aus einem Klon ausführen

Das Plugin ist der unterstützte Weg. Um am Adapter zu arbeiten oder einen eigenen Build zu installieren:

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py                     # offizielles Büro; --modo dungeon für Dungeons & Agents
py -3 -m unittest -v test_oficina test_instalar
```

Öffne das Büro mit **`Abrir oficina.lnk`** und schließe es mit `Q` oder `py -3 oficina.py --stop`. Der Klick auf einen Agenten braucht das Plugin. Quellen einschränken: `py -3 instalar.py --sources claude-code codex`.

**Dein eigener Build.** Bei geschlossenem Büro installiert `py -3 instalar.py --modo dungeon --local C:\pfad\zu\dungeons-and-agents\target\release` `pixtuoid.exe` und `pixtuoid-hook.exe` aus einem lokalen Build, dazu die `LICENSE`, die daneben oder im Wurzelverzeichnis ihres Repositorys liegt. `--url https://... --sha256 <64 hex>` installiert ein Zip mit demselben Aufbau wie Pixtuoids Windows-Zip. `app/origen.json` hält fest, was installiert ist und in welchem Modus: Ein späterer einfacher Lauf behält deinen Build und sagt das, `--pinned` kehrt zum festgelegten Build des Modus zurück, und `--modo` wechselt den Modus. Die Befehle des Plugins tun dasselbe in `%LOCALAPPDATA%\PixtuoidOrca`.

## Deinstallieren

Führe **Pixtuoid: Remove downloaded app and local data** aus und deinstalliere dann das Plugin unter **Settings → Plugins**. Bei einem Klon genügt es, seinen Ordner zu löschen.

## Danksagung und Lizenz

- Dieses Plugin: [MIT-Lizenz](LICENSE).
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid) von Ivan Wang, MIT-Lizenz. Wird bei der Installation heruntergeladen, nicht weiterverbreitet.
- [Dungeons & Agents](https://github.com/icaceresc/dungeons-and-agents), ein Mod von Pixtuoid, MIT-Lizenz. Wird bei der Installation heruntergeladen, nicht weiterverbreitet.
- Flaggen-Icons: [lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3, [MIT-Lizenz](docs/flags/LICENSE).
- Orca ist ein eigenständiges Produkt und nicht enthalten. Dies ist ein unabhängiges Plugin, kein offizielles Projekt von Pixtuoid oder Orca.
