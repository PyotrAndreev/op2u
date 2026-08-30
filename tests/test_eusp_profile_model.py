"""Regression tests for the local EUSP user-profile Markdown contract."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from eusp_profile import SCHEMA_VERSION, validate_profile_markdown
from run_experiment import build_eusp_p1_judge_packet
from compare_variants import evaluate_eusp_p1_packet

FIXTURE = ROOT / "evals/fixtures/eusp_p1_profile_model/v1/pipeline_input/profile.md"
HIDDEN_TRAITS_FIXTURE = ROOT / "evals/fixtures/eusp_p1_hidden_traits/v1"


class EuspProfileModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = FIXTURE.read_text(encoding="utf-8")

    def test_anonymized_fixture_is_a_valid_public_profile(self) -> None:
        self.assertEqual(validate_profile_markdown(self.profile, public_fixture=True), [])
        self.assertIn(SCHEMA_VERSION, self.profile)
        self.assertIn("fabricated, anonymized public evaluation fixture", self.profile)

    def test_each_recorded_field_requires_user_supplied_provenance(self) -> None:
        inferred = self.profile.replace("[user_supplied] `asset-1`", "[inferred] `asset-1`", 1)
        errors = validate_profile_markdown(inferred, public_fixture=True)
        self.assertTrue(any("provenance must be user_supplied" in error for error in errors), errors)

    def test_silence_is_permitted_and_does_not_create_a_default_fact(self) -> None:
        omitted = self.profile.replace("- [user_supplied] `preference-1`: peer-facing participation with a short feedback cycle\n", "")
        self.assertEqual(validate_profile_markdown(omitted, public_fixture=True), [])

    def test_geography_requires_user_supplied_matched_place_and_period(self) -> None:
        missing_period = self.profile.replace("- [user_supplied] `geo-1.period`: 2026-09-01/2026-09-14\n", "")
        errors = validate_profile_markdown(missing_period, public_fixture=True)
        self.assertTrue(any("must include both place and period" in error for error in errors), errors)
        reversed_period = self.profile.replace("2026-09-01/2026-09-14", "2026-09-14/2026-09-01")
        errors = validate_profile_markdown(reversed_period, public_fixture=True)
        self.assertTrue(any("starts after it ends" in error for error in errors), errors)

    def test_profile_uses_the_existing_p1_pipeline_input_surface_without_changing_preflight(self) -> None:
        direction = (HIDDEN_TRAITS_FIXTURE / "pipeline_input/direction.yaml").read_text(encoding="utf-8")
        report = json.loads((HIDDEN_TRAITS_FIXTURE / "pipeline_outputs/P1_FRONTIER.report.json").read_text(encoding="utf-8"))
        packet, diagnostics = build_eusp_p1_judge_packet(self.profile, direction, copy.deepcopy(report))
        self.assertTrue(diagnostics["valid"], diagnostics["errors"])
        self.assertEqual(packet["evaluation_context"]["profile_markdown"], self.profile)
        self.assertEqual(evaluate_eusp_p1_packet(packet)["grounding_gate"], "pass")
        self.assertEqual(evaluate_eusp_p1_packet(packet)["liveness_gate"], "pass")

    def test_actual_profile_path_remains_ignored_while_template_is_tracked(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("usr/*", gitignore)
        self.assertIn("!usr/profile.template.md", gitignore)
        self.assertTrue((ROOT / "usr/profile.template.md").is_file())


if __name__ == "__main__":
    unittest.main()
