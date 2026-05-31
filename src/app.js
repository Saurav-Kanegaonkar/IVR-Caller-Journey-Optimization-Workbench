const state = {
  payload: null,
  activeView: "command",
  selectedJourney: null,
};

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const number = new Intl.NumberFormat("en-US");

const viewTitles = {
  command: "Executive command center",
  queue: "Journey friction queue",
  flow: "Call-flow diagnostics",
  handoff: "Stakeholder handoff",
};

async function boot() {
  const response = await fetch("analysis/outputs/app_payload.json");
  state.payload = await response.json();
  state.selectedJourney = state.payload.priorityQueue[0].journey_id;
  render();
}

function render() {
  renderTabs();
  renderSummary();
  renderActiveView();
}

function renderTabs() {
  const tabs = document.querySelector("#tabs");
  tabs.innerHTML = Object.entries(viewTitles)
    .map(
      ([id, label]) => `
        <button class="${state.activeView === id ? "active" : ""}" type="button" data-view="${id}">
          <span aria-hidden="true">${iconFor(id)}</span>${label}
        </button>
      `
    )
    .join("");

  tabs.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeView = button.dataset.view;
      render();
    });
  });
}

function renderSummary() {
  const { summary } = state.payload;
  const metrics = [
    ["Modeled calls", number.format(summary.modeled_calls), "28 days"],
    ["Containment", `${summary.containment_rate}%`, "self-service"],
    ["Transfer rate", `${summary.transfer_rate}%`, "agent demand"],
    ["Top 10 value", currency.format(summary.annualized_savings_top_10), "annualized"],
  ];

  document.querySelector("#metricStrip").innerHTML = metrics
    .map(
      ([label, value, note]) => `
        <article>
          <span>${label}</span>
          <strong>${value}</strong>
          <em>${note}</em>
        </article>
      `
    )
    .join("");
}

function renderActiveView() {
  const host = document.querySelector("#surface");
  if (state.activeView === "command") host.innerHTML = commandView();
  if (state.activeView === "queue") host.innerHTML = queueView();
  if (state.activeView === "flow") host.innerHTML = flowView();
  if (state.activeView === "handoff") host.innerHTML = handoffView();
  attachSurfaceHandlers();
}

function commandView() {
  const { summary, priorityQueue, flowDiagnostics, surfaceNotes } = state.payload;
  const top = priorityQueue[0];
  const topFlow = flowDiagnostics[0];
  return `
    <section class="view-grid command-grid">
      <article class="panel lead-panel">
        <p class="eyebrow">Operating readout</p>
        <h2>${summary.top_journey}</h2>
        <p class="lead">${summary.top_next_move}</p>
        <div class="split-metrics">
          <div><span>Priority score</span><strong>${top.priority_score}</strong></div>
          <div><span>Transfer cost</span><strong>${currency.format(top.monthly_transfer_cost)}</strong></div>
          <div><span>Requests</span><strong>${top.stakeholder_requests}</strong></div>
        </div>
      </article>
      <article class="panel">
        <p class="eyebrow">Diagnostic signal</p>
        <h2>${topFlow.step_name}</h2>
        <div class="diagnostic-card">
          ${bar("Friction", topFlow.friction_index, 30)}
          ${bar("Drop off", topFlow.drop_off_rate, 18)}
          ${bar("No match", topFlow.no_match_rate, 10)}
          ${bar("Transfer", topFlow.transfer_rate, 18)}
        </div>
      </article>
      <article class="panel note-panel">
        <p class="eyebrow">Why this surface exists</p>
        <h2>${surfaceNotes[0].title}</h2>
        <p>${surfaceNotes[0].body}</p>
      </article>
      <article class="panel table-panel">
        <p class="eyebrow">Top IVR journeys</p>
        ${priorityTable(priorityQueue.slice(0, 6))}
      </article>
    </section>
  `;
}

function queueView() {
  const { priorityQueue, surfaceNotes } = state.payload;
  const selected = priorityQueue.find((row) => row.journey_id === state.selectedJourney) || priorityQueue[0];
  return `
    <section class="view-grid queue-grid">
      <article class="panel table-panel">
        <p class="eyebrow">Ranked decision queue</p>
        ${priorityTable(priorityQueue)}
      </article>
      <aside class="panel detail-panel">
        <p class="eyebrow">Selected journey</p>
        <h2>${selected.journey_name}</h2>
        <p class="lead">${selected.recommended_next_move}</p>
        <div class="detail-list">
          ${detail("Platform", selected.ivr_platform)}
          ${detail("Owner", selected.owner_team)}
          ${detail("Calls", number.format(selected.offered_calls))}
          ${detail("Containment", `${selected.containment_rate}%`)}
          ${detail("Transfer", `${selected.transfer_rate}%`)}
          ${detail("Repeat calls", `${selected.repeat_call_rate}%`)}
          ${detail("No match", `${selected.no_match_rate}%`)}
          ${detail("Data quality", selected.data_quality_score)}
          ${detail("Annual value", currency.format(selected.annualized_savings_opportunity))}
        </div>
      </aside>
      <article class="panel note-panel">
        <p class="eyebrow">Analyst lens</p>
        <h2>${surfaceNotes[1].title}</h2>
        <p>${surfaceNotes[1].body}</p>
      </article>
    </section>
  `;
}

