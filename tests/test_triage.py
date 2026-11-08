import csv
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import triage  # noqa: E402


class ThinkingBlock:
    """Mimics a reply block that has no .text attribute."""
    thinking = "reasoning here"


class FakeClient:
    def __init__(self, replies):
        self.replies = list(replies)
        self.messages = SimpleNamespace(create=self._create)
        self.calls = []

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        if isinstance(reply, tuple):  # (thinking block first, then text)
            return SimpleNamespace(content=[ThinkingBlock(), SimpleNamespace(text=reply[0])])
        return SimpleNamespace(content=[SimpleNamespace(text=reply)])


GOOD = '{"ai_priority": "P1", "rationale": "Cosmetic.", "missing_info": "none", "needs_human_review": false}'
P3 = '{"ai_priority": "p3", "rationale": "Gas.", "missing_info": "none", "needs_human_review": false}'


class ParseTests(unittest.TestCase):
    def test_plain_json(self):
        self.assertEqual(triage.parse_response(GOOD)["ai_priority"], "P1")

    def test_code_fenced_json(self):
        self.assertEqual(triage.parse_response("```json\n" + GOOD + "\n```")["ai_priority"], "P1")

    def test_priority_is_normalised(self):
        self.assertEqual(triage.parse_response(P3)["ai_priority"], "P3")

    def test_invalid_priority_rejected(self):
        with self.assertRaises(ValueError):
            triage.parse_response('{"ai_priority": "P9"}')

    def test_no_json_rejected(self):
        with self.assertRaises(ValueError):
            triage.parse_response("sorry")


class SafetyRuleTests(unittest.TestCase):
    def test_p3_always_needs_confirmation(self):
        r = triage.with_confirmation_flag(triage.parse_response(P3))
        self.assertTrue(r["requires_human_confirmation"])

    def test_flagged_p1_needs_confirmation(self):
        r = triage.parse_response(GOOD.replace("false", "true"))
        self.assertTrue(triage.with_confirmation_flag(r)["requires_human_confirmation"])

    def test_clean_p1_does_not(self):
        r = triage.with_confirmation_flag(triage.parse_response(GOOD))
        self.assertFalse(r["requires_human_confirmation"])


class TriageTests(unittest.TestCase):
    def test_api_error_fails_safe(self):
        client = FakeClient([RuntimeError("boom")])
        r = triage.triage(client, "x", "sys")
        self.assertEqual(r["ai_priority"], "ERROR")
        self.assertTrue(r["requires_human_confirmation"])

    def test_thinking_block_before_text_is_skipped(self):
        client = FakeClient([(GOOD,)])
        r = triage.triage(client, "x", "sys")
        self.assertEqual(r["ai_priority"], "P1")

    def test_reply_with_no_text_fails_safe(self):
        client = FakeClient([RuntimeError("placeholder")])
        client.messages = SimpleNamespace(create=lambda **k: SimpleNamespace(content=[ThinkingBlock()]))
        r = triage.triage(client, "x", "sys")
        self.assertEqual(r["ai_priority"], "ERROR")

    def test_context_reaches_the_model(self):
        client = FakeClient([GOOD])
        triage.triage(client, "Leaking tap", "sys", property_name="Maple Hollow Estate", trade="Plumbing")
        content = client.calls[0]["messages"][0]["content"]
        self.assertIn("Maple Hollow Estate", content)
        self.assertIn("Plumbing", content)
        self.assertIn("Leaking tap", content)

    def test_batch_writes_every_row(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d, "in.csv"), Path(d, "out.csv")
            src.write_text("request_id,request_text\nWO-001,tap drips\nWO-002,gas smell\n")
            client = FakeClient([GOOD, P3])
            n = triage.run_batch(client, src, out, "sys")
            rows = list(csv.DictReader(open(out)))
        self.assertEqual(n, 2)
        self.assertEqual([r["ai_priority"] for r in rows], ["P1", "P3"])
        self.assertEqual(rows[1]["requires_human_confirmation"], "True")

    def test_prompt_file_loads(self):
        self.assertIn("P3", triage.load_system_prompt())


if __name__ == "__main__":
    unittest.main()
