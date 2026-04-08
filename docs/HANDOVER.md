# Handover Document — For Similar App Development

> Lessons learned from Bunseki_ccc development.
> Reference for building similar apps with Claude Code CLI / claude.ai.

**Version**: 1.2
**Last Updated**: 2026-04-08

---

## 1. Project Overview

- **Purpose**: PySide6 desktop app for environmental wastewater analysis workflow
- **Distribution**: PyInstaller one-file exe via SharePoint
- **Data sharing**: `app_data/` folder on SharePoint-synced directory, shared across users
- **Dev environment**: macOS / **Production**: Windows 10/11

---

## 2. USERPROFILE-Based Path Management (Critical)

### 2.1 Path Resolution

All paths are derived from USERPROFILE (user's home folder) at startup.

**Settings file**: `~/.bunseki/settings.json`

```json
{
  "user_profile_path": "C:\\Users\\12414"
}
```

**Derivation rules**:
| Variable | Derived Path |
|----------|-------------|
| `USERPROFILE` | `C:\Users\12414` |
| `SYNC_ROOT` | `{USERPROFILE}\トクヤマグループ` |
| `DATA_PATH` | `{USERPROFILE}\トクヤマグループ\環境分析課 - ドキュメント\app_data` |

**Resolution priority**:
1. `~/.bunseki/settings.json` key `user_profile_path`
2. Fallback: `Path.home()` (if unset, shows dialog prompting user to configure)

**Backward compatibility**: If old settings (`app_data_path`, `sync_root_path`) exist, they are used as fallback.

### 2.2 Path Variables for Tool Settings

The following variables can be used in tool settings path input fields:

| Variable | Example Expansion |
|----------|------------------|
| `%USERPROFILE%` | `C:\Users\12414` |
| `%SYNC_ROOT%` | `C:\Users\12414\トクヤマグループ` |
| `%DATA_PATH%` | `C:\Users\12414\トクヤマグループ\環境分析課 - ドキュメント\app_data` |

Expansion is handled uniformly by the `_expand_path()` function:
1. Replace app-specific variables (`%SYNC_ROOT%`, `%DATA_PATH%`)
2. Expand OS environment variables (`%USERPROFILE%` etc.) via `os.path.expandvars()`

### 2.3 app_data Directory Structure

```
DATA_PATH/
├── _common/                          # Shared (read-only usage)
│   ├── master_data/source/
│   │   ├── holder_groups.json        # Holder group master
│   │   ├── valid_samples.json        # Sample master
│   │   ├── valid_holders.json        # Holder validation
│   │   └── valid_tests.json          # Test item master
│   ├── data/lab_aid/
│   │   ├── raw/                      # Extractor output (raw CSV)
│   │   └── normalized/bunseki.csv    # ETL output (normalized)
│   └── tools/
└── bunseki/                          # App-specific data
    ├── config/
    │   ├── users.json                # User accounts (SHA-256 hashed)
    │   ├── hg_config.json            # Holder group checklist config
    │   └── data_config.json          # Column settings & tool path settings
    ├── tasks/tasks.json              # Task (workflow) data
    ├── data/anomalies.json
    ├── news/news.json
    ├── jobs/jobs.json
    └── logs/
```

### 2.4 Critical Bug: DATA_PATH Cached at Import Time

All store modules cached `DATA_PATH` as module-level constants via `from app.config import DATA_PATH`.

**Fix**: Use lazy evaluation via function calls in all stores:

```python
# BAD: fixed at module level
from app.config import DATA_PATH
TASKS_FILE = DATA_PATH / "bunseki" / "tasks" / "tasks.json"

# GOOD: reads latest DATA_PATH on each call
import app.config as _cfg
def _tasks_file():
    return _cfg.DATA_PATH / "bunseki" / "tasks" / "tasks.json"
```

### 2.5 Attachment Paths Must Be Relative

SharePoint sharing means local paths differ per user.

---

## 3. Dev (macOS) vs Production (Windows) Differences

### 3.1 Fonts

| Env | Qt Font | matplotlib Font |
|-----|---------|-----------------|
| macOS | Hiragino Sans 12pt | Hiragino Sans |
| Windows | Yu Gothic UI 10pt | Yu Gothic |

### 3.2 File Open

`_open_file()` branches by OS:
- Windows: `os.startfile()` — also supports shell associations like `.appref-ms`
- macOS: `subprocess.Popen(["open", ...])`
- Linux: `subprocess.Popen(["xdg-open", ...])`

### 3.3 External Tools
`lab_aid_extract.exe` / `lab_aid_etl.exe` are Windows-only. Disable on macOS during development.

---

## 4. One-File exe (PyInstaller)

### 4.1 Build Command

```bash
pip install pyinstaller
pyinstaller bunseki.spec
# -> dist/Bunseki.exe
```

### 4.2 Splash Screen

- Does NOT use `WindowStaysOnTopHint` (allows splash to go behind other apps when user interacts with them)
- Two-stage: PyInstaller Splash (during exe extraction) + QSplashScreen (after Python starts)

### 4.3 app_data Is NOT Bundled in exe

`app_data/` lives on SharePoint sync folder, deployed separately.

---

## 5. Bug Fix Lessons (by severity)

### 5.1 [Critical] PySide6 + six + shibokensupport Import Conflict

**Fix**: Two-stage defense: restore `builtins.__import__` + `shibokensupport.feature` monkey-patch.

### 5.2 [Critical] Splash Screen Startup Order

```
1. Create QApplication (minimal imports only)
2. Show QSplashScreen (without WindowStaysOnTopHint)
3. Heavy imports (matplotlib, app.* modules)
4. Call processEvents() to keep splash rendering
5. Close splash after minimum display time
```

### 5.3 [Important] openpyxl Destroys Macros in .xlsm Files

**Symptom**: Excel shows "file format is not correct" error after saving via openpyxl.
**Cause**: `load_workbook()` default discards VBA macros.
**Fix**: `load_workbook(path, keep_vba=True)`

### 5.4 [Important] openpyxl.utils Import Path

**Symptom**: `cannot import name 'coordinate_from_string' from 'openpyxl.utils'`
**Fix**: Import from `openpyxl.utils.cell`, not `openpyxl.utils`:
```python
from openpyxl.utils.cell import coordinate_from_string, column_index_from_string
```

### 5.5 [Important] pandas Converts Integers to Floats

**Symptom**: Integer values in CSV display as `0.0`.
**Fix**: Cast float to int at display time when the value is an integer:

```python
def _to_display(val) -> str:
    if val is None:
        return ""
    if isinstance(val, float):
        if val != val:  # NaN
            return ""
        if val.is_integer():
            return str(int(val))
        return str(val)
    s = str(val)
    return "" if s in ("nan", "None") else s
```

### 5.6 [Important] Data Loss on Circulation Rejection

**Fix**: Single `update_task_field()` call for atomic write.

### 5.7 [Medium] Blocking Ops Freeze Animations

**Fix**: Run in `QThread`, call `processEvents()` on main thread.

---

## 6. Architecture

### 6.1 Layer Structure (Strict)

```
UI (pages/, states/, dialogs/)
  |
UI Wrapper (wrapper.py) — bridges UI events and services
  |
Service (services/) — business logic
  |
Core (core/) — data persistence (JSON/CSV read/write)
```

Dependencies are **one-way only**. Lower layers must never import upper layers.

### 6.2 State Machine (Workflow)

7-state progression:
```
task_setup -> analysis_targets -> analysis -> result_entry -> result_verification -> submission -> completed
```

Each state has `app/ui/states/{state_name}/` with `state.py` (UI) + `wrapper.py` (logic bridge).

### 6.3 Config Management

| Config | Location | Purpose |
|--------|----------|---------|
| USERPROFILE | `~/.bunseki/settings.json` | Path base for all derived paths |
| Column/tool settings | `{DATA_PATH}/bunseki/config/data_config.json` | Display columns, CSV export, tool paths |
| Users | `{DATA_PATH}/bunseki/config/users.json` | Login authentication |
| HG config | `{DATA_PATH}/bunseki/config/hg_config.json` | Checklists, links per holder group |

---

## 7. Tech Stack

| Item | Library | Notes |
|------|---------|-------|
| UI | PySide6 >= 6.7 | Not PyQt. License difference. |
| Data | pandas >= 2.0 | CSV read/aggregation |
| Charts | matplotlib >= 3.7 | Backend: `qtagg` (add to hiddenimports) |
| Excel I/O | openpyxl >= 3.1 | `.xlsm` requires `keep_vba=True` |
| Build | PyInstaller | One-file mode (`--onefile`) |
