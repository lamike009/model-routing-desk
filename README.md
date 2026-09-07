# Model routing desk

This is the shareable routing table for “which model do I pass this task to?”

| Copy | Where | Why |
|---|---|---|
| Private | [GitLab `agent-ops/model-routing-desk`](https://gitlab.com/vocar-studios-group/agent-ops/model-routing-desk) | Vocar ops source of record. Not in `library` (playbooks) or `live-work` (issues). |
| Public | [github.com/lamike009/model-routing-desk](https://github.com/lamike009/model-routing-desk) | Public copy you can link. Same files. |

After a push to GitLab `main`, GitLab Pages publishes the desk at the project’s **Deploy → Pages** URL (private; GitLab login required). Until Pages is up, open the HTML locally or use **Load CSV**.

| File | Role |
|---|---|
| `model-routing-by-category.csv` | **Source of truth.** Edit this. |
| `model-routing-dashboard.html` | Viewer. Reads the CSV. |
| `generate_routing_dashboard.py` | Rebuilds a frozen HTML snapshot after CSV edits. |

---

## How to update / add models

You do **not** edit the HTML by hand. You edit the CSV, then either:

1. Drop the CSV onto the open dashboard, or **Load CSV**, or
2. Keep HTML + CSV in the same folder and refresh (needs `http://`, not `file://`), or
3. Run `python generate_routing_dashboard.py` to bake a new snapshot, then commit both files.

### 1. Open the CSV

Excel, Google Sheets, or a text editor. Keep the header **exactly**:

```
category,rank,model,provider,quality_score,cost_in_per_mtok_usd,cost_out_per_mtok_usd,usd_per_sec,cost_10min_usd,cost_1hr_usd,pass,pass_to_when
```

Do not rename, reorder, or delete columns. Extra columns are ignored. Missing required columns break the upload.

Blank lines between categories are fine.

### 2. Categories (the tabs)

Use these IDs in the `category` column. Spelling must match:

| `category` | Tab label |
|---|---|
| `creative_writing` | Creative writing |
| `copywriting` | Copywriting |
| `coding` | Coding |
| `design` | Design (images; not token-billed) |
| `video_creation` | Video creation (per-second) |
| `browser_use` | Browser use |
| `agent_development` | Agent development |
| `position_of_agents` | Position of agents |

A new category is allowed: add rows with a new `category` id (`snake_case`). The dashboard will make a tab from it. Put `pass=yes` on one row in that category.

### 3. One row per model, per category

The same model can appear in several categories with different ranks, scores, and notes. That is expected.

Typical table is **12 rows per category**, ranked on **output quality in that category only**. You can have fewer or more; the dashboard counts whatever is there.

`rank` is display order evidence (1 = best quality in that category). It is **not** automatically the first-pick. First-pick is the `pass` column.

### 4. Fill the columns

| Column | What to put |
|---|---|
| `category` | One of the IDs above |
| `rank` | Integer. Unique inside that category. |
| `model` | Display name as you want it on the card. Keep it stable; changing the name is a new row as far as the desk is concerned. |
| `provider` | Anthropic, OpenAI, xAI, … |
| `quality_score` | Integer 0–100. Editorial quality **in this category**, not a global score. |
| `cost_in_per_mtok_usd` | USD per 1M input tokens. Number, two decimals. **`n/a` for image and video.** |
| `cost_out_per_mtok_usd` | USD per 1M output tokens. Same rules. |
| `usd_per_sec` | Video only. USD per output-second. Leave **blank** on token and image rows. |
| `cost_10min_usd` | Video only. Usually `usd_per_sec × 600`. Leave blank otherwise. |
| `cost_1hr_usd` | Video only. Usually `usd_per_sec × 3600`. Leave blank otherwise. |
| `pass` | `yes` on **exactly one** row per category. Blank on the rest. That is the green “Pass here” pick. |
| `pass_to_when` | One sentence: when a human should send the task to this model. |

Standing first-picks unless you deliberately change them:

- `browser_use` → Kimi K3
- `agent_development` → GPT-5.6 Sol
- `position_of_agents` → Claude Fable 5.1

### 5. Three row types (this is what “upload correctly” means)

**Token LLM** (writing, coding, browser, agents):

```
coding,5,Grok 4.6,xAI,90,2.00,6.00,,,,,Best quality-per-dollar coding; Grok Build default.
```

- Numbers in the two token-cost columns
- Three video columns **empty**
- `pass` empty unless this is the first-pick

**Image / design** (billed per image, not tokens):

```
design,1,GPT Image 2,OpenAI,95,n/a,n/a,,,,yes,Best prompt-accurate images; billed per image not tokens.
```

- `n/a` in both token-cost columns
- Video columns empty
- Dashboard will show “per image” instead of $/1M sliders

**Video** (billed per output-second; clips are short, hour cost is stitched seconds):

```
video_creation,1,MiniMax H3 Max,MiniMax / fal,94,n/a,n/a,0.080,48.00,288.00,yes,Current I2V arena leader; billed per second not tokens.
```

- `n/a` in token-cost columns
- Fill `usd_per_sec`, `cost_10min_usd`, `cost_1hr_usd`
- If you only know `$ / second`, 10 min = × 600 and 1 hour = × 3600

Wrong combinations the dashboard will mishandle:

- Token model with `n/a` costs → treated as unpriced; cost filters hide it unless sliders are “any”
- Video model with empty `$ / second` → 10 min / 1 hour show `n/a`
- Image model with token prices → token sliders appear for Design (don’t do that)
- Two `pass=yes` in one category → last one in the file wins as the strip pick; don’t

### 6. Commas in the note

If `pass_to_when` contains a comma, wrap the whole note in double quotes:

```
creative_writing,1,Claude Fable 5.1,Anthropic,96,10.00,50.00,,,,yes,"Best long-form voice, novels, essays, narrative tone."
```

A quote inside the note is written as `""`.

Save as **CSV UTF-8**. Excel “CSV (Comma delimited)” is fine if you do not let it turn `1.25` into a date.

### 7. Add a new model (checklist)

1. Pick the category (or several, one row each).
2. Insert a row. Renumber `rank` in that category so it stays 1..N with no gaps.
3. Set `quality_score` for **that category**.
4. Fill costs using the correct row type above.
5. Leave `pass` blank unless this model should become the first-pick. If it should, move `yes` off the old first-pick.
6. Write `pass_to_when`.
7. Save the CSV as `model-routing-by-category.csv` (same name, same folder as the HTML).
8. Load it in the dashboard and check:
   - the new row appears in the right tab
   - quality bar and costs look right
   - “Pass here” is still the model you intended
9. Commit and push (see below).

### 8. Change the first-pick

Set `pass` to `yes` on the new pick. Clear `pass` on the old one. One `yes` per category.

### 9. Put the update on GitLab

From this folder:

```powershell
python generate_routing_dashboard.py
git add model-routing-by-category.csv model-routing-dashboard.html
git commit -m "Update routing: <what changed>"
git push origin main
git push github main
```

`origin` is GitLab. `github` is the public copy. Push both when you refresh the table.

If Excel has the CSV open, save will fail (file locked). Close Excel, then run the generator.

Share options:

- **GitLab repo** — this project (login required)
- **Pages URL** — after the pipeline on `main` succeeds
- **One frozen file** — open the HTML, **Download HTML snapshot**, send that
- **Editable pack** — send HTML + CSV together; they Load/drop the CSV

`file://` will not auto-read a sibling CSV. Use Load/drop, or:

```powershell
python -m http.server 8765
```

then open `http://127.0.0.1:8765/model-routing-dashboard.html`.

---

## What not to do

- Do not paste models into the HTML.
- Do not keep a second CSV name as the live table (`-priced`, `.new`, Excel copies). The desk looks for `model-routing-by-category.csv`.
- Do not use rank 1 as a substitute for `pass=yes`. Browser use is the example: rank 1 is GPT-5.6 Sol, pass is Kimi K3.
- Do not put latency in this file. Quality and price only.
