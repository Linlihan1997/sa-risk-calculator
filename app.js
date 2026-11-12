(function () {
  "use strict";
  var M = window.SA_MODEL, C = window.SACalc;
  var YN = [["0", "No"], ["1", "Yes"]];
  var USE = [["0", "Never"], ["1", "Former (not in past 30 days)"], ["2", "Current (past 30 days)"]];
  var USE_S = { "0": "Never", "1": "Former", "2": "Current" };

  // Input definitions (variable, label, short label for plots, options, default)
  var GROUPS = [
    { title: "Demographics", fields: [
      { v: "grade", label: "Grade", short: "Grade", opts: [["9", "9th"], ["10", "10th"], ["11", "11th"], ["12", "12th"]], def: "10" },
      { v: "female", label: "Sex", short: "Female sex", opts: [["0", "Male"], ["1", "Female"]], def: "1" },
      { v: "raceeth", label: "Race/ethnicity", short: "Race/ethnicity", opts: [["White", "White"], ["Black", "Black"], ["Hispanic", "Hispanic"], ["Asian", "Asian"], ["Other", "Other/multiple"]], def: "White" },
      { v: "sexual_minority", label: "Sexual minority", hint: "gay/lesbian, bisexual, other or questioning", short: "Sexual minority", opts: YN, def: "0" }
    ]},
    { title: "Mental health (past 12 months)", fields: [
      { v: "sad_hopeless", label: "Persistent sadness or hopelessness", hint: "almost every day for ≥2 weeks", short: "Sadness/hopelessness", opts: YN, def: "0" },
      { v: "plan", label: "Made a suicide plan", short: "Suicide plan", opts: YN, def: "0" }
    ]},
    { title: "Substance use", fields: [
      { v: "nicotine_status", label: "Tobacco/nicotine use", hint: "cigarettes, e-cigarettes, cigars, smokeless", short: "Tobacco/nicotine", sopts: USE_S, opts: USE, def: "0" },
      { v: "alcohol_status", label: "Alcohol use", short: "Alcohol", sopts: USE_S, opts: USE, def: "0" },
      { v: "marijuana_status", label: "Marijuana use", short: "Marijuana", sopts: USE_S, opts: USE, def: "0" },
      { v: "other_drug_any", label: "Illicit drug use or prescription opioid misuse (lifetime)", short: "Illicit drug/opioid misuse", opts: YN, def: "0" },
      { v: "early_onset_any", label: "Tobacco, alcohol or marijuana use before age 13", short: "Substance use before 13", opts: YN, def: "0" }
    ]},
    { title: "Violence (past 12 months)", fields: [
      { v: "bullying_count", label: "Bullying victimization", hint: "at school and/or electronically", short: "Bullying", sopts: { "0": "None", "1": "1 type", "2": "2 types" }, opts: [["0", "None"], ["1", "One type"], ["2", "Both types"]], def: "0" },
      { v: "school_victim_any", label: "School violence victimization", hint: "felt unsafe or threatened with a weapon at school", short: "School violence", opts: YN, def: "0" },
      { v: "fighting_any", label: "Physical fighting", short: "Physical fighting", opts: YN, def: "0" },
      { v: "weapon_any", label: "Weapon carrying", short: "Weapon carrying", opts: YN, def: "0" },
      { v: "sexual_dating_violence_any", label: "Sexual or dating violence victimization", short: "Sexual/dating violence", opts: YN, def: "0" }
    ]},
    { title: "Sexual behavior and health", fields: [
      { v: "sexual_behavior", label: "Sexual behavior", short: "Sexual behavior", sopts: { "0": "Never", "1": "Active", "2": "High-risk" }, opts: [["0", "Never had sex"], ["1", "Sexually active, no high-risk features"], ["2", "First sex before 13 or ≥4 partners"]], def: "0" },
      { v: "concussion", label: "Sports-related concussion", short: "Concussion", opts: YN, def: "0" }
    ]}
  ];
  var EXAMPLE = { grade: "9", female: "1", raceeth: "Black", sexual_minority: "1", sad_hopeless: "1", plan: "1",
    nicotine_status: "2", alcohol_status: "1", marijuana_status: "2", other_drug_any: "1", early_onset_any: "0",
    bullying_count: "2", school_victim_any: "1", fighting_any: "1", weapon_any: "0", sexual_dating_violence_any: "1",
    sexual_behavior: "1", concussion: "0" };
  var FIELD = {}; GROUPS.forEach(function (g) { g.fields.forEach(function (f) { FIELD[f.v] = f; }); });

  var form = document.getElementById("inputs");
  GROUPS.forEach(function (g) {
    var t = document.createElement("div"); t.className = "group-title"; t.textContent = g.title; form.appendChild(t);
    g.fields.forEach(function (f) {
      var w = document.createElement("div"); w.className = "field";
      var l = document.createElement("label"); l.htmlFor = "in-" + f.v; l.textContent = f.label;
      if (f.hint) { var h = document.createElement("div"); h.className = "hint"; h.textContent = f.hint; l.appendChild(h); }
      var s = document.createElement("select"); s.id = "in-" + f.v; s.name = f.v;
      f.opts.forEach(function (o) { var op = document.createElement("option"); op.value = o[0]; op.textContent = o[1]; s.appendChild(op); });
      s.value = f.def; s.addEventListener("change", update);
      w.appendChild(l); w.appendChild(s); form.appendChild(w);
    });
  });

  function values() {
    var x = {};
    M.vars.forEach(function (v) { var s = document.getElementById("in-" + v).value; x[v] = v === "raceeth" ? s : Number(s); });
    return x;
  }
  function optionText(v, val) {
    var o = FIELD[v].opts.filter(function (p) { return p[0] === String(val); })[0]; return o ? o[1] : String(val);
  }
  function shortVal(v, val) { var f = FIELD[v]; return f.sopts ? f.sopts[String(val)] : optionText(v, val); }
  function setAll(obj) { Object.keys(obj).forEach(function (k) { document.getElementById("in-" + k).value = obj[k]; }); update(); }

  document.getElementById("btn-example").addEventListener("click", function () { setAll(EXAMPLE); });
  document.getElementById("btn-reset").addEventListener("click", function () {
    var d = {}; Object.keys(FIELD).forEach(function (k) { d[k] = FIELD[k].def; }); setAll(d);
  });

  // ---------- rendering ----------
  var ICON_HIGH = '<svg viewBox="0 0 48 44" width="52" height="48"><path d="M24 3L46 41H2z" fill="#c8102e"/><rect x="22" y="15" width="4" height="14" rx="2" fill="#fff"/><circle cx="24" cy="34.5" r="2.4" fill="#fff"/></svg>';
  var ICON_LOW = '<svg viewBox="0 0 48 48" width="50" height="50"><circle cx="24" cy="24" r="21" fill="#1d4ed8"/><rect x="22" y="12" width="4" height="15" rx="2" fill="#fff"/><circle cx="24" cy="33.5" r="2.4" fill="#fff"/></svg>';

  function fmt(p) { return (p * 100).toFixed(0) + "%"; }
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

  function renderRisk(p, sh) {
    var high = p >= M.threshold;
    var badge = document.getElementById("risk-badge");
    badge.textContent = high ? "Above threshold" : "Below threshold"; badge.className = "badge " + (high ? "high" : "low");
    var pr = document.getElementById("risk-prob"); pr.textContent = fmt(p); pr.className = "risk-prob " + (high ? "high" : "low");
    document.getElementById("risk-icon").innerHTML = high ? ICON_HIGH : ICON_LOW;
    document.getElementById("risk-text").textContent = high
      ? "The estimated probability is at or above the model threshold (" + fmt(M.threshold) + "), indicating a likely suicide attempt in the past 12 months."
      : "The estimated probability is below the model threshold (" + fmt(M.threshold) + "). This does not rule out a past attempt or future risk.";
    document.getElementById("meter-marker").style.left = (p * 100) + "%";
    document.getElementById("meter-threshold").style.left = (M.threshold * 100) + "%";
    document.getElementById("meter").setAttribute("aria-label", "Estimated probability " + fmt(p) + "; threshold " + fmt(M.threshold));

    var idx = sh.values.map(function (v, i) { return i; });
    var ups = idx.filter(function (i) { return sh.values[i] > 0.002; }).sort(function (a, b) { return sh.values[b] - sh.values[a]; }).slice(0, 3);
    var downs = idx.filter(function (i) { return sh.values[i] < -0.002; }).sort(function (a, b) { return sh.values[a] - sh.values[b]; }).slice(0, ups.length ? 1 : 3);
    var ul = document.getElementById("factor-list"); ul.innerHTML = "";
    ups.concat(downs).forEach(function (i) {
      var v = sh.vars[i], up = sh.values[i] > 0, li = document.createElement("li");
      li.className = up ? "up" : "down";
      li.innerHTML = '<span class="arrow">' + (up ? "↑" : "↓") + "</span><span><b>" + esc(FIELD[v].short) + "</b> (" +
        esc(shortVal(v, values()[v])) + ") " + (up ? "increases" : "decreases") + " the probability.</span>";
      ul.appendChild(li);
    });
    if (!ul.children.length) ul.innerHTML = "<li>No single predictor changes the estimate by more than 0.2 percentage points.</li>";
  }

  function renderWaterfall(sh, x) {
    var MAXR = 10, n = sh.vars.length;
    var order = sh.values.map(function (v, i) { return i; }).sort(function (a, b) { return Math.abs(sh.values[b]) - Math.abs(sh.values[a]); });
    var rows = order.slice(0, MAXR - 1).map(function (i) {
      return { label: shortVal(sh.vars[i], x[sh.vars[i]]) + " = " + FIELD[sh.vars[i]].short, val: sh.values[i] };
    });
    var rest = order.slice(MAXR - 1);
    if (rest.length) rows.push({ label: rest.length + " other predictors", val: rest.reduce(function (s, i) { return s + sh.values[i]; }, 0), other: true });

    // cumulative from the bottom row (starting at base) to the top row (ending at f(x))
    var cum = sh.base, segs = new Array(rows.length);
    for (var r = rows.length - 1; r >= 0; r--) { segs[r] = [cum, cum + rows[r].val]; cum += rows[r].val; }
    var lo = Math.min(sh.base, sh.fx), hi = Math.max(sh.base, sh.fx);
    segs.forEach(function (s) { lo = Math.min(lo, s[0], s[1]); hi = Math.max(hi, s[0], s[1]); });
    var pad = (hi - lo) * 0.12 + 0.01; lo = Math.max(0, lo - pad); hi = Math.min(1, hi + pad);

    var W = 660, L = 250, Rr = 640, top = 40, rh = 34, H = top + rows.length * rh + 52;
    var X = function (v) { return L + (v - lo) / (hi - lo) * (Rr - L); };
    var svg = ['<svg viewBox="0 0 ' + W + " " + H + '" xmlns="http://www.w3.org/2000/svg" font-family="Inter,Segoe UI,Arial,sans-serif" role="img" aria-label="SHAP waterfall plot">'];
    // grid ticks
    var step = niceStep((hi - lo) / 5), t0 = Math.ceil(lo / step) * step, axisY = top + rows.length * rh + 8;
    for (var t = t0; t <= hi + 1e-9; t += step) {
      var xt = X(t);
      svg.push('<line x1="' + xt + '" y1="' + top + '" x2="' + xt + '" y2="' + axisY + '" stroke="#eef0f3"/>');
      svg.push('<line x1="' + xt + '" y1="' + axisY + '" x2="' + xt + '" y2="' + (axisY + 5) + '" stroke="#333"/>');
      svg.push('<text x="' + xt + '" y="' + (axisY + 18) + '" font-size="12" text-anchor="middle" fill="#333">' + t.toFixed(step < 0.05 ? 2 : 1) + "</text>");
    }
    svg.push('<line x1="' + L + '" y1="' + axisY + '" x2="' + Rr + '" y2="' + axisY + '" stroke="#333"/>');
    // f(x) and E[f(X)] reference lines
    svg.push('<line x1="' + X(sh.fx) + '" y1="' + (top - 8) + '" x2="' + X(sh.fx) + '" y2="' + (top + rh) + '" stroke="#999" stroke-dasharray="2,2"/>');
    svg.push('<text x="' + X(sh.fx) + '" y="' + (top - 14) + '" font-size="12.5" text-anchor="middle" fill="#333"><tspan font-style="italic">f(x)</tspan> = ' + sh.fx.toFixed(3) + "</text>");
    svg.push('<line x1="' + X(sh.base) + '" y1="' + (axisY - rh) + '" x2="' + X(sh.base) + '" y2="' + axisY + '" stroke="#999" stroke-dasharray="2,2"/>');
    svg.push('<text x="' + X(sh.base) + '" y="' + (axisY + 36) + '" font-size="12.5" text-anchor="middle" fill="#333">E[<tspan font-style="italic">f(X)</tspan>] = ' + sh.base.toFixed(3) + "</text>");

    rows.forEach(function (row, r) {
      var y = top + r * rh + 5, h = rh - 10, a = segs[r][0], b = segs[r][1], pos = b >= a;
      var x1 = X(Math.min(a, b)), x2 = X(Math.max(a, b)), w = Math.max(x2 - x1, 1.5), tip = Math.min(8, w * 0.6);
      var col = pos ? "#ff0d57" : "#1e88e5", pts;
      if (pos) pts = [[x1, y], [x1 + w - tip, y], [x1 + w, y + h / 2], [x1 + w - tip, y + h], [x1, y + h]];
      else pts = [[x1 + w, y], [x1 + tip, y], [x1, y + h / 2], [x1 + tip, y + h], [x1 + w, y + h]];
      svg.push('<polygon points="' + pts.map(function (p) { return p[0].toFixed(1) + "," + p[1].toFixed(1); }).join(" ") + '" fill="' + col + '"/>');
      if (r < rows.length - 1) {
        var nx = X(b);
        svg.push('<line x1="' + nx + '" y1="' + (y - 5) + '" x2="' + nx + '" y2="' + (y + h + 5) + '" stroke="#bbb" stroke-width="0.8"/>');
      }
      var txt = (row.val >= 0 ? "+" : "−") + Math.abs(row.val).toFixed(3);
      var inside = w > 52;
      var tx = inside ? x1 + w / 2 : (pos ? x1 + w + 6 : x1 - 6);
      svg.push('<text x="' + tx + '" y="' + (y + h / 2 + 4) + '" font-size="12" fill="' + (inside ? "#fff" : col) + '" text-anchor="' +
        (inside ? "middle" : (pos ? "start" : "end")) + '">' + txt + "</text>");
      svg.push('<text x="' + (L - 10) + '" y="' + (y + h / 2 + 4) + '" font-size="12.5" text-anchor="end" fill="' + (row.other ? "#777" : "#333") + '">' + esc(row.label) + "</text>");
    });
    svg.push("</svg>");
    document.getElementById("waterfall").innerHTML = svg.join("");
  }
  function niceStep(raw) {
    var p = Math.pow(10, Math.floor(Math.log10(raw))), m = raw / p;
    return (m < 1.5 ? 1 : m < 3 ? 2 : m < 7 ? 5 : 10) * p;
  }

  function renderCoefTable() {
    var rows = [], z0 = M.intercept;
    M.numeric.forEach(function (n) { z0 -= n.coef * n.mean / n.scale; });
    rows.push(["Intercept", z0, null]);
    M.vars.forEach(function (v) {
      var num = M.numeric.filter(function (n) { return n.var === v; })[0];
      if (num) { var b = num.coef / num.scale; rows.push([FIELD[v].short + (v === "grade" ? " (per grade)" : v === "bullying_count" ? " (per type)" : ""), b, Math.exp(b)]); }
      else {
        var c = M.categorical.filter(function (k) { return k.var === v; })[0];
        rows.push([FIELD[v].short + " (ref: " + optionText(v, c.reference) + ")", null, null, true]);
        Object.keys(c.coefs).forEach(function (lvl) { if (lvl !== c.reference) rows.push([optionText(v, lvl), c.coefs[lvl], Math.exp(c.coefs[lvl]), false, true]); });
      }
    });
    var h = '<table class="coef"><thead><tr><th>Predictor</th><th>β</th><th>OR</th></tr></thead><tbody>';
    rows.forEach(function (r) {
      h += "<tr><td" + (r[4] ? ' class="sub"' : "") + ">" + esc(r[0]) + "</td><td>" + (r[1] === null ? "" : r[1].toFixed(3)) +
        "</td><td>" + (r[2] === null ? "" : r[2].toFixed(2)) + "</td></tr>";
    });
    document.getElementById("coef-table").innerHTML = h + "</tbody></table>";
  }

  function update() {
    var x = values(), sh = C.shap(M, x, 300, 2026);
    renderRisk(sh.fx, sh); renderWaterfall(sh, x);
    var mb = document.getElementById("mobile-bar");
    mb.innerHTML = "Estimated probability <b>" + fmt(sh.fx) + "</b> · " + (sh.fx >= M.threshold ? "Above" : "Below") + " threshold";
    mb.className = "mobile-bar " + (sh.fx >= M.threshold ? "high" : "low");
  }

  // tabs
  Array.prototype.forEach.call(document.querySelectorAll(".tab"), function (b) {
    b.addEventListener("click", function () {
      Array.prototype.forEach.call(document.querySelectorAll(".tab"), function (o) { o.classList.remove("active"); o.setAttribute("aria-selected", "false"); });
      b.classList.add("active"); b.setAttribute("aria-selected", "true");
      document.getElementById("tab-analysis").classList.toggle("hidden", b.dataset.tab !== "analysis");
      document.getElementById("tab-info").classList.toggle("hidden", b.dataset.tab !== "info");
    });
  });

  renderCoefTable();
  setAll(EXAMPLE);
})();
