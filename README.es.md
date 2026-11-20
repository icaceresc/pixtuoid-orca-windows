<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md">English</a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md"><b>Español</b></a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md">Deutsch</a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md">日本語</a>
</p>

# Pixtuoid para Orca en Windows

Una oficina flotante en pixel art que muestra tus agentes locales de Orca, sus workers y sus subagentes como compañeros de trabajo, cada uno con su proveedor, su rol y su proyecto. Se ejecuta desde un clon de este repositorio.

![Espacios de demostración: dos orquestadores con workers de Codex, Antigravity y Claude Code y un subagente Explore](docs/office-roles.png)

## Qué muestra

Un personaje por cada agente que Orca identifica en este equipo. Los hijos llevan una gorra del color de su equipo y se van con su padre. Pulsa `Tab` para ver el árbol de agentes.

![El árbol de agentes: cada orquestador con sus workers y subagentes, sus herramientas y estados](docs/office-dashboard.png)

| En Orca | Nombre en la oficina |
|---|---|
| Agente de nivel superior | `cc·my-repo` |
| Agente que despachó workers | `cc·my-repo · orchestrator` |
| Worker de orquestación, a cualquier profundidad | `cx·worker · my-repo` |
| Worker de otro proveedor que su padre | `cx·claude worker · my-repo` |
| Subagente que Orca observa dentro de una sesión | `cc·Explore subagent · my-repo` |
| Worker de un agente de Antigravity | `cx·worker of antigravity · my-repo` |
| Comando en segundo plano, monitor o llamada a herramienta | Sin personaje |

El prefijo es el proveedor (`cc` Claude Code, `cx` Codex, `oc` OpenCode, `ag` Antigravity) y el proyecto es la carpeta del espacio de trabajo de Orca. El escritorio muestra los primeros caracteres del nombre; pasa el puntero sobre un personaje o pulsa `Tab` para ver el nombre completo, su padre y su herramienta actual.

Visto en vivo con Pixtuoid v0.23.0 en Orca 1.4.266, o en 1.4.263 donde se indica. Los cuatro proveedores también se comprueban contra el Pixtuoid real con respuestas de Orca grabadas.

| Proveedor | Como agente | Como worker | Subagentes nativos |
|---|---|---|---|
| Claude Code | Sí | Sí | Sí |
| Codex | Sí (1.4.263) | Sí | Sin verificar |
| OpenCode | Sí (1.4.263) | Sí (1.4.263) | Sin verificar |
| Antigravity | Sí (1.4.263) | Sí | Orca no informa ninguno |

## Requisitos

- Windows x64 con DirectX 12
- Python 3.11+ (64 bits) con el lanzador `py`
- Orca 1.4.263 o posterior, abierto, con al menos un agente compatible instalado. Verificado hasta la 1.4.266; un Orca más nuevo muestra un aviso una sola vez y debería seguir funcionando.
- `claude`, `codex` o `agy` en el `PATH` para las fuentes Claude Code, Codex o Antigravity

