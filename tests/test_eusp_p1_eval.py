"""Focused standard-library regression tests for the EUSP priority-1 harness."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from compare_variants import (evaluate_eusp_p1_packet, eusp_p1_outcome, eusp_p1_promotion,
                              load_candidate, parser, require_eusp_p1_snapshots, run,
                              validate_eusp_p1_manifests)
from run_experiment import (STAGED, VARIANTS, build_eusp_p1_judge_packet, direction_bool,
                            direction_effort_cap, direction_snapshot_metadata, snapshot_inputs,
                            stage_result_error, variant_instructions)


DIRECTION = (ROOT / "evals/direction_eusp_p1.yaml").read_text(encoding="utf-8")
EXPERIMENT_RECORD = (ROOT / "experiments/analyses/eusp_p1_synthetic_neutral_record.md").read_text(encoding="utf-8")
PROFILE = "# Fixture profile\n\nExplicit engineering and research interests only.\n"


def report() -> dict:
    material_claims = [
        {"id": "claim-status", "kind": "status"},
        {"id": "claim-timing", "kind": "timing"},
        {"id": "claim-route", "kind": "participation_route"},
    ]
    evidence = [
        {"claim_id": "claim-status", "claim": "The call is open.", "quote": "The call is open." , "supports": ["status"],
         "temporal": {"kind": None, "date": None, "start_date": None, "end_date": None}},
        {"claim_id": "claim-timing", "claim": "The deadline is August 31.", "quote": "Submit by 31 August 2026.", "supports": ["deadline"],
         "temporal": {"kind": "deadline", "date": "2026-08-31", "start_date": None, "end_date": None}},
        {"claim_id": "claim-route", "claim": "Submit using the official form.", "quote": "Submit using the official application form.", "supports": ["participation_route"],
         "temporal": {"kind": None, "date": None, "start_date": None, "end_date": None}},
    ]
    for row in evidence:
        row.update({"ledger_id": f"verification-row-{row['claim_id']}", "candidate_id": "internal-stage-id",
                    "source_type": "official_primary", "entailment": "direct", "url": "https://example.test/call",
                    "retrieved_at": "2026-08-30T10:00:00+00:00", "current_status": "open"})
    return {
        "snapshot_date": "2026-08-30", "pipeline_metadata": "must never enter the packet",
        "candidates": [{
            "candidate_id": "internal-stage-id", "title": "Open call", "organization": "Example Org", "type": "grant",
            "status": "ACT_NOW", "claim_ids": [claim["id"] for claim in material_claims], "material_claims": material_claims,
            "profile_bridge": [{"profile_signal": "explicit interest", "why_it_matters": "direct bridge"}],
            "first_action": {"action": "Draft a one-page outline", "deliverable": "outline", "start_by_or_trigger": "Start now", "start_date": "2026-08-31", "minutes_min": 30, "minutes_max": 45},
            "scheduled_week_effort_minutes": {"min": 30, "max": 45}, "blockers": ["final fit unknown"], "uncertainties": []
        }],
        "selected_ids": {"act_now": ["internal-stage-id"], "prepare_next": [], "monitor": []},
        "weekly_allocation": {"cap_minutes": 360, "scheduled_min_minutes": 30, "scheduled_max_minutes": 45, "residual_upper_minutes": 315},
        "evidence_ledger": evidence,
    }


class EuspP1HarnessTests(unittest.TestCase):
    def test_p1_arm_definitions(self) -> None:
        self.assertEqual(VARIANTS["P1_FRONTIER"]["prompt"], "prompts/find_opportunities_general_recommended.md")
        self.assertNotIn("addenda", VARIANTS["P1_FRONTIER"])
        self.assertEqual(VARIANTS["P1_V0"]["stages"], ("report",))
        self.assertEqual(VARIANTS["P1_V0"]["mode"], "monolithic")

    def test_p1_shared_report_contract_is_snapshotted_and_report_only(self) -> None:
        contract = (ROOT / "prompts/variants/P1_REPORT_SERIALIZATION_ADDENDUM.md").read_text(encoding="utf-8")
        for variant in ("P1_V0", "P1_FRONTIER"):
            with self.subTest(variant=variant):
                self.assertIn(contract, variant_instructions(variant, "report"))
                with tempfile.TemporaryDirectory() as directory:
                    source = Path(directory)
                    profile, direction, rubric = source / "profile.md", source / "direction.yaml", source / "rubric.yaml"
                    profile.write_text(PROFILE, encoding="utf-8")
                    direction.write_text(DIRECTION, encoding="utf-8")
                    rubric.write_text("rubric", encoding="utf-8")
                    run = source / "run"
                    hashes = snapshot_inputs(run, variant, profile, direction, rubric)
                    prompt = run / "inputs/prompt.md"
                    self.assertIn(contract, prompt.read_text(encoding="utf-8"))
                    self.assertEqual(hashes["prompt.md"], hashlib.sha256(prompt.read_bytes()).hexdigest())
        for stage in set(STAGED) - {"report"}:
            self.assertNotIn(contract, variant_instructions("P1_FRONTIER", stage))

    def test_both_p1_arms_project_the_common_structured_report_contract(self) -> None:
        for variant in ("P1_V0", "P1_FRONTIER"):
            with self.subTest(variant=variant):
                self.assertIsNone(stage_result_error("report", report(), p1_packet=True))
                packet, diagnostics = build_eusp_p1_judge_packet(PROFILE, DIRECTION, report())
                self.assertTrue(diagnostics["valid"], diagnostics["errors"])
                selected = packet["portfolio"]["selected"][0]
                self.assertEqual(selected["first_action"]["start_date"], "2026-08-31")
                self.assertEqual(packet["portfolio"]["weekly_allocation"]["scheduled_max_minutes"], 45)
                evidence = packet["evidence"][0]
                self.assertEqual(evidence["source_type"], "official_primary")
                self.assertEqual(evidence["entailment"], "direct")
                self.assertEqual(evidence["current_status"], "open")
                self.assertEqual(evidence["temporal"], {"kind": None, "date": None, "start_date": None, "end_date": None})
                self.assertEqual(evidence["supports"], ["status"])
                self.assertEqual({claim["kind"] for claim in selected["material_claims"]},
                                 {"status", "timing", "participation_route"})
                self.assertTrue(all(claim["evidence_ids"] for claim in selected["material_claims"]))

    def test_fixture_metadata_and_job_opt_in(self) -> None:
        self.assertEqual(direction_snapshot_metadata(DIRECTION), ("2026-08-30", "Etc/UTC"))
        self.assertEqual(direction_effort_cap(DIRECTION), 360)
        self.assertFalse(direction_bool(DIRECTION, "explicitly_requested"))

    def test_packet_is_final_report_projection_with_stable_shape(self) -> None:
        staged = report()
        monolithic = copy.deepcopy(staged)
        monolithic["pipeline_metadata"] = "a different hidden pipeline must not leak"
        first, first_diagnostics = build_eusp_p1_judge_packet(PROFILE, DIRECTION, staged)
        second, second_diagnostics = build_eusp_p1_judge_packet(PROFILE, DIRECTION, monolithic)
        self.assertEqual(first.keys(), second.keys())
        self.assertTrue(first_diagnostics["valid"], first_diagnostics["errors"])
        self.assertTrue(second_diagnostics["valid"], second_diagnostics["errors"])
        self.assertEqual(first["portfolio"]["selected"][0]["id"], "c1")
        self.assertEqual(first["evidence"][0]["id"], "e1")
        forbidden = {"stage", "run", "variant", "model", "path", "pipeline_metadata", "artifact_hash"}

        def keys(value):
            if isinstance(value, dict):
                yield from value
                for child in value.values():
                    yield from keys(child)
            elif isinstance(value, list):
                for child in value:
                    yield from keys(child)

        self.assertFalse(forbidden & set(keys(first)))

    def test_missing_primary_quote_fails_grounding(self) -> None:
        packet, _ = build_eusp_p1_judge_packet(PROFILE, DIRECTION, report())
        packet["evidence"][0]["quote"] = None
        self.assertEqual(evaluate_eusp_p1_packet(packet)["grounding_gate"], "fail")

    def test_non_direct_material_evidence_fails_grounding(self) -> None:
        packet, _ = build_eusp_p1_judge_packet(PROFILE, DIRECTION, report())
        packet["evidence"][0]["entailment"] = None
        self.assertEqual(evaluate_eusp_p1_packet(packet)["grounding_gate"], "fail")

    def test_missing_current_temporal_support_fails_liveness(self) -> None:
        packet, _ = build_eusp_p1_judge_packet(PROFILE, DIRECTION, report())
        packet["evidence"][0]["supports"] = []
        self.assertEqual(evaluate_eusp_p1_packet(packet)["liveness_gate"], "fail")

    def test_valid_packet_has_readiness_score_and_gate_first_outcome(self) -> None:
        packet, _ = build_eusp_p1_judge_packet(PROFILE, DIRECTION, report())
        evaluation = evaluate_eusp_p1_packet(packet)
        self.assertEqual(evaluation["grounding_gate"], "pass")
        self.assertEqual(evaluation["liveness_gate"], "pass")
        self.assertEqual(evaluation["portfolio_readiness_to_act"], 100.0)
        judged = {"judge_role": "readiness", "winner": "A", "arms": {"A": evaluation, "B": evaluation}, "reasons": []}
        self.assertEqual(eusp_p1_outcome(judged, {"A": evaluation, "B": evaluation})[0], "tie")

    def test_fabricated_readiness_rows_or_score_is_rejected(self) -> None:
        packet, _ = build_eusp_p1_judge_packet(PROFILE, DIRECTION, report())
        evaluation = evaluate_eusp_p1_packet(packet)
        fabricated = {"judge_role": "readiness", "winner": "A", "arms": {
            "A": {**evaluation, "per_candidate_readiness": [], "portfolio_readiness_to_act": 100}, "B": evaluation}, "reasons": []}
        self.assertEqual(eusp_p1_outcome(fabricated, {"A": evaluation, "B": evaluation})[0], "invalid")
        mismatched = {"judge_role": "readiness", "winner": "A", "arms": {
            "A": {**evaluation, "portfolio_readiness_to_act": 99}, "B": evaluation}, "reasons": []}
        self.assertEqual(eusp_p1_outcome(mismatched, {"A": evaluation, "B": evaluation})[0], "invalid")

    def test_selected_bucket_status_conflict_is_hard_failure(self) -> None:
        invalid = report()
        invalid["candidates"][0]["status"] = "MONITOR"
        packet, _ = build_eusp_p1_judge_packet(PROFILE, DIRECTION, invalid)
        self.assertIn("selected classification", " ".join(evaluate_eusp_p1_packet(packet)["other_hard_gate_failures"]))

    def test_job_and_seven_day_policy_bypasses_fail(self) -> None:
        invalid = report()
        invalid["candidates"][0]["type"] = "generic_employment_moves"
        invalid["candidates"][0]["first_action"].update({"start_date": "2030-01-01", "minutes_max": 600})
        packet, _ = build_eusp_p1_judge_packet(PROFILE, DIRECTION, invalid)
        failures = " ".join(evaluate_eusp_p1_packet(packet)["other_hard_gate_failures"])
        self.assertIn("job-policy", failures)
        self.assertIn("seven-day", failures)

    def test_job_type_must_be_exact_while_non_job_types_remain_allowed(self) -> None:
        arbitrary_job = report()
        arbitrary_job["candidates"][0]["type"] = "unlisted_job_encoding"
        packet, _ = build_eusp_p1_judge_packet(PROFILE, DIRECTION, arbitrary_job)
        self.assertIn("job-policy", " ".join(evaluate_eusp_p1_packet(packet)["other_hard_gate_failures"]))
        for non_job_type in ("grant", "community", "other"):
            with self.subTest(non_job_type=non_job_type):
                non_job = report()
                non_job["candidates"][0]["type"] = non_job_type
                packet, _ = build_eusp_p1_judge_packet(PROFILE, DIRECTION, non_job)
                self.assertNotIn("job-policy", " ".join(evaluate_eusp_p1_packet(packet)["other_hard_gate_failures"]))

    def test_expired_structured_act_now_evidence_fails_liveness(self) -> None:
        invalid = report()
        invalid["evidence_ledger"][1]["temporal"]["date"] = "2026-08-01"
        packet, _ = build_eusp_p1_judge_packet(PROFILE, DIRECTION, invalid)
        self.assertEqual(evaluate_eusp_p1_packet(packet)["liveness_gate"], "fail")

    def test_stale_closed_or_expired_selected_items_fail_liveness_and_cannot_promote(self) -> None:
        for classification in ("ACT_NOW", "PREPARE_NEXT"):
            for mutation in ("stale", "closed", "expired"):
                with self.subTest(classification=classification, mutation=mutation):
                    invalid = report()
                    candidate = invalid["candidates"][0]
                    candidate["status"] = classification
                    selected_bucket = "act_now" if classification == "ACT_NOW" else "prepare_next"
                    invalid["selected_ids"] = {"act_now": [], "prepare_next": [], "monitor": []}
                    invalid["selected_ids"][selected_bucket] = [candidate["candidate_id"]]
                    if mutation in {"stale", "closed"}:
                        invalid["evidence_ledger"][0]["current_status"] = mutation
                    else:
                        invalid["evidence_ledger"][1]["temporal"]["date"] = "2026-08-01"
                    packet, _ = build_eusp_p1_judge_packet(PROFILE, DIRECTION, invalid)
                    preflight = evaluate_eusp_p1_packet(packet)
                    self.assertEqual(preflight["liveness_gate"], "fail")
                    judged = {"judge_role": "readiness", "winner": "A", "reasons": [], "arms": {
                        "A": {"grounding_gate": "pass", "liveness_gate": "pass", "other_hard_gate_failures": [],
                              "per_candidate_readiness": [{"candidate_id": "c1", "explicit_profile_bridge": True,
                                                           "atomic_user_controlled_action": True, "tangible_deliverable": True,
                                                           "startable_within_7_days": True, "bounded_effort_and_disclosed_blockers": True}],
                              "portfolio_readiness_to_act": 100},
                        "B": {"grounding_gate": "pass", "liveness_gate": "pass", "other_hard_gate_failures": [],
                              "per_candidate_readiness": [{"candidate_id": "c1", "explicit_profile_bridge": True,
                                                           "atomic_user_controlled_action": True, "tangible_deliverable": True,
                                                           "startable_within_7_days": True, "bounded_effort_and_disclosed_blockers": True}],
                              "portfolio_readiness_to_act": 100},
                    }}
                    winner, decision = eusp_p1_outcome(judged, {"A": preflight, "B": preflight})
                    self.assertEqual(winner, "tie")
                    calls = [{"p1_decision": decision} for _ in range(4)]
                    pairs = [{"stable_pairwise_winner": "left"}, {"stable_pairwise_winner": "left"}]
                    self.assertIsNone(eusp_p1_promotion(calls, pairs, repeats=2))

    def test_each_required_material_claim_mapping_fails_closed_when_missing(self) -> None:
        for kind in ("status", "timing", "participation_route"):
            with self.subTest(kind=kind):
                packet, _ = build_eusp_p1_judge_packet(PROFILE, DIRECTION, report())
                claim = next(claim for claim in packet["portfolio"]["selected"][0]["material_claims"]
                             if claim["kind"] == kind)
                claim["evidence_ids"] = []
                evaluation = evaluate_eusp_p1_packet(packet)
                self.assertEqual(evaluation["grounding_gate"], "fail")
                self.assertEqual(evaluation["liveness_gate"], "fail")

    def test_p1_direction_fixture_is_synthetic_and_neutral(self) -> None:
        self.assertIn("fixture_id: eusp_p1_synthetic_neutral", DIRECTION)
        self.assertIn("explicitly_requested: false", DIRECTION)
        for forbidden in ("mikhail", "hong_kong", "cape_town", "profile-derived"):
            self.assertNotIn(forbidden, DIRECTION.lower())

    def test_anonymized_experiment_record_has_required_fields_and_no_private_data(self) -> None:
        for field in ("Hypothesis", "Treatment", "Method", "Measurement", "Result", "Non-promotion", "Profile-scoped limitations"):
            self.assertIn(field, EXPERIMENT_RECORD)
        self.assertNotIn("/data/data", EXPERIMENT_RECORD)
        self.assertNotIn("Mikhail", EXPERIMENT_RECORD)

    def test_repeat_defaults_preserve_standard_and_scope_p1_pairs(self) -> None:
        self.assertEqual(parser().parse_args(["--a", "unused-a", "--b", "unused-b"]).repeats, 1)
        self.assertEqual(parser().parse_args(["--a", "unused-a", "--b", "unused-b",
                                              "--protocol", "eusp-p1"]).repeats, 2)

    def test_single_paired_repeat_is_rejected(self) -> None:
        args = parser().parse_args(["--a", "unused-a", "--b", "unused-b", "--protocol", "eusp-p1",
                                    "--target", "judge_packet", "--roles", "readiness", "--repeats", "1"])
        with self.assertRaises(SystemExit):
            run(args)

    def test_p1_manifest_hashes_the_versioned_packet_presented_to_judges(self) -> None:
        def make_run(root: Path, variant: str) -> Path:
            run_dir = root / variant
            (run_dir / "inputs").mkdir(parents=True)
            for name, content in (("profile.md", PROFILE), ("direction.yaml", DIRECTION), ("rubric.yaml", "rubric")):
                (run_dir / "inputs" / name).write_text(content, encoding="utf-8")
            stages = (["report"] if variant == "P1_V0" else
                      ["profile", "triggers", "search_plan", "discovery", "verification", "actionability", "ranking", "report"])
            (run_dir / "manifest.json").write_text(json.dumps({"variant": variant,
                "pipeline_mode": "monolithic" if variant == "P1_V0" else "staged", "stages": stages}), encoding="utf-8")
            (run_dir / "report.result.json").write_text("{}", encoding="utf-8")
            (run_dir / "report.status.json").write_text('{"state":"complete"}', encoding="utf-8")
            (run_dir / "summary.json").write_text('{"state":"complete"}', encoding="utf-8")
            report_hash = hashlib.sha256(b"{}").hexdigest()
            for suffix, content in (("", '{"packet":"old"}'), (".attempt-02", '{"packet":"latest"}')):
                packet = run_dir / f"judge_packet{suffix}.json"
                packet.write_text(content, encoding="utf-8")
                diagnostics = {"valid": True, "report_sha256": report_hash,
                               "packet_sha256": hashlib.sha256(packet.read_bytes()).hexdigest()}
                (run_dir / f"judge_packet_validation{suffix}.json").write_text(
                    json.dumps(diagnostics), encoding="utf-8")
            return run_dir

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            left, right = make_run(root, "P1_V0"), make_run(root, "P1_FRONTIER")
            output = root / "comparisons"
            args = parser().parse_args(["--a", str(left), "--b", str(right), "--protocol", "eusp-p1",
                                        "--target", "judge_packet", "--roles", "readiness", "--dry-run",
                                        "--output-dir", str(output)])
            # Dry-run judge results are intentionally invalid; the manifest is written before calls.
            with patch("compare_variants.append_jsonl"), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(run(args), 2)
            manifest = json.loads(next(output.iterdir()).joinpath("manifest.json").read_text(encoding="utf-8"))
            for identity, run_dir in (("left", left), ("right", right)):
                latest = run_dir / "judge_packet.attempt-02.json"
                self.assertEqual(manifest["input_hashes"][identity], hashlib.sha256(latest.read_bytes()).hexdigest())

    def test_wrong_arm_manifest_is_rejected(self) -> None:
        frontier = {"variant": "P1_FRONTIER", "pipeline_mode": "staged", "stages": ["profile", "triggers", "search_plan", "discovery", "verification", "actionability", "ranking", "report"]}
        baseline = {"variant": "P1_V0", "pipeline_mode": "monolithic", "stages": ["report"]}
        validate_eusp_p1_manifests(frontier, baseline)
        with self.assertRaises(ValueError):
            validate_eusp_p1_manifests(frontier, {**baseline, "variant": "V0"})
        with self.assertRaises(ValueError):
            validate_eusp_p1_manifests(frontier, {**baseline, "pipeline_mode": "staged"})

    def test_unbound_or_partial_packet_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            (run / "inputs").mkdir()
            (run / "inputs/rubric.yaml").write_text("rubric", encoding="utf-8")
            (run / "manifest.json").write_text('{"variant":"P1_V0"}', encoding="utf-8")
            (run / "report.result.json").write_text('{}', encoding="utf-8")
            (run / "report.status.json").write_text('{"state":"complete"}', encoding="utf-8")
            (run / "judge_packet.json").write_text('{}', encoding="utf-8")
            report_hash = hashlib.sha256(b"{}").hexdigest()
            packet_hash = hashlib.sha256(b"{}").hexdigest()
            (run / "judge_packet_validation.json").write_text(
                f'{{"valid":true,"report_sha256":"{report_hash}","packet_sha256":"{packet_hash}"}}', encoding="utf-8")
            (run / "summary.json").write_text('{"state":"partial"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_candidate(run, "judge_packet", "eusp-p1")
            (run / "summary.json").write_text('{"state":"complete"}', encoding="utf-8")
            (run / "judge_packet_validation.json").write_text('{"valid":true,"report_sha256":"wrong","packet_sha256":"wrong"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_candidate(run, "judge_packet", "eusp-p1")

    def test_comparison_rejects_any_snapshot_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            left, right = Path(directory) / "left", Path(directory) / "right"
            for run in (left, right):
                (run / "inputs").mkdir(parents=True)
                (run / "inputs/profile.md").write_text("same", encoding="utf-8")
                (run / "inputs/direction.yaml").write_text("same", encoding="utf-8")
                (run / "inputs/rubric.yaml").write_text("same", encoding="utf-8")
            require_eusp_p1_snapshots(left, right)
            for relative in ("profile.md", "direction.yaml", "rubric.yaml"):
                target = right / "inputs" / relative
                original = target.read_text(encoding="utf-8")
                target.write_text("different", encoding="utf-8")
                with self.assertRaises(ValueError):
                    require_eusp_p1_snapshots(left, right)
                target.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
