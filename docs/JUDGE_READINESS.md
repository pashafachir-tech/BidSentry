# Judge readiness

## Score sheet as supplied

| Element | Weight | Demonstration and evidence |
|---|---:|---|
| Problem clarity and relevance | 20% | Explain the procurement review workflow and show a clause with its extracted-text source. Bring interviews, workflow observations, or a validated user problem; the included package examples are synthetic. |
| Innovation, creativity, feasibility, monetization | 25% | Show local-first rule signals, document drop, evidence review, human confirmation, and optional integrations. Present per-workspace subscription and integration tiers only as a business hypothesis until willingness to pay and operating costs are validated. |
| User impact and benefits | 15% | Show the reviewer path from source document to a documented follow-up. In a pilot, measure time to first review, findings with traceable citations, and how often reviewers confirm or dismiss signals. No real-world impact data is currently claimed. |
| Technical execution and prototype functionality | 20% | Run the app, drop a supported file, inspect an evidence reference, filter the register, and export. Report live integrations only after a successful end-to-end check; otherwise show the local fallback honestly. |
| Responsible AI implementation | 10% | Describe scores as uncalibrated triage indices, never fraud probabilities or verdicts. Show human review, per-audit Langflow consent, local fallback, and metadata-only audit logging. |
| Hackathon class participation | 5% | Keep independent proof of attendance, checkpoints, each team member's contribution, and the final demo. The product cannot establish program participation by itself. |

The listed weights total **95%**. The remaining 5% is not specified in the supplied sheet. Ask the organizers how to handle it; do not normalize or estimate the final weighted score without their direction.

The reference fixture has been labeled as synthetic and not benchmarked. Earlier accuracy, confidence, latency, and “ground truth” claims had no supporting evaluation record, so those values were removed. The dashboard no longer converts a low synthetic risk band into a “compliance rate.” Do not cite the three fixture cases as measured model performance.

Custom findings can now receive a manual disposition: supported by evidence, needs more information, or not supported. BidSentry stores the audit ID, finding ID, selected label, and timestamp only. The UI and export show counts and coverage as **reviewer input**, not accuracy, independent adjudication, or user impact. Counts become evidence only after reviewers actually use the feature; this workspace currently has no prefilled feedback.

## Three-minute demo

1. State the user and problem, then disclose that the built-in examples are synthetic.
2. Drag a selection document into the audit form and run the local review.
3. Open a finding and show the source filename/line, evidence, and reviewer note.
4. Explain that a signal requires human verification, record an honest reviewer disposition, and show the review and follow-up draft. The saved label is an audit trail, not proof of model accuracy.
5. Show integration status. Configure credentials only when available; a configured key alone does not prove a working integration.
6. Close with a pilot measurement plan and evidence still to collect: user validation, impact measures, and willingness to pay.

## Evidence to collect before judging

- Short interviews or workflow validation with procurement staff, bidders, or legal reviewers, with consent and no sensitive tender documents.
- A pilot baseline and post-use measurements for review time and reviewer-confirmed signals.
- A supported-file demonstration on the judging machine, plus one fallback case such as an image-only PDF.
- A successful end-to-end integration run if claiming Langflow or Composio is operational; otherwise label it optional/not configured.
- Business model assumptions, pilot costs, and pricing feedback labeled as estimates until validated.
- Attendance, checkpoint, contribution, and team-role evidence for the participation category.

See [Pilot validation protocol](PILOT_VALIDATION.md) for a concrete, non-fabricated measurement plan, privacy gates, and the evidence expected for each rubric category. The dashboard now reports measured local rules-engine runtime only after real audits; this excludes file extraction, external integrations, and reviewer time.
