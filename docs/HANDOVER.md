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

All store modules cached `DATA_PATH` as module-level constants via `from app.config import DATA_PATH`. Calling `reload_paths()` did NOT update stores.

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

**Always use this pattern in new apps.**

### 2.5 Attachment Paths Must Be Relative

SharePoint sharing means local paths differ per user.

```python
# Save: convert to relative path from DATA_PATH
rel = str(dest.relative_to(_cfg.DATA_PATH))

# Load: prepend DATA_PATH if relative
if not p.is_absolute():
    p = _cfg.DATA_PATH / p
```

---

## 3. Dev (macOS) vs Production (Windows) Differences

### 3.1 Fonts

| Env | Qt Font | matplotlib Font |
|-----|---------|-----------------|
| macOS | Hiragino Sans 12pt | Hiragino Sans |
| Windows | Yu Gothic UI 10pt | Yu Gothic |

```python
if platform.system() == "Darwin":
    qapp.setFont(QFont("Hiragino Sans", 12))
    matplotlib.rcParams["font.family"] = "Hiragino Sans"
else:
    qapp.setFont(QFont("Yu Gothic UI", 10))
    matplotlib.rcParams["font.family"] = "Yu Gothic"
```

### 3.2 DATA_PATH Default
- **Windows**: SharePoint sync path for the team
- **macOS/Linux**: `~/app_data` (forces setup dialog)

### 3.3 File Open

```python
if platform.system() == "Darwin":
    subprocess.Popen(["open", str(path)])
elif platform.system() == "Windows":
    os.startfile(str(path))
else:
    subprocess.Popen(["xdg-open", str(path)])
```

### 3.4 External Tools
`lab_aid_extract.exe` / `lab_aid_etl.exe` are Windows-only. Disable via `data_update_service.py` `ENABLED = False` on macOS.

### 3.5 Dev Notes
- Test on mac -> build exe on Windows -> distribute via SharePoint
- Windows may break layout even if macOS works fine (font sizes, path separators)
- Use `Path` objects; never concatenate path strings

---

## 4. One-File exe (PyInstaller)

### 4.1 Build Command

```bash
pip install pyinstaller
pyinstaller bunseki.spec
# -> dist/Bunseki.exe
```

### 4.2 Spec File Essentials

```python
a = Analysis(
    ["main.py"],
    datas=[("resources/assets/splash.png", "resources/assets")],
    hiddenimports=[
        "matplotlib.backends.backend_qtagg",  # dynamically loaded
        "PySide6.QtSvg",                       # SVG icon support
        "PySide6.QtSvgWidgets",
        "openpyxl",                            # report output
    ],
    excludes=[
        "matplotlib.backends.backend_tk",      # not needed (size reduction)
        "matplotlib.backends.backend_tkagg",
        "PyQt5", "PyQt6",                      # prevent PySide6 conflicts
    ],
)
```

### 4.3 app_data Is NOT Bundled in exe
`app_data/` lives on SharePoint. Bundling would prevent per-user updates and bloat exe size.

### 4.4 Resources Compiled as Qt Resources
```
resources/assets/*.svg -> resources.qrc -> app/ui/generated/resources_rc.py
```
`resources_rc.py` is a Python file, auto-bundled in exe. No external file deployment needed.

---

## 5. Bug Fix Lessons (by severity)

### 5.1 [Critical] PySide6 + six + shibokensupport Import Conflict

**Symptom**: `AttributeError` on PyInstaller build, app won't start.
**Cause**: PySide6 patches `builtins.__import__`, conflicts with `six._SixMetaPathImporter`.

**Fix (two-stage defense)**:
```python
# Stage 1: restore __import__
import builtins
_original_import = builtins.__import__
# ... import PySide6 ...
builtins.__import__ = _original_import

# Stage 2: PyInstaller frozen environment
if getattr(sys, "frozen", False):
    try:
        import shibokensupport.feature as _sbk_feature
        _sbk_feature._mod_uses_pyside = lambda *_a, **_kw: False
    except Exception:
        pass
```

