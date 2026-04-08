# CLAUDE.md

> Auto-loaded by Claude Code CLI.
> Read this file and all docs under `docs/` before starting any implementation.

---

## Project Overview

Desktop tool (PySide6) for environmental wastewater analysis workflow support.
Reads CSV/JSON from SharePoint-synced folders. Performs aggregation, threshold checks, visualization, and Excel integration via openpyxl.
Does NOT perform analysis itself — automates surrounding tasks (preparation, recording, reporting).

All paths derive from a single USERPROFILE setting (`~/.bunseki/settings.json`).
Tool settings support `%USERPROFILE%`, `%SYNC_ROOT%`, `%DATA_PATH%` variables.

Detailed specs: `docs/requirements.md`

---

## Tech Stack

| Item | Value |
|------|-------|
| Language | Python |
| UI Framework | PySide6 |
| Data Processing | pandas |
| Charts | matplotlib |
| Excel I/O | openpyxl |
| Config | pydantic-settings |
| Tests | pytest |
| Package Manager | pip + requirements.txt (no poetry) |

Use well-known libraries if adding new dependencies.

---

## Directory Structure

Structure is flexible but follow these rules:
- Do NOT write logic directly in UI files
- Separate layers: UI > UI Wrapper > Service > Core (one-way dependency)
- Organize by `[page]` and `[state]` hierarchy

---

## Coding Conventions

### Naming

```
Classes:     PascalCase          e.g. WastewaterAnalyzer
Functions:   snake_case          e.g. load_csv_data
Constants:   UPPER_SNAKE_CASE    e.g. MAX_RETRY_COUNT
Files:       snake_case.py       e.g. data_reader.py
Private:     underscore prefix   e.g. _parse_row()
```

### Python Style

- **Type hints required**: all function args and return types
- **Docstrings required**: Google-style for all public functions/classes
- **Exception handling**: never swallow exceptions; log then notify UI
- **No magic numbers**: extract to constants or config
- Formatter: black (line length: 100)
- Linter: flake8

### PySide6 Rules

- Separate UI from business logic (`ui/`, `ui_wrapper/`, `core/`, `service/` are independent)
- No service/logic code in `ui/`
- Signal/slot connections in `__init__` or `_connect_signals()`
- Heavy operations (file I/O, aggregation) must run in QThread/QRunnable — never block UI
- Widget sizing via layout managers, no hardcoded sizes

---

## Implementation Workflow (mandatory)

```
1. Before: Read related docs under docs/
2. Before: Review existing code structure before adding/changing
3. During: Implement one feature at a time
4. After:  Add unit tests for created/changed modules
5. After:  Run pytest and confirm all tests pass
```

---

## Common Mistakes (do NOT do these)

```
NG: Hardcode SharePoint paths
    -> Use sharepoint_root_path from settings.json

NG: File I/O on main thread without QThread
    -> UI freezes. Always use worker threads.

NG: Ignore pandas SettingWithCopyWarning
    -> Use .copy() explicitly

NG: Change core/ logic without tests
    -> Verify against spec with tests

NG: Read/write files directly from UI components
    -> Go through core/ modules
```

---

## Design Guidelines

- Resources define approximate layout — adjust design yourself
- White-based theme (avoid pure white)
- Text color: #333333
- Charts must be rich/interactive (no plain image paste)
- Light rounded corners
- Adequate spacing
- Don't stretch content full-width unnecessarily
- No primary/saturated colors
- Text: white or #333333
- Native-feeling UI
- Watch for font garbling in charts (JP font support)
- Show loading screen during loads
