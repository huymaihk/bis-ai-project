import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from persistent_memory import MemoryStore, SheetsMemorySync


class FakeSheet:
    def __init__(self):
        self.rows = [["event_id", "event_json"]]
        self.fail = False

    def get_all_values(self):
        return list(self.rows)

    def append_rows(self, rows, **kwargs):
        if self.fail:
            raise ConnectionError("offline")
        self.rows.extend(rows)


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.a = MemoryStore(self.root / "a")
        self.b = MemoryStore(self.root / "b")

    def tearDown(self):
        self.tmp.cleanup()

    def test_restart_and_redaction(self):
        self.a.append("message", "SKU 03026A, api_key=private-value", session="employee:rd", actor="user")
        restart = MemoryStore(self.root / "a")
        messages = restart.messages("employee:rd")
        self.assertEqual(len(messages), 1)
        self.assertNotIn("private-value", messages[0]["content"])
        self.assertIn("03026A", restart.context("03026A", "employee:rd"))

    def test_revision_tombstone_and_stale_editor(self):
        old = self.a.revise("gsm", "OLD-GSM-100")
        new = self.a.revise("gsm", "NEW-GSM-200", expected=[old["id"]])
        self.assertNotIn("OLD-GSM-100", self.a.context())
        with self.assertRaises(ValueError):
            self.a.revise("gsm", "stale", expected=[old["id"]])
        self.a.revise("gsm", "", expected=[new["id"]], deleted=True)
        self.assertEqual(self.a.current(), [])
        self.assertEqual(len(self.a.events()), 3)

    def test_bidirectional_retry_conflict_and_resolution(self):
        ws = FakeSheet()
        first = self.a.revise("unit", "cuon")
        sa, sb = SheetsMemorySync(self.a, ws), SheetsMemorySync(self.b, ws)
        sa.sync()
        sb.sync()
        self.a.revise("unit", "cai", expected=[first["id"]])
        self.b.revise("unit", "bo", expected=[first["id"]])
        ws.fail = True
        with self.assertRaises(ConnectionError):
            sa.sync()
        self.assertEqual(len(self.a.events()), 2)
        ws.fail = False
        sa.sync()
        sb.sync()
        sa.sync()
        self.assertTrue(self.a.current()[0]["conflict"])
        self.assertIn("XUNG ĐỘT", self.a.context())
        self.a.revise("unit", "cuon confirmed")
        sa.sync()
        sb.sync()
        self.assertFalse(self.b.current()[0]["conflict"])
        self.assertEqual(sb.sync()["sent"], 0)
        self.assertEqual(self.a.events(), self.b.events())

    def test_concurrent_writers_no_lost_messages(self):
        def write(n):
            MemoryStore(self.root / "a").append("message", str(n), session="same")
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(write, range(80)))
        self.assertEqual(len(self.a.messages("same", 100)), 80)

    def test_source_update_manual_correction_and_bad_json(self):
        path = self.a.workspace / "PROJECT_HANDOVER.md"
        path.write_text("old fact", encoding="utf-8")
        self.a.refresh_sources()
        path.write_text("new fact", encoding="utf-8")
        self.a.refresh_sources()
        self.assertNotIn("old fact", self.a.context())
        self.a.revise("source:PROJECT_HANDOVER.md:0", "human fact", kind="correction")
        path.write_text("newer source", encoding="utf-8")
        self.a.refresh_sources()
        self.assertIn("human fact", self.a.context())
        self.assertNotIn("newer source", self.a.context())
        (self.a.events_dir / "broken.json").write_text("{", encoding="utf-8")
        self.assertTrue(self.a.events())
        self.assertEqual(self.a.read_errors, ["broken.json"])

    def test_old_source_on_new_device_is_conflict(self):
        (self.a.workspace / "PROJECT_HANDOVER.md").write_text("fresh", encoding="utf-8")
        self.a.refresh_sources()
        ws = FakeSheet()
        SheetsMemorySync(self.a, ws).sync()
        SheetsMemorySync(self.b, ws).sync()
        (self.b.workspace / "PROJECT_HANDOVER.md").write_text("old disk copy", encoding="utf-8")
        self.b.refresh_sources()
        self.assertTrue(self.b.current()[0]["conflict"])

    def test_invalid_import_path_and_context_limit(self):
        event = self.a.revise("test", "A" * 15000)
        self.assertLessEqual(len(self.a.context(max_chars=800)), 800)
        invalid = dict(event, id="../../bad")
        with self.assertRaises(ValueError):
            self.b.import_event(invalid)

    def test_employee_reply_uses_memory_and_survives_restart(self):
        from agent_employee_pool import BISEmployeeOrchestrator
        orch = BISEmployeeOrchestrator(self.a.workspace)
        with patch("agent_employee_pool.reply_with_memory", return_value="Đã hiểu yêu cầu.") as fake:
            result = orch.chat_with_employee("rd_lead", "Nhớ SKU 03026A")
        self.assertTrue(fake.called)
        self.assertIn("Đã hiểu", result["reply"].content)
        restored = BISEmployeeOrchestrator(self.a.workspace)
        self.assertEqual(len(restored.employees["rd_lead"].chat_memory), 2)
        self.assertEqual(restored.employees["rd_lead"].progress_pct, 0)

    def test_model_failure_keeps_request(self):
        from agent_employee_pool import BISEmployeeOrchestrator
        orch = BISEmployeeOrchestrator(self.a.workspace)
        with patch("agent_employee_pool.reply_with_memory", side_effect=RuntimeError("secret exception")):
            reply = orch.chat_with_employee("rd_lead", "Cần xử lý")["reply"].content
        self.assertNotIn("secret exception", reply)
        self.assertIn("chưa nhận", reply)
        self.assertEqual(len(self.a.messages("employee:rd_lead")), 2)


if __name__ == "__main__":
    unittest.main()

