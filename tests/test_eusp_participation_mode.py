"""Regression tests for the non-obvious participation-mode fixture."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from eusp_participation_mode import SCHEMA_VERSION, evaluate_participation_mode, validate_participation_mode

FIXTURE = ROOT / "evals/fixtures/eusp_participation_mode/v1/fixture.json"


class EuspParticipationModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fabricated_fixture_is_valid_and_reproducible(self) -> None:
        self.assertEqual(validate_participation_mode(self.fixture, public_fixture=True), [])
        self.assertEqual(self.fixture["schema_version"], SCHEMA_VERSION)
        self.assertEqual(evaluate_participation_mode(self.fixture), evaluate_participation_mode(self.fixture))

    def test_only_the_mode_bonus_changes_the_frozen_ranked_selection(self) -> None:
        result = evaluate_participation_mode(self.fixture)
        self.assertEqual(result["baseline"]["selected_ids"], ["pm-open-call", "pm-standard-workshop"])
        self.assertEqual(result["non_obvious_participation_mode_treatment"]["selected_ids"], ["pm-open-call", "pm-contribution-sprint"])
        metrics = result["metrics"]
        self.assertEqual(metrics["mode_novelty_proxy"]["delta"], 0.5)
        self.assertEqual(metrics["relevance_proxy"]["delta"], 0.0)
        self.assertEqual(metrics["readiness_to_act_proxy"]["delta"], 0.0)
        self.assertFalse(result["failure_condition_met"])

    def test_intervention_preserves_current_primary_source_route_provenance(self) -> None:
        result = evaluate_participation_mode(self.fixture)
        provenance = result["non_obvious_participation_mode_treatment"]["selected_route_provenance"]
        sprint = next(row for row in provenance if row["candidate_id"] == "pm-contribution-sprint")
        evidence = sprint["evidence"][0]
        self.assertEqual(evidence["source_type"], "direct_official_primary")
        self.assertIn("participation_route", evidence["supports"])
        self.assertIn("participation_mode:contribution-sprint", evidence["supports"])
        self.assertTrue(result["non_obvious_participation_mode_treatment"]["hard_gates"]["grounding"])
        self.assertTrue(all(result["non_obvious_participation_mode_treatment"]["hard_gates"].values()))

    def test_non_obvious_mode_fails_closed_without_primary_route_and_mode_evidence(self) -> None:
        invalid = copy.deepcopy(self.fixture)
        sprint = next(candidate for candidate in invalid["candidates"] if candidate["id"] == "pm-contribution-sprint")
        sprint["evidence"][0]["supports"].remove("participation_mode:contribution-sprint")
        errors = validate_participation_mode(invalid)
        self.assertTrue(any("non-obvious mode" in error for error in errors), errors)
        self.assertTrue(any("grounding-pass candidate" in error for error in errors), errors)

    def test_controls_and_liveness_cannot_be_relaxed_for_the_treatment(self) -> None:
        invalid = copy.deepcopy(self.fixture)
        invalid["controls"]["intervention"]["source_research_budget"]["max_primary_source_records"] = 5
        errors = validate_participation_mode(invalid)
        self.assertTrue(any("identical source_research_budget" in error for error in errors), errors)

        invalid = copy.deepcopy(self.fixture)
        invalid["candidates"][0]["relevance_proxy"] = 91
        errors = validate_participation_mode(invalid)
        self.assertTrue(any("frozen_input_sha256" in error for error in errors), errors)

        result = evaluate_participation_mode(self.fixture)
        self.assertNotIn("pm-stale-route", result["baseline"]["selected_ids"])
        self.assertNotIn("pm-stale-route", result["non_obvious_participation_mode_treatment"]["selected_ids"])


if __name__ == "__main__":
    unittest.main()
