-- IVR caller journey analytics SQL appendix.
-- Table names mirror the synthetic CSV files in this portfolio artifact.

-- 1. Journey performance rollup for Tableau.
select
  j.journey_id,
  j.journey_name,
  j.ivr_platform,
  j.owner_team,
  sum(d.offered_calls) as offered_calls,
  sum(d.contained_calls) * 1.0 / nullif(sum(d.offered_calls), 0) as containment_rate,
  sum(d.transferred_calls) * 1.0 / nullif(sum(d.offered_calls), 0) as transfer_rate,
  sum(d.abandoned_calls) * 1.0 / nullif(sum(d.offered_calls), 0) as abandon_rate,
  avg(d.no_match_rate) as no_match_rate,
  avg(d.no_input_rate) as no_input_rate,
  avg(d.auth_fail_rate) as auth_fail_rate,
  avg(d.data_quality_score) as data_quality_score
from daily_metrics d
join journeys j on d.journey_id = j.journey_id
group by 1, 2, 3, 4;

-- 2. Path-step friction diagnostics.
select
  journey_id,
  step_name,
  sum(drop_off_callers) * 1.0 / nullif(sum(callers_entered), 0) as drop_off_rate,
  sum(no_match_callers) * 1.0 / nullif(sum(callers_entered), 0) as no_match_rate,
  sum(no_input_callers) * 1.0 / nullif(sum(callers_entered), 0) as no_input_rate,
  sum(transferred_callers) * 1.0 / nullif(sum(callers_entered), 0) as transfer_rate
from path_events
group by 1, 2
order by drop_off_rate + no_match_rate + no_input_rate + transfer_rate desc;

-- 3. Stakeholder handoff queue.
select
  q.journey_id,
  q.priority_score,
  q.recommended_next_move,
  count(distinct r.request_id) as open_stakeholder_requests,
  count(distinct a.action_id) as action_candidates
from priority_queue q
left join stakeholder_requests r on q.journey_id = r.journey_id
left join recommended_actions a on q.journey_id = a.journey_id
group by 1, 2, 3
order by q.priority_score desc;
