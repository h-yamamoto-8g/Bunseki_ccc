# Functional Requirements & Screen Specifications

**Version**: 1.2
**Last Updated**: 2026-04-08

---

## 1. Application-Wide Specs

### Startup & Shutdown
- Runs as standalone exe (no Python environment required)
- On startup, load USERPROFILE from `~/.bunseki/settings.json` (if missing, show folder selection dialog)
- USERPROFILE is used to derive SYNC_ROOT and DATA_PATH automatically
- Splash screen is shown on startup but does NOT use WindowStaysOnTopHint (it goes behind other apps when user interacts with them)
- Default: fullscreen

### Path Resolution
- **USERPROFILE**: User's home folder (e.g., `C:\Users\12414`)
- **SYNC_ROOT**: `{USERPROFILE}\トクヤマグループ`
- **DATA_PATH**: `{USERPROFILE}\トクヤマグループ\環境分析課 - ドキュメント\app_data`
- Tool settings paths support `%USERPROFILE%`, `%SYNC_ROOT%`, `%DATA_PATH%` variables

### Window
- Single main window with tab switching
- Minimum size: 1280 x 800px
- Title bar: "Bunseki ver.{version}"

### Calculation Rule
- When calculating from `bunseki.csv::test_raw_data`, exclude string values. Use digit precision as-is from input data.

### Data Display Rules
- Display numeric values as-is from source (correct pandas float conversion)
- Integer values displayed as integers (e.g., `0` not `0.0`)
- Decimal values displayed as-is (e.g., `1.234`)
- Empty values / NaN displayed as empty string

---

## 2. Screen List

| Screen ID | Kind | Name | Description | Priority |
|-----------|------|------|-------------|----------|
| home | page | Home | Monthly schedule dashboard + today's tasks | Required |
| tasks | page | Tasks | Task creation and task list | Required |
| data | page | Data | Historical data viewer | Required |
| news | page | News | Post/view work-related announcements | Required |
| library | page | Library | Attached documents from circulation | Required |
| log | page | Log | Equipment and reagent logs | Required |
| job | page | Job | JOB number management | Required |
| settings | page | Settings | USERPROFILE, user management, tool settings | Required |
| logon | dialog | Logon | User login | Required |
| setup | dialog | Setup | USERPROFILE folder selection | Required |
| tasks.task_ticket | state | Task Ticket | Task ticket creation | Required |
| tasks.analysis_targets | state | Analysis Targets | Sample list for analysis | Required |
| tasks.analysis | state | Analysis | Pre/post analysis info and checklists | Required |
| tasks.result_entry | state | Result Entry | Data entry + input tool integration | Required |
| tasks.result_verification | state | Result Verification | Data verification + anomaly detection | Required |
| tasks.submission | state | Submission | Circulation to reviewers | Required |
| tasks.completed | state | Completed | Task completed / in-progress display | Required |

### Screen Kind Definition
- `page`: Shown in sidebar navigation
- `state`: Sub-screen within tasks workflow (not in sidebar)
- `dialog`: Modal dialog (not in sidebar)

---

## [page] home

**Purpose**: Dashboard showing monthly schedule and today's pending tasks.

