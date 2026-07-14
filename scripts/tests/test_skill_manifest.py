#!/usr/bin/env python3
"""Testy gate'u instalowalności skilla (skill_manifest). Stdlib + PyYAML.

Uruchom:  python3 -m unittest discover -s scripts/tests -v  (z roota repo)
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import skill_manifest  # noqa: E402


def _write(tmp, text):
    path = os.path.join(tmp, "SKILL.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


VALID = """\
---
name: knowledge-base
description: Robi X i używa się go, gdy user prosi o Y — wystarczająco długi opis.
---

# knowledge-base

Body.
"""


class TestSplitFrontmatter(unittest.TestCase):
    def test_extracts_block(self):
        fm, body = skill_manifest.split_frontmatter(VALID)
        self.assertIn("name: knowledge-base", fm)
        self.assertIn("# knowledge-base", body)

    def test_no_frontmatter(self):
        fm, _ = skill_manifest.split_frontmatter("# tytuł\ntekst")
        self.assertIsNone(fm)

    def test_unterminated_frontmatter(self):
        fm, _ = skill_manifest.split_frontmatter("---\nname: x\nbody bez domknięcia")
        self.assertIsNone(fm)

    def test_tolerates_bom(self):
        fm, _ = skill_manifest.split_frontmatter("﻿" + VALID)
        self.assertIsNotNone(fm)


class TestValidate(unittest.TestCase):
    def test_valid_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = skill_manifest.validate(_write(tmp, VALID))
            self.assertTrue(res["ok"], res)
            self.assertEqual(res["errors"], [])

    def test_missing_file(self):
        res = skill_manifest.validate("/nope/SKILL.md")
        self.assertFalse(res["ok"])

    def test_no_frontmatter_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = skill_manifest.validate(_write(tmp, "# knowledge-base\n\nbody"))
            self.assertFalse(res["ok"])
            self.assertTrue(any("frontmatter" in e for e in res["errors"]))

    def test_missing_name_and_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = skill_manifest.validate(_write(tmp, "---\nlicense: MIT\n---\nbody"))
            self.assertFalse(res["ok"])
            joined = " ".join(res["errors"])
            self.assertIn("name", joined)
            self.assertIn("description", joined)

    def test_bad_name_not_kebab(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = VALID.replace("name: knowledge-base", "name: Knowledge_Base")
            res = skill_manifest.validate(_write(tmp, bad))
            self.assertFalse(res["ok"])
            self.assertTrue(any("kebab" in e for e in res["errors"]))

    def test_description_too_long(self):
        with tempfile.TemporaryDirectory() as tmp:
            long_desc = "x" * (skill_manifest.DESC_MAX + 1)
            bad = VALID.replace(
                "description: Robi X i używa się go, gdy user prosi o Y — wystarczająco długi opis.",
                f"description: {long_desc}",
            )
            res = skill_manifest.validate(_write(tmp, bad))
            self.assertFalse(res["ok"])
            self.assertTrue(any("description" in e and "max" in e for e in res["errors"]))

    def test_name_dir_mismatch_warns(self):
        # katalog tmp ma losową nazwę != 'knowledge-base' → ostrzeżenie, ale ok
        with tempfile.TemporaryDirectory() as tmp:
            res = skill_manifest.validate(_write(tmp, VALID))
            self.assertTrue(res["ok"])
            self.assertTrue(any("katalog" in w for w in res["warnings"]))

    def test_repo_skill_md_is_installable(self):
        # rzeczywisty SKILL.md repo musi przechodzić gate (regression guard)
        root = os.path.join(os.path.dirname(__file__), "..", "..")
        res = skill_manifest.validate(os.path.join(root, "SKILL.md"))
        self.assertTrue(res["ok"], res)


if __name__ == "__main__":
    unittest.main()
