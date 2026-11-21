"""Show Orca's real local session states in the portable Pixtuoid window."""
import ctypes
import datetime as dt
import json
import ntpath
import os
from pathlib import Path
import shutil
import subprocess
import re
import sys
import threading
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
# What the office and the Orca plugin's worker tell each other: the worker pulses on every
# Orca agent event and opens the session a click names; the office writes those requests.
CANAL = HOME / "canal"
# Dungeons & Agents appends a line per click on a coworker here (its PIXTUOID_FOCUS_FEED).
FOCUS_FEED = CANAL / "pixtuoid-foco.jsonl"
FOCUS_REQUEST = CANAL / "orca-foco.json"
PULSE = CANAL / "orca-pulso.json"
# Present while an office runs, so the worker pulses and notifies only then.
OPEN_MARK = CANAL / "oficina.json"
SOURCES = {"claude": "claude-code", "codex": "codex", "antigravity": "antigravity",
           "opencode": "opencode", "opencode2": "opencode"}
ACTIVE = {"working", "waiting", "blocked"}
# Each Orca CLI call starts a Node runtime (about 1 s of CPU on a busy PC), so the office
# reads Orca once per cycle and waits at least twice as long as that read took.
POLL_SECONDS = 1.5
MAX_POLL_SECONDS = 10
# Run from the Orca plugin, its worker pulses on every agent event, so a timed read only
# catches what no event reports: subagents and workers coming and going under a busy agent.
EVENT_POLL_BUSY = 6
EVENT_POLL_IDLE = 30
# A pulse waits this long for the rest of its burst, and never reads sooner than this
# after the last read ended.
EVENT_SETTLE = 0.3
EVENT_GAP = 1.0
# A busy PC can take many seconds to start the CLI; killing it early only wastes that work.
ORCA_TIMEOUT = 30
# The newest Orca this adapter was verified against. A newer Orca most likely still works:
# the office says so once per version, so a change in Orca's output is not a silent surprise.
VERIFIED_ORCA = "1.4.266"
# Everything the office starts runs below normal priority, so the Human's own work wins.
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)


def office_env(pipe=None):
    env = dict(os.environ, HOME=str(PROFILE), USERPROFILE=str(PROFILE),
               APPDATA=str(PROFILE / "Roaming"), LOCALAPPDATA=str(PROFILE / "Local"),
               CLAUDE_CONFIG_DIR=str(PROFILE / "claude"), CODEX_HOME=str(PROFILE / "codex"),
               OPENCODE_CONFIG_DIR=str(PROFILE / "opencode"), XDG_CONFIG_HOME=str(PROFILE / "config"),
               XDG_STATE_HOME=str(PROFILE / "estado"), XDG_DATA_HOME=str(PROFILE / "datos"),
               TEMP=str(PROFILE / "temporal"), TMP=str(PROFILE / "temporal"), PIXTUOID_HOOK=str(SHIM),
               WGPU_BACKEND="dx12", PIXTUOID_FOCUS_FEED=str(FOCUS_FEED))
    if pipe:
        env["PIXTUOID_SOCKET"] = pipe
    else:
        env.pop("PIXTUOID_SOCKET", None)
    env.pop("PIXTUOID_LOG", None)
    return env

class CliCalls:
    """Orca CLI calls made, so the office can log how many it makes a minute."""

    def __init__(self):
        self.total = 0


CLI_CALLS = CliCalls()


def orca_json(orca, *args):
    CLI_CALLS.total += 1
    response = subprocess.run([orca, *args, "--environment", "local", "--json"],
                              stdin=subprocess.DEVNULL, capture_output=True, timeout=ORCA_TIMEOUT,
                              creationflags=NO_WINDOW)
    try:
        answer = json.loads(response.stdout)
    except ValueError:
        answer = None
    if not isinstance(answer, dict):
        answer = {}
    if response.returncode or not answer.get("ok"):
        # Orca's own error code and message, never the command's data.
        error = answer.get("error")
        error = error if isinstance(error, dict) else {}
        detail = error.get("code") or response.stderr.decode("utf-8", "replace").strip()[-300:]
        raise RuntimeError(f"orca {' '.join(args[:2])} failed ({response.returncode}): "
                           f"{detail} {error.get('message', '')}".strip())
    return answer["result"]

def clear_traces(trace, names=None):
    # Pixtuoid restores Codex sessions from rollout files at startup; the
    # synthetic rollouts of a previous run would come back as ghost coworkers.
    for rollout in trace.rglob("rollout-*.jsonl"):
        rollout.unlink()
    # The same for the provider name cards of a previous run (see Agent.name_card).
    if names is not None and names.is_dir():
        for card in names.rglob("agent-*.jsonl"):
            card.unlink()
        for folder in sorted(names.rglob("*"), key=lambda path: len(path.parts), reverse=True):
            if folder.is_dir() and not any(folder.iterdir()):
                folder.rmdir()

