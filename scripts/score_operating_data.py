import csv
import json
import math
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ROOT / "analysis" / "outputs"
ANALYSIS = ROOT / "analysis"
RNG = random.Random(42)


INTENTS = [
    ("Payment arrangement", "Billing", "Account Services", True, 0.54, 0.18),
    ("Outage status", "Support", "Service Desk", False, 0.68, 0.10),
    ("Order status", "Fulfillment", "Customer Care", False, 0.61, 0.12),
    ("Appointment reschedule", "Field Service", "Scheduling", True, 0.49, 0.20),
    ("Password reset", "Digital Support", "Account Services", True, 0.73, 0.08),
    ("Claims status", "Claims", "Customer Care", True, 0.46, 0.22),
    ("Benefits eligibility", "Member Services", "Member Care", True, 0.52, 0.17),
    ("Technical troubleshooting", "Support", "Service Desk", False, 0.39, 0.27),
    ("Service cancellation", "Retention", "Customer Care", True, 0.33, 0.31),
    ("New service quote", "Sales", "Inside Sales", False, 0.44, 0.24),
    ("Prescription refill", "Pharmacy", "Member Care", True, 0.66, 0.11),
    ("Fraud alert review", "Risk", "Account Services", True, 0.38, 0.28),
    ("Document request", "Back Office", "Customer Care", True, 0.58, 0.14),
    ("Agent callback", "Support", "Service Desk", False, 0.42, 0.23),
]

PLATFORMS = ["Genesys Cloud", "Avaya Aura", "Nuance Mix", "Amazon Connect"]
ENTRY_CHANNELS = ["toll-free", "mobile click-to-call", "branch transfer", "web callback"]
COMPLEXITY = ["Low", "Moderate", "High"]


def ensure_dirs():
    for path in [DATA, OUTPUTS, ANALYSIS, ROOT / "docs" / "images"]:
        path.mkdir(parents=True, exist_ok=True)


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def pct(value):
    return round(value * 100, 1)


def clamp(value, low, high):
    return max(low, min(high, value))


