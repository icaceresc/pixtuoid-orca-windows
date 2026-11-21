"""Regression tests for the read-only Orca projection (no Orca or Pixtuoid required)."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import oficina


SID = "8ef940e0-d3e6-4ee3-91a2-8b8c0195c103"
KID = "0b7c1f5e-2d0a-4b8e-9f1e-3c5d7a9b1e2f"
SUB = "557d4ca9-fd79-432a-ae31-7104d8b94c89"
SUB2 = "6c0e1d1a-1111-4b8e-9f1e-3c5d7a9b1e2f"
GRAND = "9a1b2c3d-4e5f-4a6b-8c7d-0e1f2a3b4c5d"


def agent(state, session_id=SID, kind="codex", **extra):
    return dict({"orcaSessionId": session_id, "agent": kind, "state": state}, **extra)


def ps_row(session_id, parent=None, children=None, observation="live", **extra):
    row = {"orcaSessionId": session_id, "paneKey": f"pane-{session_id}",
           "parentPaneKey": f"pane-{parent}" if parent else None,
           "subagentObservation": observation}
    if children is not None:
        row["children"] = children
    row.update(extra)
    return row


def child(child_id, state="working", kind="agent", membership="live", **extra):
    return dict({"id": child_id, "kind": kind, "state": state, "membership": membership,
                 "agentType": "general-purpose"}, **extra)


class FakePlaceholder:
    """Stands in for the suspended process an Antigravity coworker's pid comes from."""
    made = []

    def __init__(self):
        self.pid, self.ended = 4242 + len(FakePlaceholder.made), False
        FakePlaceholder.made.append(self)

    def end(self):
        self.ended = True


class Harness:
    """Drives Office.sync against canned Orca answers and records every hook sent."""

    def __init__(self, configured=("codex", "claude-code", "opencode", "antigravity")):
        self.hooks = []
        self.rollouts = []
        self.queries = []
        self.records = []
        self.agents, self.ps, self.truncated = [], None, False
        self.ps_error, self.ps_truncated = None, False
        # Fields `worktree ps` adds to a worktree, by its id (`bot`, `botHome`, `path`).
        self.worktree_fields = {}
        self.office = oficina.Office("orca.exe", {}, Path("."), self.record, set(configured))

    def record(self, *event):
        self.records.append(event)

    def orca_json(self, _orca, *args):
        self.queries.append(args)
        if args == ("agent", "list"):
            return {"agents": self.agents, "truncated": self.truncated}
        if args == ("worktree", "ps"):
            if self.ps_error:
                raise self.ps_error
            return {"worktrees": self.worktrees(), "truncated": self.ps_truncated}
        raise AssertionError(f"Unexpected Orca command: {args}")

    def worktrees(self):
        """Orca's `worktree ps` answer: each listed agent in its worktree, with its provider
        and state as `agent list` reports them, plus the hierarchy fields of the matching
        `ps_row` (none means Orca cannot vouch for its subagents)."""
        extra = {row["orcaSessionId"]: row for row in self.ps or []}
        groups = {}
        for row in self.agents:
            sid = row.get("orcaSessionId")
            worktree = row.get("worktreeId") or "repo::C:\\work"
            listed = dict(extra.get(sid) or {"orcaSessionId": sid}, agentType=row.get("agent"),
                          state=row.get("state"))
            groups.setdefault(worktree, []).append(listed)
        return [dict({"worktreeId": worktree, "path": worktree.partition("::")[2], "agents": rows},
                     **self.worktree_fields.get(worktree, {}))
                for worktree, rows in groups.items()]

    def emit(self, _env, source, payload, event=None):
        self.hooks.append((source, event or payload.get("type"), payload))

    def rollout(self, coworker, kind, payload):
        self.rollouts.append((coworker.key, kind, payload))

    def sync(self, agents, ps=None):
        self.agents, self.ps = agents, ps
        self.hooks.clear()
        with (patch.object(oficina, "orca_json", side_effect=self.orca_json),
              patch.object(oficina, "emit", side_effect=self.emit),
              patch.object(oficina, "placeholder", FakePlaceholder),
              patch.object(oficina.Agent, "codex_record", autospec=True, side_effect=self.rollout)):
            self.office.sync()
        return self.office.agents

    def events(self):
        return [event for _source, event, _payload in self.hooks]