def emit(env, source, payload, event=None):
    arguments = [str(SHIM), "--source", source]
    if source == "antigravity":
        arguments += ["--hook-event", event]
    elif event:
        payload["hook_event_name"] = event
    subprocess.run(arguments, input=json.dumps(payload).encode("utf-8"), env=env,
                   creationflags=NO_WINDOW, timeout=10, stdout=subprocess.DEVNULL,
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


# Pixtuoid's two-letter name prefixes, reused for the provider name on a name card.
SHORT = {"claude-code": "cc", "codex": "cx", "opencode": "oc", "antigravity": "ag"}
NAMES = {"claude-code": "claude", "codex": "codex", "opencode": "opencode", "antigravity": "antigravity"}
# Tool names Pixtuoid gives a meaning of its own (a delegation that ends its subtree,
# a permission prompt). Orca's tool name is still shown, as plain text.
RESERVED_TOOLS = {"agent", "task", "subagent", "spawn_agent", "ask_permission", "ask_question"}
UNSAFE_TEXT = str.maketrans({c: " " for c in '\\/:*?"<>|\t\r\n'})
# Pixtuoid sweeps an agent that sends nothing for 5 to 60 minutes (by source and state),
# while Orca may list it for hours: the office repeats each agent's state this often.
HEARTBEAT_SECONDS = 120


def clean_text(text, limit=40):
    """Printable, path-safe text for a label part or a tool name; '' when nothing is left."""
    if not isinstance(text, str):
        return ""
    text = "".join(c for c in text.translate(UNSAFE_TEXT) if c.isprintable())
    return " ".join(text.split())[:limit].strip(" .")


# Shell tools of the agents Orca runs. When one runs the Orca CLI the office shows the tool
# "Orca" (Dungeons & Agents shows it as the skill `Sending (Orca)`); only that verdict leaves the office.
SHELL_TOOLS = {"bash", "powershell", "shell", "exec_command", "local_shell", "run_shell_command",
               "run_command"}
# `orca` (or orca.exe / orca.cmd, bare or by path) followed by one of its top-level commands
# (`orca --help`), so a path or a word that merely says orca is not a call.
ORCA_COMMAND = re.compile(
    r"(?:^|[\s;&|(`])[\"']?(?:[^\s;&|(`\"']*[\\/])?orca(?:\.exe|\.cmd)?[\"']?\s+"
    r"(?:agent|agent-context|artifacts|account|automations|bot|calendar|chat|claude-teams|contacts|"
    r"diagnostics|docs|drive|environment|file|gmail|google|host|open|orchestration|plugin|ports|"
    r"project|reference|repo|search|serve|sheets|skills|slack|status|terminal|vm|workspace|"
    r"worktree)\b")


def tool_label(name, command=None):
    """The name Pixtuoid shows for Orca's current tool: its name only, never its input."""
    name = clean_text(name)
    if not name:
        return None
    if name.lower() in SHELL_TOOLS and isinstance(command, str) and ORCA_COMMAND.search(command):
        return "Orca"
    return f"Orca: {name}" if name.lower() in RESERVED_TOOLS else name


class Placeholder:
    """A suspended, never-resumed process whose pid stands for one Antigravity agent.

    Pixtuoid has no end hook for Antigravity: it ends an Antigravity session when the
    `_pid` its hooks carry exits. Each Antigravity coworker gets its own placeholder, so
    ending it walks exactly that coworker out. The placeholders sit in a kill-on-close job,
    so they never outlive the office, even if it is killed.
    """

    job = None

    def __init__(self):
        """Raises OSError, leaving nothing behind, when the job cannot hold the placeholder."""
        if Placeholder.job is None:
            Placeholder.job = kill_on_close_job()
        if not Placeholder.job:
            raise OSError("no kill-on-close job for Antigravity placeholders")
        self.process = subprocess.Popen([str(SHIM), "--version"], stdin=subprocess.DEVNULL,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                        creationflags=NO_WINDOW | 0x00000004)  # CREATE_SUSPENDED
        kernel = ctypes.windll.kernel32
        kernel.OpenProcess.restype = ctypes.c_void_p
        handle = kernel.OpenProcess(0x0101, False, self.process.pid)  # SET_QUOTA | TERMINATE
        held = bool(handle) and bool(kernel.AssignProcessToJobObject(ctypes.c_void_p(Placeholder.job),
                                                                      ctypes.c_void_p(handle)))
        if handle:
            kernel.CloseHandle(ctypes.c_void_p(handle))
        if not held:
            self.end()
            raise OSError("the placeholder could not join the kill-on-close job")
        self.pid = self.process.pid

    def end(self):
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=5)