function flowView() {
  const { flowDiagnostics, priorityQueue, surfaceNotes } = state.payload;
  const topJourneys = new Set(priorityQueue.slice(0, 8).map((row) => row.journey_id));
  const rows = flowDiagnostics.filter((row) => topJourneys.has(row.journey_id)).slice(0, 16);
  return `
    <section class="view-grid flow-grid">
      <article class="panel flow-map">
        <p class="eyebrow">Path-step friction</p>
        <h2>Where callers get stuck</h2>
        <div class="flow-list">
          ${rows.map(flowRow).join("")}
        </div>
      </article>
      <article class="panel">
        <p class="eyebrow">Step mix</p>
        <div class="step-stack">
          ${["Greeting and language", "Caller authentication", "Intent capture", "Eligibility or account lookup", "Self-service resolution", "Agent transfer"]
            .map((step) => {
              const stepRows = flowDiagnostics.filter((row) => row.step_name === step);
              const avg = stepRows.reduce((sum, row) => sum + row.friction_index, 0) / stepRows.length;
              return `<div>${bar(step, avg, 30)}</div>`;
            })
            .join("")}
        </div>
      </article>
      <article class="panel note-panel">
        <p class="eyebrow">User-flow view</p>
        <h2>${surfaceNotes[2].title}</h2>
        <p>${surfaceNotes[2].body}</p>
      </article>
    </section>
  `;
}

function handoffView() {
  const { stakeholderRequests, recommendedActions, surfaceNotes } = state.payload;
  return `
    <section class="view-grid handoff-grid">
      <article class="panel">
        <p class="eyebrow">Open stakeholder asks</p>
        <h2>Reporting and validation queue</h2>
        <div class="request-list">
          ${stakeholderRequests.slice(0, 8).map(requestCard).join("")}
        </div>
      </article>
      <article class="panel">
        <p class="eyebrow">Action candidates</p>
        <h2>Design handoff</h2>
        <div class="action-list">
          ${recommendedActions.slice(0, 10).map(actionCard).join("")}
        </div>
      </article>
      <article class="panel note-panel">
        <p class="eyebrow">Delivery lens</p>
        <h2>${surfaceNotes[3].title}</h2>
        <p>${surfaceNotes[3].body}</p>
      </article>
    </section>
  `;
}

function priorityTable(rows) {
  return `
    <table>
      <thead>
        <tr>
          <th>Journey</th>
          <th>Score</th>
          <th>Containment</th>
          <th>Transfer</th>
          <th>Next move</th>
        </tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (row) => `
              <tr class="${row.journey_id === state.selectedJourney ? "selected" : ""}" data-journey="${row.journey_id}">
                <td><b>${row.journey_name}</b><span>${row.intent}</span></td>
                <td>${row.priority_score}</td>
                <td>${row.containment_rate}%</td>
                <td>${row.transfer_rate}%</td>
                <td>${row.recommended_next_move}</td>
              </tr>
            `
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function flowRow(row) {
  return `
    <article>
      <div>
        <b>${row.step_name}</b>
        <span>${row.journey_id} | ${row.avg_step_seconds}s avg step</span>
      </div>
      <strong>${row.friction_index}</strong>
      ${bar("Completion", row.completion_rate, 100)}
      <small>Drop ${row.drop_off_rate}% | No match ${row.no_match_rate}% | No input ${row.no_input_rate}% | Transfer ${row.transfer_rate}%</small>
    </article>
  `;
}

function requestCard(row) {
  return `
    <article>
      <b>${row.request_id}</b>
      <strong>${row.ask_type}</strong>
      <span>${row.stakeholder} | ${row.requested_output} | ${row.sla_hours}h SLA</span>
      <p>${row.business_question}</p>
    </article>
  `;
}

function actionCard(row) {
  return `
    <article>
      <div>
        <b>${row.action_type}</b>
        <span>${row.owner_team} | ${row.status}</span>
      </div>
      <strong>${row.expected_containment_lift_pct}% lift</strong>
      <small>${row.expected_transfer_reduction_pct}% transfer reduction | ${row.effort_hours}h effort</small>
    </article>
  `;
}

function detail(label, value) {
  return `<div><span>${label}</span><strong>${value}</strong></div>`;
}

function bar(label, value, max) {
  const width = Math.max(3, Math.min(100, (value / max) * 100));
  return `
    <div class="bar-row">
      <span>${label}</span>
      <div class="bar-track"><i style="width:${width}%"></i></div>
      <b>${Number(value).toFixed(value > 20 ? 0 : 1)}</b>
    </div>
  `;
}

function iconFor(id) {
  return {
    command: "◆",
    queue: "▦",
    flow: "↳",
    handoff: "✓",
  }[id];
}

function attachSurfaceHandlers() {
  document.querySelectorAll("[data-journey]").forEach((row) => {
    row.addEventListener("click", () => {
      state.selectedJourney = row.dataset.journey;
      if (state.activeView !== "queue") state.activeView = "queue";
      render();
    });
  });
}

boot().catch((error) => {
  document.querySelector("#surface").innerHTML = `<article class="panel"><h2>Unable to load artifact data</h2><p>${error.message}</p></article>`;
});
