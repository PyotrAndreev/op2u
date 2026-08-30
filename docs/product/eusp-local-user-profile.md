# EUSP local user-profile model

This is the v1 local ingress contract for an explicit user profile. It realizes the existing [profile and consent boundary](user-profile-and-consent.md); it is not a source of inferred facts, a social connector, or a profile-enrichment pipeline.

## Storage and privacy boundary

Copy [`usr/profile.template.md`](../../usr/profile.template.md) to `usr/profile.md` and edit the copy locally. `usr/profile.md` and every other actual file below `usr/` are Git-ignored. The committed template has no profile facts. Never force-add a local profile, production run, raw trace, document, contact detail, or a profile-derived example.

The only committed example is the fabricated public fixture at [`evals/fixtures/eusp_p1_profile_model/v1/pipeline_input/profile.md`](../../evals/fixtures/eusp_p1_profile_model/v1/pipeline_input/profile.md). It follows the existing EUSP convention that public pipeline input lives under `pipeline_input/`; it is not a real person or transformed personal profile.

## Markdown schema

A conforming profile has this exact title and version line, followed by these headings in this order:

```md
# EUSP local user profile

`schema_version: eusp-local-user-profile/v1`

## Geography track
## Career ambitions
## Thematic interests
## Goals and outcomes
## Assets
## Constraints
## Preferences
## Unknowns
```

Within a section, every recorded field is one Markdown list item:

```md
- [user_supplied] `field-key`: value
```

`user_supplied` is deliberately the only permitted provenance. The bracket is per field, not per section: copied, retrieved, model-generated, assumed, and inferred facts are invalid profile inputs. `value` is literal user-provided text; it is not normalized into a fact not stated by the user.

Use these field keys:

| Section | Allowed field keys |
| --- | --- |
| Geography track | `geo-N.place` and matching `geo-N.period` |
| Career ambitions | `career_ambition-N` |
| Thematic interests | `thematic_interest-N` |
| Goals and outcomes | `goal-N`, `outcome-N` |
| Assets | `asset-N` |
| Constraints | `constraint-N` |
| Preferences | `preference-N` |
| Unknowns | `unknown-N` |

`N` is a positive integer. A geography record must contain exactly one matching place and period. Its period is an explicit inclusive ISO-date range, `YYYY-MM-DD/YYYY-MM-DD`, with the start no later than the end. Do not manufacture a geography window from an organization, a document, an IP address, a prior run, or an omitted location.

## Unknowns and omission

Silence is unknown. An absent field, absent section item, or absent geography record supplies no negative fact and no permission, eligibility, location, preference, date, or constraint. The optional **Unknowns** section records only an explicit user statement that something is unknown; it does not make an omitted fact known. Do not write a placeholder, empty value, `null`, or a guessed value to fill a gap.

## Validation

Run the deterministic, standard-library validator before using a profile in a run:

```sh
python tools/eusp_profile.py usr/profile.md
python tools/eusp_profile.py --public-fixture \
  evals/fixtures/eusp_p1_profile_model/v1/pipeline_input/profile.md
```

It rejects a wrong title/version or section order; free-form facts; empty, duplicate, or section-incompatible field keys; any provenance other than `user_supplied`; unmatched or malformed geography fields; and invalid or reversed geography dates. `--public-fixture` additionally requires the fixture's explicit fabricated-data notice. It cannot determine whether prose is personal data: keeping real profiles out of Git remains a human review and repository-boundary requirement.

The validator does not add defaults or infer facts. It validates ingress only; it does not change P1 prompts, scoring, packet projection, candidate selection, or any other discovery pipeline behavior.

## EUSP evaluation compatibility

The model is Markdown because the existing EUSP P1 packet carries `profile_markdown` verbatim. A profile conforming to this contract can therefore occupy the ordinary `pipeline_input/profile.md` surface without exposing evaluator-only hidden traits or changing the P1 serialization contract. The regression test builds the ordinary P1 packet from the anonymized profile fixture and checks that its public fields and P1 preflight remain valid.
