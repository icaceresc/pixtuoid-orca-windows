"""Show Orca's real local session states in the portable Pixtuoid window."""
import ctypes
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

LAB = Path(__file__).resolve().parent
# Code and data live apart when Orca's plugin runs this file: the plugin folder is
# replaced on every update, so the app, the isolated profile and logs go to HOME.
HOME = Path(os.environ.get("PIXTUOID_ORCA_HOME") or LAB).resolve()
APP = HOME / "app" / "pixtuoid.exe"
SHIM = APP.with_name("pixtuoid-hook.exe")
PROFILE = HOME / "perfil"
RUN = HOME / "actividad"
SOURCES = {"claude": "claude-code", "codex": "codex", "antigravity": "antigravity",
           "opencode": "opencode", "opencode2": "opencode"}
ACTIVE = {"working", "waiting", "blocked"}
POLL_SECONDS = 1.25
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def office_env(pipe=None):
    env = dict(os.environ, HOME=str(PROFILE), USERPROFILE=str(PROFILE),
               APPDATA=str(PROFILE / "Roaming"), LOCALAPPDATA=str(PROFILE / "Local"),
               CLAUDE_CONFIG_DIR=str(PROFILE / "claude"), CODEX_HOME=str(PROFILE / "codex"),
               OPENCODE_CONFIG_DIR=str(PROFILE / "opencode"), XDG_CONFIG_HOME=str(PROFILE / "config"),
               XDG_STATE_HOME=str(PROFILE / "estado"), XDG_DATA_HOME=str(PROFILE / "datos"),
               TEMP=str(PROFILE / "temporal"), TMP=str(PROFILE / "temporal"), PIXTUOID_HOOK=str(SHIM),
               WGPU_BACKEND="dx12")
    if pipe:
        env["PIXTUOID_SOCKET"] = pipe
    else:
        env.pop("PIXTUOID_SOCKET", None)
    env.pop("PIXTUOID_LOG", None)
    return env

def orca_json(orca, *args):
    response = subprocess.run([orca, *args, "--environment", "local", "--json"],
                              stdin=subprocess.DEVNULL, capture_output=True, timeout=10,
                              creationflags=NO_WINDOW, check=True)
    answer = json.loads(response.stdout)
    if not answer.get("ok"):
        raise RuntimeError("Orca did not return a successful session response")
    return answer["result"]

def clear_traces(trace):
    # Pixtuoid restores Codex sessions from rollout files at startup; the
    # synthetic rollouts of a previous run would come back as ghost coworkers.
    for rollout in trace.rglob("rollout-*.jsonl"):
        rollout.unlink()

def emit(env, source, payload, event=None):
    arguments = [str(SHIM), "--source", source]
    if source == "antigravity":
        arguments += ["--hook-event", event]
    elif event:
        payload["hook_event_name"] = event
    subprocess.run(arguments, input=json.dumps(payload).encode("utf-8"), env=env,
                   creationflags=NO_WINDOW, timeout=2, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, check=True)

# Sources whose Pixtuoid decoder links a child to a parent of the SAME source.
# Antigravity has no parent link in Pixtuoid v0.23.0, so its children stay roots.
LINKABLE = {"claude-code", "codex", "opencode"}
# Orca child-work states (AgentChildWorkView / AgentSubagentSnapshot) as office states.
CHILD_STATES = {"working": "working", "monitoring": "working", "waiting": "waiting",
                "blocked": "blocked", "idle": "done", "done": "done"}


def stable_id(identifier):
    identifier = identifier.removeprefix("orca_session_id:")
    try:
        return str(uuid.UUID(identifier))
    except ValueError:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, "orca:" + identifier))


