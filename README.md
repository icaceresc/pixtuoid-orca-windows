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

   El instalador descarga Pixtuoid v0.23.0 para Windows x64 y comprueba su SHA-256. Usa **DirectX 12** para la ventana flotante. Para preparar cada perfil aislado, Claude Code, Codex y Antigravity necesitan sus comandos respectivos en PATH: **claude**, **codex** y **agy**. Si quieres configurar un subconjunto, usa por ejemplo **python instalar.py --sources claude-code codex**.

3. Abre **Abrir oficina** con doble clic. En una sesión real de Orca inicia un turno y comprueba que el personaje se activa y vuelve a reposo cuando termina.

   Para registrar la comprobación en archivos locales, puedes abrir la oficina con **python oficina.py --evidence**. Los estados quedan en **actividad/**.

## Controles

- Arrastra una zona vacía para mover la ventana, incluso a otra pantalla.
- Arrastra la esquina inferior derecha para redimensionarla.
- Usa **Ctrl + +** o **Ctrl + -** para el zoom y **Ctrl + 0** para restablecerlo.
- Pulsa **Q** con la ventana enfocada para cerrarla y guardar su posición.

## Cómo obtiene la actividad

El adaptador consulta los estados de las sesiones con **orca agent list** y los traduce al formato de Pixtuoid. Solo proyecta los identificadores, el proveedor, el estado y la carpeta. Los eventos de pantalla representan el estado del turno que conoce Orca. Los archivos de Pixtuoid, las configuraciones aisladas y las trazas se generan dentro del clon y Git los ignora. Se usan los hooks que Orca ya tiene para reportar su actividad.

Se verificó en Windows con sesiones reales de los cuatro proveedores. Cada instalación depende de que Orca pueda listar esos agentes en su host local.

## Desinstalar

Cierra la ventana con **Q** y elimina el clon. El acceso directo, la aplicación, el perfil aislado y las trazas están dentro de esa carpeta.

[Pixtuoid v0.23.0](https://github.com/pixtuoid/pixtuoid/releases/tag/v0.23.0) · [Configuración de la ventana](https://pixtuoid.dev/config/#the-floating-window)
