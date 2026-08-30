#!/usr/bin/env python3
"""Validate the EUSP v1 local user-profile Markdown ingress contract.

This validator is intentionally an ingress check only. It accepts no inferred or
external provenance and never fills omitted fields with defaults.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path

SCHEMA_VERSION = "eusp-local-user-profile/v1"
TITLE = "# EUSP local user profile"
SECTIONS = (
    "Geography track",
    "Career ambitions",
    "Thematic interests",
    "Goals and outcomes",
    "Assets",
    "Constraints",
    "Preferences",
    "Unknowns",
)
KEY_PATTERNS = {
    "Geography track": re.compile(r"geo-([1-9][0-9]*)\.(place|period)$"),
    "Career ambitions": re.compile(r"career_ambition-[1-9][0-9]*$"),
    "Thematic interests": re.compile(r"thematic_interest-[1-9][0-9]*$"),
    "Goals and outcomes": re.compile(r"(?:goal|outcome)-[1-9][0-9]*$"),
    "Assets": re.compile(r"asset-[1-9][0-9]*$"),
    "Constraints": re.compile(r"constraint-[1-9][0-9]*$"),
    "Preferences": re.compile(r"preference-[1-9][0-9]*$"),
    "Unknowns": re.compile(r"unknown-[1-9][0-9]*$"),
}
FIELD = re.compile(r"^- \[([^]]+)\] `([^`]+)`: (.+?)\s*$")
PERIOD = re.compile(r"^(\d{4}-\d{2}-\d{2})/(\d{4}-\d{2}-\d{2})$")
PUBLIC_FIXTURE_NOTICE = ("This is a fabricated, anonymized public evaluation fixture. "
                         "It is not a real person or a profile derived from one.")


def _content_lines(markdown: str):
    """Yield non-comment lines while retaining their original line numbers."""
    in_comment = False
    for number, line in enumerate(markdown.splitlines(), 1):
        stripped = line.strip()
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if stripped.startswith("<!--"):
            if "-->" not in stripped:
                in_comment = True
            continue
        yield number, stripped


def validate_profile_markdown(markdown: str, *, public_fixture: bool = False) -> list[str]:
    """Return deterministic contract violations without deriving any profile facts."""
    errors: list[str] = []
    lines = list(_content_lines(markdown))
    if not lines or lines[0][1] != TITLE:
        errors.append(f"line 1 must be {TITLE!r}")
        return errors
    version_index = next((index for index, (_, line) in enumerate(lines)
                          if line == f"`schema_version: {SCHEMA_VERSION}`"), None)
    if version_index is None:
        errors.append(f"missing schema version {SCHEMA_VERSION!r}")
        return errors
    if any(line for _, line in lines[1:version_index]):
        errors.append("schema version must be the first non-comment line after the title")

    heading_indexes = [(index, line[3:]) for index, (_, line) in enumerate(lines)
                       if line.startswith("## ")]
    headings = [heading for _, heading in heading_indexes]
    if headings != list(SECTIONS):
        errors.append("sections must appear exactly once and in the required order")
    first_heading = min((index for index, _ in heading_indexes), default=len(lines))
    for number, line in lines[version_index + 1:first_heading]:
        if line and not (public_fixture and line == PUBLIC_FIXTURE_NOTICE):
            errors.append(f"line {number}: prose before sections is not allowed")

    seen_keys: set[str] = set()
    geography: dict[str, set[str]] = {}
    current: str | None = None
    for number, line in lines:
        if line == TITLE or line == f"`schema_version: {SCHEMA_VERSION}`":
            continue
        if line.startswith("## "):
            current = line[3:]
            continue
        if current is None:
            continue
        if not line:
            continue
        match = FIELD.fullmatch(line)
        if match is None:
            errors.append(f"line {number}: profile facts must use '- [user_supplied] `field-key`: value'")
            continue
        provenance, key, value = match.groups()
        if provenance != "user_supplied":
            errors.append(f"line {number}: {key!r} provenance must be user_supplied")
        if not value.strip() or value.strip().lower() in {"null", "none", "..."}:
            errors.append(f"line {number}: {key!r} has an empty/placeholder value")
        if key in seen_keys:
            errors.append(f"line {number}: duplicate field key {key!r}")
        seen_keys.add(key)
        pattern = KEY_PATTERNS.get(current)
        if pattern is None or pattern.fullmatch(key) is None:
            errors.append(f"line {number}: {key!r} is not valid in section {current!r}")
            continue
        geo = KEY_PATTERNS["Geography track"].fullmatch(key) if current == "Geography track" else None
        if geo:
            geography.setdefault(geo.group(1), set()).add(geo.group(2))
            if geo.group(2) == "period":
                period = PERIOD.fullmatch(value)
                if period is None:
                    errors.append(f"line {number}: geography period must be YYYY-MM-DD/YYYY-MM-DD")
                else:
                    try:
                        start, end = (dt.date.fromisoformat(date) for date in period.groups())
                        if start > end:
                            errors.append(f"line {number}: geography period starts after it ends")
                    except ValueError:
                        errors.append(f"line {number}: geography period contains an invalid ISO date")
    for identifier, fields in sorted(geography.items(), key=lambda item: int(item[0])):
        if fields != {"place", "period"}:
            missing = ", ".join(sorted({"place", "period"} - fields))
            errors.append(f"geo-{identifier} must include both place and period; missing {missing}")
    if public_fixture and PUBLIC_FIXTURE_NOTICE not in markdown:
        errors.append("public fixture lacks its explicit fabricated-data notice")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path, help="local profile Markdown to validate")
    parser.add_argument("--public-fixture", action="store_true",
                        help="require the fabricated-data notice used by committed fixtures")
    args = parser.parse_args(argv)
    try:
        markdown = args.profile.read_text(encoding="utf-8")
    except OSError as error:
        parser.error(str(error))
    errors = validate_profile_markdown(markdown, public_fixture=args.public_fixture)
    if errors:
        print("invalid EUSP local profile:")
        print("\n".join(f"- {error}" for error in errors))
        return 2
    print(f"valid {SCHEMA_VERSION}: {args.profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
