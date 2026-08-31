"""Regression tests for the EUSP one-opportunity, multi-value-hypothesis contract."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from eusp_opportunity import SCHEMA_VERSION, validate_opportunity

FIXTURE = ROOT / "evals/fixtures/eusp_opportunity/v1/opportunity.json"


class EuspOpportunityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.opportunity = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_anonymized_fixture_is_valid_and_has_multiple_independently_grounded_hypotheses(self) -> None:
        self.assertEqual(validate_opportunity(self.opportunity, public_fixture=True), [])
        self.assertEqual(self.opportunity["schema_version"], SCHEMA_VERSION)
        hypotheses = self.opportunity["value_hypotheses"]
        self.assertEqual(len(hypotheses), 2)
        self.assertNotEqual(set(hypotheses[0]["evidence_ids"]), set(hypotheses[1]["evidence_ids"]))
        for hypothesis in hypotheses:
            self.assertTrue(hypothesis["causal_bridge"])
            self.assertTrue(hypothesis["profile_basis"])
            self.assertTrue(hypothesis["evidence_ids"])
            self.assertTrue(hypothesis["uncertainty_ids"])
            self.assertIn(hypothesis["confidence"], {"low", "medium", "high"})

    def test_hypotheses_cannot_reuse_grounding_or_omit_its_explicit_support(self) -> None:
        reused = copy.deepcopy(self.opportunity)
        reused["value_hypotheses"][1]["evidence_ids"] = ["e-vh-funded-exposure"]
        errors = validate_opportunity(reused)
        self.assertTrue(any("independent grounding" in error for error in errors), errors)
        unsupported = copy.deepcopy(self.opportunity)
        unsupported["evidence"][2]["supports"] = []
        errors = validate_opportunity(unsupported)
        self.assertTrue(any("does not directly support value hypothesis" in error for error in errors), errors)

    def test_profile_basis_and_uncertainty_are_explicit_references_not_inferred_defaults(self) -> None:
        invalid = copy.deepcopy(self.opportunity)
        invalid["value_hypotheses"][0]["profile_basis"] = [{"field_id": "inferred-career-level", "provenance": "inferred"}]
        invalid["value_hypotheses"][0]["uncertainty_ids"] = ["u-not-recorded"]
        errors = validate_opportunity(invalid)
        self.assertTrue(any("invalid explicit profile field" in error for error in errors), errors)
        self.assertTrue(any("unknown uncertainty" in error for error in errors), errors)

    def test_path_is_one_owned_property_with_verified_actions_separate_from_gaps(self) -> None:
        invalid = copy.deepcopy(self.opportunity)
        invalid["paths"] = []
        invalid["path"]["gaps"][0]["evidence_ids"] = ["e-route"]
        errors = validate_opportunity(invalid)
        self.assertTrue(any("unexpected property paths" in error for error in errors), errors)
        self.assertTrue(any("gaps[0]: unexpected property evidence_ids" in error for error in errors), errors)

    def test_selected_record_fails_closed_without_direct_route_or_current_liveness(self) -> None:
        invalid = copy.deepcopy(self.opportunity)
        invalid["evidence"][1]["supports"] = []
        invalid["evidence"][0]["current_status"] = "closed"
        errors = validate_opportunity(invalid)
        self.assertTrue(any("participation route" in error for error in errors), errors)
        self.assertTrue(any("liveness gate" in error for error in errors), errors)

    def test_user_eligibility_conclusion_is_not_representable(self) -> None:
        invalid = copy.deepcopy(self.opportunity)
        invalid["user_eligibility"] = "eligible"
        errors = validate_opportunity(invalid)
        self.assertTrue(any("unexpected property user_eligibility" in error for error in errors), errors)
        self.assertEqual(self.opportunity["eligibility_assessment"], "not_assessed")

    def test_verified_action_is_bounded_and_startable_in_seven_days(self) -> None:
        invalid = copy.deepcopy(self.opportunity)
        invalid["path"]["verified_actions"][0]["start_date"] = "2026-09-10"
        invalid["path"]["verified_actions"][0]["minutes_max"] = 61
        errors = validate_opportunity(invalid)
        self.assertTrue(any("seven days" in error for error in errors), errors)
        self.assertTrue(any("above maximum" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
