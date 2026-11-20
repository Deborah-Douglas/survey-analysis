(() => {
  const get = (id) => document.getElementById(id);
  const results = get("results");
  if (!window.SURVEY) {
    results.innerHTML = '<p class="footnote" role="alert">The survey data could not load. Reload this page to try again.</p>';
    return;
  }
  const { charts, cohorts } = window.SURVEY;
  const filter = get("cohort");
  const compare = get("compare");
  const buttons = [...document.querySelectorAll("[data-view]")];
  let view = "overview";
  let mode = "bars";
  const open = new Set();
  const esc = (v) => String(v).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  const optgroups = new Map();
  cohorts.slice(1).forEach((c) => {
    if (!optgroups.has(c.group)) {
      const g = document.createElement("optgroup");
      g.label = c.group;
      optgroups.set(c.group, g);
      filter.append(g);
    }
    optgroups.get(c.group).append(new Option(c.name, c.id));
  });

  const views = {
    overview: { no: "01", title: "Survey overview", note: "The findings at a glance." },
    policy: { no: "02", title: "Federal effects", note: "What affected communities and what journalists reported." },
    pressure: { no: "03", title: "Reporting pressures", note: "What respondents experienced directly in their work." },
    editorial: { no: "04", title: "Editorial choices", note: "How journalists navigate framing, evidence and contested claims." },
    support: { no: "05", title: "Newsroom support", note: "What limits coverage, what outlets provide, and what would help." },
    methods: { no: "06", title: "Methods and sample", note: "How the results were calculated and what they can support." },
  };
  const ids = { federal:"Q9",frequency:"Q10",connection:"Q14",pressure:"Q11",overlap:"Q11",politicized:"Q15",editorial:"Q16",contested:"Q18",change:"Q19",ranking:"Q21",safety:"Q22",familiar:"Q23",resources:"Q24",tenure:"Q7",outlet:"Q6" };
  const pct = ([n, base]) => n === null || !base ? null : n / base * 100;
  const whole = (values) => pct(values) === null ? "Hidden" : `${Math.round(pct(values))}%`;
  const readout = (values) => values[0] === null ? "Small cell" : `${values[0]} / ${values[1]}`;
  const full = (values) => values[0] === null ? "Hidden" : `${whole(values)} (${readout(values)})`;
  const noteFor = (id) => ({
    pressure: "The “Prefer not to answer” selections are part of the displayed base for this question. They do not count as experiences.",
    overlap: "The two access problems are newly off-record sources and an official denial, delay, or restriction of access to information, records, or a public site.",
    editorial: "The base can vary by statement. The chart shows the combined share selecting Agree or Strongly Agree.",
    resources: "33 of 280 respondents picked fewer than three options. The same four choices ranked highest when limited to the 247 who picked exactly three.",
    ranking: "Of the 302 rankings, 43 exactly matched the export column order. Excluding those records leaves staffing or time first for 179 of 259 (69%).",
  })[id];

  function panel(id, cohort, options = {}) {
    const chart = charts[id];
    const showRef = cohort !== "all" && compare.checked;
    const table = mode === "tables" && view !== "methods";
    const rows = chart.rows.slice();
    if (chart.sort) rows.sort((a,b) => (pct(b.values[cohort]) ?? -1) - (pct(a.values[cohort]) ?? -1));
    const shown = options.limit ? rows.slice(0, options.limit) : rows;
    const key = `${view}/${id}`;
    const cohortName = cohorts.find(c => c.id === cohort).name;
    let body;
    if (table) {
      body = `<div class="table-wrap" tabindex="0" role="region" aria-label="${esc(chart.title)} data">
        <table><thead><tr><th scope="col">Response</th><th scope="col">Share</th><th scope="col">Count / base</th>${showRef ? '<th scope="col">All respondents</th>' : ""}</tr></thead>
        <tbody>${shown.map(r => `<tr><th scope="row">${esc(r.label)}</th><td>${whole(r.values[cohort])}</td><td>${readout(r.values[cohort])}</td>${showRef ? `<td class="ref-cell"><span>${whole(r.values.all)}</span> <span>(${readout(r.values.all)})</span></td>` : ""}</tr>`).join("")}</tbody>
        </table></div>`;
    } else {
      body = `<ul class="bar-list">${shown.map(r => {
        const v = r.values[cohort];
        const ref = showRef ? r.values.all : null;
        return `<li class="bar-row">
          <div class="data-line"><span class="data-label">${esc(r.label)}</span><span class="data-readout"><strong>${whole(v)}</strong><small>${readout(v)}</small></span></div>
          ${v[0] === null ? "" : `<div class="track" aria-hidden="true"><span class="fill" style="--share:${pct(v)}%"></span>${ref ? `<span class="reference" style="--ref:${pct(ref)}%"></span>` : ""}</div>`}
          ${ref ? `<div class="data-aside">All: ${full(ref)}</div>` : ""}
        </li>`;
      }).join("")}</ul><div class="axis" aria-hidden="true"><span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span></div>`;
    }
    return `<article class="panel${options.wide ? " wide" : ""}" aria-label="${esc(chart.title)}, ${esc(cohortName)}">
      <div class="panel-head"><h3>${esc(chart.title)}</h3><span class="question-id">${ids[id]}</span></div>
      <p class="panel-note">${esc(chart.note)}</p>${body}
      ${showRef && !table ? `<div class="legend" aria-hidden="true"><span><i></i>Selected group</span><span><i class="tick"></i>All respondents</span></div>` : ""}
      <details class="definition" data-detail="${key}" ${open.has(key) ? "open" : ""}><summary>Question details</summary>
      <p>${esc(chart.detail)}</p>${noteFor(id) ? `<p>${esc(noteFor(id))}</p>` : ""}</details>
    </article>`;
  }

  function stats(id, size) {
    const metrics = [
      ["Eligible respondents", size, "Completed and partial surveys"],
      ["Sources declined to go on record", ...statData(charts.pressure.rows[0].values[id])],
      ["Routine stories became contested", ...statData(charts.kpis.rows[0].values[id])],
      ["Staffing or time ranked first", ...statData(charts.kpis.rows[1].values[id])],
    ];
    return `<div class="stats" aria-label="Key figures">${metrics.map(([label,num,text]) => `<div class="stat">
      <span class="stat-name">${esc(label)}</span><strong class="stat-value">${num}</strong><span class="stat-base">${esc(text)}</span></div>`).join("")}</div>`;
  }
  const statData = (v) => [whole(v), v[0] === null ? "Small cell" : `${readout(v)} respondents`];

  function methodCards() {
    return `<article class="methods-card"><h3>Who is included</h3>
      <p>447 records: one preview and 446 live records. Of those, 421 screened in, 17 screened out and eight left eligibility blank. Of the 421 eligible starts, 298 finished and 123 did not.</p>
      <p>Both completed and partial surveys contribute to every question they answered. The 71% completion share is not an invitation response rate.</p></article>
    <article class="methods-card"><h3>How to read the numbers</h3>
      <p>Percentages use item-specific denominators and exclude blanks. Multi-select shares can sum to more than 100%. Cohort results are hidden when fewer than 30 answered or when either side of a displayed category has fewer than five respondents.</p>
      <p>The full-sample comparison includes the selected group; it is not a comparison against everyone outside that group. Groups from different filter categories can overlap.</p></article>
    ${panel("tenure","all")}${panel("outlet","all")}
    <article class="methods-card"><h3>Checks on the findings</h3>
      <p>Including partial surveys adds 60 answers on federal effects (358 total), 59 on direct pressures (352), and 10 on requested resources (280). The leading options remain the same as in the completed-only analysis.</p>
      <p>Staffing or time remained the top-ranked constraint for 69% (179/259) after excluding the 43 rankings that matched the export column order. The export does not show whether that order was displayed by default.</p></article>
    <article class="methods-card"><h3>What this survey cannot tell us</h3>
      <p>No sampling frame, invitation denominator, or weights were supplied. The survey describes who responded, not U.S. journalists as a whole. It does not establish causation, verify individual incidents, or support geographic estimates.</p>
      <p>Only aggregates are included here. Confidential follow-up information and raw written answers are not part of the dashboard.</p></article>`;
  }
  function render() {
    const c = cohorts.find((g) => g.id === filter.value) ?? cohorts[0];
    const conf = views[view];
    const isMethods = view === "methods";
    compare.disabled = c.id === "all";
    get("controls").hidden = isMethods;
    get("bars").setAttribute("aria-pressed", mode === "bars");
    get("tables").setAttribute("aria-pressed", mode === "tables");
    const card = (id, opts) => panel(id, c.id, opts);
    const topic = {
      overview: () => `${card("federal",{limit:5})}${card("resources",{limit:5})}${card("pressure",{limit:5,wide:true})}`,
      policy: () => `${card("federal")}${card("frequency")}${card("connection")}`,
      pressure: () => `${card("pressure")}${card("overlap")}
      <article class="methods-card wide"><h3>What respondents said about access</h3>
      <p>Open-ended answers, including those from partial surveys, described slower records requests, more layers between journalists and officials, and more effort to verify government information independently. Others reported little or no change in access, or described supportive newsrooms and workable conditions on their beats.</p>
      <p>These are themes from a review of 279 answers about reporting conditions and 271 about changes in access, not estimates of how common each theme was.</p></article>`,
      editorial: () => `${card("politicized")}${card("editorial")}${card("contested")}${card("change")}`,
      support: () => `${card("resources")}${card("safety")}${card("ranking")}${card("familiar")}
      <article class="methods-card wide"><h3>Practices respondents said helped</h3>
      <p>Respondents described pooling expertise across newsrooms, arranging protest check-ins, using secure channels for confidential tips, bringing in pro bono media lawyers, and following up on the local consequences of federal actions.</p>
      <p>These are examples from written responses across the full sample, not measured outcomes or subgroup findings.</p></article>`,
      methods: methodCards,
    };
    results.innerHTML = `<section aria-labelledby="view-title">
      <div class="view-head"><div>
        <div class="chapter"><span class="section-no" aria-hidden="true">${conf.no}</span><h2 id="view-title">${conf.title}</h2></div>
        <p class="view-note">${conf.note}</p>
      </div>${isMethods ? "" : `<p class="scope">${esc(c.name)} <strong>· n=${c.size}</strong></p>`}</div>
      ${view === "overview" ? stats(c.id,c.size) : ""}
      <div class="layout">${topic[view]()}</div>
      ${isMethods ? "" : `<p class="footnote">Counts use available answers from completed and partial surveys. Unanswered items do not enter the denominator.${view === "overview" ? " Topic tabs show the full lists." : ""}${c.id !== "all" ? " Small cells are hidden in group views." : ""}</p>`}
    </section>`;
    results.querySelectorAll("details").forEach((d) => d.addEventListener("toggle", () => {
      if (d.open) open.add(d.dataset.detail);
      else open.delete(d.dataset.detail);
    }));
    get("status").textContent = isMethods ? conf.title : `${conf.title}. ${c.name}, ${c.size} eligible respondents. ${mode === "bars" ? "Charts" : "Tables"}${!compare.disabled && compare.checked ? " with all-respondent comparison" : ""}.`;
  }
  buttons.forEach((button) => button.addEventListener("click", () => {
    view = button.dataset.view;
    buttons.forEach((b) => b === button ? b.setAttribute("aria-current","page") : b.removeAttribute("aria-current"));
    render();
  }));
  filter.addEventListener("change", render);
  compare.addEventListener("change", render);
  get("bars").addEventListener("click", () => { mode = "bars"; render(); });
  get("tables").addEventListener("click", () => { mode = "tables"; render(); });
  render();
})();
