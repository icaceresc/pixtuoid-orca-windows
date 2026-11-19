<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md">English</a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md"><b>Español</b></a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md">Deutsch</a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md">日本語</a>
</p>

# Pixtuoid para Orca en Windows

Una oficina flotante en pixel art que muestra tus sesiones locales de agentes de Orca como compañeros de trabajo.

## Qué muestra

Un personaje por cada sesión de agente que Orca identifica en este equipo: **Claude Code, Codex, OpenCode y Antigravity**. El personaje trabaja mientras su agente ejecuta un turno, descansa cuando termina y se va cuando se cierra la sesión.

## Requisitos

- Windows x64 con DirectX 12
- Python 3.11 o posterior (64 bits)
- Orca abierto, con al menos un agente compatible instalado
- `claude`, `codex` o `agy` en `PATH` para las fuentes Claude Code, Codex o Antigravity

## Instalación rápida

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py
py -3 -m unittest -v test_oficina
```

El instalador descarga Pixtuoid v0.23.0, verifica su SHA-256 y conecta los agentes que reporta Orca. Para limitar las fuentes: `py -3 instalar.py --sources claude-code codex`.

## Abrir la oficina

Haz doble clic en **`Abrir oficina.lnk`** dentro del clon. Solo se ejecuta una oficina a la vez. Con `py -3 oficina.py --evidence` los estados quedan registrados en `actividad/`.

## Controles

| Acción | Entrada |
|---|---|
| Mover | Arrastrar una zona vacía |
| Redimensionar | Arrastrar la esquina inferior derecha |
| Zoom | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| Ayuda · Pausa · Tema | `?` · `P` · `T` |
| Cerrar y guardar tamaño y posición | `Q` |

## Estados visibles

| Estado en Orca | En la oficina |
|---|---|
| `working` | Personaje en su escritorio, activo |
| `waiting` / `blocked` | Personaje pidiendo permiso |
| `done` | Personaje en reposo |
| Sesión cerrada | El personaje se va |

## Limitaciones

- Solo sesiones principales de agentes. Los subagentes no tienen personaje propio.
- No se muestran las sesiones que ya habían terminado al abrir la oficina.
- Los estados reflejan el turno que conoce Orca, no herramientas, tokens ni razonamiento.
- Orca se consulta aproximadamente cada 2 segundos, así que los turnos muy cortos pueden no verse.
- `waiting` / `blocked` todavía no se han verificado con sesiones reales.
- Solo el host local de Orca. Se ignoran los entornos remotos.

## Privacidad

- De `orca agent list` la oficina solo usa el ID de sesión, el proveedor, el estado y la carpeta. Nunca reenvía ni guarda prompts o respuestas.
- El único acceso a la red del adaptador es la descarga de la versión fijada desde GitHub que hace el instalador.
- La aplicación, el perfil aislado de agentes y los registros quedan dentro del clon (`app/`, `perfil/`, `actividad/`). Git los ignora.
- No se modifica la configuración global de los agentes ni de Orca.

## Desinstalar

Cierra la oficina con `Q` y elimina la carpeta del clon. No se instala nada fuera de ella.

## Créditos y licencia

- Este adaptador: [licencia MIT](LICENSE).
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid), de Ivan Wang, con licencia MIT. Se descarga al instalar; no se redistribuye.
- Iconos de banderas: [lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3, [licencia MIT](docs/flags/LICENSE).
- Orca es un producto aparte y no se incluye. Este es un adaptador independiente, no un proyecto oficial de Pixtuoid ni de Orca.
