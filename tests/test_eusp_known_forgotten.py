"""Regression tests for explicit local known-versus-forgotten handling."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from eusp_known_forgotten import SCHEMA_VERSION, evaluate_known_forgotten, validate_known_forgotten

FIXTURE = ROOT / "evals/fixtures/eusp_known_forgotten/v1/fixture.json"


class EuspKnownForgottenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_anonymized_fixture_is_valid_and_reproducible(self) -> None:
        self.assertEqual(validate_known_forgotten(self.fixture, public_fixture=True), [])
        self.assertEqual(self.fixture["schema_version"], SCHEMA_VERSION)
        self.assertEqual(evaluate_known_forgotten(self.fixture), evaluate_known_forgotten(self.fixture))

    def test_unknown_requires_no_evidence_instead_of_a_guess(self) -> None:
        invalid = copy.deepcopy(self.fixture)
        candidate = next(item for item in invalid["candidates"] if item["id"] == "kf-unknown-high")
        candidate["awareness"]["evidence"] = [{
            "kind": "explicit_current_recognition", "provenance": "user_supplied_local",
            "statement": "Guessed from an omitted history."
        }]
        errors = validate_known_forgotten(invalid)
        self.assertTrue(any("must have no awareness evidence" in error for error in errors), errors)

    def test_known_and_forgotten_need_distinct_explicit_local_evidence(self) -> None:
        invalid = copy.deepcopy(self.fixture)
        known = next(item for item in invalid["candidates"] if item["id"] == "kf-known-high")
        known["awareness"]["evidence"][0]["kind"] = "explicit_reminder_request"
        forgotten = next(item for item in invalid["candidates"] if item["id"] == "kf-forgotten-useful")
        forgotten["awareness"]["evidence"][0]["kind"] = "explicit_current_recognition"
        errors = validate_known_forgotten(invalid)
        self.assertTrue(any("known candidate" in error for error in errors), errors)
        self.assertTrue(any("forgotten candidate" in error for error in errors), errors)

    def test_reminder_is_separate_from_novelty_and_cannot_suppress_high_value_action(self) -> None:
        result = evaluate_known_forgotten(self.fixture)
        treatment = result["known_reminder_treatment"]
        self.assertEqual(result["baseline"]["action_selected_ids"], treatment["action_selected_ids"])
        self.assertIn("kf-known-high", treatment["action_selected_ids"])
        self.assertEqual(treatment["novelty_lane_ids"], ["kf-unknown-high", "kf-unknown-novel"])
        self.assertEqual(treatment["reminder_lane_ids"], ["kf-forgotten-useful", "kf-forgotten-low"])
        self.assertNotIn("kf-known-high", treatment["novelty_lane_ids"])
        self.assertEqual(result["metrics"]["false_suppression_rate"], 0.0)

    def test_gate_failed_forgotten_candidate_is_neither_action_nor_reminder(self) -> None:
        result = evaluate_known_forgotten(self.fixture)
        treatment = result["known_reminder_treatment"]
        self.assertNotIn("kf-forgotten-stale", treatment["action_selected_ids"])
        self.assertNotIn("kf-forgotten-stale", treatment["reminder_lane_ids"])

    def test_fixture_measures_reminder_usefulness_as_an_explicit_synthetic_proxy(self) -> None:
        proxy = evaluate_known_forgotten(self.fixture)["metrics"]["reminder_usefulness_proxy"]
        self.assertEqual(proxy["useful_reminder_ids"], ["kf-forgotten-useful"])
        self.assertEqual(proxy["precision"], 0.5)
        self.assertEqual(proxy["recall"], 1.0)


if __name__ == "__main__":
    unittest.main()
