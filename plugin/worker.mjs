// Orca plugin worker for Pixtuoid para Orca. It starts and stops the Python bridge that ships
// beside it (oficina.py, instalar.py), which reads Orca through its CLI and draws the office in
// Pixtuoid's floating window, a separate process that outlives this worker. The worker adds what
// only Orca's plugin API can do: it hears Orca's agent events, so the office reads Orca less; it
// brings forward the session of an adventurer clicked in Dungeons & Agents; and it says when an
// agent needs you.
import { spawn } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, watch, writeFileSync } from 'node:fs'
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
// What the office and this worker tell each other (oficina.py's CANAL).
const CANAL = join(HOME, 'canal')
const FOCUS_REQUEST = 'orca-foco.json'
const PULSE = join(CANAL, 'orca-pulso.json')
const OPEN_MARK = join(CANAL, 'oficina.json')
const ORIGIN = join(HOME, 'app', 'origen.json')
const ENV = {
  ...process.env, USERPROFILE: PROFILE, APPDATA, LOCALAPPDATA,
  PIXTUOID_ORCA_HOME: HOME, PYTHONDONTWRITEBYTECODE: '1', PYTHONUTF8: '1',
}
const WINDOWS_ONLY = 'Pixtuoid para Orca runs on Windows only.'
const NEEDS_YOU = new Set(['waiting', 'blocked'])
// One notice per agent and wait: an agent that flips back within this long stays quiet.
const NOTICE_QUIET_MS = 60_000
// Panes heard since the worker started; the oldest go first past this many.
const MAX_PANES = 500

let orca = null
let watcher = null
let handledRequest = 0
let focusing = Promise.resolve()
let needsShown = -1
const panes = new Map()
const noticed = new Map()

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

function readJson(path) {
  try {
    return JSON.parse(readFileSync(path, 'utf8'))
  } catch {
    return null
  }
}

function installed() {
  return existsSync(join(HOME, 'app', 'pixtuoid.exe')) && existsSync(join(HOME, 'perfil', 'fuentes.json'))
}

function mode() {
  return readJson(ORIGIN)?.modo === 'dungeon' ? 'Dungeons & Agents' : 'the official Pixtuoid office'
}

// The office marks itself open with its pid; a mark left by an office that died is not open.
function officeOpen() {
  const pid = readJson(OPEN_MARK)?.pid
  if (!Number.isInteger(pid)) return false
  try {
    process.kill(pid, 0)
    return true
  } catch {
    return false
  }
}

// Watches the office's requests once the installer owns HOME: creating it earlier would make
// the installer refuse a folder it did not make.
function watchCanal() {
  if (watcher || !existsSync(MARKER)) return
  mkdirSync(CANAL, { recursive: true })
  // A request older than this worker is no click of now.
  handledRequest = readJson(join(CANAL, FOCUS_REQUEST))?.seq ?? 0
  watcher = watch(CANAL, (_type, name) => { if (name === FOCUS_REQUEST) bringForward() })
  watcher.on('error', () => { watcher = null })
}

function unwatchCanal() {
  watcher?.close()
  watcher = null
}