def kill_on_close_job():
    """A job object whose processes end when the office's last handle to it closes."""
    kernel = ctypes.windll.kernel32
    kernel.CreateJobObjectW.restype = ctypes.c_void_p
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        return None

    class Limits(ctypes.Structure):
        _fields_ = [("a", ctypes.c_int64), ("b", ctypes.c_int64), ("flags", ctypes.c_uint32),
                    ("c", ctypes.c_size_t), ("d", ctypes.c_size_t), ("e", ctypes.c_uint32),
                    ("f", ctypes.c_size_t), ("g", ctypes.c_uint32), ("h", ctypes.c_uint32),
                    ("io", ctypes.c_uint64 * 6), ("i", ctypes.c_size_t * 4)]
    limits = Limits(flags=0x2000)  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not kernel.SetInformationJobObject(ctypes.c_void_p(job), 9, ctypes.byref(limits), ctypes.sizeof(limits)):
        kernel.CloseHandle(ctypes.c_void_p(job))
        return None
    return job


class Agent:
    """One coworker: an Orca session, or a subagent Orca observed inside one.

    `source` is the Pixtuoid source it is drawn in. A child is drawn in its
    parent's source, because Pixtuoid links a child only to a parent of the
    same source; `provider` keeps the agent's real provider.

    Pixtuoid names a coworker `<source prefix>·<basename of its cwd>`, so the office
    sends a folder whose basename is the coworker's title: its project (the Orca
    workspace folder) and its role, plus its provider when that differs from the
    prefix (`cx·my-repo · claude worker`). Only the title is synthetic; the parent
    folder is the real one.
    """

    # Folder of Claude Code transcripts Pixtuoid watches in the isolated profile.
    # None (tests) leaves Pixtuoid's default label.
    names = None

    def __init__(self, key, provider, cwd, trace, parent=None, label=None, owner=None, generation=0,
                 role=None):
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
        self.workdir = str(cwd)
        self.project = clean_text(ntpath.basename(self.workdir.rstrip("\\/")), 30) or "orca"
        self.role = role
        self.cwd = self.workdir if self.title == self.project else \
            ntpath.join(ntpath.dirname(self.workdir.rstrip("\\/")), self.title)
        self.label = label
        self.state = None
        self.tool = None
        self.turn = 0
        self.calls = 0
        self.call = None
        self.sent_at = 0.0
        self.placeholder = None
        now = dt.datetime.now().astimezone()
        self.rollout = trace / now.strftime("%Y/%m/%d") / f"rollout-{now:%Y-%m-%dT%H-%M-%S}-{self.id}.jsonl"

    @property
    def title(self):
        """What follows Pixtuoid's source prefix (its desk badge shows about ten characters).

        A top-level agent reads its project (`my-repo`, `my-repo · orchestrator`); a worker
        or subagent reads its role first (`worker · my-repo`, `Explore subagent · my-repo`),
        with its provider when the prefix is its parent's (`claude worker · my-repo`).
        """
        role = self.role
        if role and self.provider != self.source:
            role = f"{NAMES[self.provider]} {role}"
        return self.compose(role)

    def compose(self, role):
        if not role:
            return self.project
        return f"{self.project} · {role}" if self.owner is None else f"{role} · {self.project}"

    @property
    def session(self):
        """The session id Pixtuoid keys this agent by; its children name it as their root."""
        if self.parent and self.source == "claude-code":
            return "agent-" + self.id
        return self.id

    @property
    def name_card(self):
        """A one-line Claude Code subagent transcript naming this child's real provider.

        Pixtuoid reads it as the child's own transcript (same `agent-<id>` key) and
        relabels it from `attributionAgent`, so a Codex worker under a Claude parent
        reads "cx·my-repo · worker" while keeping its place in the tree. Only Claude Code
        has such a label path in Pixtuoid v0.23.0.
        """
        if (self.names is None or not self.parent or self.source != "claude-code"
                or self.provider == "claude-code"):
            return None
        return self.names / self.parent.session / "subagents" / f"agent-{self.id}.jsonl"

    def write_card(self):
        # Only a label: a file the profile refuses must never stall the office.
        card = self.name_card
        if card:
            title = self.compose(self.role)
            line = {"type": "assistant", "attributionAgent": f"{SHORT[self.provider]}·{title}",
                    "cwd": self.cwd, "sessionId": self.parent.session, "message": {"content": []}}
            try:
                card.parent.mkdir(parents=True, exist_ok=True)
                card.write_text(json.dumps(line) + "\n", encoding="utf-8")
            except OSError:
                pass

    def drop_card(self):
        card = self.name_card
        if card:
            try:
                card.unlink(missing_ok=True)
            except OSError:
                pass  # cleared at the next start

    def depth(self):
        return 0 if self.parent is None else 1 + self.parent.depth()

    def codex_record(self, kind, payload):
        self.rollout.parent.mkdir(parents=True, exist_ok=True)
        line = {"timestamp": dt.datetime.now(dt.timezone.utc).isoformat(), "type": kind, "payload": payload}
        with self.rollout.open("a", encoding="utf-8") as out:
            out.write(json.dumps(line) + "\n")

    def send(self, env, payload, event=None):
        # `_pid` spares the hook its process-table walk. For Antigravity it is this
        # coworker's own placeholder, whose exit Pixtuoid reads as the session's end.
        payload["_pid"] = self.placeholder.pid if self.placeholder else os.getpid()
        emit(env, self.source, payload, event)
        self.sent_at = time.monotonic()

    def transition(self, env, state, tool=None):
        """Move to an Orca state; while working, `tool` is Orca's current tool name (or None)."""
        prev = self.state
        tool = tool if state == "working" else None
        if prev == state and tool == self.tool:
            return
        if prev == state:  # still working, another tool
            self._end_call(env)
            self.tool = tool
            self._start_call(env)
            return
        if state in ACTIVE and prev not in ACTIVE:
            self.turn += 1
        if prev == "working":
            self._end_call(env)
        self.tool = tool
        self._enter(env, prev, state)
        self.state = state

    def heartbeat(self, env):
        """Repeat the current state with the same ids, so Pixtuoid never sweeps a live agent."""
        if self.state is None or self.state == "closed":
            return
        self._enter(env, self.state, self.state)

    # Per source: what enters a state, and how a tool call starts and ends.

    def _hook(self, env, event, **fields):
        if self.parent and self.source in {"claude-code", "codex"}:
            common = {"session_id": self.parent.session, "agent_id": self.id, "cwd": self.cwd}
        else:
            common = {"session_id": self.id, "cwd": self.cwd}
        self.send(env, dict(common, **fields), event)

    def _ag(self, env, event, **fields):
        self.send(env, dict(conversationId=self.id, workspacePaths=[self.cwd], **fields), event)

    def _oc(self, env, event, **fields):
        data = {"sessionID": self.id, "location": {"directory": self.cwd}, **fields}
        if self.parent and self.state is None and event == "session.execution.started":
            data["parentID"] = self.parent.session
        self.send(env, {"type": event, "turn": self.turn, "data": data})

    def _rollout(self):
        # Codex turns and tool calls ride its rollout file; children name their parent there too.
        return self.source == "codex"

    def _start_call(self, env):
        self.calls += 1
        self.call = f"{self.id}:{self.turn}:{self.calls}"
        self._send_call(env)

    def _send_call(self, env):
        name = self.tool or "Orca: active turn"
        if self.source == "claude-code":
            self._hook(env, "PreToolUse", tool_name=name, tool_use_id=self.call, tool_input={})
        elif self.source == "codex":
            self.codex_record("response_item", {"type": "function_call", "name": name,
                                                "call_id": self.call, "arguments": "{}"})
        elif self.source == "opencode":
            self._oc(env, "session.tool.input.started", id=self.call, name=name)
        else:
            self._ag(env, "PreToolUse", stepIdx=self.calls, toolCall={"name": name})

    def _end_call(self, env):
        if self.call is None:
            return
        if self.source == "claude-code":
            self._hook(env, "PostToolUse", tool_name=self.tool or "Orca: active turn",
                       tool_use_id=self.call, tool_input={}, tool_response={})
        elif self.source == "codex":
            self.codex_record("response_item", {"type": "function_call_output", "call_id": self.call,
                                                "output": ""})
        elif self.source == "opencode":
            self._oc(env, "session.tool.success", id=self.call)
        else:
            self._ag(env, "PostToolUse", stepIdx=self.calls)
        self.call = None

    def _enter(self, env, prev, state):
        """Send what moves Pixtuoid from `prev` to `state` (prev == state: a heartbeat)."""
        source, child = self.source, bool(self.parent) and self.source in {"claude-code", "codex"}
        repeat = prev == state
        turn_id = str(self.turn)
        if source == "opencode":
            if state == "closed":
                self._oc(env, "session.deleted")
            elif state == "working":
                if repeat:
                    return self._send_call(env)
                if prev in {"blocked", "waiting"}:
                    self._oc(env, "session.execution.succeeded")
                    self.turn += 1
                self._oc(env, "session.execution.started")
                self._start_call(env)
            elif state in {"blocked", "waiting"}:
                if prev is None:
                    self._oc(env, "session.execution.started")
                self._oc(env, "permission.asked", action=f"Orca: {state}")
            elif prev is None and self.parent:
                # A child first seen idle still needs its parent link.
                self._oc(env, "session.execution.started")
                self._oc(env, "session.execution.succeeded")
            else:
                self._oc(env, "session.execution.succeeded")
            return
        if source == "antigravity":
            if state == "closed":
                if self.placeholder:
                    self.placeholder.end()
                return
            if prev is None:
                try:
                    self.placeholder = placeholder()
                except (OSError, subprocess.SubprocessError):
                    # Without one it still shows; Pixtuoid's sweep then ends it, as before.
                    self.placeholder = None
                self._ag(env, "SessionStart")
            if prev in ACTIVE and not repeat:
                self._ag(env, "Stop")
            if state == "working":
                return self._send_call(env) if repeat else self._start_call(env)
            if state in {"blocked", "waiting"}:
                self._ag(env, "PreToolUse", stepIdx=self.calls + 1, toolCall={"name": "ask_question"})
            elif repeat:
                self._ag(env, "Stop")
            return
        # Claude Code and Codex: sessions and (as `agent_id` under the root's session) children.
        if prev is None:
            self._hook(env, "SubagentStart" if child else "SessionStart",
                       **({"agent_type": self.label or "subagent"} if child else {}))
            if child:
                self.write_card()
            if self._rollout():
                meta = {"id": self.id, "cwd": self.cwd, "originator": "Orca"}
                if child:
                    meta["parent_thread_id"] = self.parent.session
                self.codex_record("session_meta", meta)
        if prev in ACTIVE and not repeat:
            self._hook(env, "Stop", turn_id=turn_id)
            if self._rollout():
                self.codex_record("event_msg", {"type": "task_complete", "turn_id": turn_id})
        if state == "working":
            if repeat:
                return self._send_call(env)
            if self._rollout():
                self.codex_record("event_msg", {"type": "task_started", "turn_id": turn_id})
            self._start_call(env)
        elif state in {"blocked", "waiting"}:
            if source == "codex":
                self._hook(env, "PermissionRequest", turn_id=turn_id, tool_name=f"Orca: {state}", tool_input={})
            else:
                self._hook(env, "Notification", notification_type="permission_prompt", message=f"Orca: {state}")
        elif state == "closed":
            if child:
                self._hook(env, "SubagentStop", agent_transcript_path="")
                self.drop_card()
            else:
                self._hook(env, "SessionEnd")
        elif repeat:  # an idle heartbeat: a turn end on an idle coworker changes nothing else
            if self._rollout():
                self.codex_record("event_msg", {"type": "task_complete", "turn_id": turn_id})
            else:
                self._hook(env, "Stop", turn_id=turn_id)