def make_journeys():
    journeys = []
    for idx in range(42):
        intent, domain, owner, auth_required, containment_base, transfer_base = INTENTS[idx % len(INTENTS)]
        platform = PLATFORMS[(idx + idx // 3) % len(PLATFORMS)]
        complexity = COMPLEXITY[(idx + (2 if auth_required else 0)) % len(COMPLEXITY)]
        volume = RNG.randint(620, 3900)
        journeys.append(
            {
                "journey_id": f"JRN{idx + 1:03d}",
                "journey_name": f"{intent} flow {idx // len(INTENTS) + 1}",
                "intent": intent,
                "business_domain": domain,
                "owner_team": owner,
                "entry_channel": ENTRY_CHANNELS[idx % len(ENTRY_CHANNELS)],
                "ivr_platform": platform,
                "auth_required": "Yes" if auth_required else "No",
                "complexity": complexity,
                "baseline_daily_calls": volume,
                "target_containment_rate": round(containment_base + RNG.uniform(0.02, 0.09), 3),
                "baseline_containment_rate": round(containment_base + RNG.uniform(-0.08, 0.05), 3),
                "baseline_transfer_rate": round(transfer_base + RNG.uniform(-0.04, 0.06), 3),
                "estimated_transfer_cost": round(RNG.uniform(4.35, 8.75), 2),
            }
        )
    return journeys


def make_daily_metrics(journeys):
    rows = []
    start = date(2026, 4, 1)
    for day_offset in range(28):
        current = start + timedelta(days=day_offset)
        weekday_factor = 0.78 if current.weekday() >= 5 else 1.0 + (0.08 if current.weekday() == 0 else 0)
        for journey in journeys:
            base_calls = int(journey["baseline_daily_calls"])
            volume = max(35, int(RNG.gauss(base_calls * weekday_factor, base_calls * 0.11)))
            containment_noise = RNG.uniform(-0.045, 0.045)
            containment = clamp(float(journey["baseline_containment_rate"]) + containment_noise, 0.22, 0.84)
            transfer = clamp(float(journey["baseline_transfer_rate"]) + RNG.uniform(-0.035, 0.035), 0.05, 0.45)
            abandon = clamp(0.035 + (0.11 if journey["complexity"] == "High" else 0.06 if journey["complexity"] == "Moderate" else 0.035) + RNG.uniform(-0.02, 0.025), 0.015, 0.22)
            no_match = clamp(0.025 + (0.055 if journey["complexity"] == "High" else 0.028) + RNG.uniform(-0.012, 0.018), 0.005, 0.16)
            no_input = clamp(0.018 + (0.04 if journey["entry_channel"] == "branch transfer" else 0.024) + RNG.uniform(-0.01, 0.014), 0.004, 0.12)
            auth_fail = clamp((0.062 if journey["auth_required"] == "Yes" else 0.012) + RNG.uniform(-0.012, 0.018), 0.0, 0.17)
            repeat = clamp(0.055 + transfer * 0.19 + no_match * 0.34 + RNG.uniform(-0.012, 0.018), 0.025, 0.24)
            avg_ivr_seconds = int(RNG.gauss(145 + 180 * no_match + 150 * auth_fail + (65 if journey["complexity"] == "High" else 0), 24))
            avg_handle_seconds = int(RNG.gauss(410 + 130 * transfer + (80 if journey["complexity"] == "High" else 30), 36))
            contained = int(volume * containment)
            transferred = int(volume * transfer)
            abandoned = int(volume * abandon)
            repeat_calls = int(volume * repeat)
            quality_score = clamp(96 - no_match * 92 - no_input * 65 - auth_fail * 50 - RNG.uniform(0, 5), 70, 99.4)
            rows.append(
                {
                    "date": current.isoformat(),
                    "journey_id": journey["journey_id"],
                    "offered_calls": volume,
                    "contained_calls": contained,
                    "transferred_calls": transferred,
                    "abandoned_calls": abandoned,
                    "repeat_calls_7d": repeat_calls,
                    "avg_ivr_seconds": avg_ivr_seconds,
                    "avg_agent_handle_seconds": avg_handle_seconds,
                    "containment_rate": round(containment, 4),
                    "transfer_rate": round(transfer, 4),
                    "abandon_rate": round(abandon, 4),
                    "no_match_rate": round(no_match, 4),
                    "no_input_rate": round(no_input, 4),
                    "auth_fail_rate": round(auth_fail, 4),
                    "repeat_call_rate": round(repeat, 4),
                    "data_quality_score": round(quality_score, 1),
                    "tableau_refresh_status": "Late" if quality_score < 80 and RNG.random() < 0.22 else "Complete",
                }
            )
    return rows


def make_path_events(journeys):
    rows = []
    steps = [
        ("Greeting and language", "Menu"),
        ("Caller authentication", "Authentication"),
        ("Intent capture", "Speech recognition"),
        ("Eligibility or account lookup", "Integration"),
        ("Self-service resolution", "Automation"),
        ("Agent transfer", "Routing"),
    ]
    start = date(2026, 4, 1)
    event_id = 1
    for day_offset in range(28):
        current = start + timedelta(days=day_offset)
        sampled = journeys if day_offset % 2 == 0 else journeys[:30]
        for journey in sampled:
            entered = max(45, int(RNG.gauss(int(journey["baseline_daily_calls"]) * 0.95, int(journey["baseline_daily_calls"]) * 0.08)))
            remaining = entered
            for step_index, (step_name, step_type) in enumerate(steps):
                if step_type == "Authentication" and journey["auth_required"] == "No":
                    continue
                friction = 0.025 + step_index * 0.012 + (0.03 if journey["complexity"] == "High" else 0.0)
                if step_type == "Speech recognition":
                    friction += 0.045
                if step_type == "Integration":
                    friction += 0.028
                drop = int(remaining * clamp(friction + RNG.uniform(-0.012, 0.018), 0.005, 0.18))
                no_match = int(remaining * (0.048 + RNG.uniform(-0.015, 0.025))) if step_type == "Speech recognition" else int(remaining * RNG.uniform(0.002, 0.012))
                no_input = int(remaining * (0.032 + RNG.uniform(-0.008, 0.018))) if step_type in ["Menu", "Speech recognition"] else int(remaining * RNG.uniform(0.001, 0.009))
                transfer = int(remaining * (0.15 + RNG.uniform(-0.04, 0.06))) if step_type == "Agent transfer" else int(remaining * RNG.uniform(0.003, 0.025))
                completed = max(0, remaining - drop - transfer)
                rows.append(
                    {
                        "event_id": f"EVT{event_id:05d}",
                        "date": current.isoformat(),
                        "journey_id": journey["journey_id"],
                        "step_name": step_name,
                        "step_type": step_type,
                        "callers_entered": remaining,
                        "callers_completed": completed,
                        "drop_off_callers": drop,
                        "no_match_callers": no_match,
                        "no_input_callers": no_input,
                        "transferred_callers": transfer,
                        "avg_step_seconds": int(RNG.gauss(34 + step_index * 19, 8)),
                    }
                )
                event_id += 1
                remaining = max(12, completed)
    return rows


def make_requests_and_actions(journeys):
    requests = []
    actions = []
    stakeholders = ["CX design lead", "Contact center director", "BI product owner", "IVR architect", "Client operations sponsor"]
    asks = ["Tableau drilldown", "Excel export", "root-cause brief", "journey map annotation", "SQL validation"]
    action_types = ["prompt rewrite", "routing rule update", "authentication tuning", "self-service content change", "metric definition cleanup", "callback treatment test"]
    for idx in range(90):
        journey = journeys[idx % len(journeys)]
        requests.append(
            {
                "request_id": f"REQ{idx + 1:04d}",
                "journey_id": journey["journey_id"],
                "stakeholder": stakeholders[idx % len(stakeholders)],
                "ask_type": asks[(idx + RNG.randint(0, 3)) % len(asks)],
                "requested_output": "Tableau view" if idx % 3 == 0 else "Excel workbook" if idx % 3 == 1 else "decision memo",
                "sla_hours": [8, 24, 48, 72][idx % 4],
                "business_question": f"Where should we improve the {journey['intent'].lower()} flow first?",
            }
        )
    for idx in range(168):
        journey = journeys[(idx * 5) % len(journeys)]
        expected_lift = round(RNG.uniform(1.2, 8.8), 1)
        effort = int(RNG.gauss(22, 9))
        actions.append(
            {
                "action_id": f"ACT{idx + 1:04d}",
                "journey_id": journey["journey_id"],
                "action_type": action_types[idx % len(action_types)],
                "expected_containment_lift_pct": expected_lift,
                "expected_transfer_reduction_pct": round(RNG.uniform(0.8, 6.4), 1),
                "effort_hours": max(4, effort),
                "owner_team": journey["owner_team"],
                "status": ["ready for review", "needs SME input", "queued for test", "watch"][idx % 4],
            }
        )
    return requests, actions


def aggregate(journeys, daily_rows, path_rows, requests, actions):
    by_journey = {row["journey_id"]: row for row in journeys}
    daily = defaultdict(list)
    path = defaultdict(list)
    req_count = defaultdict(int)
    action_count = defaultdict(int)
    action_lift = defaultdict(float)
    action_effort = defaultdict(float)
    for row in daily_rows:
        daily[row["journey_id"]].append(row)
    for row in path_rows:
        path[row["journey_id"]].append(row)
    for row in requests:
        req_count[row["journey_id"]] += 1
    for row in actions:
        action_count[row["journey_id"]] += 1
        action_lift[row["journey_id"]] += float(row["expected_containment_lift_pct"])
        action_effort[row["journey_id"]] += float(row["effort_hours"])

    queue = []
    for journey_id, rows in daily.items():
        journey = by_journey[journey_id]
        offered = sum(int(r["offered_calls"]) for r in rows)
        contained = sum(int(r["contained_calls"]) for r in rows)
        transferred = sum(int(r["transferred_calls"]) for r in rows)
        abandoned = sum(int(r["abandoned_calls"]) for r in rows)
        repeats = sum(int(r["repeat_calls_7d"]) for r in rows)
        avg_quality = sum(float(r["data_quality_score"]) for r in rows) / len(rows)
        no_match = sum(float(r["no_match_rate"]) for r in rows) / len(rows)
        no_input = sum(float(r["no_input_rate"]) for r in rows) / len(rows)
        auth_fail = sum(float(r["auth_fail_rate"]) for r in rows) / len(rows)
        containment = contained / offered
        transfer_rate = transferred / offered
        abandon_rate = abandoned / offered
        repeat_rate = repeats / offered
        transfer_cost = transferred * float(journey["estimated_transfer_cost"])
        target_gap = max(0, float(journey["target_containment_rate"]) - containment)
        annualized_savings = target_gap * offered * 13 * float(journey["estimated_transfer_cost"])
        friction_score = (
            transfer_rate * 32
            + abandon_rate * 20
            + no_match * 19
            + no_input * 12
            + auth_fail * 10
            + repeat_rate * 18
            + (100 - avg_quality) / 6
        )
        score = friction_score + math.log10(max(10, offered)) * 8 + min(18, annualized_savings / 48000)
        queue.append(
            {
                "journey_id": journey_id,
                "journey_name": journey["journey_name"],
                "intent": journey["intent"],
                "owner_team": journey["owner_team"],
                "ivr_platform": journey["ivr_platform"],
                "offered_calls": offered,
                "containment_rate": pct(containment),
                "transfer_rate": pct(transfer_rate),
                "abandon_rate": pct(abandon_rate),
                "repeat_call_rate": pct(repeat_rate),
                "no_match_rate": pct(no_match),
                "no_input_rate": pct(no_input),
                "auth_fail_rate": pct(auth_fail),
                "data_quality_score": round(avg_quality, 1),
                "monthly_transfer_cost": round(transfer_cost, 0),
                "annualized_savings_opportunity": round(annualized_savings, 0),
                "stakeholder_requests": req_count[journey_id],
                "action_candidates": action_count[journey_id],
                "avg_action_lift": round(action_lift[journey_id] / max(1, action_count[journey_id]), 1),
                "avg_effort_hours": round(action_effort[journey_id] / max(1, action_count[journey_id]), 1),
                "priority_score": round(score, 1),
                "recommended_next_move": recommend_next_move(no_match, no_input, auth_fail, transfer_rate, avg_quality),
            }
        )
    queue.sort(key=lambda item: item["priority_score"], reverse=True)

    flow = []
    for journey_id, rows in path.items():
        by_step = defaultdict(lambda: defaultdict(int))
        seconds = defaultdict(list)
        for row in rows:
            bucket = by_step[row["step_name"]]
            for key in ["callers_entered", "callers_completed", "drop_off_callers", "no_match_callers", "no_input_callers", "transferred_callers"]:
                bucket[key] += int(row[key])
            seconds[row["step_name"]].append(int(row["avg_step_seconds"]))
        for step_name, values in by_step.items():
            entered = max(1, values["callers_entered"])
            flow.append(
                {
                    "journey_id": journey_id,
                    "step_name": step_name,
                    "callers_entered": entered,
                    "completion_rate": pct(values["callers_completed"] / entered),
                    "drop_off_rate": pct(values["drop_off_callers"] / entered),
                    "no_match_rate": pct(values["no_match_callers"] / entered),
                    "no_input_rate": pct(values["no_input_callers"] / entered),
                    "transfer_rate": pct(values["transferred_callers"] / entered),
                    "avg_step_seconds": round(sum(seconds[step_name]) / len(seconds[step_name]), 0),
                    "friction_index": round(
                        values["drop_off_callers"] / entered * 42
                        + values["no_match_callers"] / entered * 24
                        + values["no_input_callers"] / entered * 15
                        + values["transferred_callers"] / entered * 19,
                        1,
                    ),
                }
            )
    flow.sort(key=lambda item: item["friction_index"], reverse=True)

    return queue, flow


def recommend_next_move(no_match, no_input, auth_fail, transfer_rate, quality):
    if quality < 82:
        return "Validate source definitions before publishing"
    if auth_fail > 0.075:
        return "Tune authentication fallback and recovery prompts"
    if no_match > 0.075:
        return "Rewrite intent prompt and add grammar variants"
    if transfer_rate > 0.22:
        return "Review routing rule and self-service eligibility"
    if no_input > 0.05:
        return "Shorten menu prompt and add repeat guidance"
    return "Monitor in weekly Tableau operating review"


def make_summary(queue, daily_rows, requests):
    offered = sum(int(row["offered_calls"]) for row in daily_rows)
    contained = sum(int(row["contained_calls"]) for row in daily_rows)
    transferred = sum(int(row["transferred_calls"]) for row in daily_rows)
    late_refresh = sum(1 for row in daily_rows if row["tableau_refresh_status"] == "Late")
    savings = sum(row["annualized_savings_opportunity"] for row in queue[:10])
    return {
        "modeled_calls": offered,
        "journeys_ranked": len(queue),
        "containment_rate": pct(contained / offered),
        "transfer_rate": pct(transferred / offered),
        "annualized_savings_top_10": round(savings, 0),
        "stakeholder_requests": len(requests),
        "late_refresh_days": late_refresh,
        "top_journey": queue[0]["journey_name"],
        "top_next_move": queue[0]["recommended_next_move"],
    }


def write_docs(summary, queue, flow):
    top = queue[0]
    ANALYSIS.joinpath("executive_findings.md").write_text(
        "\n".join(
            [
                "# Executive Findings",
                "",
                "## What I Analyzed",
                "",
                f"I modeled {summary['modeled_calls']:,} synthetic IVR calls across {summary['journeys_ranked']} caller journeys, then joined daily performance, path-step friction, stakeholder requests, and action candidates into one reporting and recommendation workflow.",
                "",
                "## Findings",
                "",
                f"- The highest-priority journey is {top['journey_name']} with a priority score of {top['priority_score']}.",
                f"- The top ten opportunities represent ${summary['annualized_savings_top_10']:,.0f} in annualized transfer-cost avoidance if containment gaps are closed.",
                f"- The aggregate containment rate is {summary['containment_rate']}%, while {summary['transfer_rate']}% of calls still transfer to agents.",
                f"- The leading diagnostic signal is {flow[0]['step_name']} in {flow[0]['journey_id']}, with a friction index of {flow[0]['friction_index']}.",
                "",
                "## Recommendation",
                "",
                "Use the priority queue to select the first journey for redesign, then use the flow diagnostics to decide whether the fix belongs in prompts, authentication, integrations, routing, or reporting definitions.",
            ]
        )
        + "\n"
    )
    ANALYSIS.joinpath("analysis_plan.md").write_text(
        "\n".join(
            [
                "# Analysis Plan",
                "",
                "## Goal",
                "",
                "Create a repeatable IVR caller behavior analysis that helps CX stakeholders decide which self-service journey to redesign first and what evidence should appear in Tableau reporting.",
                "",
                "## Steps",
                "",
                "1. Generate caller journeys with platform, owner, channel, authentication, complexity, volume, containment, and transfer assumptions.",
                "2. Model daily IVR performance metrics for containment, transfer, abandonment, no-match, no-input, authentication failure, repeat calls, handle time, and data quality.",
                "3. Aggregate path-step events to locate friction inside each user flow.",
                "4. Score journeys using a transparent weighted formula that combines volume, transfer cost, containment gap, path friction, repeat-call risk, and data quality.",
                "5. Convert the queue into Tableau-ready views, SQL checks, and stakeholder handoff recommendations.",
                "",
                "## Scoring Formula",
                "",
                "Priority score equals friction score plus volume weight plus savings opportunity weight. Friction score includes transfer rate, abandon rate, no-match rate, no-input rate, authentication failure rate, repeat-call rate, and data quality gap.",
            ]
        )
        + "\n"
    )
    ANALYSIS.joinpath("sql_checks.sql").write_text(
        "\n".join(
            [
                "-- IVR caller journey analytics SQL appendix.",
                "-- Table names mirror the synthetic CSV files in this portfolio artifact.",
                "",
                "-- 1. Journey performance rollup for Tableau.",
                "select",
                "  j.journey_id,",
                "  j.journey_name,",
                "  j.ivr_platform,",
                "  j.owner_team,",
                "  sum(d.offered_calls) as offered_calls,",
                "  sum(d.contained_calls) * 1.0 / nullif(sum(d.offered_calls), 0) as containment_rate,",
                "  sum(d.transferred_calls) * 1.0 / nullif(sum(d.offered_calls), 0) as transfer_rate,",
                "  sum(d.abandoned_calls) * 1.0 / nullif(sum(d.offered_calls), 0) as abandon_rate,",
                "  avg(d.no_match_rate) as no_match_rate,",
                "  avg(d.no_input_rate) as no_input_rate,",
                "  avg(d.auth_fail_rate) as auth_fail_rate,",
                "  avg(d.data_quality_score) as data_quality_score",
                "from daily_metrics d",
                "join journeys j on d.journey_id = j.journey_id",
                "group by 1, 2, 3, 4;",
                "",
                "-- 2. Path-step friction diagnostics.",
                "select",
                "  journey_id,",
                "  step_name,",
                "  sum(drop_off_callers) * 1.0 / nullif(sum(callers_entered), 0) as drop_off_rate,",
                "  sum(no_match_callers) * 1.0 / nullif(sum(callers_entered), 0) as no_match_rate,",
                "  sum(no_input_callers) * 1.0 / nullif(sum(callers_entered), 0) as no_input_rate,",
                "  sum(transferred_callers) * 1.0 / nullif(sum(callers_entered), 0) as transfer_rate",
                "from path_events",
                "group by 1, 2",
                "order by drop_off_rate + no_match_rate + no_input_rate + transfer_rate desc;",
                "",
                "-- 3. Stakeholder handoff queue.",
                "select",
                "  q.journey_id,",
                "  q.priority_score,",
                "  q.recommended_next_move,",
                "  count(distinct r.request_id) as open_stakeholder_requests,",
                "  count(distinct a.action_id) as action_candidates",
                "from priority_queue q",
                "left join stakeholder_requests r on q.journey_id = r.journey_id",
                "left join recommended_actions a on q.journey_id = a.journey_id",
                "group by 1, 2, 3",
                "order by q.priority_score desc;",
            ]
        )
        + "\n"
    )
    ANALYSIS.joinpath("tableau_measure_catalog.md").write_text(
        "\n".join(
            [
                "# Tableau Measure Catalog",
                "",
                "| Measure | Definition | Business Use |",
                "|---|---|---|",
                "| Containment Rate | Contained calls divided by offered calls | Shows how often callers resolve inside IVR self-service. |",
                "| Transfer Rate | Transferred calls divided by offered calls | Flags journeys creating agent demand. |",
                "| No-Match Rate | Speech or DTMF misses divided by offered calls | Diagnoses prompt or grammar friction. |",
                "| No-Input Rate | Silence or timeout events divided by offered calls | Diagnoses prompt clarity and menu pacing. |",
                "| Authentication Failure Rate | Failed authentication attempts divided by offered calls | Identifies recovery and fallback issues. |",
                "| Repeat Call Rate | Seven-day repeat calls divided by offered calls | Estimates unresolved caller intent. |",
                "| Data Quality Score | Completeness and refresh reliability score generated by source checks | Indicates whether a Tableau view is safe to publish. |",
                "| Priority Score | Weighted score for volume, friction, savings opportunity, and quality risk | Ranks which IVR journey should be redesigned first. |",
            ]
        )
        + "\n"
    )
    DATA.joinpath("README.md").write_text(
        "\n".join(
            [
                "# Synthetic Data Notes",
                "",
                "This artifact uses deterministic synthetic data because real IVR path logs, authentication outcomes, DTMF or speech-recognition misses, transfer reasons, and repeat-call behavior are sensitive operational records.",
                "",
                "The generator models common contact-center self-service structures: platform, entry channel, authentication requirement, journey complexity, daily call volume, containment, transfer, abandon, no-match, no-input, authentication failure, repeat-call behavior, Tableau refresh status, stakeholder requests, and recommendation actions.",
                "",
                "Distributions are seeded in `scripts/score_operating_data.py`. Call volume uses normal variation around journey baselines with weekday effects. Containment, transfer, abandon, no-match, no-input, and authentication failure rates vary by journey type, authentication requirement, and complexity. Transfer-cost opportunity is calculated from modeled transfer volume, target containment gap, and estimated cost per transferred call.",
            ]
        )
        + "\n"
    )
    ROOT.joinpath("data_dictionary.md").write_text(
        "\n".join(
            [
                "# Data Dictionary",
                "",
                "| Table | Grain | Purpose |",
                "|---|---|---|",
                "| `data/journeys.csv` | IVR journey | Platform, owner, intent, channel, authentication, complexity, and baseline assumptions. |",
                "| `data/daily_metrics.csv` | Journey by day | IVR performance metrics for containment, transfer, abandon, repeat calls, prompt friction, handle time, and data quality. |",
                "| `data/path_events.csv` | Journey step by day | User-flow diagnostics for menu, authentication, intent capture, integration, automation, and routing steps. |",
                "| `data/stakeholder_requests.csv` | Stakeholder request | Reporting asks for Tableau views, Excel exports, root-cause briefs, journey annotations, and SQL validation. |",
                "| `data/recommended_actions.csv` | Action candidate | Redesign and reporting actions with expected lift, effort, owner, and status. |",
                "| `analysis/outputs/priority_queue.csv` | IVR journey | Scored journey queue used by the front end and SQL appendix. |",
                "| `analysis/outputs/flow_diagnostics.csv` | Journey step | Aggregated flow friction view used by the diagnostics surface. |",
                "| `analysis/outputs/app_payload.json` | Static app payload | Front-end data for metrics, charts, queues, and handoff cards. |",
            ]
        )
        + "\n"
    )


def write_payload(summary, queue, flow, requests, actions):
    payload = {
        "summary": summary,
        "priorityQueue": queue[:18],
        "flowDiagnostics": flow,
        "stakeholderRequests": requests[:16],
        "recommendedActions": actions[:18],
        "surfaceNotes": [
            {
                "title": "Executive command center",
                "body": "Shows the operating picture a BI analyst would bring to a CX stakeholder review: call volume, containment, transfer pressure, savings opportunity, and top next move.",
            },
            {
                "title": "Journey friction queue",
                "body": "Ranks IVR journeys by transparent scoring so the analyst can defend why one flow needs redesign before another.",
            },
            {
                "title": "Call-flow diagnostics",
                "body": "Moves below dashboard KPIs to pinpoint whether callers are failing in menu prompts, authentication, intent capture, integrations, automation, or routing.",
            },
            {
                "title": "Stakeholder handoff",
                "body": "Connects Tableau, Excel, SQL validation, and journey-map asks to concrete action candidates and owners.",
            },
        ],
    }
    OUTPUTS.joinpath("app_payload.json").write_text(json.dumps(payload, indent=2) + "\n")


def main():
    ensure_dirs()
    journeys = make_journeys()
    daily = make_daily_metrics(journeys)
    path_events = make_path_events(journeys)
    requests, actions = make_requests_and_actions(journeys)
    queue, flow = aggregate(journeys, daily, path_events, requests, actions)
    summary = make_summary(queue, daily, requests)

    write_csv(DATA / "journeys.csv", journeys, list(journeys[0].keys()))
    write_csv(DATA / "daily_metrics.csv", daily, list(daily[0].keys()))
    write_csv(DATA / "path_events.csv", path_events, list(path_events[0].keys()))
    write_csv(DATA / "stakeholder_requests.csv", requests, list(requests[0].keys()))
    write_csv(DATA / "recommended_actions.csv", actions, list(actions[0].keys()))
    write_csv(OUTPUTS / "priority_queue.csv", queue, list(queue[0].keys()))
    write_csv(OUTPUTS / "flow_diagnostics.csv", flow, list(flow[0].keys()))
    write_payload(summary, queue, flow, requests, actions)
    OUTPUTS.joinpath("summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_docs(summary, queue, flow)

    print(f"Generated {summary['journeys_ranked']} IVR journeys and {summary['modeled_calls']:,} modeled calls.")
    print(f"Top journey: {summary['top_journey']} - {summary['top_next_move']}")


if __name__ == "__main__":
    main()
