<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md">English</a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md"><b>Español</b></a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md">Deutsch</a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md">日本語</a> &nbsp;·&nbsp;
  <a href="README.zh.md"><img src="docs/flags/cn.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.zh.md">中文</a> &nbsp;·&nbsp;
  <a href="README.ru.md"><img src="docs/flags/ru.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ru.md">Русский</a>
</p>

# Pixtuoid para Orca

Un plugin de Orca para Windows. Abre una ventana flotante en pixel art donde tus agentes locales de Orca, sus workers y sus subagentes aparecen como personajes, cada uno con su proveedor, su rol y su proyecto. Tú eliges qué muestra la ventana:

- **La oficina oficial** (`oficina`, la opción por defecto): [Pixtuoid](https://github.com/pixtuoid/pixtuoid) v0.23.0 de Ivan Wang, tal como se publica.
- **Dungeons & Agents** (`dungeon`): [Dungeons & Agents](https://github.com/icaceresc/dungeons-and-agents), un mod de fantasía de Pixtuoid. La oficina se vuelve un campamento y pisos de mazmorra, cada agente un aventurero cuya clase muestra su rol, y al hacer clic en un aventurero se abre su sesión en Orca.

![Espacios de demostración: dos orquestadores con workers de Codex, Antigravity y Claude Code y un subagente Explore](docs/office-roles.png)

## Qué trae cada modo

| Función | Oficina oficial | Dungeons & Agents |
|---|---|---|
| Agentes, workers y subagentes como personajes, con proveedor, rol y proyecto | Sí | Sí |
| Aviso y contador en la barra de estado cuando un agente te necesita | Sí | Sí |
| Comandos en la paleta de Orca; instalar y actualizar desde Orca | Sí | Sí |
| Lee Orca cuando Orca informa un cambio de un agente, no con un temporizador rápido | Sí | Sí |
| Color del equipo | Por proyecto | Por grupo: un orquestador, sus workers y sus subagentes |
| Clase que muestra el rol (companion, orchestrator, worker, subagent) | No | Sí |
| Herramientas mostradas como habilidades (`Spell (Bash)`, `Scry (Grep)`…); una llamada a la CLI de Orca como `Sending (Orca)` | No (se muestra como la herramienta `Orca`) | Sí |
| Clic en un agente, o `Enter` sobre él en el árbol de `Tab`, para abrir su sesión en Orca | No | Sí |

## Requisitos

- Windows x64 con DirectX 12
- Python 3.11+ (64 bits) con el lanzador `py`
- Orca 1.4.265 o posterior, con al menos un agente compatible instalado. Un Orca más nuevo que el verificado muestra un aviso una sola vez y debería seguir funcionando.
- `claude`, `codex` o `agy` en `PATH` para las fuentes Claude Code, Codex o Antigravity

## Instalar desde Orca

1. En Orca, abre **Settings → Plugins**, elige **From a Git URL…** e introduce `https://github.com/icaceresc/pixtuoid-orca-windows`, o ejecuta `orca plugin install icaceresc/pixtuoid-orca-windows`. Antes de instalar, Orca muestra los accesos que pide el plugin (abajo).
2. En la paleta de comandos, ejecuta **Pixtuoid: Install or update the office app** para la oficina oficial, o **Pixtuoid: Use Dungeons & Agents**. Descarga la compilación, comprueba su SHA-256 fijado y conecta los agentes que informa Orca.
3. Ejecuta **Pixtuoid: Open office window**, o haz clic en **Pixtuoid** en la barra de estado de Orca.

| Comando | Qué hace |
|---|---|
| Pixtuoid: Open office window | Abre la ventana; solo funciona una a la vez |
| Pixtuoid: Close office window | La cierra y guarda su tamaño y posición |
| Pixtuoid: Install or update the office app | Instala o actualiza la compilación del último modo elegido |
| Pixtuoid: Use the official Pixtuoid office | Cambia a la oficina oficial |
| Pixtuoid: Use Dungeons & Agents | Cambia a Dungeons & Agents |
| Pixtuoid: Remove downloaded app and local data | Borra la app, el perfil aislado de agentes y los registros |

| Acceso que pide el plugin | Para qué |
|---|---|
| `agent:read` | Saber cuándo cambia el estado de un agente: la oficina lee Orca en ese momento, y el aviso y el contador lo siguen |
| `workspace:read` | Encontrar el espacio de trabajo de un agente clicado por su carpeta |
| `workspace:write` | Traer al frente la sesión de ese agente |
| `notifications:show` | Avisar cuando un agente te necesita |

**Actualizar.** Orca actualiza el plugin (**Settings → Plugins**, o `orca plugin update icaceresc.pixtuoid-office`). **Pixtuoid: Install or update the office app** lleva la app de la oficina a la compilación que el plugin fija para su modo y vuelve a abrir la ventana si estaba abierta. Un workflow diario de este repositorio busca una nueva versión estable de Pixtuoid, verifica su SHA-256, ejecuta las pruebas y propone el nuevo pin para revisión; nunca fusiona por sí mismo.

## Qué muestra

Un personaje por cada agente que Orca identifica en este equipo. Los hijos llevan el color de su equipo y se van con su padre. Pulsa `Tab` para ver el árbol de agentes.

![El árbol de agentes: cada orquestador con sus workers y subagentes, sus herramientas y estados](docs/office-dashboard.png)

| En Orca | Nombre en la oficina |
|---|---|
| Sesión propia de un bot de Orca (su Compañero Estratégico) | `cc·punky · companion` |
| Agente de nivel superior | `cc·my-repo · agent` |
| Agente que despacha workers, también un worker | `cc·my-repo · orchestrator` |
| Worker de orquestación, a cualquier profundidad | `cx·worker · my-repo` |
| Worker de otro proveedor que su padre | `cx·claude worker · my-repo` |
| Subagente que Orca observa dentro de una sesión | `cc·Explore subagent · my-repo` |
| Worker de un agente de Antigravity | `cx·worker of antigravity · my-repo` |
| Comando en segundo plano, monitor o llamada a herramienta | Sin personaje |

El prefijo es el proveedor (`cc` Claude Code, `cx` Codex, `oc` OpenCode, `ag` Antigravity) y el proyecto es la carpeta del espacio de trabajo de Orca. El escritorio muestra los primeros caracteres del nombre; pasa el puntero sobre un personaje o pulsa `Tab` para ver el nombre completo, su padre y su herramienta actual.

| Proveedor | Como agente | Como worker | Subagentes nativos |
|---|---|---|---|
| Claude Code | Sí | Sí | Sí |
| Codex | Sí (1.4.263) | Sí | Sin verificar |
| OpenCode | Sí (1.4.263) | Sí (1.4.263) | Sin verificar |
| Antigravity | Sí (1.4.263) | Sí | Orca no informa ninguno |

Visto en vivo en Orca 1.4.265 y 1.4.266, o en 1.4.263 donde se indica. Los cuatro proveedores también se comprueban contra el Pixtuoid real con respuestas de Orca grabadas.

## Controles

| Acción | Entrada |
|---|---|
| Mover | Arrastra una zona vacía |
| Cambiar tamaño | Arrastra la esquina inferior derecha |
| Zoom | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| Árbol de agentes | `Tab` |
| Nombre, padre, carpeta y herramienta de un agente | Pasa el puntero sobre él |
| Abrir la sesión de un agente en Orca (Dungeons & Agents) | Haz clic en él, o `Enter` sobre él en el árbol de `Tab` |
| Ayuda · Pausa · Tema | `?` · `P` · `T` |
| Cerrar y guardar tamaño y posición | `Q`, o **Pixtuoid: Close office window** |

## Estados visibles

| Estado en Orca | En la oficina |
|---|---|
| `working` | En el escritorio; la herramienta que informa Orca (como `Bash`, `Edit`, `shell`) en el monitor, en la descripción emergente y en el recuento del pie |
| `waiting` / `blocked` | Pidiendo permiso (`!`), contado como "te necesita"; un aviso de escritorio lo dice mientras la oficina está abierta, y la barra de estado de Orca lo cuenta |
| `done` / `idle` | Descansando o paseando |
| Sesión cerrada, subagente terminado o cancelado | Sale por la puerta; sus hijos salen primero |

## Limitaciones

- **Hacer clic en un agente** abre su sesión solo en Dungeons & Agents. El panel de un agente de terminal recibe el foco. Un chat de Orca no tiene terminal, así que se muestra su espacio de trabajo: cuando un espacio tiene varios chats (el hogar de un bot, por ejemplo), Orca muestra el último abierto allí, no necesariamente el clicado. Un subagente abre la sesión en la que corre.
- Pixtuoid solo enlaza un hijo con un padre del mismo proveedor. Un worker de otro proveedor se sienta bajo su padre con el prefijo del padre, y su nombre dice su propio proveedor (`cx·claude worker`). En un árbol de Claude Code el prefijo también es el del propio worker.
- Pixtuoid no puede dibujar hijos bajo un agente de Antigravity de nivel superior: sus workers aparecen como compañeros aparte llamados `worker of antigravity`.
- Pixtuoid conserva el nombre con el que aparece un compañero, así que un agente que empieza a despachar más tarde sale y vuelve como orquestador. El rol nunca se retira.
- Orca informa el nombre de la herramienta, no el modelo, el esfuerzo ni el uso de tokens, así que la oficina no muestra modelo, esfuerzo ni medidor de tokens.
- Con el plugin, la oficina lee Orca en cuanto Orca informa un cambio de un agente, y si no, cada 6 segundos mientras un agente trabaja y cada 30 segundos mientras ninguno lo hace, así que un subagente puede tardar eso en aparecer y pueden perderse herramientas muy cortas. Ejecutada desde un clon, lee cada 1,5 a 10 segundos.
- El aviso y el contador siguen los cambios de estado que informa Orca después de que arranca el plugin.
- Solo aparecen los subagentes que Orca observa. Los agentes que ya terminaron cuando se abre la oficina no se muestran.
- Solo el host local de Orca. Los entornos remotos de Orca se ignoran.

## Privacidad

- La oficina lee solo IDs, enlaces padre, proveedor, tipo de subagente, estado, nombre de herramienta, carpeta del espacio de trabajo y si el espacio es el hogar de un bot, de `orca worktree ps` (y de `orca agent list` como respaldo). Mira el comando de una herramienta de shell solo para saber si ejecuta la CLI de Orca; los prompts, las respuestas y las entradas de herramientas nunca se reenvían ni se guardan.
- El plugin guarda en memoria el estado de cada agente y los IDs de su panel, terminal y espacio de trabajo mientras funciona. El aviso muestra el título de la sesión que da Orca, solo en este equipo.
- El único acceso a la red del adaptador es la descarga de la compilación fijada desde GitHub.
- La app, el perfil aislado de agentes y los registros quedan en `%LOCALAPPDATA%\PixtuoidOrca` (en el clon cuando se ejecuta desde uno). Para nombrar el proveedor de un worker, la oficina escribe una tarjeta de una línea (nombre y carpeta) en el perfil aislado y la borra cuando el worker se va o la oficina se cierra. Un clic escribe ahí los IDs de la sesión clicada para que los lea el plugin.
- No se modifican los ajustes globales de los agentes ni de Orca.

## Ejecutar desde un clon

El plugin es la forma soportada. Para trabajar en el adaptador, o para instalar una compilación propia:

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py                     # oficina oficial; --modo dungeon para Dungeons & Agents
py -3 -m unittest -v test_oficina test_instalar
```

Abre la oficina con **`Abrir oficina.lnk`** y ciérrala con `Q` o `py -3 oficina.py --stop`. El clic en un agente necesita el plugin. Para limitar las fuentes: `py -3 instalar.py --sources claude-code codex`.

**Tu propia compilación.** Con la oficina cerrada, `py -3 instalar.py --modo dungeon --local C:\ruta\a\dungeons-and-agents\target\release` instala `pixtuoid.exe` y `pixtuoid-hook.exe` desde una compilación local, más el `LICENSE` que encuentre junto a ellos o en la raíz de su repositorio. `--url https://... --sha256 <64 hex>` instala un zip con la misma estructura que el zip de Pixtuoid para Windows. `app/origen.json` registra qué está instalado y su modo: una ejecución simple posterior conserva tu compilación y lo dice, `--pinned` vuelve a la compilación fijada del modo, y `--modo` cambia de modo. Los comandos del plugin hacen lo mismo en `%LOCALAPPDATA%\PixtuoidOrca`.

## Desinstalar

Ejecuta **Pixtuoid: Remove downloaded app and local data** y luego desinstala el plugin en **Settings → Plugins**. Un clon solo necesita que borres su carpeta.

## Créditos y licencia

- Este plugin: [Licencia MIT](LICENSE).
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid) de Ivan Wang, Licencia MIT. Se descarga al instalar, no se redistribuye.
- [Dungeons & Agents](https://github.com/icaceresc/dungeons-and-agents), un mod de Pixtuoid, Licencia MIT. Se descarga al instalar, no se redistribuye.
- Iconos de banderas: [lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3, [Licencia MIT](docs/flags/LICENSE).
- Orca es un producto aparte y no está incluido. Este es un plugin independiente, no un proyecto oficial de Pixtuoid ni de Orca.
