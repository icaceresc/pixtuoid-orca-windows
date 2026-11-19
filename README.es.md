<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md">English</a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md"><b>Español</b></a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md">Deutsch</a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md">日本語</a>
</p>

# Pixtuoid para Orca en Windows

Una oficina flotante en pixel art que muestra tus agentes locales de Orca, sus workers y sus subagentes como compañeros de trabajo. Se instala como plugin de Orca o se ejecuta desde un clon.

## Qué muestra

Un personaje por cada agente que Orca identifica en este equipo. Los hijos llevan una gorra del color de su equipo y se van con su padre.

| En Orca | En la oficina |
|---|---|
| Sesión de agente (Claude Code, Codex, OpenCode, Antigravity) | Su propio personaje |
| Worker lanzado con la orquestación de Orca, a cualquier profundidad | Hijo del agente que lo lanzó |
| Subagente que Orca observa dentro de una sesión | Hijo de esa sesión |
| Comando en segundo plano, monitor o llamada a herramienta | Sin personaje |

Verificado con sesiones reales en Orca 1.4.263:

| Proveedor | Como agente | Como worker hijo | Subagentes nativos |
|---|---|---|---|
| Claude Code | Sí | Sí | Sí |
| Codex | Sí | Sí | Sin verificar |
| OpenCode | Sí | Sí | Sin verificar |
| Antigravity | Sí | Sí | Orca no reporta ninguno |

## Requisitos

- Windows x64 con DirectX 12
- Python 3.11 o posterior (64 bits) con el lanzador `py`
- Orca 1.4.263 o posterior, abierto, con al menos un agente compatible instalado
- `claude`, `codex` o `agy` en `PATH` para las fuentes Claude Code, Codex o Antigravity

## Instalación rápida

**Como plugin de Orca**

```powershell
orca plugin install icaceresc/pixtuoid-orca-windows
```

Orca muestra lo que el plugin puede hacer y pide tu aprobación: ejecuta su propio código y no solicita permisos de Orca. Después ejecuta **Pixtuoid: Install or update the office app** desde la paleta de comandos. Descarga Pixtuoid v0.23.0 en `%LOCALAPPDATA%\PixtuoidOrca`, verifica su SHA-256 y conecta los agentes que reporta Orca.

**Desde un clon**

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py
py -3 -m unittest -v test_oficina
```

Para limitar las fuentes: `py -3 instalar.py --sources claude-code codex`.

## Abrir la oficina

- Plugin: **Pixtuoid: Open office window** y **Pixtuoid: Close office window** en la paleta de comandos.
- Clon: doble clic en **`Abrir oficina.lnk`**. Se cierra con `Q` o con `py -3 oficina.py --stop`.

La ventana flota fuera de Orca, así que puedes dejarla en un segundo monitor. Solo se ejecuta una oficina por instalación. Con `py -3 oficina.py --evidence` los estados quedan registrados en `actividad/`.

## Controles

| Acción | Entrada |
|---|---|
| Mover | Arrastrar una zona vacía |
| Redimensionar | Arrastrar la esquina inferior derecha |
| Zoom | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| Ayuda · Pausa · Tema | `?` · `P` · `T` |
| Cerrar y guardar tamaño y posición | `Q` o el comando de cierre |

## Estados visibles

| Estado en Orca | En la oficina |
|---|---|
| `working` | Personaje en su escritorio, activo |
| `waiting` / `blocked` | Personaje pidiendo permiso |
| `done` / `idle` | Personaje en reposo |
| Sesión cerrada, subagente terminado o cancelado | El personaje se va; sus hijos se van antes |

## Limitaciones

- Pixtuoid v0.23.0 solo enlaza un hijo con un padre del mismo proveedor. Un worker de otro proveedor se dibuja bajo su padre, con la gorra y la etiqueta de proveedor del padre.
- Pixtuoid no puede dibujar hijos bajo una sesión de Antigravity de nivel superior: sus workers aparecen como compañeros separados con el mismo color de equipo. Un worker de Antigravity que ya es hijo sí puede tener hijos.
- Solo aparecen los subagentes que Orca observa. La jerarquía viene de `orca worktree ps`, la única interfaz de Orca que la expone.
- No se muestran los agentes que ya habían terminado al abrir la oficina.
- Los estados reflejan el turno que conoce Orca, no herramientas, tokens ni razonamiento.
- Orca se consulta aproximadamente cada 1,25 segundos, así que los turnos muy cortos pueden no verse. Si Orca está ocupado, un hijo nuevo puede aparecer un momento antes de colocarse bajo su padre.
- `waiting` / `blocked` todavía no se han verificado con sesiones reales.
- Solo el host local de Orca. Se ignoran los entornos remotos.

## Privacidad

- De `orca agent list` y `orca worktree ps` la oficina solo lee IDs, enlaces padre-hijo, proveedor, tipo de agente, estado y carpeta. Nunca reenvía ni guarda prompts, respuestas o entradas de herramientas.
- El único acceso a la red del adaptador es la descarga de la versión fijada de Pixtuoid desde GitHub.
- La aplicación, el perfil aislado de agentes y los registros quedan en el clon o en `%LOCALAPPDATA%\PixtuoidOrca` (`app/`, `perfil/`, `actividad/`).
- No se modifica la configuración global de los agentes ni de Orca.

## Desinstalar

- Plugin: ejecuta **Pixtuoid: Remove downloaded app and local data** y luego desinstala el plugin en Orca, en Settings → Plugins.
- Clon: cierra la oficina y elimina la carpeta del clon.

No se instala nada más.

## Créditos y licencia

- Este adaptador: [licencia MIT](LICENSE).
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid), de Ivan Wang, con licencia MIT. Se descarga al instalar; no se redistribuye.
- Iconos de banderas: [lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3, [licencia MIT](docs/flags/LICENSE).
- Orca es un producto aparte y no se incluye. Este es un adaptador independiente, no un proyecto oficial de Pixtuoid ni de Orca.
