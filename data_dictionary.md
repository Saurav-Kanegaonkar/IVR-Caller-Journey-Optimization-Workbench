# Data Dictionary

| Table | Grain | Purpose |
|---|---|---|
| `data/journeys.csv` | IVR journey | Platform, owner, intent, channel, authentication, complexity, and baseline assumptions. |
| `data/daily_metrics.csv` | Journey by day | IVR performance metrics for containment, transfer, abandon, repeat calls, prompt friction, handle time, and data quality. |
| `data/path_events.csv` | Journey step by day | User-flow diagnostics for menu, authentication, intent capture, integration, automation, and routing steps. |
| `data/stakeholder_requests.csv` | Stakeholder request | Reporting asks for Tableau views, Excel exports, root-cause briefs, journey annotations, and SQL validation. |
| `data/recommended_actions.csv` | Action candidate | Redesign and reporting actions with expected lift, effort, owner, and status. |
| `analysis/outputs/priority_queue.csv` | IVR journey | Scored journey queue used by the front end and SQL appendix. |
| `analysis/outputs/flow_diagnostics.csv` | Journey step | Aggregated flow friction view used by the diagnostics surface. |
| `analysis/outputs/app_payload.json` | Static app payload | Front-end data for metrics, charts, queues, and handoff cards. |