class SessionTests(unittest.TestCase):
    def test_unidentified_terminal_session_does_not_crash(self):
        h = Harness()
        self.assertEqual(h.sync([agent("working", None), agent("working", "")]), {})
        self.assertEqual(h.hooks, [])

    def test_active_identified_session_is_projected(self):
        h = Harness()
        agents = h.sync([agent("working", "orca_session_id:" + SID)])
        tracked = agents["orca_session_id:" + SID]
        self.assertEqual((tracked.source, tracked.id), ("codex", SID))
        self.assertEqual(h.records[0][-1], "working")

    def test_already_completed_session_is_not_resurrected(self):
        h = Harness()
        self.assertEqual(h.sync([agent("done")]), {})
        self.assertEqual(h.hooks, [])
        self.assertNotIn(("worktree", "show"), [q[:2] for q in h.queries])

    def test_observed_working_session_can_finish_and_close(self):
        h = Harness()
        h.sync([agent("working")])
        h.sync([agent("done")])
        self.assertEqual(h.office.agents[SID].state, "done")
        h.sync([])
        self.assertEqual(h.office.agents, {})
        self.assertIn("SessionEnd", h.events())

    def test_unresolvable_worktree_does_not_block_sync(self):
        h = Harness()
        h.ps_error = oficina.subprocess.TimeoutExpired("orca", 5)
        real = h.orca_json

        def failing_show(orca, *args):
            if args[:2] == ("worktree", "show"):
                raise oficina.subprocess.TimeoutExpired("orca", 5)
            return real(orca, *args)
        h.orca_json = failing_show
        agents = h.sync([agent("working", worktreeId="repo::C:\\work\\gone"), agent("working", KID)])
        self.assertEqual(set(agents), {SID, KID})
        self.assertEqual(agents[SID].workdir, "C:\\work\\gone")

    def test_worktree_path_comes_from_ps_without_extra_queries(self):
        h = Harness()
        agents = h.sync([agent("working", worktreeId="repo::C:\\work")], [ps_row(SID, children=[])])
        self.assertEqual(agents[SID].workdir, "C:\\work")
        self.assertNotIn(("worktree", "show"), [q[:2] for q in h.queries])

    def test_truncated_list_is_not_misread_as_agents_exiting(self):
        h = Harness()
        h.sync([agent("working")])
        h.ps_truncated = h.truncated = True
        with self.assertRaisesRegex(RuntimeError, "truncated"):
            h.sync([])
        self.assertIn(SID, h.office.agents)

    def test_one_orca_call_per_cycle(self):
        h = Harness()
        h.sync([agent("working", SID, "claude")], [ps_row(SID, children=[child(SUB)])])
        self.assertEqual(h.queries, [("worktree", "ps")], "agent list is not needed when ps is complete")
        self.assertEqual(set(h.office.agents), {SID, "child:" + SUB})

    def test_truncated_ps_falls_back_to_agent_list(self):
        h = Harness()
        h.ps_truncated = True
        agents = h.sync([agent("working", SID, "claude"), agent("working", KID, "codex")],
                        [ps_row(SID, children=[]), ps_row(KID, parent=SID, children=[])])
        self.assertEqual(h.queries, [("worktree", "ps"), ("agent", "list")])
        self.assertIs(agents[KID].parent, agents[SID])

    def test_poll_wait_follows_the_cost_of_a_read(self):
        self.assertEqual(oficina.poll_wait(0.2), oficina.POLL_SECONDS)
        self.assertEqual(oficina.poll_wait(2.5), 5.0)
        self.assertEqual(oficina.poll_wait(30), oficina.MAX_POLL_SECONDS)
        self.assertEqual(oficina.poll_wait(0.1, failed=True), 3.0)
        self.assertEqual(oficina.poll_wait(30, failed=True), oficina.MAX_POLL_SECONDS)