def placeholder():
    return Placeholder()


def in_bots_folder(path):
    """Whether `path` is an Orca bot's home folder: `orca bot list` keeps each bot in
    `<home>/.orca/bots/<name>`."""
    if not isinstance(path, str) or not path:
        return False
    parts = [part.lower() for part in ntpath.normpath(path).rstrip("\\").split("\\")]
    return len(parts) >= 3 and parts[-3:-1] == [".orca", "bots"]


def bot_home(worktree):
    """Whether an Orca workspace is a bot's own home, where that bot (the owner's Strategic
    Companion) chats.

    Orca 1.4.265's `worktree ps` names the bot every workspace it works in is under (`bot`),
    and marks only the bot's own folder `botHome: true`: a workspace the bot created is
    under it but not its home, so its agents keep their own roles. Without the field (an
    older Orca) the bot's folder still tells.
    """
    if "botHome" in worktree:
        return worktree.get("botHome") is True
    return in_bots_folder(worktree.get("path"))


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
            # The subagent's type only: a child's `name` or description may be user text.
            out["child:" + child["id"]] = (state, child.get("agentType"))
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
        # Each Orca session's pane, which the plugin's worker knows from Orca's events.
        self.panes = {}

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
            except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError,
                    subprocess.SubprocessError):
                self.paths[worktree] = worktree.partition("::")[2] or HOME
        return self.paths[worktree]

    def read_orca(self):
        """One snapshot of Orca: agent rows plus parent links, subagents and folders.

        `orca worktree ps` alone carries each agent's provider, state, parent pane and
        children, so a cycle normally costs one CLI call. `orca agent list` is read only
        when `ps` fails or is truncated; the hierarchy is then whatever `ps` could vouch for.
        """
        try:
            ps = orca_json(self.orca, "worktree", "ps")
            worktrees = [w for w in ps.get("worktrees") or [] if isinstance(w, dict)]
        except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError,
                subprocess.SubprocessError):
            ps, worktrees = None, []
        pane_session, parents, children, paths, homes = {}, {}, {}, {}, set()
        ps_rows = []
        for worktree in worktrees:
            if worktree.get("worktreeId") and worktree.get("path"):
                paths[worktree["worktreeId"]] = worktree["path"]
            if worktree.get("worktreeId") and bot_home(worktree):
                homes.add(worktree["worktreeId"])
            for row in worktree.get("agents") or []:
                if isinstance(row, dict) and isinstance(row.get("orcaSessionId"), str) and row["orcaSessionId"]:
                    ps_rows.append(dict(row, agent=row.get("agentType"), worktreeId=worktree.get("worktreeId")))
                    if row.get("paneKey"):
                        pane_session[row["paneKey"]] = row["orcaSessionId"]
        for row in ps_rows:
            sid = row["orcaSessionId"]
            parent = pane_session.get(row.get("parentPaneKey"))
            if parent and parent != sid:
                parents[sid] = parent
            found = child_rows(row)
            if found is not None:
                children[sid] = found
        # Orca older than 1.4.266 may leave a row's provider or state out of `ps`.
        complete = all(row.get("agent") and row.get("state") for row in ps_rows)
        if ps is not None and not ps.get("truncated") and complete:
            agents = ps_rows
        else:
            snapshot = orca_json(self.orca, "agent", "list")
            if snapshot.get("truncated"):
                raise RuntimeError("Orca returned a truncated session list")
            agents = snapshot["agents"]
        return agents, parents, children, paths, homes

    def companion(self, row, homes, ps_paths):
        """Whether `row` is a bot's own session: Orca marks its workspace the bot's home, or,
        when `worktree ps` could not say, the workspace is a bot's folder."""
        worktree = row.get("worktreeId")
        if worktree in homes:
            return True
        return worktree not in ps_paths and in_bots_folder(str(self.cwd_for(row, ps_paths)))

    def role_for(self, sid, row, parent, parents, rows, dispatchers, homes, ps_paths):
        """The role a top-level coworker or worker states in its title, which Pixtuoid reads
        as its class: a bot's own session is the companion, one that dispatches workers an
        orchestrator (dispatching is the role that matters, a dispatched worker's included),
        another dispatched one a worker, and any other top-level session an agent."""
        if self.companion(row, homes, ps_paths):
            return "companion"
        if sid in dispatchers:
            return "orchestrator"
        if parents.get(sid) in rows:
            if parent is None or self.linked(parent):
                return "worker"
            return f"worker of {NAMES[parent.provider]}"
        return "agent"

    def sync(self):
        agents, parents, children, ps_paths, homes = self.read_orca()
        rows = {row["orcaSessionId"]: row for row in agents
                if isinstance(row.get("orcaSessionId"), str) and row["orcaSessionId"]
                and row.get("agent") in SOURCES and row.get("state") in ACTIVE | {"done"}}

        def rank(sid, hops=0):
            # Parents before children, so a worker can attach under its dispatcher.
            parent = parents.get(sid)
            return 0 if parent not in rows or hops > 8 else 1 + rank(parent, hops + 1)

        dispatchers = {parents[sid] for sid in rows if sid in parents}
        self.panes = {sid: row.get("paneKey") for sid, row in rows.items()}
        seen = set()
        for sid in sorted(rows, key=rank):
            row = rows[sid]
            state = row["state"]
            agent = self.agents.get(sid)
            # A completed session predating this monitor is not a live coworker.
            if agent is None and state == "done":
                continue
            parent = self.agents.get(parents.get(sid))
            role = self.role_for(sid, row, parent, parents, rows, dispatchers, homes, ps_paths)
            if agent is not None and parent is not None and self.linked(parent) is not agent.parent \
                    and agent not in self.lineage(parent):
                # First seen while `worktree ps` was unavailable: move it under the
                # dispatcher Orca now reports. A missing link never demotes a child.
                self.close(agent)
                agent = None
            if agent is not None and role == "orchestrator" and agent.role not in {"orchestrator",
                                                                                 "companion"}:
                # It has started dispatching. Pixtuoid keeps the title a coworker arrived
                # with, so it returns as an orchestrator; the role is never taken back.
                self.close(agent)
                agent = None
            if agent is None:
                agent = self.admit(sid, SOURCES[row["agent"]], self.cwd_for(row, ps_paths), parent,
                                   role=role)
                if agent is None:
                    continue
            seen.add(sid)
            self.move(agent, state, tool_label(row.get("toolName"), row.get("toolInput")))
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
                    kind = clean_text(label, 24)
                    kid = self.admit(key, agent.provider, agent.workdir, agent, label,
                                     role=f"{kind} subagent" if kind else "subagent")
                    if kid is None:
                        continue
                seen.add(key)
                self.move(kid, child_state)
        gone = [agent for key, agent in self.agents.items() if key not in seen]
        for agent in sorted(gone, key=Agent.depth, reverse=True):
            self.close(agent)
        now = time.monotonic()
        for agent in list(self.agents.values()):
            if now - agent.sent_at > HEARTBEAT_SECONDS:
                agent.heartbeat(self.env)

    def busy(self):
        """Whether an agent is working, so subagents may come and go between events."""
        return any(agent.state == "working" for agent in self.agents.values())

    def focus_target(self, source, session_id):
        """The Orca session a click on the coworker Pixtuoid keys by (source, session_id) opens:
        its own, or for a subagent the session it runs in. None when no coworker matches."""
        for agent in self.agents.values():
            if agent.source == source and session_id in (agent.session, agent.id):
                while agent.key.startswith("child:") and agent.owner is not None:
                    agent = agent.owner
                return {"orcaSessionId": agent.key, "paneKey": self.panes.get(agent.key),
                        "path": agent.workdir}
        return None

    @staticmethod
    def linked(parent):
        """The parent Pixtuoid can draw a child under, or None (Antigravity cannot parent)."""
        return parent if parent is not None and parent.source in LINKABLE else None

    @staticmethod
    def lineage(agent):
        while agent is not None:
            yield agent
            agent = agent.parent

    def admit(self, key, provider, cwd, owner, label=None, role=None):
        parent = self.linked(owner)
        source = parent.source if parent else provider
        if source not in self.configured:
            return None
        agent = Agent(key, provider, cwd, self.trace, parent, label, owner, self.generations.get(key, 0),
                      role)
        self.agents[key] = agent
        return agent

    def move(self, agent, state, tool=None):
        if state != agent.state:
            agent.transition(self.env, state, tool)
            self.record("orca", agent, state)
        elif state == "working" and tool != agent.tool:
            agent.transition(self.env, state, tool)

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
    kernel.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel.WaitForSingleObject.restype = ctypes.c_uint32
    kernel.WaitForMultipleObjects.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p),
                                              ctypes.c_bool, ctypes.c_uint32]
    kernel.WaitForMultipleObjects.restype = ctypes.c_uint32
    kernel.FindNextChangeNotification.argtypes = [ctypes.c_void_p]
    kernel.FindCloseChangeNotification.argtypes = [ctypes.c_void_p]
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

