# Analysis Plan

## Goal

Create a repeatable IVR caller behavior analysis that helps CX stakeholders decide which self-service journey to redesign first and what evidence should appear in Tableau reporting.

## Steps

1. Generate caller journeys with platform, owner, channel, authentication, complexity, volume, containment, and transfer assumptions.
2. Model daily IVR performance metrics for containment, transfer, abandonment, no-match, no-input, authentication failure, repeat calls, handle time, and data quality.
3. Aggregate path-step events to locate friction inside each user flow.
4. Score journeys using a transparent weighted formula that combines volume, transfer cost, containment gap, path friction, repeat-call risk, and data quality.
5. Convert the queue into Tableau-ready views, SQL checks, and stakeholder handoff recommendations.

## Scoring Formula

Priority score equals friction score plus volume weight plus savings opportunity weight. Friction score includes transfer rate, abandon rate, no-match rate, no-input rate, authentication failure rate, repeat-call rate, and data quality gap.
