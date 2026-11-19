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
APP = LAB / "app" / "pixtuoid.exe"
SHIM = APP.with_name("pixtuoid-hook.exe")
PROFILE = LAB / "perfil"
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
                              stdin=subprocess.DEVNULL, capture_output=True, timeout=5,
                              creationflags=NO_WINDOW, check=True)
    answer = json.loads(response.stdout)
    if not answer.get("ok"):
        raise RuntimeError("Orca did not return a successful session response")
    return answer["result"]

def emit(env, source, payload, event=None):
    arguments = [str(SHIM), "--source", source]
    if source == "antigravity":
        arguments += ["--hook-event", event]
    elif event:
        payload["hook_event_name"] = event
    subprocess.run(arguments, input=json.dumps(payload).encode("utf-8"), env=env,
                   creationflags=NO_WINDOW, timeout=2, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, check=True)

class Session:
    def __init__(self, row, cwd, trace):
        self.source = SOURCES[row["agent"]]
        identifier = row["orcaSessionId"].removeprefix("orca_session_id:")
        try:
            self.id = str(uuid.UUID(identifier))
        except ValueError:
            self.id = str(uuid.uuid5(uuid.NAMESPACE_URL, "orca:" + identifier))
        self.cwd = str(cwd)
        self.state = None
        self.turn = 0
        now = dt.datetime.now().astimezone()
        self.rollout = trace / now.strftime("%Y/%m/%d") / f"rollout-{now:%Y-%m-%dT%H-%M-%S}-{self.id}.jsonl"

    def codex_record(self, kind, payload):
        self.rollout.parent.mkdir(parents=True, exist_ok=True)
        line = {"timestamp": dt.datetime.now(dt.timezone.utc).isoformat(), "type": kind, "payload": payload}
        with self.rollout.open("a", encoding="utf-8") as out:
            out.write(json.dumps(line) + "\n")

    def transition(self, env, state):
        source = self.source
        prev = self.state
        if prev == state:
            return
        if state in ACTIVE and prev not in ACTIVE:
            self.turn += 1
        turn_id = str(self.turn)
        common = {"session_id": self.id, "cwd": self.cwd}
        def hook(event, **fields):
            emit(env, source, dict(common, **fields), event)
        def ag(event, **fields):
            emit(env, source, dict(conversationId=self.id, workspacePaths=[self.cwd], **fields), event)
        def oc(event, **fields):
            data = {"sessionID": self.id, "location": {"directory": self.cwd}, **fields}
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
        self.state = state

def sync(orca, env, trace, sessions, paths, record, configured):
    snapshot = orca_json(orca, "agent", "list")
    if snapshot.get("truncated"):
        raise RuntimeError("Orca returned a truncated session list")
    rows = {row["orcaSessionId"]: row for row in snapshot["agents"]
            if SOURCES.get(row.get("agent")) in configured and row.get("state") in ACTIVE | {"done"}}
    for sid, row in rows.items():
        state = row["state"]
        if state == "done" and sid not in sessions:
            if sid in paths:
                continue
            if not orca_json(orca, "agent", "show", sid)["places"]:
                paths[sid] = None
                continue
        if sid not in sessions:
            worktree = row.get("worktreeId")
            if worktree and worktree not in paths:
                result = orca_json(orca, "worktree", "show", "--worktree", f"id:{worktree}")
                paths[worktree] = result["worktree"]["path"]
            sessions[sid] = Session(row, paths.get(worktree, LAB), trace)
        session = sessions[sid]
        if state != session.state:
            session.transition(env, state)
            record("orca", session, state)
    for sid in sessions.keys() - rows.keys():
        session = sessions[sid]
        session.transition(env, "closed")
        record("orca", session, "closed")
        del sessions[sid]

def main():
    configured = set(json.loads((PROFILE / "fuentes.json").read_text(encoding="utf-8")))
    orca = shutil.which("orca.exe")
    if orca is None:
        raise FileNotFoundError("orca.exe")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateMutexW.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    checkout = uuid.uuid5(uuid.NAMESPACE_URL, os.path.normcase(str(LAB))).hex
    mutex = kernel.CreateMutexW(None, False, f"Local\\Pixtuoid-Orca-{checkout}")
    if not mutex:
        raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error() == 183:
        kernel.CloseHandle(mutex)
        return

    run = LAB / "actividad"
    run.mkdir(exist_ok=True)
    pipe = rf"\\.\pipe\pixtuoid-orca-{uuid.uuid4().hex}"
    trace = PROFILE / "codex" / "sessions"
    trace.mkdir(parents=True, exist_ok=True)
    env = office_env(pipe)
    audit = "--evidence" in sys.argv[1:]
    with (run / "orca-estados.jsonl").open("w", encoding="utf-8", buffering=1) as log:
        def record(channel, session=None, state=None):
            entry = {"at": dt.datetime.now(dt.timezone.utc).isoformat(), "event": channel}
            if session:
                entry.update(source=session.source, session=session.id, state=state)
            log.write(json.dumps(entry) + "\n")
        results = (run / "pixtuoid-estados.txt").open("w", encoding="utf-8") if audit else None
        window_log = (run / "pixtuoid-ventana.txt").open("w", encoding="utf-8")
        headless = office = None
        try:
            if audit:
                headless = subprocess.Popen([APP, "run", "--headless"], cwd=LAB, env=env,
                                            creationflags=NO_WINDOW, stdout=results, stderr=results)
            office = subprocess.Popen([APP, "floating", "--log-level", "debug" if audit else "warn"], cwd=LAB, env=env,
                                      creationflags=NO_WINDOW, stdout=window_log, stderr=window_log)
            (run / "ventana.pid").write_text(str(office.pid), encoding="ascii")
            for _ in range(45):
                if kernel.WaitNamedPipeW(ctypes.c_wchar_p(pipe), 100):
                    break
                if office.poll() is not None:
                    raise RuntimeError(f"Floating window exited with code {office.returncode}")
                time.sleep(0.15)
            else:
                raise RuntimeError("Pixtuoid did not open its local pipe")
            record("ready")
            sessions, paths = {}, {}
            failed = False
            while office.poll() is None:
                try:
                    sync(orca, env, trace, sessions, paths, record, configured)
                    if failed:
                        record("orca-reconnected")
                    failed = False
                except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
                    if not failed:
                        record(f"orca-sync-error:{type(error).__name__}")
                    failed = True
                time.sleep(POLL_SECONDS if not failed else 3)
            record(f"office-exit:{office.returncode}")
        finally:
            if headless and headless.poll() is None:
                headless.terminate()
                headless.wait(timeout=8)
            if results:
                results.close()
            window_log.close()
            kernel.CloseHandle(mutex)

if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        ctypes.windll.user32.MessageBoxW(0, str(error), "Pixtuoid · Orca", 0x10)