async function open() {
  if (process.platform !== 'win32') return WINDOWS_ONLY
  if (!installed()) return 'Pixtuoid is not installed yet. Run "Pixtuoid: Install or update the office app" first.'
  // pyw runs the bridge with no console; detached so the window survives worker restarts.
  // PIXTUOID_ORCA_EVENTS tells it this worker pulses on Orca's events, so it reads Orca less.
  const child = spawn('pyw', ['-3', '-B', join(ROOT, 'oficina.py')], {
    cwd: ROOT, env: { ...ENV, PIXTUOID_ORCA_EVENTS: '1' }, detached: true, windowsHide: true, stdio: 'ignore',
  })
  child.on('error', () => {})
  child.unref()
  watchCanal()
  return `Opening ${mode()}. Only one office runs at a time.`
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

// Install or update in the remembered mode, or switch with `--modo`; an office the update
// closed opens again.
async function install(args = []) {
  if (process.platform !== 'win32') return WINDOWS_ONLY
  const stopped = await stop()
  if (stopped.code !== 0) return `Close the office first: ${lastLines(stopped.out)}`
  const { code, out } = await python('instalar.py', args, { timeoutMs: 300_000 })
  if (code !== 0) return `Install failed: ${lastLines(out)}`
  watchCanal()
  if (stopped.out.endsWith('stopped')) return `${lastLines(out)}\n${await open()}`
  return lastLines(out)
}

async function removeData() {
  if (!existsSync(HOME)) return 'There is no Pixtuoid data to remove.'
  // Only a folder our installer marked: never a clone or anything else at that path.
  if (!existsSync(MARKER) || !readFileSync(MARKER, 'utf8').startsWith('Pixtuoid for Orca data folder')) {
    return `Left ${HOME} untouched: it was not created by this plugin.`
  }
  const stopped = await stop()
  if (stopped.code !== 0) return `Close the office first: ${lastLines(stopped.out)}`
  unwatchCanal()
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

const samePath = (path) => String(path).replace(/\\/g, '/').replace(/\/+$/, '').toLowerCase()

async function workspaceAt(path) {
  if (!path || !orca.host.has('workspace.list')) return null
  const { workspaces } = await orca.host.call('workspace.list')
  return workspaces.find((workspace) => samePath(workspace.path) === samePath(path))?.id ?? null
}

// The office's request names a clicked adventurer's Orca session: its pane, as Orca's events
// name it, and its workspace folder. A terminal agent's pane is focused; a chat has no
// terminal, so its workspace is shown.
async function focusSession(request) {
  const pane = panes.get(request.paneKey)
  if (pane?.terminalId && orca.host.has('terminal.focus')) {
    const { focused } = await orca.host.call('terminal.focus', { terminalId: pane.terminalId })
    if (focused) return 'focused its terminal'
  }
  const workspaceId = pane?.workspaceId ?? await workspaceAt(request.path)
  if (!workspaceId) return 'found no workspace for it'
  await orca.host.call('workspace.open', { workspaceId })
  return 'opened its workspace'
}

function bringForward() {
  focusing = focusing.then(async () => {
    const request = readJson(join(CANAL, FOCUS_REQUEST))
    if (!request || !(request.seq > handledRequest)) return
    handledRequest = request.seq
    orca.log(`click: ${await focusSession(request)}`)
  }).catch((error) => orca.log(`click failed: ${error.code || error.message}`))
}

function pulse() {
  try {
    writeFileSync(PULSE, `${Date.now()}\n`)
  } catch {
    // The office still reads Orca on its timer.
  }
}

async function notify(event) {
  const now = Date.now()
  if (now - (noticed.get(event.paneKey) ?? 0) < NOTICE_QUIET_MS || !orca.host.has('notifications.show')) return
  noticed.set(event.paneKey, now)
  const who = (event.title || '').trim().slice(0, 80) || 'An agent'
  const what = event.state === 'blocked' ? 'is blocked and needs you' : 'is waiting for you'
  try {
    await orca.host.call('notifications.show', { title: 'Pixtuoid', body: `${who} ${what}.` })
  } catch (error) {
    orca.log(`notice failed: ${error.code || error.message}`)
  }
}

// The status bar item counts the agents that need you; Orca keeps this worker running while it
// has the item, which is what lets a click reach a session at any time.
async function showNeeds() {
  const count = [...panes.values()].filter((pane) => NEEDS_YOU.has(pane.state)).length
  if (count === needsShown || !orca.host.has('statusBar.update')) return
  needsShown = count
  const text = count ? `Pixtuoid: ${count} need${count === 1 ? 's' : ''} you` : 'Pixtuoid'
  try {
    await orca.host.call('statusBar.update', { id: 'office', text, tone: count ? 'warning' : 'neutral' })
  } catch (error) {
    orca.log(`status bar failed: ${error.code || error.message}`)
  }
}

async function onStatus(event) {
  const before = panes.get(event.paneKey)
  panes.delete(event.paneKey)
  panes.set(event.paneKey, {
    terminalId: event.terminalId ?? before?.terminalId ?? null,
    workspaceId: event.workspaceListId ?? before?.workspaceId ?? null,
    state: event.state,
  })
  if (panes.size > MAX_PANES) panes.delete(panes.keys().next().value)
  if (officeOpen()) {
    pulse()
    if (NEEDS_YOU.has(event.state) && !NEEDS_YOU.has(before?.state)) await notify(event)
  }
  await showNeeds()
}

export default function activate(api) {
  orca = api
  // Each result is shown in Orca and kept in `orca plugin logs` for support.
  const logged = (id, run) => orca.commands.register(id, async () => {
    const result = await run()
    orca.log(`${id}: ${result}`)
    return result
  })
  logged('pixtuoid.open', open)
  logged('pixtuoid.close', close)
  logged('pixtuoid.install', () => install())
  logged('pixtuoid.useOffice', () => install(['--modo', 'oficina']))
  logged('pixtuoid.useDungeon', () => install(['--modo', 'dungeon']))
  logged('pixtuoid.removeData', removeData)
  orca.events.on('agent.status.changed', onStatus)
  watchCanal()
}

export function deactivate() {
  unwatchCanal()
}
