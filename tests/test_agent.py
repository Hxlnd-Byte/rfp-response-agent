"""Tests that need no AI. Run:  python -m unittest discover tests -v
They work on a temporary copy, so your own data, drafts and library are never touched."""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
TMP = Path(tempfile.mkdtemp(prefix="rfp-agent-test-"))
shutil.copy(HERE / "config.toml", TMP / "config.toml")
os.environ["RFP_HOME"] = str(TMP)
sys.path.insert(0, str(HERE))

import make_demo_data  # noqa: E402
from rfpagent import catalog, guardrails as g, learn, pipeline, retrieval, score, web  # noqa: E402
from rfpagent.common import APPROVED, DATA, PENDING, Stop, cfg, read_json  # noqa: E402

RFP = "RFP-2026-014"
FILE = lambda: DATA / "rfp" / "RFP-2026-014_Brackenfield.txt"


def fresh():
    for d in ("data", "outbox", "output"):
        shutil.rmtree(TMP / d, ignore_errors=True)
    make_demo_data.main(quiet=True)


def tearDownModule():
    shutil.rmtree(TMP, ignore_errors=True)


class Rules(unittest.TestCase):
    CAP = dict(id="C-11", text="Support 24 hours a day, 7 days a week, with a 30 minute response target.", note="", category="SUPPORT_24X7")
    KW = dict(fit="STRONG", capability=CAP, sources=[], requirement="Provide support.", blocked_names=["Norvane Systems", "Harrowgate Mutual Bank"], max_words=160)

    def test_good_answer_passes(self):
        self.assertEqual(g.check_answer("Support runs 24 hours a day with a 30 minute target. [C-11]", **self.KW), [])

    def test_missing_source_fails(self):
        self.assertTrue(g.check_answer("Support runs all day.", **self.KW))

    def test_invented_number_fails(self):
        self.assertTrue(any("number 15" in v for v in g.check_answer("We answer in 15 minutes. [C-11]", **self.KW)))

    def test_competitor_and_old_customer_names_fail(self):
        self.assertTrue(g.check_answer("Unlike Norvane Systems, we help. [C-11]", **self.KW))
        self.assertTrue(g.check_answer("As at Harrowgate Mutual Bank, we help. [C-11]", **self.KW))

    def test_sales_words_fail(self):
        self.assertTrue(g.check_answer("We guarantee world-class support. [C-11]", **self.KW))

    def test_gap_must_be_admitted(self):
        kw = dict(self.KW, fit="GAP")
        self.assertTrue(g.check_answer("We fully support this. [C-11]", **kw))
        self.assertEqual(g.check_answer("This is not offered today. [C-11]", **kw), [])

    def test_quote_must_be_in_the_page(self):
        page = "Kestrelline is cloud-only by design. There is nothing to install."
        self.assertTrue(g.verify_quote("cloud-only  by design", page))
        self.assertFalse(g.verify_quote("runs in your own data centre", page))

    def test_search_sends_only_a_name_and_an_approved_topic(self):
        c = cfg()
        self.assertEqual(web.safe_query("Norvane Systems", "pricing", c), "Norvane Systems pricing")
        with self.assertRaises(ValueError):
            web.safe_query("Norvane Systems", "patient data must be stored inside the country", c)
        with self.assertRaises(ValueError):
            web.safe_query("All patient-related and security data must be stored and processed inside the country", "pricing", c)

    def test_old_customer_sentences_are_removed_before_drafting(self):
        out = pipeline.clean_source("We support this. Orchard Vale Hospitals runs this way.", ["Orchard Vale Hospitals"])
        self.assertEqual(out, "We support this.")