def orca_version_notice(orca):
    """A one-time notice when the local Orca is newer than VERIFIED_ORCA, else None."""
    try:
        answer = subprocess.run([orca, "--version"], stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=ORCA_TIMEOUT, creationflags=NO_WINDOW).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    found = re.search(r"(\d+)\.(\d+)\.(\d+)", answer or "")
    if not found:
        return None
    version = found.group(0)
    if tuple(map(int, found.groups())) <= tuple(map(int, VERIFIED_ORCA.split("."))):
        return None
    seen = PROFILE / "orca-version-notified.txt"
    try:
        if seen.read_text(encoding="utf-8").strip() == version:
            return None
    except OSError:
        pass
    try:
        seen.write_text(version + "\n", encoding="utf-8")
    except OSError:
        pass
    return (f"Orca {version} is newer than {VERIFIED_ORCA}, the version this office was verified "
            "with. It should keep working; if agents look wrong, check "
            "github.com/icaceresc/pixtuoid-orca-windows for an update.")

def poll_wait(seconds_taken, failed=False, events=False, busy=False):
    """Seconds to wait before the next timed read: at least twice what the last read took.

    With Orca's events (`events`) a pulse wakes the office on every agent change, so the
    timer only waits for what no event reports, longer while no agent is working.
    """
    if events and not failed:
        return max(EVENT_POLL_BUSY if busy else EVENT_POLL_IDLE, 2 * seconds_taken)
    return min(MAX_POLL_SECONDS, max(3.0 if failed else POLL_SECONDS, 2 * seconds_taken))