class Agent:
    """One coworker: an Orca session, or a subagent Orca observed inside one.

    `source` is the Pixtuoid source it is drawn in. A child is drawn in its
    parent's source, because Pixtuoid links a child only to a parent of the
    same source; `provider` keeps the agent's real provider for the log.
    """

    def __init__(self, key, provider, cwd, trace, parent=None, label=None, owner=None, generation=0):
        self.key = key
        self.provider = provider
        self.parent = parent
        # The Orca agent this one belongs to, even when Pixtuoid cannot draw the link.
        self.owner = owner or parent
        self.source = parent.source if parent else provider
        self.id = stable_id(key.removeprefix("child:"))
        if generation:
            # Back after leaving (its dispatcher closed first): a new coworker, so
            # Pixtuoid never sees a start for an id it is still ending.
            self.id = str(uuid.uuid5(uuid.UUID(self.id), str(generation)))
        self.cwd = str(cwd)
        self.label = label
        self.state = None
        self.turn = 0
        now = dt.datetime.now().astimezone()
        self.rollout = trace / now.strftime("%Y/%m/%d") / f"rollout-{now:%Y-%m-%dT%H-%M-%S}-{self.id}.jsonl"

    @property
    def session(self):
        """The session id Pixtuoid keys this agent by; its children name it as their root."""
        if self.parent and self.source == "claude-code":
            return "agent-" + self.id
        return self.id

    def depth(self):
        return 0 if self.parent is None else 1 + self.parent.depth()

    def codex_record(self, kind, payload):
        self.rollout.parent.mkdir(parents=True, exist_ok=True)
        line = {"timestamp": dt.datetime.now(dt.timezone.utc).isoformat(), "type": kind, "payload": payload}
        with self.rollout.open("a", encoding="utf-8") as out:
            out.write(json.dumps(line) + "\n")

    def transition(self, env, state):
        prev = self.state
        if prev == state:
            return
        if state in ACTIVE and prev not in ACTIVE:
            self.turn += 1
        if self.parent and self.source != "opencode":
            self._child_hooks(env, prev, state)
        else:
            self._session_hooks(env, prev, state)
        self.state = state

    def _child_hooks(self, env, prev, state):
        # Claude Code and Codex subagent hooks: the root's session_id plus agent_id.
        common = {"session_id": self.parent.session, "agent_id": self.id, "cwd": self.cwd}
        def hook(event, **fields):
            emit(env, self.source, dict(common, **fields), event)
        if prev is None:
            hook("SubagentStart", agent_type=self.label or "subagent")
        if prev in ACTIVE:
            hook("Stop", turn_id=str(self.turn))
        if state == "working":
            hook("PreToolUse", tool_name="Orca: active turn", tool_use_id=f"{self.id}:{self.turn}",
                 tool_input={})
        elif state in {"blocked", "waiting"}:
            if self.source == "codex":
                hook("PermissionRequest", turn_id=str(self.turn), tool_name=f"Orca: {state}", tool_input={})
            else:
                hook("Notification", notification_type="permission_prompt", message=f"Orca: {state}")
        elif state == "closed":
            hook("SubagentStop", agent_transcript_path="")

    def _session_hooks(self, env, prev, state):
        source = self.source
        turn_id = str(self.turn)
        common = {"session_id": self.id, "cwd": self.cwd}
        def hook(event, **fields):
            emit(env, source, dict(common, **fields), event)
        def ag(event, **fields):
            emit(env, source, dict(conversationId=self.id, workspacePaths=[self.cwd], **fields), event)
        def oc(event, **fields):
            data = {"sessionID": self.id, "location": {"directory": self.cwd}, **fields}
            if self.parent and prev is None and event == "session.execution.started":
                data["parentID"] = self.parent.session
            emit(env, source, {"type": event, "turn": self.turn, "data": data})
        if source == "opencode":
            if state == "closed":
                oc("session.deleted")
            elif state == "working":
                if prev in {"blocked", "waiting"}:
                    oc("session.execution.succeeded")
                    self.turn += 1
                oc("session.execution.started")
            elif state in {"blocked", "waiting"}:
                if prev is None:
                    oc("session.execution.started")
                oc("permission.asked", action=f"Orca: {state}")
            elif prev is None and self.parent:
                # A child first seen idle still needs its parent link.
                oc("session.execution.started")
                oc("session.execution.succeeded")
            else:
                oc("session.execution.succeeded")
        elif source == "antigravity":
            if prev is None:
                ag("SessionStart")
            if prev in ACTIVE:
                ag("PostToolUse", stepIdx=1)
                ag("Stop")
            if state == "working":
                ag("PreToolUse", stepIdx=1, toolCall={"name": "Orca: active turn"})
            elif state in {"blocked", "waiting"}:
                ag("PreToolUse", stepIdx=1, toolCall={"name": "ask_question"})
        elif source == "codex":
            if prev is None:
                hook("SessionStart")
                self.codex_record("session_meta", {"id": self.id, "cwd": self.cwd, "originator": "Orca"})
            if prev in ACTIVE and prev != state:
                hook("Stop", turn_id=turn_id)
                self.codex_record("event_msg", {"type": "task_complete", "turn_id": turn_id})
            if state == "working":
                self.turn += 1
                self.codex_record("event_msg", {"type": "task_started", "turn_id": str(self.turn)})
            elif state in {"blocked", "waiting"}:
                hook("PermissionRequest", turn_id=turn_id, tool_name=f"Orca: {state}", tool_input={})
            elif state == "closed":
                hook("SessionEnd")
        else:
            if prev is None:
                hook("SessionStart")
            if prev in ACTIVE:
                hook("Stop")
            if state == "working":
                hook("PreToolUse", tool_name="Orca: active turn", tool_use_id=turn_id, tool_input={})
            elif state in {"blocked", "waiting"}:
                hook("Notification", notification_type="permission_prompt", message=f"Orca: {state}")
            elif state == "closed":
                hook("SessionEnd")