### 5.2 [Critical] Splash Screen Startup Order

**Final solution**: Two-stage splash: PyInstaller Splash (during exe extraction) + QSplashScreen (after Python starts). Do NOT use `WindowStaysOnTopHint` — splash should go behind other apps when user switches.

**Required order**:
```
1. Create QApplication (minimal imports only)
2. Show QSplashScreen (no WindowStaysOnTopHint)
3. Heavy imports (matplotlib, app.* modules)
4. Call processEvents() to keep splash rendering
5. Close splash after minimum display time (1500ms)
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

**Symptom**: Integer `0` displayed as `0.0` in tables.
**Fix**: Check `float.is_integer()` at display time and cast to int:
```python
if isinstance(val, float) and val.is_integer():
    return str(int(val))
```

### 5.6 [Important] Blocking Ops Freeze Animations

**Symptom**: Loading spinner shows but doesn't animate.
**Cause**: `subprocess.run()` blocks main thread, `QTimer` events don't process.
**Fix**: Run in `QThread`, call `processEvents()` on main thread.

### 5.7 [Important] Variable Name `app` Shadows Package `app`

**Fix**: Name QApplication variable `qapp`. Never use variable names matching package names.

### 5.8 [Important] Data Loss on Circulation Rejection

**Cause**: Two-step `update` creates intermediate inconsistency.
**Fix**: Single `update_task_field()` call for atomic write.

### 5.9 [Medium] Login Dialog Hidden Behind Windows

**Fix**: `WindowStaysOnTopHint` + `raise_()` + `activateWindow()` (all three required).

### 5.10 [Medium] Setup Dialog Not Shown for Unconfigured Users

**Fix**: Check `~/.bunseki/settings.json` existence/content, not just path existence.

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

## 7. New App Development Checklist

### 7.1 Initial Setup
1. Copy this repo as template
2. Rewrite `docs/requirements.md` for new business
3. Update `docs/CLAUDE.md` project overview
4. Update `app/config.py` paths for new app name
5. Redesign states for new workflow

### 7.2 Info to Provide Claude Code First
```
1. CLAUDE.md (coding conventions, architecture rules)
2. requirements.md (functional requirements)
3. HANDOVER.md (past bugs and lessons)
4. app/config.py (path design example)
5. main.py startup sequence (splash -> login -> main window)
```

### 7.3 Defensive Code to Include From Day One
```python
# 1. Restore builtins.__import__ (PySide6 + six conflict prevention)
# 2. shibokensupport monkey-patch (PyInstaller frozen env)
# 3. DATA_PATH via function (lazy evaluation)
# 4. QApplication var named `qapp` (avoid shadowing `app` package)
# 5. Splash -> heavy import -> login startup order
# 6. External process execution in QThread
# 7. File paths as Path objects + relative paths for storage
```

---

## 8. Tech Stack

| Item | Library | Notes |
|------|---------|-------|
| UI | PySide6 >= 6.7 | Not PyQt. License difference. |
| Data | pandas >= 2.0 | CSV read/aggregation |
| Charts | matplotlib >= 3.7 | Backend: `qtagg` (add to hiddenimports) |
| Excel I/O | openpyxl >= 3.1 | Excel read/write; use `keep_vba=True` for .xlsm |
| Build | PyInstaller | One-file mode (`--onefile`) |
| Icon gen | cairosvg + Pillow | `tools/gen_icon.py`, `tools/gen_splash.py` |

---

## 9. Development Timeline

- **2/26**: Initial commit
- **3/2**: UI creation, feature additions
- **3/3 AM**: Production path switching, SharePoint support, relative attachment paths
- **3/3 PM**: PyInstaller work begins -> DATA_PATH lazy evaluation bug fix
- **3/4 late night~morning**: PySide6+six conflict, splash, startup order, variable name collision — **hardest period**
- **3/4 AM**: Loading UI, one-file build complete

**Key lesson**: Don't delay PyInstaller build — **test exe build early**. Import order, path resolution, and library conflicts only appear in frozen environments.
