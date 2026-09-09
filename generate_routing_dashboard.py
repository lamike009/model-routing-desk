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
    "video_creation": "Video",
    "browser_use": "Browser",
    "agent_development": "Agent build",
    "position_of_agents": "Orchestration",
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
    return {"rows": items, "labels": labels, "pass": pass_map, "as_of": "2026-09-07"}


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Model routing desk</title>
<style>
  :root {
    --bg: #16090c;
    --ink: #faf4f2;
    --muted: #e0c9c6;
    --line: #5a2430;
    --accent: #9a1a2c;
    --accent-hot: #c42338;
    --card: #241016;
    --chip: #2e141b;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font: 16px/1.45 "Segoe UI", system-ui, sans-serif;
  }
  body.drop { outline: 3px dashed var(--accent-hot); outline-offset: -8px; }
  a { color: var(--ink); }
  header { padding: 24px 20px 8px; max-width: 1100px; margin: 0 auto; }
  h1 { font-size: 1.6rem; font-weight: 700; letter-spacing: -0.03em; margin: 0 0 6px; }
  .sub { color: var(--muted); font-size: 0.95rem; max-width: 62ch; }
  .wrap { max-width: 1100px; margin: 0 auto; padding: 0 20px 48px; }
  .cats {
    display: flex; gap: 8px; overflow-x: auto; padding: 12px 0 4px;
    scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch;
  }
  .cats button {
    flex: 0 0 auto; scroll-snap-align: start;
    min-height: 44px; padding: 10px 16px;
    background: var(--chip); color: var(--ink);
    border: 1px solid var(--line); border-radius: 999px;
    font-size: 0.95rem; cursor: pointer;
  }
  .cats button.active {
    background: var(--accent); border-color: var(--accent-hot); color: #fff; font-weight: 700;
  }
  .blurb {
    color: var(--muted); font-size: 0.95rem; margin: 10px 0 18px; max-width: 70ch;
  }
  .estimator {
    background: var(--card); border: 1px solid var(--line);
    border-radius: 14px; padding: 16px 18px 14px; margin-bottom: 22px;
  }
  .estimator h2 { font-size: 0.8rem; text-transform: uppercase; letter-spacing: .08em;
    color: var(--muted); margin: 0 0 8px; font-weight: 650; }
  .scrub { display: grid; gap: 8px; }
  .scrub-top { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; flex-wrap: wrap; }
  .scrub-val { color: #fff; font-weight: 700; font-variant-numeric: tabular-nums; font-size: 1.15rem; }
  input[type="range"] {
    width: 100%; height: 32px; accent-color: var(--accent-hot); cursor: pointer;
  }
  .assume { color: var(--muted); font-size: 0.85rem; margin: 4px 0 12px; }
  .top5 { display: grid; gap: 8px; }
  .est {
    display: grid; grid-template-columns: minmax(0,1fr) auto;
    gap: 4px 12px; align-items: center;
    padding: 8px 4px; border-top: 1px solid var(--line);
  }
  .est:first-child { border-top: 0; }
  .est .name { font-weight: 650; }
  .est .prov { color: var(--muted); font-size: 0.8rem; }
  .est .dollars { font-variant-numeric: tabular-nums; font-weight: 750; font-size: 1.1rem; text-align: right; }
  .bar { grid-column: 1 / -1; height: 6px; background: #3a1820; border-radius: 99px; }
  .bar > i { display: block; height: 100%; border-radius: 99px; background: var(--accent-hot); }
  .pick { display: inline-block; margin-left: 6px; font-size: 0.7rem; letter-spacing: .06em;
    text-transform: uppercase; background: var(--accent); color: #fff;
    border-radius: 999px; padding: 2px 7px; font-weight: 700; vertical-align: 1px; }
  h3 { font-size: 1.05rem; margin: 8px 0 10px; }
  .list { display: grid; gap: 8px; }
  .row {
    display: grid; grid-template-columns: 2.2rem 1fr auto;
    gap: 8px 12px; background: var(--card); border: 1px solid var(--line);
    border-radius: 12px; padding: 12px 14px; align-items: start;
  }
  .row.pass { border-color: var(--accent-hot); }
  .rank { color: var(--muted); font-variant-numeric: tabular-nums; padding-top: 2px; }
  .model { font-weight: 700; }
  .prov { color: var(--muted); font-size: 0.85rem; }
  .q { font-variant-numeric: tabular-nums; font-weight: 700; text-align: right; white-space: nowrap; }
  .price { color: var(--muted); font-size: 0.85rem; text-align: right; font-variant-numeric: tabular-nums; }
  .note { grid-column: 2 / -1; color: var(--muted); font-size: 0.92rem; }
  .share { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 8px 0 0; }
  .share button, .share label.file-btn {
    min-height: 44px; padding: 8px 14px; background: var(--chip); color: var(--ink);
    border: 1px solid var(--line); border-radius: 999px; cursor: pointer; font-size: 0.9rem;
  }
  .share input[type="file"] { display: none; }
  .source { color: var(--muted); font-size: 0.85rem; }
  .err { color: #ffb4b0; font-size: 0.85rem; }
  footer { color: var(--muted); font-size: 0.85rem; margin-top: 28px; max-width: 72ch; }
  footer code { color: var(--ink); }
  @media (min-width: 800px) {
    .top5 { grid-template-columns: 1fr; }
    .row { grid-template-columns: 2.2rem 1.4fr 0.7fr 2fr; }
    .note { grid-column: auto; }
    .q, .price { text-align: left; }
  }
</style>
</head>
<body>
<header>
  <h1>Model routing desk</h1>
  <p class="sub">Twelve models per job. Scrub how much work you have; the top five show an estimated bill.</p>
</header>
<div class="wrap">
  <nav class="cats" id="cats" aria-label="Use cases"></nav>
  <p class="blurb" id="blurb"></p>

  <section class="estimator" aria-labelledby="estTitle">
    <h2 id="estTitle">Workload</h2>
    <div class="scrub">
      <div class="scrub-top">
        <label for="work" id="workLabel">How much</label>
        <div class="scrub-val" id="workOut"></div>
      </div>
      <input id="work" type="range" />
    </div>
    <p class="assume" id="assume"></p>
    <div class="top5" id="top5"></div>
  </section>

  <h3 id="listTitle">The twelve</h3>
  <div class="list" id="list"></div>

  <div class="share">
    <label class="file-btn">Load CSV<input id="csvFile" type="file" accept=".csv,text/csv" /></label>
    <button type="button" id="saveCsv">Download CSV</button>
    <button type="button" id="saveHtml">Download HTML</button>
    <span class="source" id="source"></span>
    <span class="err" id="err"></span>
  </div>
  <footer>
    Estimates use list prices and the assumptions under the slider — not a quote.
    Written jobs count 3 revisions per piece. Token prices are USD per 1 million tokens.
    Video is USD per output-second. Design is billed per image, so the slider counts units, not dollars.
  </footer>
</div>
<script type="application/json" id="snapshot">__SNAPSHOT__</script>
<script>
const DEFAULT_LABELS = {
  creative_writing: "Creative writing",
  copywriting: "Copywriting",
  coding: "Coding",
  design: "Design",
  video_creation: "Video",
  browser_use: "Browser",
  agent_development: "Agent build",
  position_of_agents: "Orchestration",
};
const BLURB = {
  creative_writing: "Long-form voice: essays, chapters, narrative. First pick is usually the most literary model, not the cheapest.",
  copywriting: "Ads, landing pages, CTAs. Conversion copy that still reads human.",
  coding: "Repos, patches, tests. Workload is lines of code in play — about a page is ~100 lines.",
  design: "Still images and layouts. These tools bill per image, not tokens.",
  video_creation: "Generated clips. Cost is stitched output-seconds (clips are short; an hour is many clips).",
  browser_use: "Live web tasks. Minutes of the agent actually browsing and extracting.",
  agent_development: "Building the agent itself — harness, tools, evals. Count discrete build tasks.",
  position_of_agents: "Orchestration: the lead that plans and hands work to specialist agents. Not the workers. Count dispatch jobs.",
};
const WORK = {
  creative_writing: {
    label: "Blogs",
    min: 5, max: 50, step: 5, value: 5,
    assume: "Each blog is 3 generation runs (draft + 2 revisions). One run ≈ 4,000 input + 2,500 output tokens (~1,800 words out).",
    tokens: (n) => ({ inn: n * 3 * 4000, out: n * 3 * 2500, runs: n * 3 }),
    format: (n) => n + " blogs",
    extra: (n) => n + " × 3 revisions = " + (n * 3) + " runs",
  },
  copywriting: {
    label: "Pieces",
    min: 5, max: 50, step: 5, value: 5,
    assume: "Each piece is 3 generation runs (draft + 2 revisions). One run ≈ 3,500 input + 1,800 output tokens.",
    tokens: (n) => ({ inn: n * 3 * 3500, out: n * 3 * 1800, runs: n * 3 }),
    format: (n) => n + " pieces",
    extra: (n) => n + " × 3 revisions = " + (n * 3) + " runs",
  },
  coding: {
    label: "Lines of code",
    min: 5000, max: 50000, step: 5000, value: 10000,
    assume: "About 16 tokens/line to read, 4 tokens/line written back (a quarter of the file changes). Here 10 pages means 10,000 lines.",
    tokens: (n) => ({ inn: n * 16, out: n * 4, runs: 1 }),
    format: (n) => n.toLocaleString() + " lines",
    extra: (n) => "≈ " + Math.round(n / 1000) + " pages",
  },
  design: {
    label: "Design units",
    min: 5, max: 50, step: 5, value: 5,
    kind: "design",
    assume: "One unit is one image or layout pass. These models are not token-billed, so the top five show quality, not a dollar estimate.",
    format: (n) => n + " units",
    extra: () => "per-image billing",
  },
  video_creation: {
    label: "Minutes of video",
    min: 1, max: 60, step: 1, value: 10,
    kind: "video",
    assume: "Minutes of finished output, billed per second. A 10-minute ask is 600 seconds of generation (usually many short clips).",
    format: (n) => n + " min",
    extra: (n) => (n * 60) + " seconds of output",
  },
  browser_use: {
    label: "Minutes of browsing",
    min: 5, max: 120, step: 5, value: 15,
    assume: "Each minute of agent browsing ≈ 10,000 input + 2,500 output tokens (page text, tools, notes).",
    tokens: (n) => ({ inn: n * 10000, out: n * 2500, runs: n }),
    format: (n) => n + " min",
    extra: () => "live web loop",
  },
  agent_development: {
    label: "Build tasks",
    min: 1, max: 20, step: 1, value: 5,
    assume: "One task is a build session: spec, implementation, tests. ≈ 40,000 input + 16,000 output tokens.",
    tokens: (n) => ({ inn: n * 40000, out: n * 16000, runs: n }),
    format: (n) => n + " tasks",
    extra: () => "build sessions",
  },
  position_of_agents: {
    label: "Dispatch jobs",
    min: 1, max: 25, step: 1, value: 5,
    assume: "One job is a plan + handoff to workers. ≈ 8,000 input + 3,000 output tokens. This is the conductor, not the specialists.",
    tokens: (n) => ({ inn: n * 8000, out: n * 3000, runs: n }),
    format: (n) => n + " jobs",
    extra: () => "orchestration",
  },
};
const CSV_FIELDS = [
  "category","rank","model","provider","quality_score",
  "cost_in_per_mtok_usd","cost_out_per_mtok_usd",
  "usd_per_sec","cost_10min_usd","cost_1hr_usd","pass","pass_to_when"
];
const CAT_ORDER = [
  "creative_writing","copywriting","coding","design",
  "video_creation","browser_use","agent_development","position_of_agents"
];

const $ = (id) => document.getElementById(id);
const baked = JSON.parse($("snapshot").textContent);
let DATA = { rows: [], labels: {}, pass: {} };
let category = "creative_writing";
const workVal = {};

function parseCsv(text) {
  const rows = [];
  let i = 0, field = "", row = [], inQuotes = false;
  const pushField = () => { row.push(field); field = ""; };
  const pushRow = () => { if (row.some((c) => c.trim() !== "")) rows.push(row); row = []; };
  while (i < text.length) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') { if (text[i + 1] === '"') { field += '"'; i++; } else inQuotes = false; }
      else field += c;
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
function yes(v) { return /^(1|y|yes|true|pass)$/i.test(String(v ?? "").trim()); }
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
      category: cat, rank: parseInt(r.rank, 10) || 0, model,
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
function moneyCell(n, places) { return n == null ? "" : Number(n).toFixed(places); }
function tokenCell(n) { return n == null ? "n/a" : Number(n).toFixed(2); }
function toCsv(data) {
  const lines = [CSV_FIELDS.join(",")];
  const cats = CAT_ORDER.filter((c) => data.labels[c]).concat(Object.keys(data.labels).filter((c) => !CAT_ORDER.includes(c)));
  cats.forEach((cat, i) => {
    if (i) lines.push("");
    data.rows.filter((r) => r.category === cat).sort((a, b) => a.rank - b.rank).forEach((r) => {
      const rec = {
        category: r.category, rank: r.rank, model: r.model, provider: r.provider,
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
function money(n) {
  if (n == null || Number.isNaN(n)) return "n/a";
  if (n < 0.01) return "$" + n.toFixed(4);
  if (n < 1) return "$" + n.toFixed(3);
  if (n < 100) return "$" + n.toFixed(2);
  return "$" + n.toFixed(0);
}
function ktok(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
  if (n >= 1000) return Math.round(n / 1000) + "k";
  return String(n);
}
function catsOf() {
  const have = Object.keys(DATA.labels);
  return CAT_ORDER.filter((c) => have.includes(c)).concat(have.filter((c) => !CAT_ORDER.includes(c)));
}
function workFor() {
  const spec = WORK[category] || WORK.creative_writing;
  const n = workVal[category] ?? spec.value;
  return { spec, n };
}
function estimate(row, spec, n) {
  if (spec.kind === "video") {
    if (row.usd_per_sec == null) return null;
    return n * 60 * row.usd_per_sec;
  }
  if (spec.kind === "design") return null;
  const t = spec.tokens(n);
  if (row.cost_in == null || row.cost_out == null) return null;
  return (t.inn / 1e6) * row.cost_in + (t.out / 1e6) * row.cost_out;
}
function listPrice(r) {
  if (r.usd_per_sec != null) return money(r.usd_per_sec) + "/s";
  if (r.cost_in == null) return "per image";
  return money(r.cost_in) + " in · " + money(r.cost_out) + " out";
}

function applyData(data, sourceLabel) {
  DATA = data;
  const cats = catsOf();
  if (!cats.includes(category)) category = cats[0];
  $("cats").innerHTML = cats.map((c) =>
    `<button type="button" data-cat="${c}" aria-pressed="false">${DATA.labels[c]}</button>`
  ).join("");
  $("source").textContent = sourceLabel;
  $("err").textContent = "";
  render();
}

function render() {
  const cats = catsOf();
  document.querySelectorAll(".cats button").forEach((b) => {
    const on = b.dataset.cat === category;
    b.classList.toggle("active", on);
    b.setAttribute("aria-pressed", on ? "true" : "false");
  });
  $("blurb").textContent = BLURB[category] || "";
  $("listTitle").textContent = "The twelve — " + (DATA.labels[category] || category);

  const spec = WORK[category] || WORK.creative_writing;
  const slider = $("work");
  if (workVal[category] == null) workVal[category] = spec.value;
  slider.min = spec.min; slider.max = spec.max; slider.step = spec.step;
  slider.value = workVal[category];
  slider.setAttribute("aria-valuemin", spec.min);
  slider.setAttribute("aria-valuemax", spec.max);
  slider.setAttribute("aria-valuenow", workVal[category]);
  $("workLabel").textContent = spec.label;
  const n = +slider.value;
  workVal[category] = n;
  $("workOut").textContent = spec.format(n) + (spec.extra ? " · " + spec.extra(n) : "");
  $("assume").textContent = spec.assume;
  if (spec.tokens) {
    const t = spec.tokens(n);
    $("assume").textContent += " This scrub ≈ " + ktok(t.inn) + " input / " + ktok(t.out) + " output tokens.";
  }

  const ranked = DATA.rows.filter((r) => r.category === category).sort((a, b) => a.rank - b.rank);
  const top = ranked.slice(0, 5);
  const costs = top.map((r) => estimate(r, spec, n));
  const finite = costs.filter((c) => c != null && c > 0);
  const maxC = finite.length ? Math.max(...finite) : 1;
  $("top5").innerHTML = top.map((r, i) => {
    const c = costs[i];
    const pct = c == null || maxC <= 0 ? 0 : Math.round((c / maxC) * 100);
    const dollars = spec.kind === "design" ? "per image" : money(c);
    return `<div class="est">
      <div><div class="name">${r.model}${r.pass ? '<span class="pick">First pick</span>' : ""}</div>
      <div class="prov">${r.provider} · quality ${r.quality}</div></div>
      <div class="dollars">${dollars}</div>
      <div class="bar" aria-hidden="true"><i style="width:${pct}%"></i></div>
    </div>`;
  }).join("");

  $("list").innerHTML = ranked.map((r) => `<article class="row${r.pass ? " pass" : ""}">
    <div class="rank">${r.rank}</div>
    <div><div class="model">${r.model}${r.pass ? '<span class="pick">First pick</span>' : ""}</div>
      <div class="prov">${r.provider}</div></div>
    <div><div class="q">${r.quality}</div><div class="price">${listPrice(r)}</div></div>
    <div class="note">${r.note}</div>
  </article>`).join("");
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
$("work").addEventListener("input", () => {
  workVal[category] = +$("work").value;
  render();
});
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
    rows: DATA.rows, labels: DATA.labels, pass: DATA.pass,
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
  } catch (_) {}
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