def child_rows(row):
    """Real subagents Orca observed in one agent row of `orca worktree ps`.

    `children` (AgentChildWorkView) wins over the hook roster `subagents`
    (AgentSubagentSnapshot), even when empty, as Orca's own contract says.
    Only kind "agent" runs an independent agent: background commands,
    monitors and workflows are tool work, not coworkers. Returns None when
    Orca cannot vouch for the list, so the caller keeps what it had.
    """
    if row.get("subagentObservation") != "live":
        return None
    if isinstance(row.get("children"), list):
        out = {}
        for child in row["children"]:
            if not isinstance(child, dict) or child.get("kind") != "agent" or not child.get("id"):
                continue
            if child.get("membership") == "settled":
                state = "closed"
            else:
                state = CHILD_STATES.get(child.get("state"))
            out["child:" + child["id"]] = (state, child.get("agentType") or child.get("name"))
        return out
    if isinstance(row.get("subagents"), list):
        return {"child:" + child["id"]: (CHILD_STATES.get(child.get("state")), child.get("agentType"))
                for child in row["subagents"] if isinstance(child, dict) and child.get("id")}
    return {}


class Office:
    """Projects Orca's agents, orchestrated workers and subagents into Pixtuoid."""

    def __init__(self, orca, env, trace, record, configured):
        self.orca, self.env, self.trace = orca, env, trace
        self.record, self.configured = record, configured
        self.agents = {}
        self.generations = {}
        self.paths = {}

    def cwd_for(self, row, ps_paths):
        worktree = row.get("worktreeId")
        if not worktree:
            return HOME
        if worktree in ps_paths:
            return ps_paths[worktree]
        if worktree not in self.paths:
            # One unresolvable workspace must not freeze every other session.
            try:
                result = orca_json(self.orca, "worktree", "show", "--worktree", f"id:{worktree}")
                self.paths[worktree] = result["worktree"]["path"]
            except (OSError, ValueError, KeyError, TypeError, RuntimeError,
                    subprocess.SubprocessError):
                self.paths[worktree] = worktree.partition("::")[2] or HOME
        return self.paths[worktree]

    def hierarchy(self):
        """Orca's parent links and subagents, or None when `worktree ps` is unavailable."""
        try:
            ps = orca_json(self.orca, "worktree", "ps")
            worktrees = list(ps.get("worktrees") or [])
        except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError,
                subprocess.SubprocessError):
            return None
        pane_session, parents, children, paths = {}, {}, {}, {}
        rows = []
        for worktree in worktrees:
            if worktree.get("worktreeId") and worktree.get("path"):
                paths[worktree["worktreeId"]] = worktree["path"]
            for row in worktree.get("agents") or []:
                if isinstance(row.get("orcaSessionId"), str) and row["orcaSessionId"]:
                    rows.append(row)
                    if row.get("paneKey"):
                        pane_session[row["paneKey"]] = row["orcaSessionId"]
        for row in rows:
            sid = row["orcaSessionId"]
            parent = pane_session.get(row.get("parentPaneKey"))
            if parent and parent != sid:
                parents[sid] = parent
            found = child_rows(row)
            if found is not None:
                children[sid] = found
        return parents, children, paths

    def sync(self):
        snapshot = orca_json(self.orca, "agent", "list")
        if snapshot.get("truncated"):
            raise RuntimeError("Orca returned a truncated session list")
        rows = {row["orcaSessionId"]: row for row in snapshot["agents"]
                if isinstance(row.get("orcaSessionId"), str) and row["orcaSessionId"]
                and row.get("agent") in SOURCES and row.get("state") in ACTIVE | {"done"}}
        hierarchy = self.hierarchy()
        parents, children, ps_paths = hierarchy if hierarchy else ({}, {}, {})

        def rank(sid, hops=0):
            # Parents before children, so a worker can attach under its dispatcher.
            parent = parents.get(sid)
            return 0 if parent not in rows or hops > 8 else 1 + rank(parent, hops + 1)

        seen = set()
        for sid in sorted(rows, key=rank):
            row = rows[sid]
            state = row["state"]
            agent = self.agents.get(sid)
            # A completed session predating this monitor is not a live coworker.
            if agent is None and state == "done":
                continue
            parent = self.agents.get(parents.get(sid))
            if agent is not None and parent is not None and self.linked(parent) is not agent.parent \
                    and agent not in self.lineage(parent):
                # First seen while `worktree ps` was unavailable: move it under the
                # dispatcher Orca now reports. A missing link never demotes a child.
                self.close(agent)
                agent = None
            if agent is None:
                agent = self.admit(sid, SOURCES[row["agent"]], self.cwd_for(row, ps_paths), parent)
                if agent is None:
                    continue
            seen.add(sid)
            self.move(agent, state)
            found = children.get(sid)
            if found is None:
                # Orca cannot vouch for this row's subagents now: keep them as they were.
                seen.update(key for key, kid in self.agents.items() if kid.owner is agent
                            and key.startswith("child:"))
                continue
            for key, (child_state, label) in found.items():
                kid = self.agents.get(key)
                if child_state is None:
                    if kid:  # unverifiable: keep a known one, never invent a new one
                        seen.add(key)
                    continue
                if child_state == "closed" or (kid is None and child_state == "done"):
                    continue
                if kid is None:
                    kid = self.admit(key, agent.provider, agent.cwd, agent, label)
                    if kid is None:
                        continue
                seen.add(key)
                self.move(kid, child_state)
        gone = [agent for key, agent in self.agents.items() if key not in seen]
        for agent in sorted(gone, key=Agent.depth, reverse=True):
            self.close(agent)

    @staticmethod
    def linked(parent):
        """The parent Pixtuoid can draw a child under, or None (Antigravity cannot parent)."""
        return parent if parent is not None and parent.source in LINKABLE else None

    @staticmethod
    def lineage(agent):
        while agent is not None:
            yield agent
            agent = agent.parent

    def admit(self, key, provider, cwd, owner, label=None):
        parent = self.linked(owner)
        source = parent.source if parent else provider
        if source not in self.configured:
            return None
        agent = Agent(key, provider, cwd, self.trace, parent, label, owner, self.generations.get(key, 0))
        self.agents[key] = agent
        return agent

    def move(self, agent, state):
        if state != agent.state:
            agent.transition(self.env, state)
            self.record("orca", agent, state)

    def close(self, agent):
        if agent.key not in self.agents:
            return
        # Pixtuoid ends a subtree with its root; mirror it so nothing lingers.
        for kid in [kid for kid in self.agents.values() if kid.parent is agent
                    or (kid.owner is agent and kid.key.startswith("child:"))]:
            self.close(kid)
        agent.transition(self.env, "closed")
        self.record("orca", agent, "closed")
        del self.agents[agent.key]
        self.generations[agent.key] = self.generations.get(agent.key, 0) + 1