class Pipeline(unittest.TestCase):
    def setUp(self):
        fresh()

    def test_requirements_are_found_by_code(self):
        r = pipeline.parse_rfp(FILE().read_text(encoding="utf-8"))
        self.assertEqual((len(r["requirements"]), r["customer"], r["rfp_id"]), (18, "Brackenfield Health Network", RFP))

    def test_clean_run_matches_the_answer_key_and_leaks_nothing(self):
        pipeline.run(FILE(), "mock")
        s = score.score(RFP)
        self.assertEqual((s["fit_correct"], s["capability_correct"], s["past_answer_found"], s["answers_failing_checks"]), (18, 18, 18, 0))
        self.assertEqual((s["competitor_claims_found"], s["customer_statements_found"], s["talking_points_without_valid_source"]), (18, 8, 0))
        text = (PENDING / RFP / "response_draft.md").read_text(encoding="utf-8")
        for name in pipeline.world()["company"]["competitors"] + pipeline.world()["past_customers"]:
            self.assertNotIn(name, text)
        self.assertNotIn("[W-", text)

    def test_planted_mistakes_are_caught(self):
        pack = pipeline.run(FILE(), "noisy_mock")
        self.assertGreater(len(pack["blocked"]), 0)                      # claims with a quote that is not in the page
        self.assertGreater(sum(bool(a["violations"]) for a in pack["answers"]), 0)  # answers with an old customer name and an invented number
        with self.assertRaises(ValueError):
            pipeline.approve(RFP, "technical", "Sam")                    # a pack with failing answers cannot be signed

    def test_two_different_people_must_sign_and_nothing_is_overwritten(self):
        pipeline.run(FILE(), "mock")
        with self.assertRaises(ValueError):
            pipeline.approve(RFP, "technical", "")
        self.assertEqual(pipeline.approve(RFP, "technical", "Sam")["status"], "PENDING_APPROVAL")
        with self.assertRaises(ValueError):
            pipeline.approve(RFP, "account", "sam")
        self.assertEqual(pipeline.approve(RFP, "account", "Lee")["status"], "APPROVED")
        self.assertTrue((APPROVED / RFP / "response_final.md").exists())
        self.assertFalse((PENDING / RFP).exists())
        with self.assertRaises(ValueError):
            pipeline.edit_answer(RFP, "R-01", "changed", "Sam")
        with self.assertRaises(ValueError):
            pipeline.run(FILE(), "mock")

    def test_an_edit_is_rechecked_and_clears_sign_offs(self):
        pipeline.run(FILE(), "mock")
        pipeline.approve(RFP, "technical", "Sam")
        self.assertTrue(pipeline.edit_answer(RFP, "R-13", "We guarantee an answer in 5 minutes.", "Lee"))
        self.assertEqual(pipeline.load_pack(RFP)["approvals"], {})

    def test_review_adds_approved_answers_once(self):
        pipeline.run(FILE(), "mock")
        pipeline.edit_answer(RFP, "R-14", "Vantora Launch reaches full operation in 12 weeks, in three stages, each signed off by you. [C-12]", "Sam")
        pipeline.approve(RFP, "technical", "Sam")
        pipeline.approve(RFP, "account", "Lee")
        before = len(read_json(DATA / "library.json")["answers"])
        self.assertEqual(learn.review("test")["learned"], 0)             # no result recorded yet, so nothing is learned
        pipeline.set_outcome(RFP, "won")
        r = learn.review("test")
        lib = read_json(DATA / "library.json")
        self.assertEqual((r["learned"], len(lib["answers"]) - before, lib["version"]), (1, 18, 2))
        self.assertIn("Answers the team edited before approving: 1 of 18", r["report"])
        self.assertFalse(any("[C-" in a["answer"] for a in lib["answers"]))
        self.assertEqual(learn.review("test")["added"], 0)

    def test_spec_sheet_only_suggests_and_a_person_sets_the_status(self):
        before = len(read_json(DATA / "catalog.json"))
        items = catalog.propose("Vantora Beacon data sheet. Beacon supports single sign-on through the same identity provider as Sentry. Short line.")
        self.assertEqual([i["category"] for i in items], ["IDENTITY"])
        self.assertEqual(len(read_json(DATA / "catalog.json")), before)      # suggesting adds nothing
        with self.assertRaises(ValueError):
            catalog.add_entry("Vantora Beacon", "IDENTITY", "", items[0]["text"], "", "Sam")   # no status chosen
        with self.assertRaises(ValueError):
            catalog.add_entry("Vantora Beacon", "IDENTITY", "available", items[0]["text"], "", "")  # no name
        self.assertEqual(catalog.add_entry("Vantora Beacon", "IDENTITY", "partial", items[0]["text"], "Pilot only.", "Sam")["id"], "C-21")

    def test_kill_switch(self):
        (TMP / "STOP").write_text("x")
        try:
            with self.assertRaises(Stop):
                pipeline.run(FILE(), "mock")
        finally:
            (TMP / "STOP").unlink()

    def test_past_answers_prefer_wins_and_recent_bids(self):
        lib = read_json(DATA / "library.json")
        import datetime as dt
        top = retrieval.past_answers(lib, "Describe the training provided for administrators and analysts", dt.date(2026, 11, 16), cfg())[0]
        self.assertEqual((top["category"], top["bid"]), ("TRAINING", "B-2026-02"))


if __name__ == "__main__":
    unittest.main()
