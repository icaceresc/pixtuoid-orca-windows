"""Regression tests for the read-only Orca session projection (no Orca required)."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import oficina


SID = "orca_session_id:8ef940e0-d3e6-4ee3-91a2-8b8c0195c103"


def agent(state, session_id=SID):
    return {"orcaSessionId": session_id, "agent": "codex", "state": state}


class SessionSyncTests(unittest.TestCase):
    def run_snapshot(self, rows, sessions=None, truncated=False):
        sessions = {} if sessions is None else sessions
        records = []

        def fake_orca_json(_orca, *args):
            if args != ("agent", "list"):
                raise AssertionError(f"Unexpected Orca command: {args}")
            return {"agents": rows, "truncated": truncated}

        with (
            patch.object(oficina, "orca_json", side_effect=fake_orca_json) as query,
            patch.object(oficina.Session, "transition", autospec=True) as transition,
        ):
            if truncated:
                with self.assertRaisesRegex(RuntimeError, "truncated"):
                    oficina.sync("orca.exe", {}, Path("."), sessions, {},
                                lambda *event: records.append(event), {"codex"})
            else:
                oficina.sync("orca.exe", {}, Path("."), sessions, {},
                            lambda *event: records.append(event), {"codex"})
            return sessions, records, query, transition

    def test_unidentified_terminal_session_does_not_crash(self):
        sessions, events, query, transition = self.run_snapshot(
            [agent("working", None), agent("working", "")]
        )
        self.assertEqual(sessions, {})
        self.assertEqual(events, [])
        self.assertEqual(query.call_count, 1)
        transition.assert_not_called()

    def test_active_identified_session_is_projected(self):
        sessions, events, query, transition = self.run_snapshot([agent("working")])
        self.assertIn(SID, sessions)
        self.assertEqual(sessions[SID].source, "codex")
        self.assertEqual(sessions[SID].id, SID.removeprefix("orca_session_id:"))
        self.assertEqual(events[0][-1], "working")
        transition.assert_called_once()

    def test_already_completed_session_is_not_resurrected(self):
        sessions, events, query, transition = self.run_snapshot([agent("done")])
        self.assertEqual(sessions, {})
        self.assertEqual(events, [])
        self.assertEqual(query.call_count, 1, "No extra agent show query")
        transition.assert_not_called()

    def test_observed_working_session_can_finish(self):
        tracked = oficina.Session(agent("working"), Path("."), Path("."))
        tracked.state = "working"
        sessions, events, _query, transition = self.run_snapshot(
            [agent("done")], {SID: tracked}
        )
        self.assertIs(sessions[SID], tracked)
        self.assertEqual(events[0][-1], "done")
        self.assertEqual(transition.call_args.args[2], "done")

    def test_disappeared_session_closes(self):
        tracked = oficina.Session(agent("working"), Path("."), Path("."))
        tracked.state = "working"
        sessions, events, _query, transition = self.run_snapshot([], {SID: tracked})
        self.assertEqual(sessions, {})
        self.assertEqual(events[0][-1], "closed")
        self.assertEqual(transition.call_args.args[2], "closed")

    def test_truncated_list_is_not_misread_as_agents_exiting(self):
        self.run_snapshot([], truncated=True)


class TraceTests(unittest.TestCase):
    def test_previous_codex_rollouts_are_cleared_at_startup(self):
        with tempfile.TemporaryDirectory(prefix="tmp-test-", dir=Path(__file__).parent) as directory:
            trace = Path(directory)
            old = oficina.Session(agent("working"), Path("."), trace)
            old.codex_record("session_meta", {"id": old.id})
            unrelated = trace / "notes.txt"
            unrelated.write_text("keep", encoding="utf-8")
            oficina.clear_traces(trace)
            self.assertFalse(old.rollout.exists())
            self.assertTrue(unrelated.exists())


if __name__ == "__main__":
    unittest.main()
