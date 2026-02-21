# Refactoring Plan: `main.py` → Modular Architecture

## Overview

Split the monolithic 1268-line `main.py` into 5 focused modules, extract 8 helper functions to eliminate ~300 lines of duplicated code, fix all typos, remove dead code, and correct two bugs.

**Target structure:**
```
main.py          (~20 lines)   — entry point only
data.py          (~60 lines)   — data loading & constants
helpers.py       (~80 lines)   — reusable utility functions
layout.py        (~170 lines)  — Dash layout components
callbacks.py     (~700 lines)  — all 21 callbacks (cleaned up)
```

---

## Step 1 — Create `helpers.py`

Extract these reusable functions to eliminate duplicated patterns:

| Function | Replaces | Occurrences |
|---|---|---|
| `get_theme(toggle)` | `theme = "cosmo" if toogle else "cyborg"` | 15 × |
| `get_period_params(period_value)` | `if period_value == 'monthly': period = 'MS' ...` | 4 × 14 lines = 56 lines |
| `get_missing_data_annotations(missing_data_dates, period)` | `missing_data_resample = ...; anno_dates = ...` | 4 × 2 lines |
| `filter_by_country(df, country_value)` | `if country_value == '': ... != ... else: ... == ...` | 12+ occurrences |
| `compute_end_date(end_date)` | `dd_end = datetime.strptime(...); the_last_date_fo_month = ...; new_end_date = ...` | 4 × 3 lines |
| `apply_date_xaxis(fig, start_date, new_end_date)` | `fig.update_layout(xaxis=dict(autorangeoptions=..., rangeslider=..., type="date"))` | 4 × 9 lines |
| `apply_standard_legend(fig, legend_fontsize)` | `fig.update_layout(legend=dict(yanchor="bottom", y=1.00, ...))` | 4 × 7 lines |
| `add_incomplete_data_annotations(fig, anno_dates, day_shift, anno_y, fontsize)` | `for dd in anno_dates: fig.add_annotation(...)` | 4 loops |

Also define:
```python
OPT_IN_DISCLAIMER = f"* {opt_in_frac*100:.1f}% users who allowed to share the telemetry data"
```
Replaces 8 copies of the same inline f-string across tab content callbacks.

---

## Step 2 — Create `data.py`

Move all data loading and global constants from `main.py` lines 20–56:

- Config reading (`configParser`)
- CSV loading (`users_df`, `sessions_df`, `entries_df`, `files_df`, `missing_data_dates`)
- Datetime conversion for all DataFrames
- `opt_in_frac` computation
- `size_label` list and `size_label_index` dict
- `SHOWED_COUNTRY_NUM = 10`
- `LIGHT_THEME = dbc.themes.COSMO`

**Remove:**
- `DARK_THEME` — defined but never used anywhere
- `init_date` — defined but never used in `main.py` (only in `preprocess_df.py` which has its own copy)

**Fix:**
- Replace `users_df.__len__()` → `len(users_df)` (anti-pattern, appears in `home_tab` definition)

---

## Step 3 — Create `layout.py`

Move all layout component definitions from `main.py` lines 62–186 and `serve_layout()` at lines 1216–1253:

- `home_tab`, `country_tab`, `users_tab`, `version_os_tab`, `file_tab`
- `date_range_button_group`, `country_selection`
- `serve_layout()` function

**Fix — stale `today`:** The module-level `today = datetime.today().date()` is set at import time and goes stale overnight. Move into `serve_layout()`:
```python
def serve_layout():
    end_date = datetime.today().strftime('%Y-%m-%d')  # fresh on every page load
    ...
```

**Fix — repeated disclaimer:** Replace 8 inline `f"...{opt_in_frac*100:.1f}%..."` f-strings with the `OPT_IN_DISCLAIMER` constant from `helpers.py`.

---

## Step 4 — Create `callbacks.py`

Move all 21 callbacks from `main.py` lines 190–1213.

### 4a — Fix duplicate function names
Two callbacks are both named `render_content` (Python allows it because the decorator registers them, but the second shadows the first as a plain function). Rename:
- Line 206: `render_content` → `render_counts_content`

### 4b — Fix `toogle` → `toggle` typo (16 occurrences)
All callback parameters and bodies: `toogle` → `toggle`

Files and lines affected:
- `toggle_theme_class` — parameter at line 279
- `update_country_map_chart`, `update_country_pie_chart`, `update_other_country_chart` — lines 292, 312, 337
- All 4 users-tab callbacks — lines 371, 498, 627, 734
- All 3 version/OS callbacks — lines 820, 856, 887
- All 5 file-tab callbacks — lines 984, 1022, 1064, 1099, 1182