class HierarchyTests(unittest.TestCase):
    def test_same_provider_worker_links_to_its_dispatcher(self):
        h = Harness()
        agents = h.sync([agent("working", KID, "claude"), agent("working", SID, "claude")],
                        [ps_row(SID, children=[]), ps_row(KID, parent=SID, children=[])])
        self.assertIs(agents[KID].parent, agents[SID])
        start = next(p for s, e, p in h.hooks if e == "SubagentStart")
        self.assertEqual((start["session_id"], start["agent_id"]), (SID, KID))

    def test_cross_provider_worker_is_drawn_in_its_parents_source(self):
        h = Harness()
        agents = h.sync([agent("working", SID, "claude"), agent("working", KID, "codex")],
                        [ps_row(SID, children=[]), ps_row(KID, parent=SID, children=[])])
        self.assertEqual((agents[KID].source, agents[KID].provider), ("claude-code", "codex"))
        self.assertEqual(h.records[-1][1].provider, "codex")

    def test_antigravity_cannot_parent_so_its_worker_stays_a_root(self):
        h = Harness()
        agents = h.sync([agent("working", SID, "antigravity"), agent("working", KID, "codex")],
                        [ps_row(SID, children=[]), ps_row(KID, parent=SID, children=[])])
        self.assertIsNone(agents[KID].parent)
        self.assertEqual(agents[KID].source, "codex")

    def test_native_subagent_appears_and_tool_work_does_not(self):
        h = Harness()
        agents = h.sync([agent("working", SID, "claude")],
                        [ps_row(SID, children=[child(SUB), child(SUB2, kind="command")])])
        self.assertEqual(set(agents), {SID, "child:" + SUB})
        self.assertEqual(agents["child:" + SUB].label, "general-purpose")

    def test_two_simultaneous_subagents_get_distinct_stable_identities(self):
        h = Harness()
        rows = [agent("working", SID, "claude")]
        ps = [ps_row(SID, children=[child(SUB), child(SUB2)])]
        first = h.sync(rows, ps)
        ids = {first["child:" + SUB].id, first["child:" + SUB2].id}
        h.sync(rows, ps)
        self.assertEqual(ids, {SUB, SUB2})
        self.assertEqual(h.events(), [], "A repeated snapshot sends nothing")

    def test_subagent_finishing_before_parent_leaves_alone(self):
        h = Harness()
        rows = [agent("working", SID, "claude")]
        h.sync(rows, [ps_row(SID, children=[child(SUB), child(SUB2)])])
        h.sync(rows, [ps_row(SID, children=[child(SUB, "done", membership="settled",
                                                  outcome="succeeded"), child(SUB2)])])
        self.assertEqual(set(h.office.agents), {SID, "child:" + SUB2})
        self.assertEqual(h.events(), ["PostToolUse", "Stop", "SubagentStop"],
                         "Only that child ends its call and turn, and leaves")

    def test_vanished_hook_roster_subagent_closes(self):
        h = Harness()
        rows = [agent("working", SID, "codex")]
        h.sync(rows, [ps_row(SID, subagents=[{"id": SUB, "state": "working"}])])
        self.assertIn("child:" + SUB, h.office.agents)
        h.sync(rows, [ps_row(SID, subagents=[])])
        self.assertNotIn("child:" + SUB, h.office.agents)

    def test_settled_or_idle_child_is_never_resurrected(self):
        h = Harness()
        agents = h.sync([agent("working", SID, "claude")],
                        [ps_row(SID, children=[child(SUB, "done", membership="settled"),
                                               child(SUB2, "idle")])])
        self.assertEqual(set(agents), {SID})

    def test_unverifiable_observation_or_ps_failure_keeps_subagents(self):
        h = Harness()
        rows = [agent("working", SID, "claude")]
        h.sync(rows, [ps_row(SID, children=[child(SUB)])])
        h.sync(rows, [ps_row(SID, children=[], observation="unverifiable")])
        self.assertIn("child:" + SUB, h.office.agents)
        h.ps_error = RuntimeError("down")
        h.sync(rows)
        self.assertIn("child:" + SUB, h.office.agents)
        self.assertEqual(h.events(), [])

    def test_parent_closing_cascades_deepest_first(self):
        h = Harness()
        h.sync([agent("working", SID, "claude"), agent("working", KID, "claude")],
               [ps_row(SID, children=[]), ps_row(KID, parent=SID, children=[child(SUB)])])
        grandchild = h.office.agents["child:" + SUB]
        self.assertEqual(grandchild.depth(), 2)
        start = [p for s, e, p in h.hooks if e == "SubagentStart"][-1]
        self.assertEqual(start["session_id"], "agent-" + KID, "Grandchild roots on the child")
        h.sync([])
        self.assertEqual(h.office.agents, {})
        closed = [r[1].key for r in h.records if r[-1] == "closed"]
        self.assertEqual(closed, ["child:" + SUB, KID, SID])

    def test_cancelled_worker_session_closes_without_ghosts(self):
        h = Harness()
        h.sync([agent("working", SID, "claude"), agent("working", KID, "claude")],
               [ps_row(SID, children=[]), ps_row(KID, parent=SID, children=[])])
        h.sync([agent("working", SID, "claude")], [ps_row(SID, children=[])])
        self.assertEqual(set(h.office.agents), {SID})
        self.assertEqual(h.events(), ["PostToolUse", "Stop", "SubagentStop"],
                         "Only that child ends its call and turn, and leaves")

    def test_opencode_child_names_its_parent_once(self):
        h = Harness()
        h.sync([agent("working", SID, "opencode"), agent("working", KID, "opencode2")],
               [ps_row(SID, children=[]), ps_row(KID, parent=SID, children=[])])
        child_events = [p for s, e, p in h.hooks if p.get("data", {}).get("sessionID") == KID]
        self.assertEqual(child_events[0]["data"]["parentID"], SID)

    def test_worker_first_seen_without_ps_moves_under_its_dispatcher(self):
        h = Harness()
        rows = [agent("working", SID, "opencode2"), agent("working", KID, "codex")]
        h.sync(rows, [ps_row(SID, children=[])])
        h.ps_error = RuntimeError("timeout")
        h.sync(rows)
        self.assertIsNone(h.office.agents[KID].parent)
        h.ps_error = None
        agents = h.sync(rows, [ps_row(SID, children=[]), ps_row(KID, parent=SID, children=[])])
        self.assertIs(agents[KID].parent, agents[SID])
        self.assertEqual(agents[KID].source, "opencode")
        h.sync(rows, [ps_row(SID, children=[]), ps_row(KID, children=[])])
        self.assertIs(h.office.agents[KID].parent, agents[SID], "A missing link never demotes a child")
        self.assertEqual(h.events(), [])

    def test_worker_outliving_its_dispatcher_returns_as_a_new_coworker(self):
        h = Harness()
        h.sync([agent("working", SID, "codex"), agent("working", KID, "codex")],
               [ps_row(SID, children=[]), ps_row(KID, parent=SID, children=[])])
        old = h.office.agents[KID].id
        h.sync([agent("working", KID, "codex")], [ps_row(KID, children=[])])
        self.assertEqual(set(h.office.agents), set())
        h.sync([agent("working", KID, "codex")], [ps_row(KID, children=[])])
        self.assertEqual(set(h.office.agents), {KID})
        self.assertNotEqual(h.office.agents[KID].id, old, "Pixtuoid never sees a reused id")
        h.sync([agent("working", KID, "codex")], [ps_row(KID, children=[])])
        self.assertEqual(h.events(), [], "Stable after re-entry")

    def test_subagents_of_an_antigravity_root_survive_an_observation_gap(self):
        h = Harness()
        rows = [agent("working", SID, "antigravity")]
        h.sync(rows, [ps_row(SID, children=[child(SUB)])])
        self.assertIsNone(h.office.agents["child:" + SUB].parent)
        h.sync(rows, [ps_row(SID, children=[], observation="unverifiable")])
        self.assertIn("child:" + SUB, h.office.agents)
        h.sync([], [])
        self.assertEqual(h.office.agents, {}, "Closing the owner closes its subagents")

    def test_unconfigured_source_is_skipped(self):
        h = Harness(configured=("codex",))
        self.assertEqual(h.sync([agent("working", SID, "claude")], [ps_row(SID, children=[child(SUB)])]), {})


class OrcaCliTests(unittest.TestCase):
    def answer(self, stdout, code=0):
        done = oficina.subprocess.CompletedProcess([], code, stdout, b"boom")
        with patch.object(oficina.subprocess, "run", return_value=done):
            return oficina.orca_json("orca.exe", "agent", "list")

    def test_unexpected_answers_raise_runtime_errors(self):
        for stdout, code in ((b"null", 0), (b'{"ok": false, "error": "text"}', 1), (b"not json", 1)):
            with self.assertRaises(RuntimeError):
                self.answer(stdout, code)

    def test_error_names_orca_code_not_command_data(self):
        stdout = b'{"ok": false, "error": {"code": "runtime_unavailable", "message": "APPDATA is not set"}}'
        with self.assertRaisesRegex(RuntimeError, "agent list failed \\(1\\): runtime_unavailable APPDATA"):
            self.answer(stdout, 1)


class TraceTests(unittest.TestCase):
    def test_previous_codex_rollouts_are_cleared_at_startup(self):
        with tempfile.TemporaryDirectory(prefix="tmp-test-", dir=Path(__file__).parent) as directory:
            trace = Path(directory)
            old = oficina.Agent(SID, "codex", Path("."), trace)
            old.codex_record("session_meta", {"id": old.id})
            unrelated = trace / "notes.txt"
            unrelated.write_text("keep", encoding="utf-8")
            oficina.clear_traces(trace)
            self.assertFalse(old.rollout.exists())
            self.assertTrue(unrelated.exists())