**Content**:
- Monthly schedule (QWebView rendering Excel)
- Active task list (separated: own tasks vs others')
- New task button

**Actions**:
- "New Task" button -> navigate to `tasks.task_ticket`
- Double-click task row -> navigate to that task's current `tasks.{state}`

---

## [page] tasks

**Purpose**: Central page for task workflow management.
Initial view shows task list + new task button. Display latest 100 tasks.

**Content**:
- Task table columns: Created At, Holder Group, JOB Numbers, Status, Assignee, Last Updated, Actions
- Status filter (All / In Progress / Completed / Mine / By Assignee)
- "Load More" button for next 100 records

### State Transition Flow

```
task_ticket -> analysis_targets -> analysis -> result_entry -> result_verification -> submission -> completed
```

**Navigation rules**:
- All states are navigable from any other state
- `task_ticket` and `analysis_targets` require "Edit" button to enable editing
- After circulation to reviewer: `result_verification` and `submission` only are editable

---

### [state] tasks.task_ticket

**Purpose**: Create new task ticket.

**Content**:
- Holder group dropdown (`holder_groups.json`)
- JOB number input + add button (tag-style)
- News list (filtered by selected holder group)

**Notes**:
- Task ID: `{creation_datetime}_{holder_group_code}`
- Task name: `{creation_datetime}_{holder_group_name}`

---

### [state] tasks.analysis_targets

**Purpose**: View/edit sample list for this task.

**Content**:
- Sample table (column visibility, order, and display name configurable in settings)
- Calculated columns: Median, Max, Min

**Data source**:
- Sample table file: `bunseki.csv`
- Sample add dropdown file: `valid_samples.json`

---

### [state] tasks.analysis

**Purpose**: Provide analysis info (manuals, tools, checklists) and wait for user to complete analysis.

**Content**:
- Pre-analysis: links, checklists
- Post-analysis: logs, checklists

---

### [state] tasks.result_entry

**Purpose**: Data entry after analysis with input tool (Excel) integration.

**Action bar (button layout)**:
```
Lab-Aid (left) | 分析結果の読み込み, 入力ツールへ引継ぎ, データ更新, 入力チェック (center) | 一時保存 (right)
```

**Button functions**:

| Button | Function |
|--------|----------|
| Lab-Aid | Launch Lab-Aid application (from configured path; supports `.appref-ms` etc.) |
| 分析結果の読み込み | Load analysis result files (CSV/txt/PDF) using per-holder-group Python parser. Opens a matching dialog to map analysis samples to system samples, then auto-fills `input_data`. Saves file as attachment for submission. |
| 入力ツールへ引継ぎ | Write data to configured Excel file's specified sheet/cell, then open the Excel file |
| データ更新 | Reload bunseki.csv |
| 入力チェック | Compare `input_data` vs `bunseki.csv::data_raw_data`, highlight mismatched rows in red |
| 一時保存 | Save input data to state_data |

**Table**:
- Tabs per holder
- Column visibility and order configurable in settings
- Only `input_data` column is editable (yellow background)
- Enter/Tab auto-moves to next row

**Input tool handoff details**:
- Writes data for columns selected in "CSV export column settings"
- Header row is NOT written (data only)
- `.xlsm` file macros are preserved (`keep_vba=True`)
- Triggers temporary save after writing

**Data verification (入力チェック) details**:
- Compares: `input_data` (user input) vs `bunseki.csv::data_raw_data` (actual measured data)
- Rows with empty input are skipped
- Mismatched rows highlighted with light red background
- Matched rows reset to original color
- Shows result count in a dialog

---

### [state] tasks.result_verification

**Purpose**: Verify entered data with automatic anomaly detection.

**Content**:
- Tabs per `valid_holder_display_name`
- Data table (column visibility and order configurable in settings)
- Calculated columns: Upper Limit (min of specs 1-4), Lower Limit (max of specs 1-4), Anomaly Flag
- Color-coded anomaly detection results
- Trend graph button
- Confirmation checkboxes

---

### [state] tasks.submission

**Purpose**: Circulate results with attachments to reviewers.

**Circulation**:
- No direct SMTP — use Outlook via pywin32 (create + display email, user sends)
- HTML-designed notification email
- If anomalies exist: warning-style email

---

### [state] tasks.completed

**Purpose**: Display task completion status or in-progress status.

**Content**:
- When task is actually completed (`current_state == "completed"`):
  - "Task has been completed" + task name, holder group, JOB numbers, assignee, sample count, created at, completed at
- When task is still in progress:
  - "Task is in progress" + task name, holder group, JOB numbers, assignee, sample count, created at

---

## [page] data

**Purpose**: View/search historical analysis data. CSV export available.

---

## [page] news

**Purpose**: Post/view work-related announcements. File attachment and Outlook email support.

---

## [page] library

**Purpose**: Browse/manage documents attached during task circulation.

---

## [page] log

**Purpose**: Record/view equipment and reagent usage logs.

---

## [page] job

**Purpose**: Manage JOB numbers for analysis.

---

## [page] settings

**Purpose**: Edit application settings.

### USERPROFILE Section (always visible above tabs)
- Show current USERPROFILE path (read-only)
- "Change" button -> folder selection dialog
- Derived path preview:
  - Sync root: `{USERPROFILE}\トクヤマグループ`
  - Data path: `{USERPROFILE}\トクヤマグループ\環境分析課 - ドキュメント\app_data`

### Tab Structure

**User Management tab**: Add/delete/edit users

**Home Settings tab**: Home page configuration

**Task Settings tab** (sub-tabs):
- **Analysis Item Settings**: Checklists and links per holder group
- **Column Display Settings**: Column visibility, order, and display name for each table
  - Analysis Targets table
  - Result Verification table
  - Result Entry table
  - Result Entry table CSV export column config
- **Tool Settings**: Lab-Aid / input tool (Excel) path configuration

**Data Settings tab**: CSV column display configuration

### Column Display Settings Details
- Checkbox toggles column visibility
- Checked columns auto-sort to top (newly checked items added at end of checked group)
- Up/Down buttons to change display order
- Display name freely editable
- Columns with `locked` flag (e.g., `input_data`) cannot be unchecked

### Tool Settings Details

**Available variables** (with copy buttons):
- `%USERPROFILE%` -> user profile path
- `%SYNC_ROOT%` -> sync root path
- `%DATA_PATH%` -> data path

**Lab-Aid**: Application path or URL (supports `.appref-ms`, variable expansion)

**Input Tool (Excel)**:
- Excel file path (variable expansion)
- Sheet name (defaults to active sheet if unspecified)
- Start cell (defaults to A1 if unspecified)

Real-time preview below path input fields:
- Shows full path after variable expansion
- Red text warning if file does not exist

---

## [dialog] logon

**Purpose**: User authentication on startup. ID and password input.

---

## [dialog] setup (USERPROFILE)

**Purpose**: Select user profile folder on first startup.

**Content**: Explanation message + folder selection dialog (OS native)

**Behavior**: Save selected path to `~/.bunseki/settings.json`. SYNC_ROOT and DATA_PATH are derived automatically.

---

## 4. Common UI Specs

### Sidebar
- Show only `kind=page` screens (no states or dialogs)
- Highlight current page
- Icon-based navigation

### Task State Header (`tasks.{state}`)
- State icons centered at top
- States are clickable links
- Task name on left, user name on right

### Error Handling
- Unexpected errors: `QMessageBox.critical` with stack trace
- Error log: `{DATA_PATH}/bunseki/logs/app.log`
