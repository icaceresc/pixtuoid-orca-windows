// Orca plugin worker for Pixtuoid Office. It only starts and stops the Python bridge that
// ships beside it (oficina.py, instalar.py); the bridge reads Orca through its own CLI and
// draws the office in Pixtuoid's floating window, a separate process that outlives this
// worker. Nothing here calls the Orca host API, so the plugin asks for no capabilities.
import { spawn } from 'node:child_process'
import { existsSync, readdirSync, readFileSync, rmSync } from 'node:fs'
import { homedir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')
// Orca starts plugin workers with a reduced environment (no APPDATA). The Orca CLI needs
// APPDATA to find its runtime, so restore the standard per-user Windows folders.
const PROFILE = process.env.USERPROFILE || homedir()
const APPDATA = process.env.APPDATA || join(PROFILE, 'AppData', 'Roaming')
const LOCALAPPDATA = process.env.LOCALAPPDATA || join(PROFILE, 'AppData', 'Local')
// Data lives outside the plugin folder, which Orca replaces on every update.
const HOME = join(LOCALAPPDATA, 'PixtuoidOrca')
const MARKER = join(HOME, '.pixtuoid-orca-home')
const ENV = {
  ...process.env, USERPROFILE: PROFILE, APPDATA, LOCALAPPDATA,
  PIXTUOID_ORCA_HOME: HOME, PYTHONDONTWRITEBYTECODE: '1', PYTHONUTF8: '1',
}

function python(script, args = [], { timeoutMs = 60_000 } = {}) {
  return new Promise((done) => {
    const child = spawn('py', ['-3', '-B', join(ROOT, script), ...args], {
      cwd: ROOT, env: ENV, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'],
    })
    let out = ''
    child.stdout.on('data', (chunk) => { out += chunk })
    child.stderr.on('data', (chunk) => { out += chunk })
    const timer = setTimeout(() => child.kill(), timeoutMs)
    child.on('error', (error) => { clearTimeout(timer); done({ code: -1, out: String(error.message) }) })
    child.on('close', (code) => { clearTimeout(timer); done({ code, out: out.trim() }) })
  })
}

function lastLines(text, count = 3) {
  return text.split(/\r?\n/).filter(Boolean).slice(-count).join('\n')
}

function installed() {
  return existsSync(join(HOME, 'app', 'pixtuoid.exe')) && existsSync(join(HOME, 'perfil', 'fuentes.json'))
}

async function open() {
  if (process.platform !== 'win32') return 'Pixtuoid Office runs on Windows only.'
  if (!installed()) return 'Pixtuoid is not installed yet. Run "Pixtuoid: Install or update the office app" first.'
  // pyw runs the bridge with no console; detached so the window survives worker restarts.
  const child = spawn('pyw', ['-3', '-B', join(ROOT, 'oficina.py')], {
    cwd: ROOT, env: ENV, detached: true, windowsHide: true, stdio: 'ignore',
  })
  child.on('error', () => {})
  child.unref()
  return 'Opening the Pixtuoid office window. Only one runs at a time.'
}

// Waits until the office has exited, so nothing it holds is replaced or deleted under it.
function stop() {
  return python('oficina.py', ['--stop'], { timeoutMs: 75_000 })
}

async function close() {
  const { code, out } = await stop()
  if (code !== 0) return `The office did not close yet: ${lastLines(out)}`
  return out.endsWith('not-running')
    ? 'The Pixtuoid office is not open.'
    : 'Closed the Pixtuoid office; it saved its size and position.'
}

async function install() {
  if (process.platform !== 'win32') return 'Pixtuoid Office runs on Windows only.'
  const stopped = await stop()
  if (stopped.code !== 0) return `Close the office first: ${lastLines(stopped.out)}`
  const { code, out } = await python('instalar.py', [], { timeoutMs: 300_000 })
  return code === 0 ? lastLines(out) : `Install failed: ${lastLines(out)}`
}

async function removeData() {
  if (!existsSync(HOME)) return 'There is no Pixtuoid data to remove.'
  // Only a folder our installer marked: never a clone or anything else at that path.
  if (!existsSync(MARKER) || !readFileSync(MARKER, 'utf8').startsWith('Pixtuoid for Orca data folder')) {
    return `Left ${HOME} untouched: it was not created by this plugin.`
  }
  const stopped = await stop()
  if (stopped.code !== 0) return `Close the office first: ${lastLines(stopped.out)}`
  try {
    // The marker goes last, so a failed attempt can be retried.
    for (const name of readdirSync(HOME)) {
      if (join(HOME, name) !== MARKER) rmSync(join(HOME, name), { recursive: true, maxRetries: 3, retryDelay: 1000 })
    }
    rmSync(HOME, { recursive: true, maxRetries: 3, retryDelay: 1000 })
  } catch (error) {
    return `Could not remove ${HOME}: ${error.message}. Close the office and try again.`
  }
  return `Removed ${HOME}. Uninstall the plugin from Settings → Plugins to finish.`
}

export default function activate(orca) {
  // Each result is shown in Orca and kept in `orca plugin logs` for support.
  const logged = (id, run) => orca.commands.register(id, async () => {
    const result = await run()
    orca.log(`${id}: ${result}`)
    return result
  })
  logged('pixtuoid.open', open)
  logged('pixtuoid.close', close)
  logged('pixtuoid.install', install)
  logged('pixtuoid.removeData', removeData)
}
