"""Regression tests for the EUSP local artifact-action contract."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from eusp_action import SCHEMA_VERSION, validate_action_portfolio

FIXTURE = ROOT / "evals/fixtures/eusp_action/v1/actions.json"


class EuspActionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.portfolio = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_anonymized_fixture_has_only_bounded_evidenced_local_actions(self) -> None:
        self.assertEqual(validate_action_portfolio(self.portfolio, public_fixture=True), [])
        self.assertEqual(self.portfolio["schema_version"], SCHEMA_VERSION)
        for action in self.portfolio["actions"]:
            self.assertIn(action["classification"], {"ACT_NOW", "PREPARE_NEXT"})
            self.assertTrue(action["deliverable"])
            self.assertLessEqual(action["minutes_min"], action["minutes_max"])
            self.assertLessEqual(action["minutes_max"], 60)
            self.assertTrue(action["blockers"])
            self.assertTrue(action["evidence_ids"])

    def test_every_action_fails_closed_without_a_deliverable_blocker_or_supporting_evidence(self) -> None:
        invalid = copy.deepcopy(self.portfolio)
        action = invalid["actions"][0]
        del action["deliverable"]
        action["blockers"] = []
        action["evidence_ids"] = ["e-orientation"]
        errors = validate_action_portfolio(invalid)
        self.assertTrue(any("missing required property deliverable" in error for error in errors), errors)
        self.assertTrue(any("fewer than minItems" in error for error in errors), errors)
        self.assertTrue(any("does not directly support action" in error for error in errors), errors)

    def test_selected_actions_must_be_act_now_or_prepare_next_and_start_within_seven_days(self) -> None:
        invalid = copy.deepcopy(self.portfolio)
        invalid["actions"][0]["classification"] = "MONITOR"
        invalid["actions"][0]["start_date"] = "2026-09-08"
        invalid["actions"][0]["minutes_min"] = 50
        invalid["actions"][0]["minutes_max"] = 40
        errors = validate_action_portfolio(invalid)
        self.assertTrue(any("not in enum" in error for error in errors), errors)
        self.assertTrue(any("seven days" in error for error in errors), errors)
        self.assertTrue(any("minutes_min exceeds" in error for error in errors), errors)

    def test_cold_outreach_is_an_unsent_draft_only_with_verified_shared_context(self) -> None:
        invalid = copy.deepcopy(self.portfolio)
        draft_action = invalid["actions"][1]
        del draft_action["draft"]
        invalid["evidence"][1]["purpose"] = "action_basis"
        errors = validate_action_portfolio(invalid)
        self.assertTrue(any("must produce a local draft" in error for error in errors), errors)

        invalid = copy.deepcopy(self.portfolio)
        invalid["evidence"][1]["purpose"] = "action_basis"
        invalid["actions"][1]["draft"]["shared_context"]["provenance"] = "inferred"
        errors = validate_action_portfolio(invalid)
        self.assertTrue(any("lacks verified shared-context evidence" in error for error in errors), errors)
        self.assertTrue(any("does not equal const 'user_supplied'" in error for error in errors), errors)

    def test_draft_cannot_invent_a_relationship_route_or_permission(self) -> None:
        invalid = copy.deepcopy(self.portfolio)
        invalid["actions"][1]["draft"]["text"] = (
            "Our mutual connection introduced us; I have permission to use their email address.")
        invalid["actions"][1]["recipient"] = "A fictional person"
        errors = validate_action_portfolio(invalid)
        self.assertTrue(any("unexpected property recipient" in error for error in errors), errors)
        self.assertTrue(any("invents a relationship, introduction, or permission" in error for error in errors), errors)
        self.assertTrue(any("invents or embeds a contact route" in error for error in errors), errors)

    def test_no_action_can_be_an_external_write(self) -> None:
        invalid = copy.deepcopy(self.portfolio)
        invalid["actions"][0]["action"] = "Send the checklist to the organization."
        errors = validate_action_portfolio(invalid)
        self.assertTrue(any("external act" in error for error in errors), errors)

    def test_only_the_draft_kind_can_describe_outreach(self) -> None:
        invalid = copy.deepcopy(self.portfolio)
        invalid["actions"][0]["deliverable"] = "A local outreach draft."
        errors = validate_action_portfolio(invalid)
        self.assertTrue(any("only cold outreach" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