### 4c — Fix `showed_linux_num` bug in `update_os_detail_pie_chart` (lines 918–920)
**Current buggy code:**
```python
if linux_sub.keys().__len__() < 3:
    showed_num = linux_sub.keys().__len__()   # ← assigns showed_num
else:
    showed_linux_num = 3                       # ← assigns showed_linux_num

for i in range(showed_linux_num):              # ← NameError if len < 3!
```
**Fix:**
```python
showed_linux_num = min(len(linux_sub), 3)
```

### 4d — Eliminate all duplicated code blocks using helpers
Each of the 4 users-tab callbacks (`update_users_unique_IP_chart`, `update_users_uuid_chart`, `update_users_active_IP_chart`, `update_users_session_chart`) reduces from ~100 lines to ~40 lines by replacing:
- Period parsing block → `get_period_params(period_value)`
- Missing data query → `get_missing_data_annotations(missing_data_dates, period)`
- Country filter → `filter_by_country(df, country_value)`
- End date computation → `compute_end_date(end_date)`
- X-axis layout → `apply_date_xaxis(fig, start_date, new_end_date)`
- Legend layout → `apply_standard_legend(fig, legend_fontsize)`
- Annotation loop → `add_incomplete_data_annotations(fig, anno_dates, day_shift, anno_y, fontsize)`

### 4e — Additional clean-ups
| Item | Fix |
|---|---|
| `update_file_shape_XY_chart` | Rename → `update_action_bar_chart` (renders `action-bar`, not file shapes) |
| `redundent` loop variable (4 occurrences) | Replace with `_` |
| `.__len__()` calls | Replace with `len()` |
| `ss` dict name in `update_file_size_bar_chart` | Rename → `size_by_type` |
| `the_last_date_fo_month` typo | Fixed inside `compute_end_date()` |

---

## Step 5 — Slim Down `main.py`

Reduce to ~20 lines:
```python
import dash
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

load_figure_template(["cosmo", "cyborg"])

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
server = app.server

from layout import serve_layout
import callbacks  # registers all callbacks as side effect

app.layout = serve_layout

if __name__ == '__main__':
    import configparser
    configParser = configparser.ConfigParser()
    configParser.read('config')
    debug_mode = configParser.get('SERVER', 'debug') == 'True'
    host_ip = configParser.get('SERVER', 'host') or 'localhost'
    port = configParser.get('SERVER', 'port') or 8050
    app.run(debug=debug_mode, host=host_ip, port=port)
```

---

## Step 6 — Remove Dead Code

| Item | Location | Action |
|---|---|---|
| `from dash import ... dash_table` | `main.py` line 2 | Remove `dash_table` from import |
| `# import dash_daq as daq` | `main.py` line 3 | Delete |
| `DARK_THEME = dbc.themes.DARKLY` | `main.py` line 30 | Delete |
| `init_date = date(2021, 12, 1)` | `main.py` line 22 | Delete |
| `# fig.update_traces(textposition='outside', ...)` | lines 321–322 | Delete |
| `# go.Bar(x=monthly_uniqueIP.keys(), ...)` | line 427 | Delete |
| `# others = versions.version.value_counts()...` | line 831 | Delete |
| `# fig.update_traces(textinfo='percent+label')` | line 838 | Delete |
| `# fig.add_trace(go.Scatter(x=[0,5], ...))` | lines 1163–1165 | Delete |
| `# margin=dict(l=0, r=0, t=0, b=0)` | line 1168 | Delete |
| Broken CSS rule `[id=tabs=content]` | `assets/main.css` line 196 | Fix to `[id=tabs-content]` or delete |

---

## Verification Checklist

After refactoring, verify:

- [ ] `python main.py` starts without errors
- [ ] All 5 main tabs navigate correctly (Home, Countries, Users, Versions and OS, Files and actions)
- [ ] Dark/light theme toggle switches all 15 figures correctly
- [ ] Date range buttons (Today, 1 month, 3 month, 6 month, 1 year, All) update the date picker
- [ ] Users tab: monthly/weekly/daily radio switch updates charts, "incomplete data" annotations appear
- [ ] Versions tab: OS detail sunburst renders (tests `showed_linux_num` bug fix)
- [ ] Country filter (South Africa, Taiwan, United States, All) filters all visible charts
- [ ] Font size inputs in Users tab update charts
- [ ] `gunicorn main:server` starts correctly (tests `server` export)

---

## Impact Summary

| Metric | Before | After |
|---|---|---|
| Lines in `main.py` | 1268 | ~700 (split across 5 files) |
| Duplicated code blocks | ~300 lines | ~0 |
| Helper functions | 0 | 8 |
| Named bugs | 1 (`showed_linux_num`) | 0 |
| Typo instances | 20+ | 0 |
| Dead imports/variables | 4 | 0 |
| Commented-out code lines | ~10 | 0 |