def write_json(path, value):
    """Replace `path` whole, so its reader never sees half a request."""
    partial = path.with_name(path.name + ".tmp")
    partial.write_text(json.dumps(value) + "\n", encoding="utf-8")
    os.replace(partial, path)


class FocusFeed:
    """The clicks Dungeons & Agents appends to FOCUS_FEED, each whole line once."""

    def __init__(self, path):
        self.path, self.offset, self.partial = path, 0, b""

    def read_new(self):
        try:
            with self.path.open("rb") as feed:
                feed.seek(self.offset)
                data = feed.read()
        except OSError:
            return []
        self.offset += len(data)
        *lines, self.partial = (self.partial + data).split(b"\n")
        clicks = []
        for line in lines:
            try:
                click = json.loads(line)
            except ValueError:
                continue
            if isinstance(click, dict) and isinstance(click.get("source"), str) \
                    and isinstance(click.get("session_id"), str):
                clicks.append({"source": click["source"], "session_id": click["session_id"]})
        return clicks


class Pulse:
    """The worker's pulse file: whether Orca reported an agent change since the last look."""

    def __init__(self, path):
        self.path = path
        self.seen = self.read()

    def read(self):
        try:
            return self.path.stat().st_mtime_ns
        except OSError:
            return None

    def changed(self):
        current = self.read()
        changed, self.seen = current != self.seen, current
        return changed


