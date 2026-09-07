"""Build the shareable model-routing dashboard from the CSV.

CSV is the source of truth. The HTML embeds a snapshot so a single file can be
emailed, and it can also load a sibling/edited CSV without regenerating.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "model-routing-by-category.csv"
OUT_PATH = ROOT / "model-routing-dashboard.html"

FIELDNAMES = [
    "category",
    "rank",
    "model",
    "provider",
    "quality_score",
    "cost_in_per_mtok_usd",
    "cost_out_per_mtok_usd",
    "usd_per_sec",
    "cost_10min_usd",
    "cost_1hr_usd",
    "pass",
    "pass_to_when",
]

VIDEO = {
    "MiniMax H3 Max": {"usd_per_sec": 0.08, "cost_10min_usd": 48.00, "cost_1hr_usd": 288.00},
    "Seedance 2.0 / 2.5": {"usd_per_sec": 0.23, "cost_10min_usd": 138.72, "cost_1hr_usd": 832.32},
    "Gemini Omni Flash": {"usd_per_sec": 0.10, "cost_10min_usd": 60.00, "cost_1hr_usd": 360.00},
    "MiniMax H3": {"usd_per_sec": 0.08, "cost_10min_usd": 48.00, "cost_1hr_usd": 288.00},
    "Veo 3.1": {"usd_per_sec": 0.40, "cost_10min_usd": 240.00, "cost_1hr_usd": 1440.00},
    "Wan 3.0": {"usd_per_sec": 0.10, "cost_10min_usd": 60.00, "cost_1hr_usd": 360.00},
    "Grok Imagine Video 1.5": {"usd_per_sec": 0.14, "cost_10min_usd": 84.00, "cost_1hr_usd": 504.00},
    "Kling 3.0": {"usd_per_sec": 0.168, "cost_10min_usd": 100.80, "cost_1hr_usd": 604.80},
    "Runway Gen-4.5": {"usd_per_sec": 0.12, "cost_10min_usd": 72.00, "cost_1hr_usd": 432.00},
    "Kling 3.0 Turbo": {"usd_per_sec": 0.09, "cost_10min_usd": 54.00, "cost_1hr_usd": 324.00},
    "PixVerse V6": {"usd_per_sec": 0.08, "cost_10min_usd": 48.00, "cost_1hr_usd": 288.00},
    "Wan 2.7": {"usd_per_sec": 0.08, "cost_10min_usd": 48.00, "cost_1hr_usd": 288.00},
}

PASS = {
    "creative_writing": "Claude Fable 5.1",
    "copywriting": "Claude Opus 5",
    "coding": "Claude Opus 5",
    "design": "GPT Image 2",
    "video_creation": "MiniMax H3 Max",
    "browser_use": "Kimi K3",
    "agent_development": "GPT-5.6 Sol",
    "position_of_agents": "Claude Fable 5.1",
}

LABELS = {
    "creative_writing": "Creative writing",
    "copywriting": "Copywriting",
    "coding": "Coding",
    "design": "Design",
    "video_creation": "Video creation",
    "browser_use": "Browser use",
    "agent_development": "Agent development",
    "position_of_agents": "Position of agents",
}


def money_cell(value: str | None, places: int = 2) -> str:
    raw = (value or "").strip()
    if not raw or raw.lower() == "n/a":
        return ""
    return f"{float(raw):.{places}f}"


def token_cell(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw or raw.lower() == "n/a":
        return "n/a"
    return f"{float(raw):.2f}"


def is_yes(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "y", "yes", "true", "pass"}


def load_csv(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            if not (raw.get("category") or "").strip():
                continue
            category = raw["category"].strip()
            model = raw["model"].strip()
            video = VIDEO.get(model, {}) if category == "video_creation" else {}
            pass_flag = is_yes(raw.get("pass")) or model == PASS.get(category)
            row = {
                "category": category,
                "rank": str(int(raw["rank"])),
                "model": model,
                "provider": raw["provider"].strip(),
                "quality_score": str(int(float(raw["quality_score"]))),
                "cost_in_per_mtok_usd": token_cell(raw.get("cost_in_per_mtok_usd")),
                "cost_out_per_mtok_usd": token_cell(raw.get("cost_out_per_mtok_usd")),
                "usd_per_sec": money_cell(raw.get("usd_per_sec") or str(video.get("usd_per_sec") or ""), 3),
                "cost_10min_usd": money_cell(raw.get("cost_10min_usd") or str(video.get("cost_10min_usd") or ""), 2),
                "cost_1hr_usd": money_cell(raw.get("cost_1hr_usd") or str(video.get("cost_1hr_usd") or ""), 2),
                "pass": "yes" if pass_flag else "",
                "pass_to_when": (raw.get("pass_to_when") or "").strip(),
            }
            if category == "video_creation" and row["usd_per_sec"] and not row["cost_10min_usd"]:
                sec = float(row["usd_per_sec"])
                row["cost_10min_usd"] = f"{sec * 600:.2f}"
                row["cost_1hr_usd"] = f"{sec * 3600:.2f}"
            rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    grouped: dict[str, list[dict]] = {}
    order: list[str] = []
    for row in rows:
        grouped.setdefault(row["category"], []).append(row)
        if row["category"] not in order:
            order.append(row["category"])
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for i, category in enumerate(order):
            if i:
                f.write("\n")
            writer.writerows(grouped[category])


def num(value: str | None):
    raw = (value or "").strip()
    if not raw or raw.lower() == "n/a":
        return None
    return float(raw)


def snapshot(rows: list[dict]) -> dict:
    items = []
    pass_map: dict[str, str] = {}
    for r in rows:
        item = {
            "category": r["category"],
            "rank": int(r["rank"]),
            "model": r["model"],
            "provider": r["provider"],
            "quality": int(r["quality_score"]),
            "cost_in": num(r["cost_in_per_mtok_usd"]),
            "cost_out": num(r["cost_out_per_mtok_usd"]),
            "usd_per_sec": num(r["usd_per_sec"]),
            "cost_10min": num(r["cost_10min_usd"]),
            "cost_1hr": num(r["cost_1hr_usd"]),
            "note": r["pass_to_when"],
            "pass": r["pass"] == "yes",
        }
        if item["pass"]:
            pass_map[item["category"]] = item["model"]
        items.append(item)
    labels = {cat: LABELS.get(cat, cat.replace("_", " ").title()) for cat in {r["category"] for r in rows}}
    return {"rows": items, "labels": labels, "pass": pass_map, "as_of": "2026-09-04"}


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Model routing desk</title>
<style>
  :root {
    --bg: #14110d;
    --bg-2: #1c1812;
    --ink: #f3eadc;
    --muted: #b7aa96;
    --line: #3a3228;
    --accent: #d4a054;
    --accent-2: #7ea37a;
    --warn: #c45c3e;
    --card: #211c16;
    --chip: #2a241c;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; background: var(--bg); color: var(--ink);
    font: 15px/1.45 "Segoe UI", "Iowan Old Style", Georgia, sans-serif; }
  body.drop { outline: 3px dashed var(--accent); outline-offset: -8px; }
  header {
    padding: 28px 28px 12px;
    border-bottom: 1px solid var(--line);
    background: linear-gradient(180deg, #1a1611, var(--bg));
  }
  h1 { font-size: 28px; font-weight: 650; letter-spacing: -0.03em; margin: 0 0 6px; }
  .sub { color: var(--muted); font-size: 13px; }
  .share-bar {
    display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
    padding: 10px 28px 0;
  }
  .share-bar button, .share-bar label.file-btn {
    background: var(--chip); color: var(--ink); border: 1px solid var(--line);
    border-radius: 999px; padding: 6px 12px; cursor: pointer; font-size: 13px;
  }
  .share-bar button:hover, .share-bar label.file-btn:hover { border-color: var(--accent); }
  .share-bar input[type="file"] { display: none; }
  .source { color: var(--muted); font-size: 12px; margin-left: 4px; }
  .source b { color: var(--accent); font-weight: 650; }
  .err { color: var(--warn); font-size: 12px; }
  .pass-strip {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 8px;
    padding: 16px 28px 8px;
  }
  .pass-card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 10px 12px;
    cursor: pointer;
  }
  .pass-card:hover { border-color: var(--accent); }
  .pass-card small { display: block; color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }
  .pass-card b { color: var(--accent); font-size: 14px; }
  .controls {
    display: flex; flex-wrap: wrap; gap: 12px 18px; align-items: end;
    padding: 12px 28px 16px;
    position: sticky; top: 0; z-index: 5;
    background: color-mix(in srgb, var(--bg) 92%, black);
    border-bottom: 1px solid var(--line);
    backdrop-filter: blur(8px);
  }
  .cats { display: flex; flex-wrap: wrap; gap: 6px; width: 100%; }
  .cats button, .presets button {
    background: var(--chip); color: var(--ink); border: 1px solid var(--line);
    border-radius: 999px; padding: 6px 12px; cursor: pointer; font-size: 13px;
  }
  .cats button.active { background: var(--accent); color: #1a140c; border-color: var(--accent); font-weight: 650; }
  .presets button { color: var(--muted); }
  .presets button:hover { color: var(--ink); }
  label { display: flex; flex-direction: column; gap: 4px; font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; }
  select, input[type="range"] { accent-color: var(--accent); }
  select {
    background: var(--card); color: var(--ink); border: 1px solid var(--line);
    border-radius: 8px; padding: 7px 10px; min-width: 160px;
  }
  .slider-wrap { min-width: 180px; }
  .slider-wrap output { color: var(--accent); font-variant-numeric: tabular-nums; }
  .count { margin-left: auto; color: var(--muted); font-size: 13px; }
  main { padding: 8px 28px 48px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
  th { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .08em; cursor: pointer; user-select: none; }
  th:hover { color: var(--accent); }
  tr.pass td { background: color-mix(in srgb, var(--accent-2) 12%, transparent); }
  .model { font-weight: 650; }
  .provider { color: var(--muted); font-size: 12px; }
  .qbar { height: 6px; background: #342c22; border-radius: 99px; width: 88px; display: inline-block; vertical-align: middle; margin-right: 8px; }
  .qbar > i { display: block; height: 100%; border-radius: 99px; background: var(--accent); }
  .q { font-variant-numeric: tabular-nums; font-weight: 650; }
  .cost { font-variant-numeric: tabular-nums; white-space: nowrap; }
  .note { color: var(--muted); font-size: 13px; max-width: 42ch; }
  .badge { display: inline-block; font-size: 10px; letter-spacing: .08em; text-transform: uppercase;
    background: var(--accent-2); color: #10210f; border-radius: 999px; padding: 2px 7px; margin-left: 8px; font-weight: 700; }
  .empty { padding: 48px 8px; color: var(--muted); }
  footer { padding: 8px 28px 32px; color: var(--muted); font-size: 12px; max-width: 86ch; }
  footer code { color: var(--ink); }
  .is-off { display: none !important; }
  @media (max-width: 800px) {
    .note { display: none; }
    header, .controls, main, footer, .pass-strip, .share-bar { padding-left: 14px; padding-right: 14px; }
    .pass-strip { display: flex; overflow-x: auto; gap: 8px; }
    .pass-card { min-width: 168px; flex: 0 0 auto; }
  }
</style>
</head>
<body>
<header>
  <h1>Model routing desk</h1>
  <div class="sub">Pass the task to the right model. Sort quality · filter cost. CSV is the live table.</div>
</header>
<div class="share-bar">
  <label class="file-btn">Load CSV
    <input id="csvFile" type="file" accept=".csv,text/csv" />
  </label>
  <button type="button" id="saveCsv">Download CSV</button>
  <button type="button" id="saveHtml">Download HTML snapshot</button>
  <span class="source" id="source"></span>
  <span class="err" id="err"></span>
</div>
<section class="pass-strip" id="passStrip"></section>
<div class="controls">
  <div class="cats" id="cats"></div>
  <label>Sort
    <select id="sort">
      <option value="quality-desc">Quality high → low</option>
      <option value="quality-asc">Quality low → high</option>
      <option value="costin-asc">Cost in cheap → dear</option>
      <option value="costout-asc">Cost out cheap → dear</option>
      <option value="blended-asc">Blended 3:1 cheap → dear</option>
      <option value="video10-asc">Video 10 min cheap → dear</option>
      <option value="videohr-asc">Video 1 hour cheap → dear</option>
      <option value="rank-asc">Table rank</option>
    </select>
  </label>
  <label class="slider-wrap">Min quality <output id="qOut">70</output>
    <input id="minQ" type="range" min="70" max="100" value="70" />
  </label>
  <label class="slider-wrap" id="inWrap">Max $ / 1M in <output id="inOut">any</output>
    <input id="maxIn" type="range" min="0" max="10" step="0.25" value="10" />
  </label>
  <label class="slider-wrap" id="outWrap">Max $ / 1M out <output id="outOut">any</output>
    <input id="maxOut" type="range" min="0" max="50" step="0.25" value="50" />
  </label>
  <label class="slider-wrap is-off" id="vidWrap">Max $ / 10 min video <output id="vidOut">any</output>
    <input id="maxVid" type="range" min="40" max="240" step="4" value="240" />
  </label>
  <div class="presets">
    <button type="button" data-preset="reset">Reset</button>
    <button type="button" data-preset="cheap">Under $3 in</button>
    <button type="button" data-preset="mid">Under $5 in / $15 out</button>
    <button type="button" data-preset="quality">Quality 90+</button>
  </div>
  <div class="count" id="count"></div>
</div>
<main>
  <table>
    <thead>
      <tr>
        <th data-sort="rank-asc">#</th>
        <th data-sort="quality-desc">Model</th>
        <th data-sort="quality-desc">Quality</th>
        <th id="costHead">Cost</th>
        <th>When to pass</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
  <div class="empty" id="empty" hidden>Nothing matches these cost/quality filters. Loosen a slider or hit Reset.</div>
</main>
<footer>
  Token prices are USD per 1 million tokens. Video dollars assume stitched output-seconds (clips are 5–30s). Design tools bill per image, so token filters hide them.<br />
  To update: edit <code>model-routing-by-category.csv</code> (mark the first-pick with <code>pass=yes</code>). Drop the file here, or keep HTML + CSV in the same folder and serve them over http so the page reloads the CSV automatically. Download HTML snapshot to email a frozen copy that still opens without a server.
</footer>
<script type="application/json" id="snapshot">__SNAPSHOT__</script>
<script>
const DEFAULT_LABELS = {
  creative_writing: "Creative writing",
  copywriting: "Copywriting",
  coding: "Coding",
  design: "Design",
  video_creation: "Video creation",
  browser_use: "Browser use",
  agent_development: "Agent development",
  position_of_agents: "Position of agents",
};
const CSV_FIELDS = [
  "category","rank","model","provider","quality_score",
  "cost_in_per_mtok_usd","cost_out_per_mtok_usd",
  "usd_per_sec","cost_10min_usd","cost_1hr_usd","pass","pass_to_when"
];

const $ = (id) => document.getElementById(id);
const baked = JSON.parse($("snapshot").textContent);
let DATA = { rows: [], labels: {}, pass: {} };
let category = "browser_use";
let sliderCap = { in: 10, out: 50, vid: 240 };

function parseCsv(text) {
  const rows = [];
  let i = 0, field = "", row = [], inQuotes = false;
  const pushField = () => { row.push(field); field = ""; };
  const pushRow = () => {
    if (row.some((c) => c.trim() !== "")) rows.push(row);
    row = [];
  };
  while (i < text.length) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else inQuotes = false;
      } else field += c;
    } else if (c === '"') inQuotes = true;
    else if (c === ",") pushField();
    else if (c === "\n") { pushField(); pushRow(); }
    else if (c !== "\r") field += c;
    i++;
  }
  if (field.length || row.length) { pushField(); pushRow(); }
  if (!rows.length) return [];
  const headers = rows[0].map((h) => h.trim());
  return rows.slice(1).map((cols) => {
    const obj = {};
    headers.forEach((h, idx) => { obj[h] = cols[idx] ?? ""; });
    return obj;
  });
}

function num(v) {
  const s = String(v ?? "").trim();
  if (!s || s.toLowerCase() === "n/a") return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

function yes(v) {
  return /^(1|y|yes|true|pass)$/i.test(String(v ?? "").trim());
}

function labelFor(cat) {
  return DEFAULT_LABELS[cat] || cat.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase());
}

function dataFromRows(rawRows, fallbackPass) {
  const rows = [];
  const pass = {};
  const labels = {};
  for (const r of rawRows) {
    const cat = (r.category || "").trim();
    if (!cat) continue;
    const model = (r.model || "").trim();
    const usd = num(r.usd_per_sec);
    const item = {
      category: cat,
      rank: parseInt(r.rank, 10) || 0,
      model,
      provider: (r.provider || "").trim(),
      quality: parseInt(r.quality_score, 10) || 0,
      cost_in: num(r.cost_in_per_mtok_usd),
      cost_out: num(r.cost_out_per_mtok_usd),
      usd_per_sec: usd,
      cost_10min: num(r.cost_10min_usd) ?? (usd == null ? null : +(usd * 600).toFixed(2)),
      cost_1hr: num(r.cost_1hr_usd) ?? (usd == null ? null : +(usd * 3600).toFixed(2)),
      note: (r.pass_to_when || "").trim(),
      pass: yes(r.pass),
    };
    if (item.usd_per_sec == null) {
      const prev = (baked.rows || []).find((p) => p.category === cat && p.model === model);
      if (prev) {
        item.usd_per_sec = prev.usd_per_sec;
        item.cost_10min = item.cost_10min ?? prev.cost_10min;
        item.cost_1hr = item.cost_1hr ?? prev.cost_1hr;
      }
    }
    if (item.pass) pass[cat] = model;
    labels[cat] = labelFor(cat);
    rows.push(item);
  }
  Object.keys(labels).forEach((cat) => {
    if (!pass[cat] && fallbackPass && fallbackPass[cat]) pass[cat] = fallbackPass[cat];
    if (!pass[cat]) {
      const first = rows.filter((r) => r.category === cat).sort((a, b) => a.rank - b.rank)[0];
      if (first) pass[cat] = first.model;
    }
    rows.filter((r) => r.category === cat).forEach((r) => { r.pass = r.model === pass[cat]; });
  });
  return { rows, labels, pass };
}

function csvEscape(v) {
  const s = v == null ? "" : String(v);
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function moneyCell(n, places) {
  return n == null ? "" : Number(n).toFixed(places);
}

function tokenCell(n) {
  return n == null ? "n/a" : Number(n).toFixed(2);
}

function toCsv(data) {
  const lines = [CSV_FIELDS.join(",")];
  const cats = Object.keys(data.labels);
  cats.forEach((cat, i) => {
    if (i) lines.push("");
    data.rows.filter((r) => r.category === cat).sort((a, b) => a.rank - b.rank).forEach((r) => {
      const rec = {
        category: r.category,
        rank: r.rank,
        model: r.model,
        provider: r.provider,
        quality_score: r.quality,
        cost_in_per_mtok_usd: tokenCell(r.cost_in),
        cost_out_per_mtok_usd: tokenCell(r.cost_out),
        usd_per_sec: moneyCell(r.usd_per_sec, 3),
        cost_10min_usd: moneyCell(r.cost_10min, 2),
        cost_1hr_usd: moneyCell(r.cost_1hr, 2),
        pass: r.pass ? "yes" : "",
        pass_to_when: r.note,
      };
      lines.push(CSV_FIELDS.map((k) => csvEscape(rec[k])).join(","));
    });
  });
  return lines.join("\n") + "\n";
}

function download(filename, text, type) {
  const blob = new Blob([text], { type });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function money(n, d=2) {
  if (n == null || Number.isNaN(n)) return "n/a";
  return "$" + n.toFixed(d);
}

function blended(r) {
  if (r.cost_in == null || r.cost_out == null) return Infinity;
  return r.cost_in * 0.75 + r.cost_out * 0.25;
}

function setSource(label) {
  $("source").innerHTML = "Showing <b>" + label + "</b>";
  $("err").textContent = "";
}

function applyData(data, sourceLabel) {
  DATA = data;
  const cats = Object.keys(DATA.labels);
  if (!cats.includes(category)) category = cats.includes("browser_use") ? "browser_use" : cats[0];
  const qualities = DATA.rows.map((r) => r.quality);
  const ins = DATA.rows.map((r) => r.cost_in).filter((n) => n != null);
  const outs = DATA.rows.map((r) => r.cost_out).filter((n) => n != null);
  const vids = DATA.rows.map((r) => r.cost_10min).filter((n) => n != null);
  $("minQ").min = Math.min(70, ...qualities, 0);
  $("minQ").max = Math.max(100, ...qualities);
  sliderCap.in = Math.max(10, Math.ceil(Math.max(0, ...ins)));
  sliderCap.out = Math.max(50, Math.ceil(Math.max(0, ...outs)));
  sliderCap.vid = Math.max(240, Math.ceil(Math.max(0, ...vids)));
  $("maxIn").max = sliderCap.in;
  $("maxOut").max = sliderCap.out;
  $("maxVid").max = sliderCap.vid;
  if (+$("maxIn").value > sliderCap.in) $("maxIn").value = sliderCap.in;
  if (+$("maxOut").value > sliderCap.out) $("maxOut").value = sliderCap.out;
  if (+$("maxVid").value > sliderCap.vid) $("maxVid").value = sliderCap.vid;

  $("cats").innerHTML = cats.map((c) =>
    `<button type="button" data-cat="${c}">${DATA.labels[c]}</button>`
  ).join("");
  $("passStrip").innerHTML = cats.map((c) =>
    `<div class="pass-card" data-cat="${c}"><small>${DATA.labels[c]}</small><b>${DATA.pass[c] || "—"}</b></div>`
  ).join("");
  setSource(sourceLabel);
  render();
}

function render() {
  const minQ = +$("minQ").value;
  const maxIn = +$("maxIn").value;
  const maxOut = +$("maxOut").value;
  const maxVid = +$("maxVid").value;
  const sort = $("sort").value;
  const isVideo = category === "video_creation";
  const isDesign = category === "design";
  const inAny = maxIn >= sliderCap.in;
  const outAny = maxOut >= sliderCap.out;
  const vidAny = maxVid >= sliderCap.vid;

  $("qOut").textContent = minQ;
  $("inOut").textContent = inAny ? "any" : money(maxIn);
  $("outOut").textContent = outAny ? "any" : money(maxOut);
  $("vidOut").textContent = vidAny ? "any" : money(maxVid, 0);
  $("vidWrap").classList.toggle("is-off", !isVideo);
  $("inWrap").classList.toggle("is-off", isVideo || isDesign);
  $("outWrap").classList.toggle("is-off", isVideo || isDesign);
  $("costHead").textContent = isVideo ? "10 min / 1 hour" : isDesign ? "Billing" : "$ / 1M in · out";

  document.querySelectorAll(".cats button").forEach((b) => b.classList.toggle("active", b.dataset.cat === category));

  const total = DATA.rows.filter((r) => r.category === category).length;
  let list = DATA.rows.filter((r) => r.category === category && r.quality >= minQ);
  if (isVideo) {
    list = list.filter((r) => r.cost_10min == null || vidAny || r.cost_10min <= maxVid);
  } else if (!isDesign) {
    list = list.filter((r) => {
      if (r.cost_in == null) return inAny && outAny;
      return (inAny || r.cost_in <= maxIn) && (outAny || r.cost_out <= maxOut);
    });
  }

  const key = {
    "quality-desc": (a,b) => b.quality - a.quality || a.rank - b.rank,
    "quality-asc": (a,b) => a.quality - b.quality,
    "costin-asc": (a,b) => (a.cost_in ?? 999) - (b.cost_in ?? 999),
    "costout-asc": (a,b) => (a.cost_out ?? 999) - (b.cost_out ?? 999),
    "blended-asc": (a,b) => blended(a) - blended(b),
    "video10-asc": (a,b) => (a.cost_10min ?? 9999) - (b.cost_10min ?? 9999),
    "videohr-asc": (a,b) => (a.cost_1hr ?? 9999) - (b.cost_1hr ?? 9999),
    "rank-asc": (a,b) => a.rank - b.rank,
  }[sort];
  list.sort(key);

  $("count").textContent = list.length + " of " + total + " in " + (DATA.labels[category] || category);
  $("empty").hidden = list.length > 0;
  $("tbody").innerHTML = list.map((r) => {
    const qpct = Math.round((r.quality / 100) * 100);
    let cost = "";
    if (isVideo) cost = `<div class="cost">${money(r.cost_10min, 0)} / ${money(r.cost_1hr, 0)}</div><div class="provider">${money(r.usd_per_sec, 3)}/s</div>`;
    else if (isDesign) cost = `<div class="cost">per image</div>`;
    else cost = `<div class="cost">${money(r.cost_in)} in</div><div class="provider">${money(r.cost_out)} out</div>`;
    return `<tr class="${r.pass ? "pass" : ""}">
      <td>${r.rank}</td>
      <td><div class="model">${r.model}${r.pass ? '<span class="badge">Pass here</span>' : ""}</div><div class="provider">${r.provider}</div></td>
      <td><span class="qbar"><i style="width:${qpct}%"></i></span><span class="q">${r.quality}</span></td>
      <td>${cost}</td>
      <td class="note">${r.note}</td>
    </tr>`;
  }).join("");
}

function loadCsvText(text, label) {
  const parsed = parseCsv(text);
  if (!parsed.length) throw new Error("No rows in CSV");
  applyData(dataFromRows(parsed, baked.pass), label);
}

$("cats").addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (!b) return;
  category = b.dataset.cat;
  render();
});
$("passStrip").addEventListener("click", (e) => {
  const card = e.target.closest(".pass-card");
  if (!card) return;
  category = card.dataset.cat;
  render();
});
["sort","minQ","maxIn","maxOut","maxVid"].forEach((id) => $(id).addEventListener("input", render));
document.querySelectorAll("[data-preset]").forEach((b) => b.addEventListener("click", () => {
  const p = b.dataset.preset;
  if (p === "reset") {
    $("minQ").value = 70;
    $("maxIn").value = sliderCap.in;
    $("maxOut").value = sliderCap.out;
    $("maxVid").value = sliderCap.vid;
    $("sort").value = "quality-desc";
  }
  if (p === "cheap") { $("maxIn").value = Math.min(3, sliderCap.in); $("maxOut").value = Math.min(15, sliderCap.out); }
  if (p === "mid") { $("maxIn").value = Math.min(5, sliderCap.in); $("maxOut").value = Math.min(15, sliderCap.out); }
  if (p === "quality") { $("minQ").value = 90; }
  render();
}));
document.querySelectorAll("th[data-sort]").forEach((th) => th.addEventListener("click", () => {
  $("sort").value = th.dataset.sort;
  render();
}));

$("csvFile").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  try { loadCsvText(await file.text(), file.name); }
  catch (err) { $("err").textContent = err.message; }
  e.target.value = "";
});
$("saveCsv").addEventListener("click", () => {
  download("model-routing-by-category.csv", toCsv(DATA), "text/csv;charset=utf-8");
});
$("saveHtml").addEventListener("click", () => {
  const snap = JSON.stringify({
    rows: DATA.rows,
    labels: DATA.labels,
    pass: DATA.pass,
    as_of: new Date().toISOString().slice(0, 10),
  }).replace(/</g, "\\u003c");
  const html = "<!DOCTYPE html>\n" + document.documentElement.outerHTML.replace(
    /<script type="application\/json" id="snapshot">[\s\S]*?<\/script>/,
    "<script type=\"application/json\" id=\"snapshot\">" + snap + "</" + "script>"
  );
  download("model-routing-dashboard.html", html, "text/html;charset=utf-8");
});

["dragenter","dragover"].forEach((ev) => document.addEventListener(ev, (e) => {
  if (![...e.dataTransfer.items].some((it) => it.kind === "file")) return;
  e.preventDefault();
  document.body.classList.add("drop");
}));
["dragleave","drop"].forEach((ev) => document.addEventListener(ev, (e) => {
  e.preventDefault();
  document.body.classList.remove("drop");
}));
document.addEventListener("drop", async (e) => {
  const file = [...e.dataTransfer.files].find((f) => /\.csv$/i.test(f.name) || f.type === "text/csv");
  if (!file) return;
  try { loadCsvText(await file.text(), file.name); }
  catch (err) { $("err").textContent = err.message; }
});

applyData(baked, baked.as_of ? "snapshot " + baked.as_of : "embedded snapshot");

(async () => {
  const params = new URLSearchParams(location.search);
  const csvUrl = params.get("csv") || "model-routing-by-category.csv";
  if (location.protocol === "file:") return;
  try {
    const res = await fetch(csvUrl + (csvUrl.includes("?") ? "&" : "?") + "t=" + Date.now());
    if (!res.ok) return;
    loadCsvText(await res.text(), csvUrl.split("/").pop());
  } catch (_) { /* keep snapshot */ }
})();
</script>
</body>
</html>
"""


def main() -> None:
    rows = load_csv(CSV_PATH)
    csv_out = CSV_PATH
    try:
        write_csv(CSV_PATH, rows)
    except PermissionError:
        csv_out = ROOT / "model-routing-by-category.new.csv"
        write_csv(csv_out, rows)
        print("CSV locked, wrote", csv_out)
    payload = json.dumps(snapshot(rows), ensure_ascii=True).replace("<", "\\u003c")
    OUT_PATH.write_text(HTML.replace("__SNAPSHOT__", payload), encoding="utf-8")
    print("wrote", csv_out, "rows", len(rows))
    print("wrote", OUT_PATH, "bytes", OUT_PATH.stat().st_size)


if __name__ == "__main__":
    main()
