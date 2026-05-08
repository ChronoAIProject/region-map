# Region Map — Architecture

> Owner: loning
> Original spec: 2026-05-07
> Migrated to public repo: 2026-05-08

## 1. Background

### Origin

The newmath (BEDC) project uses a region dependency graph to manage an "AI agents attacking mathematical theorems" workflow: nodes = namecert regions, edges = dependencies, color = 6-stage closure (seed → obligation → scoped → public → bridged → mature), shape = formalization level, size = proof obligation count, red border = current AI focus.

[newmath live demo](https://the-omega-institute.github.io/newmath/visualization.html)

### Hypothesis

Company epic-level goals (NyxID-OAuth-flow / Aevatar-Workflow-YAML / Voice-Avatar-Stage-A) are isomorphic to mathematical theorem attacks — both are "work units connected by dependencies, independently verifiable, monotonically advancing." So newmath's viz + closure mental model can be applied directly to company epics.

11-person company, 8 product lines, 3 GitHub orgs — no existing board gives a "whole-company epic map" across orgs and products. Region Map fills that gap.

### Goals

1. **Cross-product, cross-org unified view**: one picture shows the company's current epic state
2. **Surface cross-product dependencies**: NyxID-M0 blocking Aevatar integration is no longer hidden in heads
3. **Objective status promotion rules**: status promotion has trigger events (assignee set / RFC merged / release shipped / 30 days stable), not owner subjective judgment
4. **Adapt to future change without hardcoding**: adding a product / renaming a status / changing a color = one config line, never code

### Non-goals

- Does not replace GitHub Projects boards (epic-internal tasks / sprint cadence stay on boards)
- No real-time sync (fields manually maintained; automation comes later)
- Not a generic library (no npm package, no public API)

### Design principles

- **GitHub is the single source of truth**: every region must map to actual GitHub state (issue / PR / code directory / release / project board column). Internal docs, GTM artifacts, and conceptual aggregations without GitHub backing are NOT regions. `closure` claims must have GitHub evidence — `mature` requires a release tag AND 30 days incident-free, not just "the feature works." Every region should have a `gh_query` field so `audit.yml` can detect drift weekly.
- **Three-layer separation (config / data / code)**: business info only lives in config or data files; code never references concrete product names / region names / status copy / colors
- **Monotonic closure**: the closure field can only advance (mental model from newmath — proven theorems don't get unproven)
- **Archive after mature**: mature nodes are not updated; follow-up work opens new nodes that depend on the original
- **YAGNI**: no abstraction for imagined future needs, but every business value identified as "will change" lives in config

## 2. Architecture

### Directory structure

```
region-map/                       (public repo root)
├── _quarto.yml                   ← Quarto site config
├── visualization.qmd             ← viz source (Quarto + Cytoscape.js)
├── config.json                   ← schema config (products / closure tiers / formal levels / UI copy)
├── regions.json                  ← business data (region instances + deps)
├── assets/region-map.css         ← styles
├── tools/
│   ├── validate_config.py        ← schema validator
│   ├── validate_regions.py       ← region cross-ref validator
│   ├── audit_regions.py          ← drift detection (gh_query)
│   └── test_validate.py          ← unit tests
├── .github/workflows/
│   ├── publish.yml               ← Quarto build → GitHub Pages
│   ├── validate.yml              ← schema + tests on PR
│   └── audit.yml                 ← drift detection (Mon 09:00 SGT)
├── README.md                     ← usage + promote rules
└── ARCHITECTURE.md               ← this file
```

Self-contained: the repo has its own toolchain, depends on no external repo, can be moved or forked wholesale.

### Three-layer separation

| Layer | Files | Contents | Who edits / how often |
| --- | --- | --- | --- |
| **Code** | `visualization.qmd`, `_quarto.yml`, `assets/region-map.css` | viz engine + styles | viz behavior change (rare) |
| **Config** | `config.json` | product enum, closure tier defs (key/label/color), formal level defs (key/label/shape), focus-border rule, UI i18n copy | add product / rename status / change color / switch language (medium) |
| **Data** | `regions.json` | region instances (label/desc/closure/owner/...) + dependency edges | status promotion / add region (high, weekly) |

Code reads config + data and references no concrete business value. Renaming a region = edit `regions.json`. Adding a product = add to `config.json` `products` list + add regions in `regions.json`. Changing a status's UI copy (e.g. "已承诺" → "对外宣告") = edit `config.json` `closure_tiers[].label.zh`, code unchanged.

### Tech stack

- **Quarto** (>= 1.4): static site generator, `.qmd` → `.html`
- **Cytoscape.js 3.30.2** + **cytoscape-dagre**: graph rendering (CDN, no npm)
- **JSON**: config + data storage
- **Python 3** (stdlib only): validators + audit tooling
- **Local preview**: `quarto preview` (opens localhost)

## 3. Data schema

### `config.json`

```json
{
  "_meta": {"version": 1},
  "products": [
    {"key": "nyxid", "label": {"en": "NyxID", "zh": "NyxID"}}
  ],
  "closure_tiers": [
    {
      "key": "seed",
      "label": {"en": "Proposed", "zh": "提出"},
      "color": "#bdc3c7",
      "trigger": {"en": "issue / discussion created", "zh": "issue / discussion 已创建"}
    }
  ],
  "formal_levels": [
    {"key": "none", "shape": "ellipse", "label": {"en": "No automation", "zh": "无自动化"}}
  ],
  "focus_quarter": {
    "label": {"en": "2026 Q2 Focus", "zh": "2026 Q2 焦点"},
    "border_color": "#c0392b"
  },
  "archive_rule": {"after_mature_days": 30, "opacity": 0.35},
  "ui": {
    "title": {"en": "Chrono AI Region Map", "zh": "Chrono AI 攻坚地图"},
    "default_lang": "zh"
  }
}
```

The 6 closure tiers (in order): `seed`, `obligation`, `scoped`, `public`, `bridged`, `mature`. The 4 formal levels: `none`, `sop`, `checked`, `audited`.

### `regions.json`

```json
{
  "_meta": {"version": 1},
  "regions": {
    "NyxID-OAuth-flow": {
      "label": {"en": "OAuth Flow", "zh": "OAuth 流程"},
      "desc": {"en": "...", "zh": "..."},
      "closure": "bridged",
      "formal": "checked",
      "product": "nyxid",
      "milestone": "M0",
      "owner": "kaiweijw",
      "issue_count": 12,
      "focus": true,
      "archived": false,
      "promoted_at": {
        "obligation": "2026-02-15",
        "scoped": "2026-03-01",
        "public": "2026-03-15",
        "bridged": "2026-04-10"
      },
      "deps": ["NyxID-Reverse-Proxy"],
      "gh_query": "OAuth in:title repo:ChronoAIProject/NyxID"
    }
  }
}
```

Field reference:

| Field | Type | Meaning |
| --- | --- | --- |
| `label.{en,zh}` | string | node display label |
| `desc.{en,zh}` | string | detail panel description |
| `closure` | enum | must be a `config.closure_tiers[].key` |
| `formal` | enum | must be a `config.formal_levels[].key` |
| `product` | enum | must be a `config.products[].key` |
| `milestone` | string (free) | e.g. `M0` / `Stage-A`; not enforced (milestones rename frequently) |
| `owner` | string | GitHub username (matches `team.yaml` upstream) |
| `issue_count` | int | issue count under this region — drives node size |
| `focus` | bool | current focus region (red border) |
| `archived` | bool | archived flag (translucent) |
| `promoted_at` | object | promotion date per stage, audit trail |
| `deps` | string[] | upstream region keys (edges from dep → this region) |
| `gh_query` | string \| object (optional) | GitHub search query for `audit_regions.py` drift detection |

### Edges

Edges live inside each region's `deps` field — no separate `dependency.json`. Construction: walk all regions, for each `deps[i]` emit edge `{from: deps[i], to: regionKey}`.

### Schema validation

`tools/validate_config.py` and `tools/validate_regions.py` enforce:

- Every `regions[*].closure` is in `config.closure_tiers`
- Every `regions[*].formal` is in `config.formal_levels`
- Every `regions[*].product` is in `config.products`
- Every `regions[*].deps[*]` is a known region key
- No self-deps
- No `deps: null` (must be array or absent)

Closure-state-machine monotonicity is **not** enforced at build time (manually respected; could become a pre-commit hook).

## 4. UI design

### Visual encoding (all config-driven)

| Dimension | Source | Implementation |
| --- | --- | --- |
| Node color | `config.closure_tiers[*].color` | viz fetches config at startup, generates Cytoscape style rules dynamically |
| Node shape | `config.formal_levels[*].shape` | same |
| Node size | `regions[*].issue_count` | Cytoscape `mapData` |
| Red border | `regions[*].focus = true` + `config.focus_quarter.border_color` | Cytoscape selector |
| Translucent | `regions[*].archived = true` | Cytoscape opacity from `config.archive_rule.opacity` |
| Title / legend / detail copy | `config.ui` + `config.closure_tiers[*].label` etc. | injected at startup per `config.ui.default_lang` |

### Detail panel (right side)

Click a node:

- region en/zh label + desc (from `regions.json`)
- status: closure tier label + formal level label (composed from config + region)
- owner + product + milestone
- dependency list (upstream from `deps`, downstream computed in reverse)
- `promoted_at` timeline ("接手 02-15 → 设计完 03-01 → 已承诺 03-15 → 已集成 04-10")
- (extension point) GitHub Project / issue links via URL templates in config

## 5. Drift detection (audit)

`tools/audit_regions.py` reads each region's optional `gh_query` and compares the actual GitHub issue count against `issue_count`. Three modes:

```bash
python3 tools/audit_regions.py            # report only
python3 tools/audit_regions.py --strict   # exit 1 on drift (CI gate)
python3 tools/audit_regions.py --markdown # markdown report (issue body)
```

`gh_query` accepts a string or `{repo, label, state}` object. Regions without `gh_query` are skipped — opt-in for the regions you want CI-monitored. The `closure / formal / promoted_at / focus` judgment fields are **not** auto-derived; CI only validates schema compliance.

Workflow `audit.yml`:
- **PR mode**: `--strict`, blocks merge on drift
- **Cron** (Mon 09:00 SGT) **and `workflow_dispatch`**: posts `--markdown` report as a comment on the existing "Weekly region drift audit" issue (creates one with the `audit` label if missing)

## 6. Open questions

Carried from the original spec; revisit when relevant:

1. **Node ID convention**: `NyxID-OAuth-flow` vs `nyxid/oauth-flow`. Currently PascalCase + dash; revisit if name collisions emerge.
2. **Incident region styling**: should incident nodes be marked differently? Not done; observe in practice and add only if confusion arises.
3. **Stage-stuck alert**: should viz overlay "stuck in obligation for 21 days"? `promoted_at` already records the data; UI overlay is a future iteration.
4. **Status promotion authority**: `seed → obligation → scoped` by owner; `scoped → public` needs strategic approval; `public →` back to owner. Captured in README; not enforced by viz.
5. **v2 supersedes v1**: two mature nodes coexist; v2 going mature does not modify v1. No "superseded" state.
6. **Edge weight**: currently constant 1. If "PR-count-per-edge" weighting becomes useful, the `deps` field upgrades to an object-array (backward compatible).
7. **Auto-promote from GitHub events**: currently manual. Future hook: when an assignee is set on the linked issue, propose a `seed → obligation` promote in a PR.