class ControlTests(unittest.TestCase):
    def test_stop_without_a_running_office_is_a_no_op(self):
        with tempfile.TemporaryDirectory(prefix="tmp-test-", dir=Path(__file__).parent) as directory:
            with patch.object(oficina, "HOME", Path(directory)):
                self.assertFalse(oficina.request_stop())

    def test_each_data_folder_has_its_own_office(self):
        with patch.object(oficina, "HOME", Path("C:/a")):
            first = oficina.names()
        with patch.object(oficina, "HOME", Path("C:/b")):
            second = oficina.names()
        self.assertNotEqual(first, second)


class PluginManifestTests(unittest.TestCase):
    """Static checks of the Orca plugin contract; `orca plugin validate .` is the full check."""

    def setUp(self):
        import json
        root = Path(__file__).parent
        self.root = root
        self.manifest = json.loads((root / "orca-plugin.json").read_text(encoding="utf-8"))

    def test_least_privilege(self):
        # agent:read hears agent events; workspace:read finds a chat's workspace by its folder;
        # workspace:write shows that workspace or focuses a terminal; notifications:show says
        # when an agent needs you. Nothing reads or types into a terminal.
        self.assertEqual([c["kind"] for c in self.manifest["capabilities"]],
                         ["agent:read", "workspace:read", "workspace:write", "notifications:show"])
        self.assertEqual(self.manifest["contributes"]["events"], [{"on": "agent.status.changed"}])
        self.assertNotIn("hooks", self.manifest["contributes"])
        self.assertNotIn("publisher", self.manifest)

    def test_status_bar_item_opens_the_office(self):
        item, = self.manifest["contributes"]["statusBarItems"]
        self.assertEqual(item["command"], "pixtuoid.open")
        worker = (self.root / self.manifest["main"]).read_text(encoding="utf-8")
        self.assertIn(f"id: '{item['id']}'", worker)

    def test_the_worker_writes_what_the_office_reads(self):
        worker = (self.root / self.manifest["main"]).read_text(encoding="utf-8")
        for name in (oficina.FOCUS_REQUEST.name, oficina.PULSE.name, oficina.OPEN_MARK.name):
            self.assertIn(f"'{name}'", worker)
        self.assertIn(f"join(HOME, '{oficina.CANAL.name}')", worker)
        self.assertIn("PIXTUOID_ORCA_EVENTS: '1'", worker)

    def test_every_command_is_registered_by_the_worker(self):
        worker = (self.root / self.manifest["main"]).read_text(encoding="utf-8")
        for command in self.manifest["contributes"]["commands"]:
            self.assertIn(f"logged('{command['id']}'", worker)

    def test_worker_keeps_data_out_of_the_plugin_folder(self):
        worker = (self.root / self.manifest["main"]).read_text(encoding="utf-8")
        self.assertIn("PIXTUOID_ORCA_HOME", worker)
        self.assertIn("PYTHONDONTWRITEBYTECODE", worker)


class NameCardTests(unittest.TestCase):
    """Cross-provider children under a Claude Code parent show their real provider."""

    def run_tree(self, parent_kind, child_kind):
        directory = tempfile.TemporaryDirectory(prefix="tmp-test-", dir=Path(__file__).parent)
        self.addCleanup(directory.cleanup)
        names = Path(directory.name)
        h = Harness()
        with patch.object(oficina.Agent, "names", names):
            h.sync([agent("working", SID, parent_kind), agent("working", KID, child_kind)],
                   [ps_row(SID, children=[]), ps_row(KID, parent=SID, children=[])])
            cards = list(names.rglob("agent-*.jsonl"))
        return h, names, cards

    def test_codex_worker_under_claude_gets_a_codex_card(self):
        h, names, cards = self.run_tree("claude", "codex")
        self.assertEqual([c.name for c in cards], [f"agent-{KID}.jsonl"])
        self.assertEqual(cards[0].parent.parent.name, SID, "Card sits under the parent session")
        line = __import__("json").loads(cards[0].read_text(encoding="utf-8"))
        self.assertEqual(line["attributionAgent"], "cx·worker · work")
        self.assertEqual(set(line), {"type", "attributionAgent", "cwd", "sessionId", "message"},
                         "No prompt, title or tool data")
        with patch.object(oficina.Agent, "names", names):
            h.sync([agent("working", SID, "claude")], [ps_row(SID, children=[])])
        self.assertFalse(cards[0].exists(), "Card removed when the child leaves")

    def test_same_provider_and_non_claude_parents_get_no_card(self):
        for parent_kind, child_kind in (("claude", "claude"), ("codex", "claude"), ("opencode2", "codex")):
            _h, _names, cards = self.run_tree(parent_kind, child_kind)
            self.assertEqual(cards, [], f"{parent_kind} -> {child_kind}")

    def test_a_refused_card_never_stalls_the_office(self):
        h = Harness()
        with patch.object(oficina.Agent, "names", Path(".")), \
                patch.object(Path, "write_text", side_effect=PermissionError("locked")), \
                patch.object(Path, "mkdir"):
            h.sync([agent("working", SID, "claude"), agent("working", KID, "codex")],
                   [ps_row(SID, children=[]), ps_row(KID, parent=SID, children=[])])
        self.assertEqual(h.office.agents[KID].state, "working")

    def test_cleanup_also_removes_empty_folders(self):
        with tempfile.TemporaryDirectory(prefix="tmp-test-", dir=Path(__file__).parent) as directory:
            names = Path(directory) / "names"
            (names / SID / "subagents").mkdir(parents=True)
            oficina.clear_traces(Path(directory) / "codex", names)
            self.assertEqual(list(names.iterdir()), [])

    def test_cards_of_a_previous_run_are_cleared(self):
        with tempfile.TemporaryDirectory(prefix="tmp-test-", dir=Path(__file__).parent) as directory:
            names = Path(directory) / "names"
            card = names / SID / "subagents" / f"agent-{KID}.jsonl"
            card.parent.mkdir(parents=True)
            card.write_text("{}", encoding="utf-8")
            oficina.clear_traces(Path(directory) / "codex", names)
            self.assertFalse(card.exists())


