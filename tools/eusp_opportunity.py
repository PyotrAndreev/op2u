#!/usr/bin/env python3
"""Validate the EUSP v1 one-opportunity, multi-value-hypothesis contract.

This is a deterministic record check. It never discovers a source, fills a
profile gap, or determines user eligibility.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

from run_experiment import ROOT, _schema_errors, read_json

SCHEMA_VERSION = "eusp-opportunity/v1"
PUBLIC_FIXTURE_NOTICE = ("This is a fabricated, anonymized public evaluation fixture. "
                         "It is not a real opportunity, person, profile, or source snapshot.")
PROFILE_FIELD_ID = re.compile(
    r"(?:geo-[1-9][0-9]*\.(?:place|period)|career_ambition-[1-9][0-9]*|"
    r"thematic_interest-[1-9][0-9]*|(?:goal|outcome)-[1-9][0-9]*|"
    r"asset-[1-9][0-9]*|constraint-[1-9][0-9]*|preference-[1-9][0-9]*|"
    r"unknown-[1-9][0-9]*)$")
PATH_COMPONENTS = frozenset({"travel", "lodging", "visa", "funding", "outreach_route"})
FUNDING_OFFICIAL_FACTS = frozenset({"programme", "deadline", "requirements", "documents"})
COMPETITIVENESS_INDICATORS = frozenset({"pool_size", "acceptance_rate", "prior_recipients"})
FUNDING_PACKET_SUBJECTS = FUNDING_OFFICIAL_FACTS | COMPETITIVENESS_INDICATORS
USER_OUTCOME = re.compile(
    r"(?:\b(?:user|you|your)\b.{0,80}\b(?:eligible|ineligible|qualif(?:y|ies|ied)|"
    r"chance|odds|probability|likely|unlikely)\b|"
    r"\b(?:chance|odds|probability)\b.{0,80}\b(?:user|you|your)\b)", re.IGNORECASE)


def _additional_property_errors(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Fill the one JSON-Schema feature deliberately absent from the shared subset."""
    errors: list[str] = []
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}: unexpected property {key}")
        for key, child in value.items():
            if key in properties and isinstance(properties[key], dict):
                errors.extend(_additional_property_errors(child, properties[key], f"{path}.{key}"))
    elif isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, child in enumerate(value):
            errors.extend(_additional_property_errors(child, schema["items"], f"{path}[{index}]"))
    return errors


def _date(value: Any, label: str, errors: list[str]) -> dt.date | None:
    if not isinstance(value, str):
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label} must be an ISO date")
        return None


def _timestamp(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        return
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label} must be an ISO date-time")


def _funding_packet_text_is_user_outcome(value: Any) -> bool:
    """Reject conclusions or predictions about this user, not source requirements."""
    return isinstance(value, str) and USER_OUTCOME.search(value) is not None


def _ordered_range(record: Any, label: str, errors: list[str]) -> tuple[int | float, int | float] | None:
    """Check a disclosed range without deriving a single value from it."""
    if not isinstance(record, dict):
        return None
    minimum, maximum = record.get("minimum"), record.get("maximum")
    numeric = (int, float)
    if (not isinstance(minimum, numeric) or isinstance(minimum, bool)
            or not isinstance(maximum, numeric) or isinstance(maximum, bool)):
        return None
    if minimum > maximum:
        errors.append(f"{label} minimum exceeds maximum")
    return minimum, maximum


