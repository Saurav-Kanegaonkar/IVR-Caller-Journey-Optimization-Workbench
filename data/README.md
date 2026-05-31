# Synthetic Data Notes

This artifact uses deterministic synthetic data because real IVR path logs, authentication outcomes, DTMF or speech-recognition misses, transfer reasons, and repeat-call behavior are sensitive operational records.

The generator models common contact-center self-service structures: platform, entry channel, authentication requirement, journey complexity, daily call volume, containment, transfer, abandon, no-match, no-input, authentication failure, repeat-call behavior, Tableau refresh status, stakeholder requests, and recommendation actions.

Distributions are seeded in `scripts/score_operating_data.py`. Call volume uses normal variation around journey baselines with weekday effects. Containment, transfer, abandon, no-match, no-input, and authentication failure rates vary by journey type, authentication requirement, and complexity. Transfer-cost opportunity is calculated from modeled transfer volume, target containment gap, and estimated cost per transferred call.