class IdentificationTests(unittest.TestCase):
    """Pixtuoid names a coworker `<prefix>·<cwd basename>`: the basename carries project and role."""

    def tree(self, parent_kind, child_kind):
        h = Harness()
        agents = h.sync([agent("working", SID, parent_kind), agent("working", KID, child_kind)],
                        [ps_row(SID, children=[child(SUB, agentType="Explore")]),
                         ps_row(KID, parent=SID, children=[])])
        return h, agents

    def basename(self, coworker):
        return oficina.ntpath.basename(coworker.cwd)

    def test_top_level_agent_keeps_its_real_parent_folder(self):
        h = Harness()
        agents = h.sync([agent("working", SID, "claude", worktreeId="repo::C:\\work\\my-repo")])
        self.assertEqual(agents[SID].workdir, "C:\\work\\my-repo")
        self.assertEqual(agents[SID].cwd, "C:\\work\\my-repo · agent")
        self.assertEqual(h.hooks[0][2]["cwd"], "C:\\work\\my-repo · agent")

    def test_roles_and_project_in_every_label(self):
        _h, agents = self.tree("claude", "claude")
        self.assertEqual(self.basename(agents[SID]), "work · orchestrator")
        self.assertEqual(self.basename(agents[KID]), "worker · work")
        self.assertEqual(self.basename(agents["child:" + SUB]), "Explore subagent · work")
        self.assertEqual(oficina.ntpath.dirname(agents[KID].cwd), "C:\\", "Real parent folder")

    def test_issue_5_cross_provider_child_names_its_provider_in_codex_and_opencode_trees(self):
        for parent_kind, child_kind, expected in (("codex", "claude", "claude worker · work"),
                                                  ("opencode2", "claude", "claude worker · work"),
                                                  ("opencode", "codex", "codex worker · work")):
            h, agents = self.tree(parent_kind, child_kind)
            self.assertEqual(self.basename(agents[KID]), expected)
            sent = [p for s, e, p in h.hooks if p.get("agent_id") == KID or
                    p.get("data", {}).get("sessionID") == KID]
            directory = sent[0].get("cwd") or sent[0]["data"]["location"]["directory"]
            self.assertTrue(directory.endswith(expected), directory)

    def test_worker_of_antigravity_names_its_dispatcher(self):
        with patch.object(oficina, "placeholder", FakePlaceholder):
            _h, agents = self.tree("antigravity", "codex")
        self.assertEqual(self.basename(agents[KID]), "worker of antigravity · work")

    def test_label_text_is_path_safe(self):
        self.assertEqual(oficina.clean_text('a/b\\c:*?"<>|d\n'), "a b c d")
        self.assertEqual(oficina.tool_label("Agent"), "Orca: Agent")
        self.assertEqual(oficina.tool_label("ask_question"), "Orca: ask_question")
        self.assertIsNone(oficina.tool_label(None))


class RoleTests(unittest.TestCase):
    """Each coworker states its role in its title; Pixtuoid dresses it as that role's class."""

    def basename(self, coworker):
        return oficina.ntpath.basename(coworker.cwd)

    def home(self, h, fields):
        h.worktree_fields["folder:punky"] = dict({"path": "C:\\Users\\me\\.orca\\bots\\punky"},
                                                 **fields)
        return h.sync([agent("working", SID, "claude", worktreeId="folder:punky")])

    def test_a_bots_home_session_is_the_companion(self):
        agents = self.home(Harness(), {"bot": "Punky", "botHome": True})
        self.assertEqual(self.basename(agents[SID]), "punky · companion")

    def test_without_the_flag_the_bots_folder_still_tells(self):
        agents = self.home(Harness(), {})
        self.assertEqual(self.basename(agents[SID]), "punky · companion")
        self.assertTrue(oficina.in_bots_folder("C:/Users/me/.orca/bots/punky/"))
        self.assertFalse(oficina.in_bots_folder("C:\\work\\bots\\punky"))
        self.assertFalse(oficina.in_bots_folder("C:\\Users\\me\\.orca\\bots"))
        self.assertFalse(oficina.in_bots_folder(None))

    def test_a_workspace_a_bot_works_in_is_not_its_home(self):
        h = Harness()
        h.worktree_fields["repo::C:\\work\\my-repo"] = {"bot": "Punky", "botHome": None}
        agents = h.sync([agent("working", SID, "claude", worktreeId="repo::C:\\work\\my-repo")])
        self.assertEqual(self.basename(agents[SID]), "my-repo · agent")

    def test_the_companion_stays_one_when_it_dispatches(self):
        h = Harness()
        h.worktree_fields["folder:punky"] = {"path": "C:\\Users\\me\\.orca\\bots\\punky",
                                             "botHome": True}
        agents = h.sync([agent("working", SID, "claude", worktreeId="folder:punky"),
                         agent("working", KID, "claude")],
                        [ps_row(SID, children=[]), ps_row(KID, parent=SID, children=[])])
        self.assertEqual(self.basename(agents[SID]), "punky · companion")
        self.assertEqual(self.basename(agents[KID]), "worker · work")

    def test_a_worker_that_dispatches_is_an_orchestrator(self):
        h = Harness()
        agents = h.sync([agent("working", sid, "claude") for sid in (SID, KID, GRAND)],
                        [ps_row(SID, children=[]), ps_row(KID, parent=SID, children=[]),
                         ps_row(GRAND, parent=KID, children=[])])
        self.assertEqual(self.basename(agents[SID]), "work · orchestrator")
        self.assertEqual(self.basename(agents[KID]), "orchestrator · work")
        self.assertEqual(self.basename(agents[GRAND]), "worker · work")

    def test_a_session_that_starts_dispatching_returns_as_an_orchestrator(self):
        h = Harness()
        h.sync([agent("working", SID, "claude")], [ps_row(SID, children=[])])
        before = h.office.agents[SID]
        self.assertEqual(self.basename(before), "work · agent")
        agents = h.sync([agent("working", SID, "claude"), agent("working", KID, "claude")],
                        [ps_row(SID, children=[]), ps_row(KID, parent=SID, children=[])])
        self.assertEqual(self.basename(agents[SID]), "work · orchestrator")
        self.assertNotEqual(agents[SID].id, before.id, "Pixtuoid never sees a reused id")
        self.assertIs(agents[KID].parent, agents[SID])
        events = h.events()
        self.assertLess(events.index("SessionEnd"), events.index("SessionStart"))
        h.sync([agent("working", SID, "claude")], [ps_row(SID, children=[])])
        self.assertEqual(self.basename(h.office.agents[SID]), "work · orchestrator",
                         "The role is never taken back")
        self.assertNotIn("SessionStart", h.events())