## Instalación rápida

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py
py -3 -m unittest -v test_oficina
```

`instalar.py` descarga Pixtuoid v0.23.0 dentro del clon, verifica su SHA-256 y conecta los agentes que informa Orca. Para limitar las fuentes: `py -3 instalar.py --sources claude-code codex`.

**Actualizaciones.** Un flujo diario de este repositorio busca una nueva versión estable de Pixtuoid, verifica su SHA-256, ejecuta las pruebas y propone el nuevo pin para revisión; nunca lo fusiona por su cuenta. Después de traer una actualización, cierra la oficina y vuelve a ejecutar `py -3 instalar.py`.

El plugin de Orca (v2.0.0) está en pausa: todavía se instala y abre la oficina, pero sin las funciones de arriba. Usa el clon.

## Abrir la oficina

Haz doble clic en **`Abrir oficina.lnk`**. Ciérrala con `Q` o ejecuta `py -3 oficina.py --stop`.

La ventana flota fuera de Orca, así que puedes dejarla en un segundo monitor. Solo corre una oficina por carpeta. Todo lo que inicia corre con prioridad inferior a la normal y lee Orca con una sola llamada a la CLI por ciclo, así tu PC mantiene la prioridad. `py -3 oficina.py --evidence` registra los estados en `actividad/`.

## Controles

| Acción | Entrada |
|---|---|
| Mover | Arrastrar un área vacía |
| Cambiar tamaño | Arrastrar la esquina inferior derecha |
| Zoom | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| Árbol de agentes | `Tab` |
| Nombre, padre, carpeta y herramienta de un agente | Pasar el puntero encima |
| Ayuda · Pausa · Tema | `?` · `P` · `T` |
| Cerrar y guardar tamaño y posición | `Q`, o `py -3 oficina.py --stop` |

## Estados visibles

| Estado en Orca | En la oficina |
|---|---|
| `working` | En el escritorio; la herramienta que informa Orca (como `Bash`, `Edit`, `shell`) en el monitor, en la ficha y en el recuento del pie |
| `waiting` / `blocked` | Pidiendo permiso (`!`), contado como "te necesita" |
| `done` / `idle` | Descansando o paseando |
| Sesión cerrada, subagente terminado o cancelado | Sale por la puerta; sus hijos salen primero |

## Limitaciones

- Pixtuoid enlaza un hijo solo con un padre del mismo proveedor. Un worker de otro proveedor se ubica bajo su padre con el prefijo y el color del padre, y su nombre indica su propio proveedor (`cx·claude worker`). En un árbol de Claude Code también el prefijo es el del worker.
- Pixtuoid no puede dibujar hijos bajo un agente de Antigravity de nivel superior: sus workers aparecen como compañeros separados llamados `worker of antigravity`.
- El rol es el que muestra Orca cuando el agente aparece por primera vez. Un agente que empieza a despachar después conserva su nombre; sus workers igual aparecen bajo él.
- Orca informa el nombre de la herramienta, no el modelo, el esfuerzo ni el uso de tokens, así que la oficina no muestra modelo, esfuerzo ni medidor de tokens. Nunca se lee la entrada de la herramienta, así que no aparece ningún archivo ni comando junto a ella.
- Hacer clic en un personaje no enfoca su terminal: Orca no expone el proceso del agente y el enfoque de Pixtuoid en Windows solo cubre su propia integración con Antigravity.
- La oficina espera de 1,5 a 10 segundos entre lecturas de Orca, más mientras el PC u Orca están ocupados, así que turnos y herramientas muy cortos pueden no verse. Mientras Orca está ocupado, un hijo nuevo puede aparecer un momento antes de ubicarse bajo su padre.
- Solo aparecen los subagentes que el propio Orca observa. No se muestran los agentes ya terminados cuando se abre la oficina.
- Solo el host local de Orca. Se ignoran los entornos remotos de Orca.

## Privacidad

- La oficina lee solo IDs, enlaces de padre, proveedor, tipo de subagente, estado, nombre de herramienta y carpeta del espacio de trabajo desde `orca worktree ps` (y `orca agent list` como respaldo). Nunca reenvía ni guarda prompts, respuestas ni entradas de herramientas.
- El único acceso a la red del adaptador es la descarga de la versión fijada de Pixtuoid desde GitHub.
- La app, el perfil aislado de agentes y los registros quedan en el clon (`app/`, `perfil/`, `actividad/`). Para nombrar el proveedor de un worker, la oficina escribe una ficha de una línea (nombre y carpeta) en el perfil aislado y la borra cuando el worker se va o la oficina se cierra.
- No se modifica la configuración global de los agentes ni de Orca.

## Desinstalar

Cierra la oficina y borra la carpeta del clon. No se instala nada más. Si instalaste el plugin en pausa, ejecuta **Pixtuoid: Remove downloaded app and local data** y desinstálalo en Orca, en Settings → Plugins.

## Créditos y licencia

- Este adaptador: [licencia MIT](LICENSE).
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid) de Ivan Wang, licencia MIT. Se descarga al instalar, no se redistribuye.
- Iconos de banderas: [lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3, [licencia MIT](docs/flags/LICENSE).
- Orca es un producto aparte y no está incluido. Este es un adaptador independiente, no un proyecto oficial de Pixtuoid ni de Orca.
