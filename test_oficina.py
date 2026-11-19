"""Regression tests for the read-only Orca projection (no Orca or Pixtuoid required)."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import oficina


SID = "8ef940e0-d3e6-4ee3-91a2-8b8c0195c103"
KID = "0b7c1f5e-2d0a-4b8e-9f1e-3c5d7a9b1e2f"
SUB = "557d4ca9-fd79-432a-ae31-7104d8b94c89"
SUB2 = "6c0e1d1a-1111-4b8e-9f1e-3c5d7a9b1e2f"


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


class Harness:
    """Drives Office.sync against canned Orca answers and records every hook sent."""

    def __init__(self, configured=("codex", "claude-code", "opencode", "antigravity")):
        self.hooks = []
        self.queries = []
        self.records = []
        self.agents, self.ps, self.truncated = [], None, False
        self.ps_error = None
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
            return {"worktrees": [{"worktreeId": "repo::C:\\work", "path": "C:\\work",
                                   "agents": self.ps or []}]}
        raise AssertionError(f"Unexpected Orca command: {args}")

    def emit(self, _env, source, payload, event=None):
        self.hooks.append((source, event or payload.get("type"), payload))

    def sync(self, agents, ps=None):
        self.agents, self.ps = agents, ps
        self.hooks.clear()
        with (patch.object(oficina, "orca_json", side_effect=self.orca_json),
              patch.object(oficina, "emit", side_effect=self.emit),
              patch.object(oficina.Agent, "codex_record")):
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
        self.assertEqual(agents[SID].cwd, "C:\\work\\gone")

    def test_worktree_path_comes_from_ps_without_extra_queries(self):
        h = Harness()
        agents = h.sync([agent("working", worktreeId="repo::C:\\work")], [ps_row(SID, children=[])])
        self.assertEqual(agents[SID].cwd, "C:\\work")
        self.assertNotIn(("worktree", "show"), [q[:2] for q in h.queries])

    def test_truncated_list_is_not_misread_as_agents_exiting(self):
        h = Harness()
        h.sync([agent("working")])
        h.truncated = True
        with self.assertRaisesRegex(RuntimeError, "truncated"):
            h.sync([])
        self.assertIn(SID, h.office.agents)


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
        self.assertEqual(h.events(), ["Stop", "SubagentStop"], "Only that child ends its turn and leaves")

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
        self.assertEqual(h.events(), ["Stop", "SubagentStop"], "Only that child ends its turn and leaves")

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

    def test_unconfigured_source_is_skipped(self):
        h = Harness(configured=("codex",))
        self.assertEqual(h.sync([agent("working", SID, "claude")], [ps_row(SID, children=[child(SUB)])]), {})


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
        self.assertEqual(self.manifest["capabilities"], [])
        self.assertNotIn("events", self.manifest["contributes"])
        self.assertNotIn("hooks", self.manifest["contributes"])
        self.assertNotIn("publisher", self.manifest)

    def test_every_command_is_registered_by_the_worker(self):
        worker = (self.root / self.manifest["main"]).read_text(encoding="utf-8")
        for command in self.manifest["contributes"]["commands"]:
            self.assertIn(f"register('{command['id']}'", worker)

    def test_worker_keeps_data_out_of_the_plugin_folder(self):
        worker = (self.root / self.manifest["main"]).read_text(encoding="utf-8")
        self.assertIn("PIXTUOID_ORCA_HOME", worker)
        self.assertIn("PYTHONDONTWRITEBYTECODE", worker)


if __name__ == "__main__":
    unittest.main()