class FeatureTests(unittest.TestCase):
    def test_real_tool_name_without_its_input(self):
        h = Harness()
        secret = "rm -rf C:/private"
        row = ps_row(SID, children=[], toolName="Bash", toolInput=secret, prompt=secret,
                     lastAssistantMessage=secret, taskTitle=secret, conversationName=secret)
        h.sync([agent("working", SID, "claude")], [row])
        start = next(p for s, e, p in h.hooks if e == "PreToolUse")
        self.assertEqual((start["tool_name"], start["tool_input"]), ("Bash", {}))
        h.sync([agent("working", SID, "claude")], [dict(row, toolName="Edit")])
        self.assertEqual(h.events(), ["PostToolUse", "PreToolUse"])
        self.assertEqual(h.hooks[-1][2]["tool_name"], "Edit")
        everything = repr(h.hooks) + repr(h.records)
        self.assertNotIn("private", everything, "Prompts, replies and tool inputs never leave Orca")

    def test_every_source_shows_the_tool(self):
        for kind, check in (("codex", None), ("opencode2", "session.tool.input.started"),
                            ("antigravity", "PreToolUse")):
            h = Harness()
            h.sync([agent("working", SID, kind)], [ps_row(SID, children=[], toolName="Read")])
            calls = [(record, payload) for _key, record, payload in h.rollouts]
            if check:
                payload = next(p for s, e, p in h.hooks if e == check)
                self.assertIn("Read", repr(payload))
            else:
                self.assertIn(("response_item", {"type": "function_call", "name": "Read",
                                                  "call_id": h.office.agents[SID].call,
                                                  "arguments": "{}"}), calls)

    def test_codex_child_gets_its_own_rollout_with_its_parent(self):
        h = Harness()
        h.sync([agent("working", SID, "codex"), agent("working", KID, "codex")],
               [ps_row(SID, children=[]), ps_row(KID, parent=SID, children=[])])
        records = h.rollouts
        meta = next(r for key, kind, r in records if key == KID and kind == "session_meta")
        self.assertEqual(meta["parent_thread_id"], SID)
        self.assertIn((KID, "event_msg", {"type": "task_started", "turn_id": "1"}), records,
                      "A Codex child shows working through its own turn")

    def test_heartbeat_repeats_the_state_with_the_same_ids(self):
        h = Harness()
        rows = [agent("working", SID, "claude")]
        h.sync(rows, [ps_row(SID, children=[], toolName="Bash")])
        first = next(p for s, e, p in h.hooks if e == "PreToolUse")
        h.sync(rows, [ps_row(SID, children=[], toolName="Bash")])
        self.assertEqual(h.events(), [], "Nothing before the heartbeat is due")
        h.office.agents[SID].sent_at -= oficina.HEARTBEAT_SECONDS + 1
        h.sync(rows, [ps_row(SID, children=[], toolName="Bash")])
        self.assertEqual(h.events(), ["PreToolUse"])
        self.assertEqual(h.hooks[0][2]["tool_use_id"], first["tool_use_id"], "Counted once by Pixtuoid")
        h.sync([agent("done", SID, "claude")], [ps_row(SID, children=[])])
        h.office.agents[SID].sent_at -= oficina.HEARTBEAT_SECONDS + 1
        h.sync([agent("done", SID, "claude")], [ps_row(SID, children=[])])
        self.assertEqual(h.events(), ["Stop"], "An idle coworker is refreshed by a turn end")

    def test_antigravity_leaves_when_its_placeholder_ends(self):
        FakePlaceholder.made.clear()
        h = Harness()
        with patch.object(oficina, "placeholder", FakePlaceholder):
            h.sync([agent("working", SID, "antigravity"), agent("working", KID, "antigravity")])
            pids = {p["_pid"] for s, e, p in h.hooks if p.get("conversationId") == SID}
            self.assertEqual(pids, {FakePlaceholder.made[0].pid}, "Its own pid on every hook")
            h.sync([agent("working", KID, "antigravity")])
        self.assertTrue(FakePlaceholder.made[0].ended)
        self.assertFalse(FakePlaceholder.made[1].ended)

    def test_subagent_name_never_stands_in_for_its_type(self):
        h = Harness()
        agents = h.sync([agent("working", SID, "claude")],
                        [ps_row(SID, children=[child(SUB, agentType=None, name="private title")])])
        self.assertEqual(oficina.ntpath.basename(agents["child:" + SUB].cwd), "subagent · work")
        self.assertNotIn("private", repr(h.hooks))

    def test_antigravity_without_a_placeholder_still_shows(self):
        h = Harness()
        with patch.object(oficina, "placeholder", side_effect=OSError("no job")):
            with (patch.object(oficina, "orca_json", side_effect=h.orca_json),
                  patch.object(oficina, "emit", side_effect=h.emit),
                  patch.object(oficina.Agent, "codex_record")):
                h.agents, h.ps = [agent("working", SID, "antigravity")], None
                h.office.sync()
        self.assertIsNone(h.office.agents[SID].placeholder)
        self.assertEqual({p["_pid"] for s, e, p in h.hooks}, {oficina.os.getpid()})

    @unittest.skipUnless(sys.platform == "win32", "Windows job objects")
    def test_placeholder_is_a_suspended_process_held_by_a_kill_on_close_job(self):
        with patch.object(oficina, "SHIM", Path(sys.executable)):
            held = oficina.Placeholder()
        try:
            self.assertIsNone(held.process.poll(), "Suspended, not exited")
        finally:
            held.end()
        self.assertIsNotNone(held.process.poll())

    def test_older_orca_without_provider_in_ps_reads_agent_list(self):
        h = Harness()
        original = h.worktrees

        def without_provider():
            groups = original()
            for group in groups:
                for row in group["agents"]:
                    row.pop("agentType")
            return groups
        h.worktrees = without_provider
        agents = h.sync([agent("working", SID, "claude")], [ps_row(SID, children=[])])
        self.assertIn(SID, agents)
        self.assertEqual(h.queries, [("worktree", "ps"), ("agent", "list")])


