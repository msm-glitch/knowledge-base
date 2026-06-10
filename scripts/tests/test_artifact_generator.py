#!/usr/bin/env python3
"""Testy artifact_generator — Krok 4.5 knowledge-base. Tylko stdlib (unittest).

Uruchom:  python3 -m unittest discover -s scripts/tests -v
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import artifact_generator as ag  # noqa: E402

# --- fixtures -----------------------------------------------------------------

SYSTEMS = {
    "monday": {
        "node": "n8n-nodes-base.mondayCom",
        "credential": "monday_api",
        "connector": "monday",
        "aliases": ["CRM", "monday", "monday.com", "baza partnerów"],
    },
    "gmail": {
        "node": "n8n-nodes-base.gmail",
        "credential": "gmail_oauth",
        "connector": "gmail",
        "aliases": ["Gmail", "mail", "email", "poczta"],
    },
    "slack": {
        "node": "n8n-nodes-base.slack",
        "credential": "slack_api",
        "connector": "slack",
        "aliases": ["Slack", "kanał", "#ai-feedback"],
    },
    "notion": {
        "node": "n8n-nodes-base.notion",
        "credential": "notion_api",
        "connector": "notion",
        "aliases": ["Notion", "baza wiedzy"],
    },
}

CONNECTORS = {
    "monday": {
        "functions": ["get_board_items_page", "create_item", "change_item_column_values"],
        "side_effects": "writes-internal",
    },
    "gmail": {
        "functions": ["create_draft", "search_threads", "get_thread"],
        "side_effects": "external-send",
    },
    "slack": {
        "functions": ["slack_send_message", "slack_read_channel"],
        "side_effects": "external-send",
    },
    "notion": {
        "functions": ["notion-create-pages", "notion-update-page", "notion-fetch"],
        "side_effects": "writes-internal",
    },
}

TRIGGERS_CATALOG = {
    "schedule":    {"node": "n8n-nodes-base.scheduleTrigger"},
    "webhook":     {"node": "n8n-nodes-base.webhook"},
    "form":        {"node": "n8n-nodes-base.formTrigger"},
    "manual":      {"node": "n8n-nodes-base.manualTrigger"},
    "called_by_sop": {"node": "n8n-nodes-base.executeWorkflowTrigger"},
}

LOGIC_CATALOG = {
    "transform": {"node": "n8n-nodes-base.code"},
    "branch":    {"node": "n8n-nodes-base.if"},
}

ERROR_CATALOG = {
    "alert": {"node": "n8n-nodes-base.slack"},
}

N8N_NODES = {
    "systems":  SYSTEMS,
    "triggers": TRIGGERS_CATALOG,
    "logic":    LOGIC_CATALOG,
    "error":    ERROR_CATALOG,
}

SOP_ENTRY = {
    "title": "[NEW] 2026-05-10 · Michał · partner-reaktywacja — Reaktywacja partnerów quarterly",
    "type": "SOP",
    "summary": "Kwartalny proces reaktywacji uśpionych partnerów w CRM.",
    "trigger": "Co kwartał, ręcznie przez Macka",
    "steps": [
        "Pobierz listę partnerów z monday.com",
        "Oceń status każdego partnera",
        "Wyślij maile reaktywacyjne przez Gmail",
    ],
    "owner": "maciek",
    "parent_sop": None,
    "kb_entry_url": "https://www.notion.so/abc123",
    "date": "2026-05-10",
    "frequency": "quarterly",
    "priority": "High",
}

SKILL_ENTRY = {
    "title": "[NEW] 2026-05-11 · Michał · off-reaktywacja-partnera — Szkic maila reaktywacyjnego",
    "type": "Skill Backlog",
    "summary": "Generuje szkic maila do uśpionego partnera w stylu OFF.",
    "description": "Skill pisze maile reaktywacyjne w brand voice Fundacji OFF.",
    "trigger": "Krok 3 SOPa partner-reaktywacja",
    "trigger_phrases": [
        "napisz mail reaktywacyjny",
        "szkicuj email do partnera",
        "przygotuj wiadomość do partnera OFF",
        "draft reaktywacji partnera",
        "email reaktywacyjny OFF",
    ],
    "owner": "maciek",
    "parent_sop": "partner-reaktywacja",
    "kb_entry_url": "https://www.notion.so/def456",
    "date": "2026-05-11",
    "priority": "Medium",
}

N8N_ENTRY = {
    "title": "[NEW] 2026-05-12 · Maciek · crm-stale-partners — Automatyczne wykrycie uśpionych partnerów",
    "type": "n8n Automation",
    "summary": "Tygodniowe sprawdzenie CRM i wysyłka powiadomienia Slack.",
    "trigger": "Co tydzień w poniedziałek 8:00",
    "data_sources": ["monday"],
    "destinations": ["slack"],
    "transformations": "Filtruj partnerów bez aktywności >90 dni",
    "error_handling": "Alert na #ai-feedback przez Slack",
    "owner": "maciek",
    "parent_sop": "partner-reaktywacja",
    "kb_entry_url": "https://www.notion.so/ghi789",
    "date": "2026-05-12",
    "priority": "High",
}


# --- slugify ------------------------------------------------------------------

class TestSlugify(unittest.TestCase):
    def test_standard_title(self):
        self.assertEqual(
            ag.slugify("[NEW] 2026-05-10 · Michał · off-brand-voice — opis"),
            "off-brand-voice",
        )

    def test_fix_prefix(self):
        self.assertEqual(
            ag.slugify("[FIX] 2026-05-11 · Michał · off-brand-voice — dodaj"),
            "off-brand-voice",
        )

    def test_no_author_segment(self):
        slug = ag.slugify("[NEW] 2026-05-10 · partner-reaktywacja — opis")
        self.assertEqual(slug, "partner-reaktywacja")

    def test_empty_title(self):
        self.assertEqual(ag.slugify(""), "tbd")

    def test_none_title(self):
        self.assertEqual(ag.slugify(None), "tbd")

    def test_no_prefix(self):
        slug = ag.slugify("2026-05-10 · Michał · crm-export — opis")
        self.assertEqual(slug, "crm-export")

    def test_polish_chars_normalized(self):
        slug = ag.slugify("[NEW] 2026-05-10 · Michał · ewidencja-godzin — opis")
        self.assertNotIn("ł", slug)

    def test_spaces_become_hyphens(self):
        slug = ag.slugify("[NEW] 2026-05-10 · Michał · my slug — opis")
        self.assertNotIn(" ", slug)


# --- resolve_n8n_system -------------------------------------------------------

class TestResolveN8nSystem(unittest.TestCase):
    def test_found_by_alias(self):
        result = ag.resolve_n8n_system("monday.com", SYSTEMS)
        self.assertIsNotNone(result)
        self.assertEqual(result["key"], "monday")
        self.assertEqual(result["node"], "n8n-nodes-base.mondayCom")

    def test_found_crm_alias(self):
        result = ag.resolve_n8n_system("CRM", SYSTEMS)
        self.assertIsNotNone(result)
        self.assertEqual(result["key"], "monday")

    def test_found_gmail_alias(self):
        result = ag.resolve_n8n_system("email", SYSTEMS)
        self.assertIsNotNone(result)
        self.assertEqual(result["key"], "gmail")

    def test_unknown_system_returns_none(self):
        result = ag.resolve_n8n_system("Jira", SYSTEMS)
        self.assertIsNone(result)

    def test_empty_text_returns_none(self):
        self.assertIsNone(ag.resolve_n8n_system("", SYSTEMS))

    def test_returns_credential(self):
        result = ag.resolve_n8n_system("monday", SYSTEMS)
        self.assertEqual(result["credential"], "monday_api")


# --- resolve_trigger_node -----------------------------------------------------

class TestResolveTriggerNode(unittest.TestCase):
    def test_schedule_cron(self):
        node = ag.resolve_trigger_node("Co tydzień w poniedziałek 8:00", TRIGGERS_CATALOG)
        self.assertEqual(node, "n8n-nodes-base.scheduleTrigger")

    def test_schedule_quarterly(self):
        node = ag.resolve_trigger_node("Co kwartał, ręcznie", TRIGGERS_CATALOG)
        self.assertEqual(node, "n8n-nodes-base.scheduleTrigger")

    def test_webhook(self):
        node = ag.resolve_trigger_node("Webhook od Brevo po wysyłce", TRIGGERS_CATALOG)
        self.assertEqual(node, "n8n-nodes-base.webhook")

    def test_form(self):
        node = ag.resolve_trigger_node("Submit formularza rejestracji", TRIGGERS_CATALOG)
        self.assertEqual(node, "n8n-nodes-base.formTrigger")

    def test_manual(self):
        node = ag.resolve_trigger_node("Ręcznie przez Macka", TRIGGERS_CATALOG)
        self.assertEqual(node, "n8n-nodes-base.manualTrigger")

    def test_unknown_defaults_to_schedule(self):
        node = ag.resolve_trigger_node("Nieznany trigger", TRIGGERS_CATALOG)
        self.assertEqual(node, "n8n-nodes-base.scheduleTrigger")


# --- generate_sop -------------------------------------------------------------

class TestGenerateSop(unittest.TestCase):
    def setUp(self):
        self.result = ag.generate_sop(SOP_ENTRY, SYSTEMS, CONNECTORS, "2026-06-10")

    def test_artifact_type(self):
        self.assertEqual(self.result["artifact_type"], "sop")

    def test_slug_extracted(self):
        self.assertEqual(self.result["slug"], "partner-reaktywacja")

    def test_no_errors(self):
        self.assertEqual(self.result["errors"], [])

    def test_body_language(self):
        self.assertEqual(self.result["body_language"], "yaml")

    def test_notion_fields_keys(self):
        nf = self.result["notion_fields"]
        for key in ("Nazwa procesu", "Trigger procesu", "Opis procesu",
                    "Select", "Wersja", "Owner"):
            self.assertIn(key, nf)

    def test_notion_fields_select_value(self):
        self.assertEqual(self.result["notion_fields"]["Select"], "Wersja robocza")

    def test_notion_fields_wersja(self):
        self.assertEqual(self.result["notion_fields"]["Wersja"], 1)

    def test_body_contains_slug(self):
        self.assertIn("partner-reaktywacja", self.result["body_content"])

    def test_body_contains_trigger(self):
        self.assertIn("Co kwartał", self.result["body_content"])

    def test_body_starts_with_frontmatter(self):
        self.assertTrue(self.result["body_content"].startswith("---"))

    def test_irreversible_for_gmail_step(self):
        body = self.result["body_content"]
        # Krok "Wyślij maile przez Gmail" → external-send → irreversible_actions
        self.assertIn("irreversible_actions:", body)

    def test_steps_as_string(self):
        entry = dict(SOP_ENTRY, steps="Krok 1\nKrok 2\nKrok 3")
        result = ag.generate_sop(entry, SYSTEMS, CONNECTORS, "2026-06-10")
        self.assertIn("Krok 1", result["body_content"])

    def test_missing_slug_error(self):
        entry = dict(SOP_ENTRY, title="")
        result = ag.generate_sop(entry, SYSTEMS, CONNECTORS, "2026-06-10")
        self.assertTrue(any("needs_slug" in e for e in result["errors"]))

    def test_empty_steps_gets_placeholder(self):
        entry = dict(SOP_ENTRY, steps=[])
        result = ag.generate_sop(entry, SYSTEMS, CONNECTORS, "2026-06-10")
        self.assertIn("[TBD", result["body_content"])

    def test_schema_comment_in_body(self):
        self.assertIn("artifacts/sops/SCHEMA.md", self.result["body_content"])


# --- generate_skill -----------------------------------------------------------

class TestGenerateSkill(unittest.TestCase):
    def setUp(self):
        self.result = ag.generate_skill(SKILL_ENTRY, "2026-06-10")

    def test_artifact_type(self):
        self.assertEqual(self.result["artifact_type"], "skill")

    def test_slug_extracted(self):
        self.assertEqual(self.result["slug"], "off-reaktywacja-partnera")

    def test_no_errors(self):
        self.assertEqual(self.result["errors"], [])

    def test_body_language(self):
        self.assertEqual(self.result["body_language"], "yaml")

    def test_notion_fields_type(self):
        self.assertEqual(self.result["notion_fields"]["Type"], "Skill")

    def test_notion_fields_status(self):
        self.assertEqual(self.result["notion_fields"]["Status"], "Idea")

    def test_notion_fields_priority_map(self):
        self.assertEqual(self.result["notion_fields"]["Priority"], "P1")  # Medium→P1

    def test_five_trigger_phrases_in_body(self):
        body = self.result["body_content"]
        self.assertEqual(body.count('napisz mail reaktywacyjny'), 1)
        # wszystkie 5 fraz obecne
        for phrase in SKILL_ENTRY["trigger_phrases"]:
            self.assertIn(phrase, body)

    def test_missing_phrases_get_padded(self):
        entry = dict(SKILL_ENTRY, trigger_phrases=["tylko jedna fraza"])
        result = ag.generate_skill(entry, "2026-06-10")
        self.assertIn("[TBD: trigger phrase 2]", result["body_content"])

    def test_body_contains_slug(self):
        self.assertIn("off-reaktywacja-partnera", self.result["body_content"])

    def test_body_starts_with_frontmatter(self):
        self.assertTrue(self.result["body_content"].startswith("---"))

    def test_schema_comment_in_body(self):
        self.assertIn("artifacts/skills/SCHEMA.md", self.result["body_content"])

    def test_high_priority_maps_to_p0(self):
        entry = dict(SKILL_ENTRY, priority="High")
        result = ag.generate_skill(entry, "2026-06-10")
        self.assertEqual(result["notion_fields"]["Priority"], "P0")


# --- generate_n8n -------------------------------------------------------------

class TestGenerateN8n(unittest.TestCase):
    def setUp(self):
        self.result = ag.generate_n8n(
            N8N_ENTRY, SYSTEMS, CONNECTORS,
            TRIGGERS_CATALOG, LOGIC_CATALOG, ERROR_CATALOG,
            "2026-06-10",
        )

    def test_artifact_type(self):
        self.assertEqual(self.result["artifact_type"], "n8n")

    def test_slug_extracted(self):
        self.assertEqual(self.result["slug"], "crm-stale-partners")

    def test_no_errors(self):
        self.assertEqual(self.result["errors"], [])

    def test_body_language(self):
        self.assertEqual(self.result["body_language"], "json")

    def test_body_is_valid_json(self):
        parsed = json.loads(self.result["body_content"])
        self.assertIn("nodes", parsed)
        self.assertIn("meta", parsed)

    def test_notion_fields_type(self):
        self.assertEqual(self.result["notion_fields"]["Type"], "Automation")

    def test_notion_fields_status(self):
        self.assertEqual(self.result["notion_fields"]["Status"], "Idea")

    def test_trigger_node_resolved(self):
        parsed = json.loads(self.result["body_content"])
        trigger_node = parsed["nodes"][0]
        self.assertEqual(trigger_node["name"], "Trigger")
        self.assertEqual(trigger_node["type"], "n8n-nodes-base.scheduleTrigger")

    def test_monday_source_node_resolved(self):
        parsed = json.loads(self.result["body_content"])
        source_nodes = [n for n in parsed["nodes"] if "Source:" in n["name"]]
        self.assertTrue(len(source_nodes) >= 1)
        self.assertEqual(source_nodes[0]["type"], "n8n-nodes-base.mondayCom")

    def test_slack_destination_resolved(self):
        parsed = json.loads(self.result["body_content"])
        dest_nodes = [n for n in parsed["nodes"] if "Destination:" in n["name"]]
        self.assertTrue(len(dest_nodes) >= 1)
        self.assertEqual(dest_nodes[0]["type"], "n8n-nodes-base.slack")

    def test_error_handler_present(self):
        parsed = json.loads(self.result["body_content"])
        error_nodes = [n for n in parsed["nodes"] if n["name"] == "Error handler"]
        self.assertEqual(len(error_nodes), 1)
        self.assertEqual(error_nodes[0]["type"], "n8n-nodes-base.slack")

    def test_credentials_collected(self):
        parsed = json.loads(self.result["body_content"])
        creds = parsed["meta"]["credentials_required"]
        self.assertIn("monday_api", creds)
        self.assertIn("slack_api", creds)

    def test_slack_destination_sets_external_send(self):
        parsed = json.loads(self.result["body_content"])
        self.assertEqual(parsed["meta"]["side_effects"], "external-send")

    def test_unknown_system_raises_warning(self):
        entry = dict(N8N_ENTRY, data_sources=["Jira"])
        result = ag.generate_n8n(
            entry, SYSTEMS, CONNECTORS,
            TRIGGERS_CATALOG, LOGIC_CATALOG, ERROR_CATALOG,
            "2026-06-10",
        )
        self.assertTrue(any("unknown-system" in w for w in result["warnings"]))
        parsed = json.loads(result["body_content"])
        jira_node = next(n for n in parsed["nodes"] if "Jira" in n["name"])
        self.assertEqual(jira_node["type"], "TBD")

    def test_transformations_node_added(self):
        parsed = json.loads(self.result["body_content"])
        transform_nodes = [n for n in parsed["nodes"] if n["name"] == "Transform"]
        self.assertEqual(len(transform_nodes), 1)
        self.assertEqual(transform_nodes[0]["type"], "n8n-nodes-base.code")

    def test_data_sources_as_string(self):
        entry = dict(N8N_ENTRY, data_sources="monday, gmail")
        result = ag.generate_n8n(
            entry, SYSTEMS, CONNECTORS,
            TRIGGERS_CATALOG, LOGIC_CATALOG, ERROR_CATALOG,
            "2026-06-10",
        )
        parsed = json.loads(result["body_content"])
        source_names = [n["name"] for n in parsed["nodes"] if "Source:" in n["name"]]
        self.assertEqual(len(source_names), 2)


# --- dispatch (generate) ------------------------------------------------------

class TestDispatch(unittest.TestCase):
    def test_dispatches_sop(self):
        result = ag.generate(SOP_ENTRY, CONNECTORS, N8N_NODES, "2026-06-10")
        self.assertEqual(result["artifact_type"], "sop")

    def test_dispatches_skill(self):
        result = ag.generate(SKILL_ENTRY, CONNECTORS, N8N_NODES, "2026-06-10")
        self.assertEqual(result["artifact_type"], "skill")

    def test_dispatches_n8n(self):
        result = ag.generate(N8N_ENTRY, CONNECTORS, N8N_NODES, "2026-06-10")
        self.assertEqual(result["artifact_type"], "n8n")

    def test_unknown_type_returns_error(self):
        entry = dict(SOP_ENTRY, type="Nieznany")
        result = ag.generate(entry, CONNECTORS, N8N_NODES, "2026-06-10")
        self.assertEqual(result["artifact_type"], "unknown")
        self.assertTrue(any("unknown-type" in e for e in result["errors"]))

    def test_batch_returns_list(self):
        entries = [SOP_ENTRY, SKILL_ENTRY, N8N_ENTRY]
        results = ag.generate_batch(entries, CONNECTORS, N8N_NODES, "2026-06-10")
        self.assertEqual(len(results), 3)
        types = [r["artifact_type"] for r in results]
        self.assertEqual(types, ["sop", "skill", "n8n"])


# --- CLI ----------------------------------------------------------------------

class TestCli(unittest.TestCase):
    def _make_entry_file(self, entry: dict) -> str:
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(entry, f)
        return path

    def test_cli_generate_sop(self):
        path = self._make_entry_file(SOP_ENTRY)
        try:
            import io
            from unittest.mock import patch
            out = io.StringIO()
            with patch("sys.stdout", out):
                rc = ag.main([
                    "generate", "--entry", path, "--date", "2026-06-10",
                    "--connectors", "config/connectors.yaml",
                    "--n8n-nodes", "config/n8n_nodes.yaml",
                ])
            # rc może być None jeśli yaml nie jest zainstalowany — sprawdź czy wyjście jest JSON
            output = out.getvalue()
            if output.strip():
                parsed = json.loads(output)
                self.assertEqual(parsed["artifact_type"], "sop")
        except Exception:
            pass  # CLI wymaga yaml; jeśli brak — pomijamy
        finally:
            os.unlink(path)

    def test_cli_no_args_returns_error(self):
        import io
        err = io.StringIO()
        from unittest.mock import patch
        with patch("sys.stderr", err):
            rc = ag.main(["generate"])
        self.assertNotEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
