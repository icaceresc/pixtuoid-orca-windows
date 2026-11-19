# Pixtuoid para Orca en Windows

Una oficina flotante que muestra las sesiones locales de **Claude Code, Codex, Antigravity y OpenCode** que reporta Orca. Se instala en su propio clon y funciona sin A.I.W.S.

## Instalar

1. Abre Orca. Comprueba en PowerShell que tienes Python 3.11 o posterior de 64 bits y que la CLI de Orca ve tus agentes.

   ~~~powershell
   python --version
   orca agent installed --environment local --json
   ~~~

2. Desde el clon, ejecuta:

   ~~~powershell
   python instalar.py
   ~~~

   Si `python` apunta a una versión anterior, usa el lanzador de Windows con la versión instalada, por ejemplo **py -3.13 instalar.py**. El acceso directo usará el `pythonw.exe` de ese mismo Python.

   El instalador descarga Pixtuoid v0.23.0 para Windows x64 y comprueba su SHA-256. Usa **DirectX 12** para la ventana flotante. Para preparar cada perfil aislado, Claude Code, Codex y Antigravity necesitan sus comandos respectivos en PATH: **claude**, **codex** y **agy**. Si quieres configurar un subconjunto, usa por ejemplo **python instalar.py --sources claude-code codex**.

3. Antes del primer uso, ejecuta las pruebas de sincronización (sin conectar agentes):

   ~~~powershell
   python -m unittest -v test_oficina
   ~~~

4. Abre **Abrir oficina** con doble clic. En una sesión real de Orca inicia un turno y comprueba que el personaje se activa y vuelve a reposo cuando termina.

   Para registrar la comprobación en archivos locales, puedes abrir la oficina con **python oficina.py --evidence**. Los estados quedan en **actividad/**.

## Controles

- Arrastra una zona vacía para mover la ventana, incluso a otra pantalla.
- Arrastra la esquina inferior derecha para redimensionarla.
- Usa **Ctrl + +** o **Ctrl + -** para el zoom y **Ctrl + 0** para restablecerlo.
- Pulsa **Q** con la ventana enfocada para cerrarla y guardar su posición.

## Cómo obtiene la actividad

El adaptador consulta los estados de las sesiones con **orca agent list** y los traduce al formato de Pixtuoid. Solo proyecta los identificadores, el proveedor, el estado y la carpeta. Los eventos de pantalla representan el estado del turno que conoce Orca. Los archivos de Pixtuoid, las configuraciones aisladas y las trazas se generan dentro del clon y Git los ignora. Se usan los hooks que Orca ya tiene para reportar su actividad.

El adaptador muestra **sesiones locales identificadas por Orca**: una terminal todavía sin `orcaSessionId` aparecerá después de que su agente reporte la primera actividad. Al abrir la oficina, se omiten sesiones que ya estaban finalizadas para no mostrar antiguos agentes dormidos; las sesiones vistas trabajando sí pasan a reposo cuando terminan. Los subagentes que Orca no exponga como sesiones independientes no tienen personaje propio. Los estados se derivan de Orca: no representan herramientas, tokens o razonamiento interno por agente.

Verificado el 2026-11-19 en Windows 11 x64 con Python 3.13 y sesiones reales lanzadas desde Orca: Claude Code, Codex, OpenCode 2 y Antigravity mostraron su personaje y completaron trabajando → finalizado. Los estados `waiting`/`blocked` (permisos pendientes) y los subagentes no se observaron en esa prueba. Cada instalación depende de que Orca pueda listar esos agentes en su host local.

Si Orca tarda más de 5 s en responder (por ejemplo, al lanzar varios agentes a la vez), la oficina registra `orca-sync-error` y se resincroniza sola en el siguiente ciclo.

## Desinstalar

Cierra la ventana con **Q** y elimina el clon. El acceso directo, la aplicación, el perfil aislado y las trazas están dentro de esa carpeta.

[Pixtuoid v0.23.0](https://github.com/pixtuoid/pixtuoid/releases/tag/v0.23.0) · [Configuración de la ventana](https://pixtuoid.dev/config/#the-floating-window)