class OrcaVersionTests(unittest.TestCase):
    def notice(self, version_line, profile):
        done = oficina.subprocess.CompletedProcess([], 0, version_line, "")
        with patch.object(oficina.subprocess, "run", return_value=done), \
                patch.object(oficina, "PROFILE", profile):
            return oficina.orca_version_notice("orca.exe")

    def test_newer_orca_is_noticed_once_per_version(self):
        with tempfile.TemporaryDirectory(prefix="tmp-test-", dir=Path(__file__).parent) as directory:
            profile = Path(directory)
            self.assertIsNone(self.notice(oficina.VERIFIED_ORCA + "\n", profile))
            self.assertIsNone(self.notice("1.4.100\n", profile))
            self.assertIn("1.5.0", self.notice("1.5.0\n", profile))
            self.assertIsNone(self.notice("1.5.0\n", profile), "Once per version")
            self.assertIn("1.5.1", self.notice("1.5.1\n", profile))
            self.assertIsNone(self.notice("unexpected\n", profile))


def load_bump():
    import importlib.util
    path = Path(__file__).parent / ".github" / "scripts" / "bump_pixtuoid.py"
    spec = importlib.util.spec_from_file_location("bump_pixtuoid", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseCheckTests(unittest.TestCase):
    """The scheduled workflow's bump logic, against release fixtures (no network)."""

    def setUp(self):
        self.bump = load_bump()
        self.installer = (Path(__file__).parent / "instalar.py").read_text(encoding="utf-8")

    def release(self, tag, digest="sha256:" + "a" * 64, **extra):
        version = tag.removeprefix("v")
        asset = {"name": f"pixtuoid-v{version}-x86_64-pc-windows-msvc.zip", "digest": digest,
                 "browser_download_url": f"https://example.invalid/{version}.zip"}
        return dict({"tag_name": tag, "draft": False, "prerelease": False, "assets": [asset]}, **extra)

    def test_newer_stable_release_bumps_version_and_sha(self):
        version, _url, sha = self.bump.asset_for(self.release("v9.1.0"))
        text = self.bump.bump(self.installer, version, sha)
        self.assertIn('VERSION = "9.1.0"', text)
        self.assertIn('SHA256 = "' + "a" * 64 + '"', text)
        self.assertEqual(len(text.splitlines()), len(self.installer.splitlines()), "Only the pin changes")

    def test_current_or_older_release_changes_nothing(self):
        pinned = ".".join(map(str, self.bump.pinned(self.installer)))
        self.assertIsNone(self.bump.bump(self.installer, pinned, "b" * 64))
        self.assertIsNone(self.bump.bump(self.installer, "0.1.0", "b" * 64))

    def test_drafts_prereleases_and_unverifiable_assets_are_refused(self):
        for release in (self.release("v9.1.0", prerelease=True), self.release("v9.1.0", draft=True),
                        self.release("v9.1.0-rc.1"), self.release("v9.1.0", digest=None),
                        dict(self.release("v9.1.0"), assets=[])):
            with self.assertRaises(ValueError):
                self.bump.asset_for(release)

    def test_the_pin_matches_the_published_digest_of_v0_23_0(self):
        # Verified with `gh api repos/pixtuoid/pixtuoid/releases/latest` on 2026-11-20.
        self.assertIn('SHA256 = "e52205aba4061112f94f40529d920e0346c98c0f4123edeceebee12e80303dad"',
                      self.installer)

    def test_the_bump_leaves_the_dungeon_pin_alone(self):
        text = self.bump.bump(self.installer, "9.1.0", "a" * 64)
        self.assertIn("DUNGEON_SHA256 = None", text)


class OrcaToolTests(unittest.TestCase):
    """An agent running the Orca CLI shows the tool "Orca" (Dungeons & Agents casts it as a spell)."""

    def test_a_shell_call_of_the_orca_cli_is_the_orca_tool(self):
        for command in ("orca worktree ps --json", "cd C:/x && orca agent list",
                        '"C:/Program Files/Orca/bin/orca.exe" terminal send --terminal t',
                        "C:\\Orca\\orca.cmd orchestration check"):
            self.assertEqual(oficina.tool_label("Bash", command), "Orca", command)
        self.assertEqual(oficina.tool_label("exec_command", "orca plugin list"), "Orca")

    def test_anything_else_keeps_its_own_name(self):
        for name, command in (("Bash", "cd ~/orca && ls"), ("Bash", "git log orca"),
                              ("Bash", 'echo "orca rocks"'), ("Edit", "orca worktree ps"),
                              ("Bash", None)):
            self.assertEqual(oficina.tool_label(name, command), name, command)

    def test_the_office_shows_it_without_the_command(self):
        h = Harness()
        secret = "orca terminal send --terminal t --text private"
        h.sync([agent("working", SID, "claude")], [ps_row(SID, children=[], toolName="Bash", toolInput=secret)])
        start = next(p for s, e, p in h.hooks if e == "PreToolUse")
        self.assertEqual(start["tool_name"], "Orca")
        self.assertNotIn("private", repr(h.hooks))


class FocusTests(unittest.TestCase):
    """A click on a coworker in Dungeons & Agents names its Orca session for the plugin to open."""

    def test_a_coworker_names_its_own_orca_session_and_pane(self):
        h = Harness()
        agents = h.sync([agent("working", SID, "claude", worktreeId="repo::C:\\work\\atlas")],
                        [ps_row(SID, children=[])])
        target = h.office.focus_target("claude-code", agents[SID].session)
        self.assertEqual(target, {"orcaSessionId": SID, "paneKey": f"pane-{SID}", "path": "C:\\work\\atlas"})

    def test_a_subagent_or_worker_opens_the_session_it_runs_in(self):
        h = Harness()
        agents = h.sync([agent("working", SID, "claude"), agent("working", KID, "codex")],
                        [ps_row(SID, children=[child(SUB)]), ps_row(KID, parent=SID, children=[])])
        subagent = agents["child:" + SUB]
        self.assertEqual(h.office.focus_target("claude-code", subagent.session)["orcaSessionId"], SID)
        # A worker is drawn under its dispatcher but is an Orca session of its own.
        worker = agents[KID]
        self.assertEqual(h.office.focus_target(worker.source, worker.session)["orcaSessionId"], KID)

    def test_an_unknown_or_foreign_session_opens_nothing(self):
        h = Harness()
        agents = h.sync([agent("working", SID, "claude")], [ps_row(SID, children=[])])
        self.assertIsNone(h.office.focus_target("claude-code", "someone-else"))
        self.assertIsNone(h.office.focus_target("codex", agents[SID].session))

    def test_the_feed_yields_whole_lines_once(self):
        with tempfile.TemporaryDirectory(prefix="tmp-test-", dir=Path(__file__).parent) as directory:
            path = Path(directory) / "feed.jsonl"
            feed = oficina.FocusFeed(path)
            self.assertEqual(feed.read_new(), [])
            with path.open("a", encoding="utf-8") as out:
                out.write('{"source": "codex", "session_id": "a"}\nnot json\n{"source": "cod')
            self.assertEqual(feed.read_new(), [{"source": "codex", "session_id": "a"}])
            with path.open("a", encoding="utf-8") as out:
                out.write('ex", "session_id": "b"}\n')
            self.assertEqual(feed.read_new(), [{"source": "codex", "session_id": "b"}])
            self.assertEqual(feed.read_new(), [])

    def test_a_pulse_is_seen_once_per_write(self):
        with tempfile.TemporaryDirectory(prefix="tmp-test-", dir=Path(__file__).parent) as directory:
            path = Path(directory) / "pulse.json"
            pulse = oficina.Pulse(path)
            self.assertFalse(pulse.changed(), "No worker has pulsed yet")
            path.write_text("1\n", encoding="utf-8")
            self.assertTrue(pulse.changed())
            self.assertFalse(pulse.changed())
            os.utime(path, ns=(1, path.stat().st_mtime_ns + 1_000_000))
            self.assertTrue(pulse.changed())

    def test_a_request_replaces_the_last_one_whole(self):
        with tempfile.TemporaryDirectory(prefix="tmp-test-", dir=Path(__file__).parent) as directory:
            path = Path(directory) / "request.json"
            oficina.write_json(path, {"seq": 1})
            oficina.write_json(path, {"seq": 2, "orcaSessionId": SID})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"seq": 2, "orcaSessionId": SID})
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ["request.json"])

    def test_the_office_tells_pixtuoid_where_clicks_go(self):
        env = oficina.office_env()
        self.assertEqual(env["PIXTUOID_FOCUS_FEED"], str(oficina.FOCUS_FEED))
        self.assertEqual(oficina.FOCUS_FEED.parent, oficina.CANAL)