def _validate_cost_source(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        return
    _timestamp(value.get("retrieved_at"), f"{label}.retrieved_at", errors)
    source = value.get("source_provenance")
    if not isinstance(source, dict):
        return
    url = source.get("url")
    if not isinstance(url, str) or not url.startswith("https://"):
        errors.append(f"{label} needs an HTTPS source provenance URL")
    if not isinstance(source.get("quote"), str) or not source["quote"].strip():
        errors.append(f"{label} needs an exact source provenance quote")


def _validate_cost_dimension(dimension: Any, name: str, errors: list[str]) -> list[dict[str, Any]]:
    """Validate one independent path-cost ledger; never compare it to another."""
    if not isinstance(dimension, dict):
        return []
    estimates = dimension.get("estimates")
    gaps = dimension.get("gaps")
    estimate_rows = [row for row in estimates if isinstance(row, dict)] if isinstance(estimates, list) else []
    gap_rows = [row for row in gaps if isinstance(row, dict)] if isinstance(gaps, list) else []
    status = dimension.get("status")
    if status == "known" and (not estimate_rows or gap_rows):
        errors.append(f"path cost {name} marked known needs estimates and no gaps")
    elif status == "partial" and (not estimate_rows or not gap_rows):
        errors.append(f"path cost {name} marked partial needs estimates and explicit gaps")
    elif status == "unknown" and (estimate_rows or not gap_rows):
        errors.append(f"path cost {name} marked unknown needs no estimates and explicit gaps")

    categories: set[str] = set()
    for estimate in estimate_rows:
        category = estimate.get("category")
        if isinstance(category, str):
            if category in categories:
                errors.append(f"duplicate path cost {name} category {category!r}")
            categories.add(category)
        _ordered_range(estimate.get("range"), f"path cost {name} estimate {category!r} range", errors)
        _validate_cost_source(estimate, f"path cost {name} estimate {category!r}", errors)
    for index, gap in enumerate(gap_rows):
        searched = gap.get("searched_sources")
        if not isinstance(searched, list) or not searched:
            errors.append(f"path cost {name} gap {index} needs cited searched sources")
    return estimate_rows


def _unique(records: Any, label: str, errors: list[str]) -> set[str]:
    ids: set[str] = set()
    if not isinstance(records, list):
        return ids
    for index, record in enumerate(records):
        identifier = record.get("id") if isinstance(record, dict) else None
        if not isinstance(identifier, str):
            continue
        if identifier in ids:
            errors.append(f"duplicate {label} id {identifier!r}")
        ids.add(identifier)
    return ids


def _current_temporal(evidence: dict[str, Any], snapshot: dt.date) -> bool:
    if evidence.get("current_status") not in {"open", "upcoming", "rolling"}:
        return False
    temporal = evidence.get("temporal")
    if not isinstance(temporal, dict):
        return False
    kind = temporal.get("kind")
    try:
        if kind in {"deadline", "event"}:
            return dt.date.fromisoformat(temporal["date"]) >= snapshot
        if kind == "rolling":
            end = temporal.get("end_date")
            return end is None or dt.date.fromisoformat(end) >= snapshot
    except (KeyError, TypeError, ValueError):
        return False
    return False


def validate_opportunity(value: Any, *, public_fixture: bool = False) -> list[str]:
    """Return contract violations without making factual or eligibility claims."""
    schema = read_json(ROOT / "evals/schemas/eusp_opportunity.schema.json")
    errors = _schema_errors(value, schema) + _additional_property_errors(value, schema)
    if not isinstance(value, dict):
        return errors

    if public_fixture:
        if value.get("synthetic") is not True:
            errors.append("public fixture must set synthetic to true")
        if value.get("fixture_notice") != PUBLIC_FIXTURE_NOTICE:
            errors.append("public fixture lacks its explicit fabricated-data notice")

    snapshot = _date(value.get("snapshot_date"), "snapshot_date", errors)
    evidence = value.get("evidence")
    uncertainties = value.get("uncertainties")
    hypotheses = value.get("value_hypotheses")
    path = value.get("path")
    evidence_ids = _unique(evidence, "evidence", errors)
    uncertainty_ids = _unique(uncertainties, "uncertainty", errors)
    hypothesis_ids = _unique(hypotheses, "value hypothesis", errors)

    evidence_by_id = {row.get("id"): row for row in evidence if isinstance(row, dict) and isinstance(row.get("id"), str)} if isinstance(evidence, list) else {}
    used_hypothesis_evidence: set[str] = set()
    if isinstance(evidence, list):
        for index, row in enumerate(evidence):
            if not isinstance(row, dict):
                continue
            _timestamp(row.get("retrieved_at"), f"evidence[{index}].retrieved_at", errors)
            temporal = row.get("temporal")
            if isinstance(temporal, dict):
                for key in ("date", "start_date", "end_date"):
                    if temporal.get(key) is not None:
                        _date(temporal[key], f"evidence[{index}].temporal.{key}", errors)

    if isinstance(hypotheses, list):
        for index, hypothesis in enumerate(hypotheses):
            if not isinstance(hypothesis, dict):
                continue
            identifier = hypothesis.get("id")
            for profile_basis in hypothesis.get("profile_basis", []):
                profile_field = profile_basis.get("field_id") if isinstance(profile_basis, dict) else None
                if not isinstance(profile_field, str) or PROFILE_FIELD_ID.fullmatch(profile_field) is None:
                    errors.append(f"value hypothesis {identifier!r} has an invalid explicit profile field reference {profile_field!r}")
                if not isinstance(profile_basis, dict) or profile_basis.get("provenance") != "user_supplied":
                    errors.append(f"value hypothesis {identifier!r} profile basis must be user_supplied")
            for uncertainty_id in hypothesis.get("uncertainty_ids", []):
                if uncertainty_id not in uncertainty_ids:
                    errors.append(f"value hypothesis {identifier!r} references unknown uncertainty {uncertainty_id!r}")
            for evidence_id in hypothesis.get("evidence_ids", []):
                row = evidence_by_id.get(evidence_id)
                if row is None:
                    errors.append(f"value hypothesis {identifier!r} references unknown evidence {evidence_id!r}")
                    continue
                if evidence_id in used_hypothesis_evidence:
                    errors.append(f"value hypothesis {identifier!r} reuses evidence {evidence_id!r}; hypotheses need independent grounding")
                used_hypothesis_evidence.add(evidence_id)
                if f"value_hypothesis:{identifier}" not in row.get("supports", []):
                    errors.append(f"evidence {evidence_id!r} does not directly support value hypothesis {identifier!r}")

    if isinstance(path, dict):
        action_ids = _unique(path.get("verified_actions"), "verified action", errors)
        gap_ids = _unique(path.get("gaps"), "path gap", errors)
        overlap = action_ids & gap_ids
        if overlap:
            errors.append(f"verified action and path gap IDs must be distinct: {sorted(overlap)}")
        actions = path.get("verified_actions")
        if isinstance(actions, list):
            for index, action in enumerate(actions):
                if not isinstance(action, dict):
                    continue
                action_id = action.get("id")
                start_date = _date(action.get("start_date"), f"verified action {action_id!r} start_date", errors)
                minimum, maximum = action.get("minutes_min"), action.get("minutes_max")
                if isinstance(minimum, int) and isinstance(maximum, int) and minimum > maximum:
                    errors.append(f"verified action {action_id!r} minutes_min exceeds minutes_max")
                for evidence_id in action.get("evidence_ids", []):
                    row = evidence_by_id.get(evidence_id)
                    if row is None:
                        errors.append(f"verified action {action_id!r} references unknown evidence {evidence_id!r}")
                    elif "participation_route" not in row.get("supports", []):
                        errors.append(f"verified action {action_id!r} evidence {evidence_id!r} does not support a participation route")
                if (value.get("classification") in {"ACT_NOW", "PREPARE_NEXT"} and snapshot is not None and start_date is not None
                        and not snapshot <= start_date <= snapshot + dt.timedelta(days=7)):
                    errors.append(f"verified action {action_id!r} is not startable within seven days of the snapshot")

        funding_packet = path.get("funding_packet")
        if isinstance(funding_packet, dict):
            official_facts = funding_packet.get("official_facts")
            indicators = funding_packet.get("indirect_indicators")
            funding_gaps = funding_packet.get("gaps")
            _unique(official_facts, "funding official fact", errors)
            _unique(indicators, "competitiveness indicator", errors)
            _unique(funding_gaps, "funding gap", errors)
            recorded_subjects: set[str] = set()
            gap_subjects: set[str] = set()

            if isinstance(official_facts, list):
                for fact in official_facts:
                    if not isinstance(fact, dict):
                        continue
                    identifier = fact.get("id")
                    kind = fact.get("kind")
                    if isinstance(kind, str):
                        recorded_subjects.add(kind)
                    if _funding_packet_text_is_user_outcome(fact.get("claim")):
                        errors.append(f"funding official fact {identifier!r} makes a user eligibility or chances conclusion")
                    for evidence_id in fact.get("evidence_ids", []):
                        row = evidence_by_id.get(evidence_id)
                        if row is None:
                            errors.append(f"funding official fact {identifier!r} references unknown evidence {evidence_id!r}")
                        elif f"funding_packet:official_fact:{identifier}" not in row.get("supports", []):
                            errors.append(f"evidence {evidence_id!r} does not directly support funding official fact {identifier!r}")

            if isinstance(indicators, list):
                for indicator in indicators:
                    if not isinstance(indicator, dict):
                        continue
                    identifier = indicator.get("id")
                    kind = indicator.get("kind")
                    if isinstance(kind, str):
                        recorded_subjects.add(kind)
                    for field in ("claim", "uncertainty"):
                        if _funding_packet_text_is_user_outcome(indicator.get(field)):
                            errors.append(f"competitiveness indicator {identifier!r} makes a user eligibility or chances conclusion")
                    source = indicator.get("source")
                    if isinstance(source, dict):
                        _timestamp(source.get("retrieved_at"),
                                   f"competitiveness indicator {identifier!r} source.retrieved_at", errors)

            if isinstance(funding_gaps, list):
                for gap in funding_gaps:
                    if not isinstance(gap, dict):
                        continue
                    identifier = gap.get("id")
                    subject = gap.get("subject")
                    if isinstance(subject, str):
                        if subject in gap_subjects:
                            errors.append(f"duplicate funding gap subject {subject!r}")
                        gap_subjects.add(subject)
                    if _funding_packet_text_is_user_outcome(gap.get("question")):
                        errors.append(f"funding gap {identifier!r} makes a user eligibility or chances conclusion")
                    for source_index, source in enumerate(gap.get("searched_sources", [])):
                        if isinstance(source, dict):
                            _timestamp(source.get("retrieved_at"),
                                       f"funding gap {identifier!r} searched_sources[{source_index}].retrieved_at", errors)

            for subject in FUNDING_PACKET_SUBJECTS:
                if subject not in recorded_subjects and subject not in gap_subjects:
                    errors.append(f"funding packet lacks {subject!r}; record a grounded fact or a cited gap")
                if subject in recorded_subjects and subject in gap_subjects:
                    errors.append(f"funding packet {subject!r} is both recorded and a gap")

        components = path.get("components")
        component_names: set[str] = set()
        component_gaps = 0
        if isinstance(components, list):
            for index, component in enumerate(components):
                if not isinstance(component, dict):
                    continue
                name = component.get("component")
                if isinstance(name, str):
                    if name in component_names:
                        errors.append(f"duplicate path component {name!r}")
                    component_names.add(name)
                _timestamp(component.get("retrieved_at"), f"path component {name!r} retrieved_at", errors)
                status = component.get("status")
                applicability = component.get("applicability")
                if applicability == "applicable" and status not in {"verified", "gap"}:
                    errors.append(f"applicable path component {name!r} must be verified or a gap")
                elif applicability == "unknown" and status != "gap":
                    errors.append(f"unknown path component {name!r} must be a gap, not a fact")
                elif applicability == "not_applicable" and status != "not_applicable":
                    errors.append(f"not-applicable path component {name!r} must have not_applicable status")

                evidence_refs = component.get("evidence_ids")
                source_links = component.get("source_links")
                searched_sources = component.get("searched_sources")
                if status == "gap":
                    component_gaps += 1
                    if not isinstance(component.get("gap_reason"), str) or not component["gap_reason"].strip():
                        errors.append(f"path component {name!r} gap needs an explicit reason")
                    if not isinstance(searched_sources, list) or not searched_sources:
                        errors.append(f"path component {name!r} gap needs cited searched sources")
                    elif not isinstance(source_links, list) or not set(searched_sources).issubset(source_links):
                        errors.append(f"path component {name!r} searched sources must be source links")
                    if evidence_refs:
                        errors.append(f"path component {name!r} gap must not present unavailable information as evidence")
                else:
                    if component.get("gap_reason") is not None or searched_sources:
                        errors.append(f"path component {name!r} is not a gap but records a gap reason or searched sources")
                    if not isinstance(evidence_refs, list) or not evidence_refs:
                        errors.append(f"path component {name!r} needs direct evidence")
                    for evidence_id in evidence_refs if isinstance(evidence_refs, list) else []:
                        row = evidence_by_id.get(evidence_id)
                        if row is None:
                            errors.append(f"path component {name!r} references unknown evidence {evidence_id!r}")
                        elif f"path_component:{name}" not in row.get("supports", []):
                            errors.append(f"evidence {evidence_id!r} does not directly support path component {name!r}")
        if component_names != PATH_COMPONENTS:
            errors.append("path components must record travel, lodging, visa, funding, and outreach_route exactly once")

        path_cost = path.get("path_cost")
        if isinstance(path_cost, dict):
            date_basis = path_cost.get("date_basis")
            if isinstance(date_basis, dict):
                selected_date = _date(date_basis.get("selected_date"), "path cost selected_date", errors)
                opportunity_date = _date(date_basis.get("opportunity_date"), "path cost opportunity_date", errors)
                basis_kind = date_basis.get("kind")
                evidence_id = date_basis.get("evidence_id")
                profile_field = date_basis.get("profile_field_id")
                profile_provenance = date_basis.get("profile_provenance")
                if basis_kind == "opportunity_date":
                    if opportunity_date is None or selected_date != opportunity_date:
                        errors.append("path cost dated opportunity must use its opportunity date")
                    if profile_field is not None or profile_provenance is not None:
                        errors.append("path cost opportunity-date basis must not substitute a profile date")
                    row = evidence_by_id.get(evidence_id)
                    if row is None or "path_cost:date_basis" not in row.get("supports", []):
                        errors.append("path cost opportunity date needs direct official date evidence")
                elif basis_kind == "nearest_user_available_date":
                    if opportunity_date is not None:
                        errors.append("path cost uses a user date only when the opportunity has no date")
                    if evidence_id is not None:
                        errors.append("path cost undated opportunity must not invent official date evidence")
                    if (not isinstance(profile_field, str) or PROFILE_FIELD_ID.fullmatch(profile_field) is None
                            or profile_provenance != "user_supplied"):
                        errors.append("path cost undated opportunity needs an explicit user-supplied availability field")

            duration = path_cost.get("programme_duration_days")
            duration_range = None
            if isinstance(duration, dict):
                duration_range = _ordered_range(duration.get("range"), "programme duration range", errors)
                _validate_cost_source(duration, "programme duration", errors)

            money_rows = _validate_cost_dimension(path_cost.get("money"), "money", errors)
            _validate_cost_dimension(path_cost.get("time"), "time", errors)
            _validate_cost_dimension(path_cost.get("stress"), "stress", errors)
            money = path_cost.get("money")
            if isinstance(money, dict):
                for estimate in money_rows:
                    if estimate.get("currency") is not None and not isinstance(estimate.get("currency"), str):
                        errors.append("path cost money estimate needs a currency")
                if duration_range is not None and duration_range[1] >= 14:
                    living = [row for row in money_rows if row.get("category") == "cost_of_living"]
                    living_gaps = [row for row in money.get("gaps", [])
                                   if isinstance(row, dict) and row.get("category") == "cost_of_living"]
                    if not living and not living_gaps:
                        errors.append("long programme needs a cost_of_living estimate or explicit gap before flights")
                    if any(row.get("research_priority") != "primary" for row in living):
                        errors.append("long programme cost_of_living must be primary")
                    if any(row.get("research_priority") != "secondary" for row in money_rows
                           if row.get("category") == "flights"):
                        errors.append("long programme flights must be secondary to cost_of_living")

        route_status = path.get("route_status")
        action_count = len(actions) if isinstance(actions, list) else 0
        if route_status == "verified_actions":
            if not action_count:
                errors.append("verified-actions path needs a verified action")
            if component_gaps:
                errors.append("verified-actions path cannot hide component gaps; use high_value_with_gaps")
        elif route_status == "high_value_with_gaps":
            if not component_gaps:
                errors.append("high-value path needs an explicit component gap")
        elif route_status == "exploration_lead":
            if action_count:
                errors.append("exploration lead cannot contain verified actions")
            if not component_gaps:
                errors.append("exploration lead needs an explicit component gap")
            if value.get("classification") in {"ACT_NOW", "PREPARE_NEXT"}:
                errors.append("exploration lead is not a selected opportunity")

    if value.get("classification") in {"ACT_NOW", "PREPARE_NEXT"}:
        route_rows = [row for row in evidence_by_id.values() if "participation_route" in row.get("supports", [])]
        if not route_rows:
            errors.append("grounding gate: selected opportunity lacks direct official participation-route evidence")
        if snapshot is not None and not any("liveness" in row.get("supports", []) and _current_temporal(row, snapshot)
                                            for row in evidence_by_id.values()):
            errors.append("liveness gate: selected opportunity lacks current source-backed liveness evidence")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("opportunity", type=Path, help="opportunity JSON record to validate")
    parser.add_argument("--public-fixture", action="store_true",
                        help="require the fabricated-data notice used by committed fixtures")
    args = parser.parse_args(argv)
    try:
        value = json.loads(args.opportunity.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        parser.error(str(error))
    errors = validate_opportunity(value, public_fixture=args.public_fixture)
    if errors:
        print("invalid EUSP opportunity:")
        print("\n".join(f"- {error}" for error in errors))
        return 2
    print(f"valid {SCHEMA_VERSION}: {args.opportunity}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
