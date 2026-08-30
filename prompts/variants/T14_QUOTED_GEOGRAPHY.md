# T14 — Quote-bounded geographic scope

Parent: `T13_FUNDING_COMPONENTS`
Affected stage: report only

## Falsifiable hypothesis

Requiring an exact official quote for both event/participation dates and place will remove unsupported geographic-window failures without discarding otherwise valid opportunities or weakening non-geographic route credit.

Failure: an item receives geographic overlap credit when its ledger proves only the date or only the place; a place is inferred from title, URL, organization, profile window, or prior artifact prose; or a valid non-geographic opportunity is unnecessarily rejected.

## Report-only mutation

1. A non-null `opportunity_horizon.geographic_window` requires direct official-primary ledger evidence for:
   - event or participation date overlapping the supplied window; and
   - the place/city/country claimed by that window.
2. The exact quote itself must contain the claimed place at sufficient specificity. Page title, URL path, organization address, search snippet, candidate name, source metadata, or profile presence cannot fill a quote-level location gap.
3. Date and place may come from separate direct official rows for the same candidate, but both rows must be retained in the final ledger and referenced by claim IDs.
4. If date is supported but place is not:
   - keep the candidate and its non-geographic family/role value when otherwise valid;
   - set `geographic_window` to null;
   - remove it from geographic coverage counts;
   - state `location not directly supported by retained exact quote` as uncertainty.
5. If place is supported but event/participation date is not, apply the same no-credit treatment.
6. Do not infer city from a broader country or country from a city unless the exact quote directly supports the claimed mapping.
7. Recompute breadth/geographic summaries and anti-collapse checks. Do not change effort or selection unless geographic overlap is itself required for liveness.

All T13 evidence projection, quoted time, seven-day action, funding-component, cap, lead-tier, and safety rules remain unchanged.