class EventPollTests(unittest.TestCase):
    """With Orca's events the office reads Orca on a slow timer; without them, as before."""

    def test_events_slow_the_timer_by_how_busy_the_office_is(self):
        self.assertEqual(oficina.poll_wait(0.5, events=True, busy=True), oficina.EVENT_POLL_BUSY)
        self.assertEqual(oficina.poll_wait(0.5, events=True), oficina.EVENT_POLL_IDLE)
        self.assertEqual(oficina.poll_wait(9, events=True, busy=True), 18)
        self.assertGreater(oficina.EVENT_POLL_IDLE, oficina.EVENT_POLL_BUSY)
        self.assertGreater(oficina.EVENT_POLL_BUSY, oficina.POLL_SECONDS)

    def test_a_failed_read_retries_as_before(self):
        self.assertEqual(oficina.poll_wait(0.1, failed=True, events=True), 3.0)

    def test_busy_means_an_agent_is_working(self):
        h = Harness()
        h.sync([agent("waiting", SID, "claude")], [ps_row(SID, children=[])])
        self.assertFalse(h.office.busy())
        h.sync([agent("working", SID, "claude")], [ps_row(SID, children=[])])
        self.assertTrue(h.office.busy())

    def test_cli_calls_are_counted(self):
        before = oficina.CLI_CALLS.total
        done = oficina.subprocess.CompletedProcess([], 0, b'{"ok": true, "result": {}}', b"")
        with patch.object(oficina.subprocess, "run", return_value=done):
            oficina.orca_json("orca.exe", "worktree", "ps")
        self.assertEqual(oficina.CLI_CALLS.total, before + 1)


if __name__ == "__main__":
    unittest.main()