def canal_watch(kernel):
    """A handle signalled when a file in CANAL is written, renamed or created; None if Windows
    cannot watch it (the timer still reads Orca)."""
    kernel.FindFirstChangeNotificationW.restype = ctypes.c_void_p
    handle = kernel.FindFirstChangeNotificationW(ctypes.c_wchar_p(str(CANAL)), False,
                                                 0x1 | 0x10)  # FILE_NAME | LAST_WRITE
    return None if handle in (None, ctypes.c_void_p(-1).value) else handle

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
    # Below normal priority for the bridge too: a visual aid must never slow the PC down.
    kernel.SetPriorityClass(ctypes.c_void_p(-1), 0x00004000)
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
    CANAL.mkdir(parents=True, exist_ok=True)
    for stale in (FOCUS_FEED, FOCUS_REQUEST):
        stale.unlink(missing_ok=True)  # a click of a previous run opens nothing now
    write_json(OPEN_MARK, {"pid": os.getpid()})
    pipe = rf"\\.\pipe\pixtuoid-orca-{uuid.uuid4().hex}"
    trace = PROFILE / "codex" / "sessions"
    trace.mkdir(parents=True, exist_ok=True)
    Agent.names = PROFILE / "claude" / "projects" / "orca-pixtuoid"
    clear_traces(trace, Agent.names)
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
        headless = office = watch = None
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
            notice = orca_version_notice(orca)
            if notice:
                record("orca-newer-than-verified")
                # Its own thread: the notice never holds the office back.
                threading.Thread(target=ctypes.windll.user32.MessageBoxW,
                                 args=(0, notice, "Pixtuoid · Orca", 0x40 | 0x10000), daemon=True).start()
            office_state = Office(orca, env, trace, record, configured)
            # The Orca plugin's worker sets it when it pulses on Orca's agent events.
            events = os.environ.get("PIXTUOID_ORCA_EVENTS") == "1"
            watch = canal_watch(kernel)
            handles = (ctypes.c_void_p * 2)(stop, watch)
            feed, pulse = FocusFeed(FOCUS_FEED), Pulse(PULSE)
            failed, next_read, read_ended = False, 0.0, 0.0
            counted_at, counted = time.monotonic(), CLI_CALLS.total
            while office.poll() is None:
                started = time.monotonic()
                if started >= next_read:
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
                    read_ended = time.monotonic()
                    taken = read_ended - started
                    if taken > 5:
                        record(f"orca-slow-read:{taken:.0f}s")
                    next_read = read_ended + poll_wait(taken, failed, events, office_state.busy())
                if started - counted_at >= 60:
                    record(f"orca-cli-calls:{CLI_CALLS.total - counted} in {started - counted_at:.0f}s")
                    counted_at, counted = started, CLI_CALLS.total
                wait = max(0, int(1000 * (next_read - time.monotonic())))
                woke = kernel.WaitForMultipleObjects(2 if watch else 1, handles, False, wait)
                if woke == 0:
                    record("stop-requested")
                    close_window(office)
                elif woke == 1:
                    kernel.FindNextChangeNotification(watch)
                    for click in feed.read_new():
                        target = office_state.focus_target(click["source"], click["session_id"])
                        record("focus" if target else "focus-unknown")
                        if target:
                            write_json(FOCUS_REQUEST, dict(target, seq=time.time_ns()))
                    if pulse.changed():
                        next_read = min(next_read, max(time.monotonic() + EVENT_SETTLE,
                                                       read_ended + EVENT_GAP))
            record(f"office-exit:{office.returncode}")
        finally:
            if office and office.poll() is None:
                close_window(office)
            try:
                clear_traces(trace, Agent.names)  # nothing of this run outlives the office
            except OSError:
                pass
            if headless and headless.poll() is None:
                headless.terminate()
                headless.wait(timeout=8)
            if results:
                results.close()
            window_log.close()
            try:
                OPEN_MARK.unlink(missing_ok=True)
            except OSError:
                pass
            if watch:
                kernel.FindCloseChangeNotification(watch)
            kernel.CloseHandle(stop)
            kernel.CloseHandle(mutex)

if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        ctypes.windll.user32.MessageBoxW(0, str(error), "Pixtuoid · Orca", 0x10)
