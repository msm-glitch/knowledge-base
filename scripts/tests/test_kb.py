#!/usr/bin/env python3
"""Testy rdzenia deterministycznego knowledge-base. Tylko stdlib (unittest).

Uruchom:  python3 -m unittest discover -s scripts/tests -v
          (z roota repo)
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import kb_lib          # noqa: E402
import compliance      # noqa: E402
import kb_state        # noqa: E402
import metrics         # noqa: E402


class TestKbLib(unittest.TestCase):
    def test_jaccard(self):
        self.assertEqual(kb_lib.jaccard({"a", "b"}, {"a", "b"}), 1.0)
        self.assertEqual(kb_lib.jaccard({"a"}, {"b"}), 0.0)
        self.assertEqual(kb_lib.jaccard(set(), set()), 0.0)
        self.assertAlmostEqual(kb_lib.jaccard({"a", "b", "c"}, {"a", "b"}), 2 / 3)

    def test_skill_name_from_title(self):
        t = "[FIX] 2026-05-11 · Michał · off-brand-voice — dodaj 'podopieczni'"
        self.assertEqual(kb_lib.skill_name_from_title(t), "off-brand-voice")

    def test_similarity_same_skill_same_user_merges(self):
        draft = {"title": "[FIX] 2026-05-17 · Michał · off-brand-voice — dodaj podopieczni",
                 "user": "Michał"}
        existing = {"title": "[FIX] 2026-05-11 · Michał · off-brand-voice — dodaj stypendyści",
                    "user": "Michał"}
        sim = kb_lib.similarity(draft, existing)
        self.assertGreaterEqual(sim, kb_lib.MERGE_AT)
        self.assertEqual(kb_lib.dedup_action(sim), "MERGE")

    def test_similarity_different_skill_creates(self):
        draft = {"title": "[NEW] 2026-05-17 · Michał · partner-reaktywacja — coś", "user": "Michał"}
        existing = {"title": "[NEW] 2026-05-11 · Michał · mr-mass-outreach — co innego", "user": "Michał"}
        sim = kb_lib.similarity(draft, existing)
        self.assertLess(sim, kb_lib.FLAG_AT)
        self.assertEqual(kb_lib.dedup_action(sim), "CREATE")

    def test_best_match_picks_highest(self):
        draft = {"title": "[FIX] · Michał · off-brand-voice — x", "user": "Michał"}
        cands = [
            {"title": "[NEW] · Maciek · mr-mass-outreach — y", "user": "Maciek"},
            {"title": "[FIX] · Michał · off-brand-voice — z", "user": "Michał"},
        ]
        res = kb_lib.best_match(draft, cands)
        self.assertEqual(res["action"], "MERGE")
        self.assertIn("off-brand-voice", res["match"]["title"])

    def test_dedup_action_bands(self):
        self.assertEqual(kb_lib.dedup_action(0.80), "MERGE")
        self.assertEqual(kb_lib.dedup_action(0.60), "FLAG")
        self.assertEqual(kb_lib.dedup_action(0.30), "CREATE")

    def test_levenshtein(self):
        self.assertEqual(kb_lib.levenshtein("kot", "kot"), 0)
        self.assertEqual(kb_lib.levenshtein("kot", "kit"), 1)
        self.assertEqual(kb_lib.levenshtein("", "abc"), 3)

    def test_catalog_match(self):
        cat = ["off-brand-voice", "followup-mail", "ewidencja-godzinowa-miesieczna"]
        self.assertEqual(kb_lib.catalog_match("off-brand-voice", cat)["matched"], "off-brand-voice")
        # substring → istniejący skill, wymuś [FIX]
        self.assertEqual(kb_lib.catalog_match("ewidencja-godzinowa", cat)["matched"],
                         "ewidencja-godzinowa-miesieczna")
        # literówka w granicy Levenshtein<=3
        self.assertEqual(kb_lib.catalog_match("folowup-mail", cat)["matched"], "followup-mail")
        # nic podobnego → [NEW]
        self.assertIsNone(kb_lib.catalog_match("partner-reaktywacja-kwartalna", cat)["matched"])

    def test_roi_score(self):
        self.assertEqual(kb_lib.roi_score(10, 2, 120, "M"), 600.0)   # /4
        self.assertEqual(kb_lib.roi_score(10, 2, 120, "S"), 2400.0)  # /1
        self.assertEqual(kb_lib.roi_score(10, 2, 120, "L"), 200.0)   # /12

    def test_meets_threshold(self):
        self.assertFalse(kb_lib.meets_threshold("Skill Backlog", 2))
        self.assertTrue(kb_lib.meets_threshold("Skill Backlog", 3))
        self.assertTrue(kb_lib.meets_threshold("SOP", 2))
        self.assertFalse(kb_lib.meets_threshold("n8n Automation", 1))

    def test_normalize_priorities_demotes(self):
        entries = [{"id": str(i), "priority": "High", "score": 100 - i} for i in range(6)]
        entries += [{"id": "lo%d" % i, "priority": "Low", "score": 1} for i in range(4)]
        res = kb_lib.normalize_priorities(entries)  # 6/10 High = 60% > 35%
        self.assertEqual(res["high_pct_before"], 0.6)
        self.assertEqual(res["high_pct_after"], 0.2)  # keep round(10*0.2)=2
        self.assertEqual(len(res["changes"]), 4)
        # zostają najwyższe score
        highs = [e for e in res["entries"] if e["priority"] == "High"]
        self.assertEqual({e["id"] for e in highs}, {"0", "1"})

    def test_normalize_priorities_noop_when_under_cap(self):
        entries = [{"id": "1", "priority": "High", "score": 10}] + \
                  [{"id": str(i), "priority": "Low", "score": 1} for i in range(9)]
        res = kb_lib.normalize_priorities(entries)  # 10% < 35%
        self.assertEqual(res["changes"], [])


class TestCompliance(unittest.TestCase):
    VALID_PESEL = "44051401359"
    VALID_NIP = "8461627563"

    def test_pesel_checksum(self):
        self.assertTrue(compliance.pesel_valid(self.VALID_PESEL))
        self.assertFalse(compliance.pesel_valid("44051401358"))  # zła cyfra kontrolna
        self.assertFalse(compliance.pesel_valid("123"))

    def test_nip_checksum(self):
        self.assertTrue(compliance.nip_valid(self.VALID_NIP))
        self.assertFalse(compliance.nip_valid("8461627560"))

    def test_redact_pesel_and_nip(self):
        text = f"Beneficjent PESEL {self.VALID_PESEL}, firma NIP {self.VALID_NIP}."
        red, findings = compliance.redact(text)
        self.assertIn("[REDACTED:PESEL]", red)
        self.assertIn("[REDACTED:NIP]", red)
        self.assertNotIn(self.VALID_PESEL, red)
        self.assertTrue(compliance.must_block(text))

    def test_no_false_positive_on_random_11_digits(self):
        # losowy 11-cyfrowy ciąg bez poprawnej sumy → NIE redagujemy
        text = "id zamówienia 12345678901 z systemu"
        red, findings = compliance.redact(text)
        self.assertEqual(findings, [])
        self.assertEqual(red, text)
        self.assertFalse(compliance.must_block(text))

    def test_redact_email_medium(self):
        text = "napisz do jan.kowalski@off.org.pl jutro"
        red, findings = compliance.redact(text)
        self.assertIn("[REDACTED:EMAIL]", red)
        # email to medium → nie blokuje twardo
        self.assertFalse(compliance.must_block(text))

    def test_redact_phone(self):
        text = "tel +48 501 602 703 do biura"
        red, _ = compliance.redact(text)
        self.assertIn("[REDACTED:PHONE]", red)


class TestKbState(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cpath = os.path.join(self.tmp, "candidates.json")
        self.wpath = os.path.join(self.tmp, "watermarks.json")

    def test_accumulation_across_runs(self):
        data = kb_state.load_candidates(self.cpath)
        kb_state.record_occurrence(data, "Skill Backlog", "off-x", "2026-05-10",
                                   "Claude Chat", "Michał", "url1")
        kb_state.save_candidates(data, self.cpath)
        # nowy run, inne źródło/url
        data = kb_state.load_candidates(self.cpath)
        kb_state.record_occurrence(data, "Skill Backlog", "off-x", "2026-05-17",
                                   "Slack", "Michał", "url2")
        c = data["candidates"]["Skill Backlog::off-x"]
        self.assertEqual(c["occurrences"], 2)
        # jeszcze nie próg (3) → nie gotowy
        self.assertEqual(kb_state.ready_to_promote(data), [])
        # trzecie wystąpienie → próg osiągnięty
        kb_state.record_occurrence(data, "Skill Backlog", "off-x", "2026-05-20",
                                   "Gmail", "Michał", "url3")
        ready = kb_state.ready_to_promote(data)
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0]["occurrences"], 3)
        self.assertEqual(sorted(ready[0]["sources"]), ["Claude Chat", "Gmail", "Slack"])

    def test_idempotent_on_same_url(self):
        data = kb_state.load_candidates(self.cpath)
        kb_state.record_occurrence(data, "SOP", "proc-y", "2026-05-10", "Gmail", "Maciek", "u1")
        kb_state.record_occurrence(data, "SOP", "proc-y", "2026-05-10", "Gmail", "Maciek", "u1")
        c = data["candidates"]["SOP::proc-y"]
        self.assertEqual(c["occurrences"], 1)  # ten sam URL nie liczy się 2×

    def test_promote_flag(self):
        data = kb_state.load_candidates(self.cpath)
        kb_state.record_occurrence(data, "n8n Automation", "flow-z", "2026-05-10", "Gmail", "M", "a")
        kb_state.record_occurrence(data, "n8n Automation", "flow-z", "2026-05-11", "Slack", "M", "b")
        self.assertEqual(len(kb_state.ready_to_promote(data)), 1)
        kb_state.mark_promoted(data, "n8n Automation::flow-z")
        self.assertEqual(kb_state.ready_to_promote(data), [])  # już wypromowany

    def test_watermarks(self):
        data = kb_state.load_watermarks(self.wpath)
        self.assertIsNone(kb_state.get_watermark(data, "gmail"))
        kb_state.set_watermark(data, "gmail", "2026-05-20T10:00:00Z")
        kb_state.save_watermarks(data, self.wpath)
        data2 = kb_state.load_watermarks(self.wpath)
        self.assertEqual(kb_state.get_watermark(data2, "gmail"), "2026-05-20T10:00:00Z")


class TestMetrics(unittest.TestCase):
    def test_rollup(self):
        entries = [
            {"Type": "SOP", "Status": "New", "Priority": "High", "ROI score": 100},
            {"Type": "Skill Backlog", "Status": "Implemented", "Priority": "Medium", "ROI score": 50},
            {"Type": "n8n Automation", "Status": "Rejected", "Priority": "Low", "ROI score": 0},
            {"Type": "SOP", "Status": "Validated", "Priority": "High", "ROI score": 80},
        ]
        m = metrics.rollup(entries)
        self.assertEqual(m["total"], 4)
        self.assertEqual(m["by_type"]["SOP"], 2)
        self.assertEqual(m["rejected_rate"], 0.25)
        # done=2 (Implemented+Validated), non_rejected=3 → 0.667
        self.assertAlmostEqual(m["implemented_rate"], round(2 / 3, 3))
        self.assertEqual(m["backlog_open"], 1)  # tylko New

    def test_high_inflation_alert(self):
        entries = [{"Type": "SOP", "Status": "New", "Priority": "High", "ROI score": 1}
                   for _ in range(4)]
        entries.append({"Type": "SOP", "Status": "New", "Priority": "Low", "ROI score": 1})
        m = metrics.rollup(entries)  # 4/5 = 80% High
        self.assertTrue(m["high_pct_alert"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