def kernel32():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    for name in ("CreateMutexW", "OpenMutexW", "CreateEventW", "OpenEventW"):
        getattr(kernel, name).restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.SetEvent.argtypes = [ctypes.c_void_p]
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel.WaitForSingleObject.restype = ctypes.c_uint32
    return kernel

def names():
    """Mutex and stop-event names, one pair per data folder (clone or plugin home)."""
    tag = uuid.uuid5(uuid.NAMESPACE_URL, os.path.normcase(str(HOME))).hex
    return f"Local\\Pixtuoid-Orca-{tag}", f"Local\\Pixtuoid-Orca-Stop-{tag}"

def request_stop(wait_seconds=60):
    """Ask the running office of this data folder to close and wait until it has exited.

    Returns False when none was running. Raises TimeoutError if it is still running
    after `wait_seconds`, so callers never touch its files while it holds them.
    """
    kernel = kernel32()
    mutex_name, stop_name = names()
    event = kernel.OpenEventW(0x0002, False, stop_name)  # EVENT_MODIFY_STATE
    if not event:
        return False
    try:
        kernel.SetEvent(event)
    finally:
        kernel.CloseHandle(event)
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        mutex = kernel.OpenMutexW(0x00100000, False, mutex_name)  # SYNCHRONIZE
        if not mutex:
            return True
        kernel.CloseHandle(mutex)
        time.sleep(0.25)
    raise TimeoutError("The office is still closing")

