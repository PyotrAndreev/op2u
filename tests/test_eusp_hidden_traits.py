"""Regression tests for the evaluator-only synthetic EUSP P1 hidden-traits fixture."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from compare_variants import evaluate_eusp_p1_packet
from eusp_hidden_traits import (RESULT_VERSION, build_hidden_traits_packet, hidden_traits_pair_prompt,
                                leakage_errors, load_fixture, validate_hidden_traits_result)

FIXTURE = ROOT / "evals/fixtures/eusp_p1_hidden_traits/v1"


class EuspHiddenTraitsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.packets, self.diagnostics = load_fixture(FIXTURE)

    def test_committed_fixture_is_valid_and_only_synthetic(self) -> None:
        self.assertTrue(self.diagnostics["valid"], self.diagnostics["errors"])
        profile = (FIXTURE / "pipeline_input/profile.md").read_text(encoding="utf-8").lower()
        self.assertIn("fabricated evaluation fixture", profile)
        self.assertNotIn("mikhail", profile)

    def test_hidden_traits_are_absent_from_pipeline_surfaces(self) -> None:
        traits = json.loads((FIXTURE / "evaluator_only/hidden_traits.json").read_text(encoding="utf-8"))
        values = []
        for path in sorted((FIXTURE / "pipeline_input").glob("*")) + sorted((FIXTURE / "pipeline_outputs").glob("*")):
            value = path.read_text(encoding="utf-8") if path.suffix != ".json" else json.loads(path.read_text(encoding="utf-8"))
            values.append((path.name, value))
        self.assertEqual(leakage_errors(values, traits), [])
        leaked = copy.deepcopy(values)
        leaked.append(("bad-report", {"hidden_traits": [traits["traits"][0]["id"]]}))
        leaked.append(("bad-direction", "evaluator_only: true"))
        errors = leakage_errors(leaked, traits)
        self.assertTrue(any("evaluator-only" in error for error in errors), errors)

    def test_evaluator_packet_keeps_canaries_out_but_preserves_public_p1_measurement(self) -> None:
        for packet in self.packets.values():
            self.assertTrue(packet["evaluator_only"])
            self.assertTrue(packet["measurement"]["trait_alignment_is_secondary"])
            serialized = json.dumps(packet, sort_keys=True)
            self.assertNotIn("EUSP-HT-V1-", serialized)
            preflight = evaluate_eusp_p1_packet(packet["pipeline_packet"])
            self.assertEqual(preflight["grounding_gate"], "pass")
            self.assertEqual(preflight["liveness_gate"], "pass")
        self.assertEqual(evaluate_eusp_p1_packet(self.packets["P1_V0"]["pipeline_packet"])["portfolio_readiness_to_act"], 80.0)
        self.assertEqual(evaluate_eusp_p1_packet(self.packets["P1_FRONTIER"]["pipeline_packet"])["portfolio_readiness_to_act"], 100.0)

    def test_packet_builder_fails_closed_on_a_trait_canary_in_a_report(self) -> None:
        traits = json.loads((FIXTURE / "evaluator_only/hidden_traits.json").read_text(encoding="utf-8"))
        profile = (FIXTURE / "pipeline_input/profile.md").read_text(encoding="utf-8")
        direction = (FIXTURE / "pipeline_input/direction.yaml").read_text(encoding="utf-8")
        report = json.loads((FIXTURE / "pipeline_outputs/P1_V0.report.json").read_text(encoding="utf-8"))
        report["pipeline_metadata"] = traits["traits"][0]["leakage_marker"]
        _, diagnostics = build_hidden_traits_packet(profile, direction, report, traits)
        self.assertFalse(diagnostics["valid"])
        self.assertTrue(any("evaluator-only token" in error for error in diagnostics["errors"]))

    def test_judge_prompt_and_result_bind_traits_without_replacing_readiness(self) -> None:
        prompt = hidden_traits_pair_prompt({"A": self.packets["P1_V0"], "B": self.packets["P1_FRONTIER"]}, "rubric")
        self.assertIn('"judge_role":"readiness_hidden_traits"', prompt)
        self.assertIn("Trait alignment is a secondary annotation", prompt)
        arms = {}
        for label, packet in (("A", self.packets["P1_V0"]), ("B", self.packets["P1_FRONTIER"])):
            preflight = evaluate_eusp_p1_packet(packet["pipeline_packet"])
            arms[label] = {key: copy.deepcopy(preflight[key]) for key in ("grounding_gate", "liveness_gate", "other_hard_gate_failures", "per_candidate_readiness", "portfolio_readiness_to_act")}
            arms[label]["hidden_trait_matches"] = [
                {"trait_id": trait["id"], "matched": False, "reason": "Synthetic regression annotation."}
                for trait in packet["hidden_traits"]
            ]
        result = {"schema_version": RESULT_VERSION, "judge_role": "readiness_hidden_traits", "arms": arms,
                  "winner": "B", "reasons": ["Synthetic fixture only."]}
        winner, decision = validate_hidden_traits_result(result, {"A": self.packets["P1_V0"], "B": self.packets["P1_FRONTIER"]})
        self.assertEqual(winner, "B")
        self.assertEqual(decision["readiness_scores"], {"A": 80.0, "B": 100.0})
        result["arms"]["A"]["hidden_trait_matches"] = []
        self.assertEqual(validate_hidden_traits_result(result, {"A": self.packets["P1_V0"], "B": self.packets["P1_FRONTIER"]})[0], "invalid")


if __name__ == "__main__":
    unittest.main()
