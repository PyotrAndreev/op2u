"""Regression tests for the frozen EUSP local-unexpectedness experiment."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from eusp_local_unexpectedness import (SCHEMA_VERSION, _unexpected_locally,
                                       evaluate_local_unexpectedness,
                                       validate_local_unexpectedness)

FIXTURE = ROOT / "evals/fixtures/eusp_local_unexpectedness/v1/fixture.json"


class EuspLocalUnexpectednessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_public_fixture_is_valid_and_reproducible(self) -> None:
        self.assertEqual(validate_local_unexpectedness(self.fixture, public_fixture=True), [])
        self.assertEqual(self.fixture["schema_version"], SCHEMA_VERSION)
        self.assertEqual(evaluate_local_unexpectedness(self.fixture), evaluate_local_unexpectedness(self.fixture))

    def test_only_the_local_unexpectedness_signal_changes_the_frozen_control(self) -> None:
        result = evaluate_local_unexpectedness(self.fixture)
        self.assertEqual(result["baseline"]["selected"][0]["candidate_id"], "lu-known-local")
        self.assertEqual([row["candidate_id"] for row in result["treatment"]["selected"]],
                         ["lu-unknown-local-one", "lu-unknown-local-two"])
        self.assertEqual(result["shared_budgets"], self.fixture["frozen_inputs"])
        self.assertFalse(result["failure_condition_met"], result["failure_reasons"])
        self.assertEqual(result["treatment"]["metrics"]["local_unexpectedness_novelty_count"], 2)
        self.assertGreaterEqual(result["treatment"]["metrics"]["mean_relevance_proxy"],
                                result["baseline"]["metrics"]["mean_relevance_proxy"])

    def test_proxy_never_inferrs_place_or_date_and_never_conflates_unknown_with_known(self) -> None:
        candidates = {candidate["id"]: candidate for candidate in self.fixture["candidates"]}
        self.assertFalse(_unexpected_locally(candidates["lu-known-local"], self.fixture["supplied_windows"]))
        self.assertFalse(_unexpected_locally(candidates["lu-unknown-outside"], self.fixture["supplied_windows"]))
        near_match = copy.deepcopy(candidates["lu-unknown-local-one"])
        near_match["locality"]["place"] = "Cedar Bay District"
        self.assertFalse(_unexpected_locally(near_match, self.fixture["supplied_windows"]))
        out_of_window = copy.deepcopy(candidates["lu-unknown-local-one"])
        out_of_window["locality"]["start_date"] = "2026-11-01"
        out_of_window["locality"]["end_date"] = "2026-11-01"
        self.assertFalse(_unexpected_locally(out_of_window, self.fixture["supplied_windows"]))

    def test_provenance_and_frozen_candidate_inputs_fail_closed_when_changed(self) -> None:
        changed_provenance = copy.deepcopy(self.fixture)
        changed_provenance["candidates"][0]["evidence"][0]["quote"] = "A changed quote."
        errors = validate_local_unexpectedness(changed_provenance)
        self.assertTrue(any("provenance hash" in error for error in errors), errors)
        changed_input = copy.deepcopy(self.fixture)
        changed_input["candidates"][0]["relevance_proxy"] = 1
        errors = validate_local_unexpectedness(changed_input)
        self.assertTrue(any("candidate-set hash" in error for error in errors), errors)
        changed_window = copy.deepcopy(self.fixture)
        changed_window["supplied_windows"][0]["end_date"] = "2026-11-01"
        errors = validate_local_unexpectedness(changed_window)
        self.assertTrue(any("input-bundle hash" in error for error in errors), errors)

    def test_gate_and_act_now_safeguard_failures_are_rejected_before_selection(self) -> None:
        stale = copy.deepcopy(self.fixture)
        for evidence in stale["candidates"][0]["evidence"]:
            if "liveness" in evidence["supports"]:
                evidence["current_status"] = "closed"
        errors = validate_local_unexpectedness(stale)
        self.assertTrue(any("lacks current source-backed liveness" in error for error in errors), errors)
        delayed = copy.deepcopy(self.fixture)
        delayed["candidates"][0]["first_action"]["start_date"] = "2026-10-01"
        errors = validate_local_unexpectedness(delayed)
        self.assertTrue(any("within seven days" in error for error in errors), errors)

    def test_selected_outputs_keep_exact_evidence_and_local_action_safeguards(self) -> None:
        result = evaluate_local_unexpectedness(self.fixture)
        source_candidates = {candidate["id"]: candidate for candidate in self.fixture["candidates"]}
        for arm in ("baseline", "treatment"):
            self.assertEqual(result[arm]["metrics"]["grounding_rate"], 1.0)
            self.assertEqual(result[arm]["metrics"]["readiness_to_act_proxy"], 100.0)
            for selected in result[arm]["selected"]:
                source = source_candidates[selected["candidate_id"]]
                self.assertEqual(selected["evidence"], source["evidence"])
                self.assertEqual(selected["classification"], "ACT_NOW")
                self.assertLessEqual(selected["first_action"]["minutes_max"], 60)

    def test_different_arm_capacity_is_not_an_identical_budget_experiment(self) -> None:
        invalid = copy.deepcopy(self.fixture)
        invalid["treatment"]["selection_capacity"] = 3
        errors = validate_local_unexpectedness(invalid)
        self.assertTrue(any("identical frozen selection capacity" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