def close_window(office):
    """Close our own floating window as its title bar would, so Pixtuoid saves its geometry."""
    user = ctypes.windll.user32
    found = []
    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def visit(window, _):
        owner = ctypes.c_ulong()
        user.GetWindowThreadProcessId(ctypes.c_void_p(window), ctypes.byref(owner))
        if owner.value == office.pid:
            found.append(window)
        return True
    user.EnumWindows(visit, None)
    for window in found:
        user.PostMessageW(ctypes.c_void_p(window), 0x0010, 0, 0)  # WM_CLOSE
    try:
        office.wait(timeout=10)
    except subprocess.TimeoutExpired:
        office.terminate()
        office.wait(timeout=8)

def main():
    if "--stop" in sys.argv[1:]:
        try:
            print("stopped" if request_stop() else "not-running")
        except TimeoutError:
            print("still-closing")
            raise SystemExit(1)
        return
    configured = set(json.loads((PROFILE / "fuentes.json").read_text(encoding="utf-8")))
    orca = shutil.which("orca.exe")
    if orca is None:
        raise FileNotFoundError("orca.exe")
    kernel = kernel32()
    mutex_name, stop_name = names()
    mutex = kernel.CreateMutexW(None, False, mutex_name)
    if not mutex:
        raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error() == 183:
        kernel.CloseHandle(mutex)
        return
    stop = kernel.CreateEventW(None, True, False, stop_name)
    if not stop:
        kernel.CloseHandle(mutex)
        raise ctypes.WinError(ctypes.get_last_error())

    RUN.mkdir(parents=True, exist_ok=True)
    pipe = rf"\\.\pipe\pixtuoid-orca-{uuid.uuid4().hex}"
    trace = PROFILE / "codex" / "sessions"
    trace.mkdir(parents=True, exist_ok=True)
    clear_traces(trace)
    env = office_env(pipe)
    audit = "--evidence" in sys.argv[1:]
    with (RUN / "orca-estados.jsonl").open("w", encoding="utf-8", buffering=1) as log:
        def record(channel, agent=None, state=None):
            entry = {"at": dt.datetime.now(dt.timezone.utc).isoformat(), "event": channel}
            if agent:
                entry.update(source=agent.source, provider=agent.provider, session=agent.id, state=state)
                if agent.parent:
                    entry["parent"] = agent.parent.id
            log.write(json.dumps(entry) + "\n")
        results = (RUN / "pixtuoid-estados.txt").open("w", encoding="utf-8") if audit else None
        window_log = (RUN / "pixtuoid-ventana.txt").open("w", encoding="utf-8")
        headless = office = None
        try:
            if audit:
                headless = subprocess.Popen([APP, "run", "--headless"], cwd=HOME, env=env,
                                            creationflags=NO_WINDOW, stdout=results, stderr=results)
            office = subprocess.Popen([APP, "floating", "--log-level", "debug" if audit else "warn"], cwd=HOME, env=env,
                                      creationflags=NO_WINDOW, stdout=window_log, stderr=window_log)
            (RUN / "ventana.pid").write_text(str(office.pid), encoding="ascii")
            # A first start compiles shaders for a fresh profile and can take many seconds.
            for _ in range(120):
                if kernel.WaitNamedPipeW(ctypes.c_wchar_p(pipe), 100):
                    break
                if office.poll() is not None:
                    raise RuntimeError(f"Floating window exited with code {office.returncode}")
                time.sleep(0.15)
            else:
                raise RuntimeError("Pixtuoid did not open its local pipe")
            record("ready")
            office_state = Office(orca, env, trace, record, configured)
            failed = False
            while office.poll() is None:
                try:
                    office_state.sync()
                    if failed:
                        record("orca-reconnected")
                    failed = False
                except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError,
                        subprocess.SubprocessError) as error:
                    if not failed:
                        record(f"orca-sync-error:{type(error).__name__}")
                    failed = True
                wait = int(1000 * (POLL_SECONDS if not failed else 3))
                if kernel.WaitForSingleObject(stop, wait) == 0:
                    record("stop-requested")
                    close_window(office)
            record(f"office-exit:{office.returncode}")
        finally:
            if office and office.poll() is None:
                close_window(office)
            if headless and headless.poll() is None:
                headless.terminate()
                headless.wait(timeout=8)
            if results:
                results.close()
            window_log.close()
            kernel.CloseHandle(stop)
            kernel.CloseHandle(mutex)

if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        ctypes.windll.user32.MessageBoxW(0, str(error), "Pixtuoid · Orca", 0x10)
