#!/usr/bin/env python3
"""Testy walidatora artefaktów wykonywalnych (sop_schema). Stdlib + PyYAML.

Uruchom:  python3 -m unittest discover -s scripts/tests -v  (z roota repo)
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import sop_schema  # noqa: E402


# --------------------------------------------------------------------------- #
# Fixtures — minimalne POPRAWNE artefakty (testy je mutują na błędne)
# --------------------------------------------------------------------------- #
def _min_sop(slug="proc-x", steps=None, irreversible_actions=None):
    return {
        "slug": slug, "version": 1, "status": "draft", "owner": "author",
        "source_url": "x", "parent_sop": None,
        "trigger": {"type": "schedule", "spec": "weekly", "description": "d"},
        "executor_overall": "human", "frequency": "weekly",
        "inputs": [], "outputs": [],
        "steps": steps or [{"id": 1, "action": "a", "automatable": False,
                            "executor": "human", "tool": None}],
        "guardrails": {"autonomy_level": "supervised",
                       "irreversible_actions": irreversible_actions or []},
        "acceptance_criteria": [], "metrics": {"log_to": "x", "fields": []},
    }


def _min_skill(name="skill-x", io=None, side_effects="read-only"):
    return {
        "name": name, "version": 1, "status": "draft", "description": "d", "parent_sop": None,
        "triggers": ["a", "b", "c", "d", "e"],
        "io": io or {"input": [{"name": "in1", "type": "t", "required": True}],
                     "output": [{"name": "out1", "type": "t"}]},
        "capabilities": {"allow": [], "deny": []},
        "side_effects": side_effects, "autonomy": "supervised",
        "guardrails": {"pii_handling": "x", "requires_human_review": False}, "evals": [],
    }


def _min_n8n(slug="flow-x", io=None, side_effects="read-only", irreversible=False, parent=None):
    return {
        "slug": slug, "version": 1, "status": "draft", "capability_ref": f"n8n:{slug}",
        "io": io or {"input": [], "output": [{"name": "out1", "type": "t"}]},
        "trigger": {"type": "webhook", "spec": "x"}, "side_effects": side_effects,
        "credentials_required": [],
        "guardrails": {"autonomy": "supervised", "irreversible": irreversible},
        "verification": {"test_plan": "x", "healthcheck": "x"},
        "parent_sop": parent, "notion_entry": "x", "source_url": "x",
    }


def _write_md(path: Path, fm, body="\n# tytuł\nbody\n"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
                    + "---\n" + body, encoding="utf-8")


def _write_n8n(path: Path, meta, name="flow"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"name": name, "nodes": [], "connections": {}, "meta": meta}),
                    encoding="utf-8")


class _Tmp(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.root = Path(self._d.name)

    def tearDown(self):
        self._d.cleanup()

    def sop(self, fm, name=None):
        _write_md(self.root / "sops" / f"{name or fm['slug']}.md", fm)

    def skill(self, fm):
        _write_md(self.root / "skills" / fm["name"] / "SKILL.md", fm)

    def n8n(self, meta, name=None):
        _write_n8n(self.root / "n8n" / f"{name or meta['slug']}.json", meta)

    def run_validate(self):
        return sop_schema.validate(str(self.root))


# --------------------------------------------------------------------------- #
# Integracja — realne wzorce w repo muszą przechodzić
# --------------------------------------------------------------------------- #
class TestRepoExamples(unittest.TestCase):
    def test_repo_examples_pass(self):
        repo_root = Path(__file__).resolve().parents[2]
        res = sop_schema.validate(str(repo_root / "artifacts"))
        self.assertTrue(res["ok"], msg=f"błędy: {res['errors']}")
        self.assertGreaterEqual(res["summary"]["sops"], 1)
        self.assertGreaterEqual(res["summary"]["skills"], 1)
        self.assertGreaterEqual(res["summary"]["n8n"], 2)


# --------------------------------------------------------------------------- #
# Struktura
# --------------------------------------------------------------------------- #
class TestStructure(_Tmp):
    def test_valid_minimal_sop_passes(self):
        self.sop(_min_sop())
        self.assertTrue(self.run_validate()["ok"])

    def test_automatable_true_requires_tool(self):
        self.sop(_min_sop(steps=[{"id": 1, "action": "a", "automatable": True,
                                  "executor": "auto", "tool": None}]))
        res = self.run_validate()
        self.assertFalse(res["ok"])
        self.assertTrue(any("automatable:true" in e for e in res["errors"]))

    def test_bad_tool_prefix(self):
        self.sop(_min_sop(steps=[{"id": 1, "action": "a", "automatable": True,
                                  "executor": "auto", "tool": "magic-do-it"}]))
        self.assertFalse(self.run_validate()["ok"])

    def test_irreversible_action_not_in_steps(self):
        self.sop(_min_sop(irreversible_actions=[9]))
        res = self.run_validate()
        self.assertFalse(res["ok"])
        self.assertTrue(any("irreversible_actions zawiera id 9" in e for e in res["errors"]))

    def test_duplicate_slug(self):
        self.sop(_min_sop(slug="proc-x"), name="a")
        self.sop(_min_sop(slug="proc-x"), name="b")
        res = self.run_validate()
        self.assertFalse(res["ok"])
        self.assertTrue(any("zduplikowany" in e for e in res["errors"]))

    def test_non_kebab_slug(self):
        self.sop(_min_sop(slug="Proc_X"), name="badslug")
        self.assertFalse(self.run_validate()["ok"])

    def test_missing_frontmatter(self):
        p = self.root / "sops" / "x.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# tylko body, brak frontmattera\n", encoding="utf-8")
        res = self.run_validate()
        self.assertFalse(res["ok"])
        self.assertTrue(any("frontmattera" in e for e in res["errors"]))


# --------------------------------------------------------------------------- #
# Binding I/O (cross-artefaktowe) + SAFETY
# --------------------------------------------------------------------------- #
class TestBindingAndSafety(_Tmp):
    def _sop_calling(self, tool, inputs, outputs, irreversible_actions=None):
        return _min_sop(steps=[{"id": 1, "action": "a", "automatable": True,
                                "executor": "ai", "tool": tool,
                                "inputs": inputs, "outputs": outputs}],
                        irreversible_actions=irreversible_actions)

    def test_skill_io_match_passes(self):
        self.sop(self._sop_calling("skill:skill-x", ["in1"], ["out1"]))
        self.skill(_min_skill())
        self.assertTrue(self.run_validate()["ok"])

    def test_skill_output_mismatch_fails(self):
        self.sop(self._sop_calling("skill:skill-x", ["in1"], ["WRONG"]))
        self.skill(_min_skill())
        res = self.run_validate()
        self.assertFalse(res["ok"])
        self.assertTrue(any("wyjścia kroku" in e for e in res["errors"]))

    def test_skill_missing_required_input_fails(self):
        self.sop(self._sop_calling("skill:skill-x", [], ["out1"]))
        self.skill(_min_skill())
        res = self.run_validate()
        self.assertFalse(res["ok"])
        self.assertTrue(any("wymaga wejść" in e for e in res["errors"]))

    def test_referenced_skill_missing_is_warning_not_error(self):
        self.sop(self._sop_calling("skill:nieistnieje", ["in1"], ["out1"]))
        res = self.run_validate()
        self.assertTrue(res["ok"])  # warning, nie error
        self.assertTrue(any("nieistnieje" in w for w in res["warnings"]))

    def test_external_send_must_be_gated(self):
        # n8n external-send wołany przez krok, którego NIE ma w irreversible_actions → SAFETY błąd
        self.sop(self._sop_calling("n8n:flow-x", [], ["out1"], irreversible_actions=[]))
        self.n8n(_min_n8n(side_effects="external-send", parent="proc-x"))
        res = self.run_validate()
        self.assertFalse(res["ok"])
        self.assertTrue(any("SAFETY" in e for e in res["errors"]))

    def test_external_send_gated_passes(self):
        self.sop(self._sop_calling("n8n:flow-x", [], ["out1"], irreversible_actions=[1]))
        self.n8n(_min_n8n(side_effects="external-send", parent="proc-x"))
        self.assertTrue(self.run_validate()["ok"])

    def test_irreversible_flow_must_be_gated(self):
        self.sop(self._sop_calling("n8n:flow-x", [], ["out1"], irreversible_actions=[]))
        self.n8n(_min_n8n(irreversible=True, parent="proc-x"))
        res = self.run_validate()
        self.assertFalse(res["ok"])
        self.assertTrue(any("SAFETY" in e for e in res["errors"]))


# --------------------------------------------------------------------------- #
# n8n meta
# --------------------------------------------------------------------------- #
class TestN8nMeta(_Tmp):
    def test_capability_ref_mismatch_fails(self):
        m = _min_n8n(slug="flow-x")
        m["capability_ref"] = "n8n:WRONG"
        self.n8n(m)
        res = self.run_validate()
        self.assertFalse(res["ok"])
        self.assertTrue(any("capability_ref" in e for e in res["errors"]))

    def test_invalid_json_fails(self):
        p = self.root / "n8n" / "broken.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{ to nie jest json ", encoding="utf-8")
        res = self.run_validate()
        self.assertFalse(res["ok"])
        self.assertTrue(any("JSON" in e for e in res["errors"]))


if __name__ == "__main__":
    unittest.main()
