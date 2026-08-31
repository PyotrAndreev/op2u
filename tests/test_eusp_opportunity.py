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
        next(row for row in unsupported["evidence"]
             if row["id"] == "e-vh-funded-exposure")["supports"] = []
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

    def test_funding_packet_separates_official_facts_from_indirect_indicators(self) -> None:
        packet = self.opportunity["path"]["funding_packet"]
        self.assertEqual({fact["kind"] for fact in packet["official_facts"]},
                         {"programme", "deadline", "requirements", "documents"})
        self.assertEqual({indicator["kind"] for indicator in packet["indirect_indicators"]},
                         {"pool_size", "prior_recipients"})
        self.assertEqual({gap["subject"] for gap in packet["gaps"]}, {"acceptance_rate"})
        for fact in packet["official_facts"]:
            self.assertTrue(fact["evidence_ids"])
        for indicator in packet["indirect_indicators"]:
            self.assertTrue(indicator["quote"])
            self.assertTrue(indicator["uncertainty"])
            self.assertTrue(indicator["source"]["retrieved_at"])
            self.assertTrue(indicator["source"]["verification_artifact_sha256"])
        for gap in packet["gaps"]:
            self.assertTrue(gap["searched_sources"])
            self.assertTrue(gap["searched_sources"][0]["retrieved_at"])

    def test_funding_packet_fails_closed_for_unsupported_facts_and_uncited_missing_subjects(self) -> None:
        invalid = copy.deepcopy(self.opportunity)
        invalid["path"]["funding_packet"]["official_facts"][0]["evidence_ids"] = ["e-route"]
        invalid["path"]["funding_packet"]["gaps"] = []
        errors = validate_opportunity(invalid)
        self.assertTrue(any("does not directly support funding official fact" in error for error in errors), errors)
        self.assertTrue(any("acceptance_rate" in error and "cited gap" in error for error in errors), errors)

    def test_funding_packet_cannot_mix_indicator_evidence_or_predict_user_outcomes(self) -> None:
        invalid = copy.deepcopy(self.opportunity)
        indicator = invalid["path"]["funding_packet"]["indirect_indicators"][0]
        indicator["evidence_ids"] = ["e-status"]
        indicator["uncertainty"] = "The user's chances are likely high."
        errors = validate_opportunity(invalid)
        self.assertTrue(any("unexpected property evidence_ids" in error for error in errors), errors)
        self.assertTrue(any("user eligibility or chances conclusion" in error for error in errors), errors)

    def test_path_components_cover_the_fixed_research_surface_with_cited_gaps(self) -> None:
        components = self.opportunity["path"]["components"]
        self.assertEqual({component["component"] for component in components},
                         {"travel", "lodging", "visa", "funding", "outreach_route"})
        self.assertEqual(self.opportunity["path"]["route_status"], "high_value_with_gaps")
        for component in components:
            self.assertTrue(component["source_links"])
            self.assertTrue(component["retrieved_at"])
            self.assertTrue(component["assumptions"])
        for component in (component for component in components if component["status"] == "gap"):
            self.assertTrue(component["gap_reason"])
            self.assertTrue(component["searched_sources"])
            self.assertEqual(component["evidence_ids"], [])

    def test_component_gap_cannot_be_an_uncited_fact_or_hidden_by_a_verified_route(self) -> None:
        invalid = copy.deepcopy(self.opportunity)
        lodging = invalid["path"]["components"][1]
        lodging["searched_sources"] = []
        lodging["evidence_ids"] = ["e-vh-funded-exposure"]
        errors = validate_opportunity(invalid)
        self.assertTrue(any("cited searched sources" in error for error in errors), errors)
        self.assertTrue(any("must not present unavailable information as evidence" in error for error in errors), errors)

        hidden_gaps = copy.deepcopy(self.opportunity)
        hidden_gaps["path"]["route_status"] = "verified_actions"
        errors = validate_opportunity(hidden_gaps)
        self.assertTrue(any("cannot hide component gaps" in error for error in errors), errors)

    def test_path_cost_keeps_money_time_and_high_stress_separate_without_a_composite(self) -> None:
        cost = self.opportunity["path"]["path_cost"]
        self.assertEqual(set(cost), {"date_basis", "programme_duration_days", "money", "time", "stress"})
        self.assertEqual(cost["stress"]["estimates"][0]["range"],
                         {"minimum": 4, "maximum": 5, "scale": "stress_1_to_5"})
        self.assertEqual(self.opportunity["path"]["route_status"], "high_value_with_gaps")
        self.assertEqual(validate_opportunity(self.opportunity), [])

        invalid = copy.deepcopy(self.opportunity)
        invalid["path"]["path_cost"]["overall_score"] = 1
        errors = validate_opportunity(invalid)
        self.assertTrue(any("unexpected property overall_score" in error for error in errors), errors)

    def test_path_cost_requires_sourced_ranges_and_preserves_unknowns_as_gaps(self) -> None:
        invalid = copy.deepcopy(self.opportunity)
        living = invalid["path"]["path_cost"]["money"]["estimates"][0]
        del living["currency"]
        living["range"] = {"minimum": 1200, "maximum": 900}
        del living["source_provenance"]["quote"]
        invalid["path"]["path_cost"]["time"] = {"status": "unknown", "estimates": [], "gaps": []}
        errors = validate_opportunity(invalid)
        self.assertTrue(any("missing required property currency" in error for error in errors), errors)
        self.assertTrue(any("minimum exceeds maximum" in error for error in errors), errors)
        self.assertTrue(any("missing required property quote" in error for error in errors), errors)
        self.assertTrue(any("time marked unknown" in error for error in errors), errors)

    def test_path_cost_uses_opportunity_date_or_explicit_user_availability_for_undated_records(self) -> None:
        invalid = copy.deepcopy(self.opportunity)
        date_basis = invalid["path"]["path_cost"]["date_basis"]
        date_basis["selected_date"] = "2026-10-02"
        date_basis["profile_field_id"] = "geo-1.period"
        date_basis["profile_provenance"] = "user_supplied"
        errors = validate_opportunity(invalid)
        self.assertTrue(any("must use its opportunity date" in error for error in errors), errors)
        self.assertTrue(any("must not substitute a profile date" in error for error in errors), errors)

        undated = copy.deepcopy(self.opportunity)
        date_basis = undated["path"]["path_cost"]["date_basis"]
        date_basis.update({
            "kind": "nearest_user_available_date",
            "selected_date": "2026-10-04",
            "opportunity_date": None,
            "evidence_id": None,
            "profile_field_id": "geo-1.period",
            "profile_provenance": "user_supplied",
        })
        self.assertEqual(validate_opportunity(undated), [])

    def test_long_programme_prioritizes_cost_of_living_before_flights(self) -> None:
        invalid = copy.deepcopy(self.opportunity)
        money = invalid["path"]["path_cost"]["money"]
        money["estimates"][0]["research_priority"] = "secondary"
        money["estimates"][1]["research_priority"] = "primary"
        errors = validate_opportunity(invalid)
        self.assertTrue(any("cost_of_living must be primary" in error for error in errors), errors)
        self.assertTrue(any("flights must be secondary" in error for error in errors), errors)

        invalid = copy.deepcopy(self.opportunity)
        money = invalid["path"]["path_cost"]["money"]
        money["estimates"] = [money["estimates"][1]]
        errors = validate_opportunity(invalid)
        self.assertTrue(any("cost_of_living estimate or explicit gap" in error for error in errors), errors)

    def test_exploration_lead_cannot_receive_verified_action_credit(self) -> None:
        invalid = copy.deepcopy(self.opportunity)
        invalid["path"]["route_status"] = "exploration_lead"
        errors = validate_opportunity(invalid)
        self.assertTrue(any("cannot contain verified actions" in error for error in errors), errors)
        self.assertTrue(any("not a selected opportunity" in error for error in errors), errors)

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
