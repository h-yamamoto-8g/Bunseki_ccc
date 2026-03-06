# Functional Requirements & Screen Specifications

**Version**: 1.1
**Last Updated**: 2026-03-01

---

## 1. Application-Wide Specs

### Startup & Shutdown
- Runs as standalone exe (no Python environment required)
- On startup, load `{app_data}/bunseki/config/settings.json` (if missing, show setup dialog)
- Default: fullscreen

### Window
- Single main window with tab switching
- Minimum size: 1280 x 800px
- Title bar: "Bunseki ver.{version}"

### Calculation Rule
- When calculating from `bunseki.csv::test_raw_data`, exclude string values. Use digit precision as-is from input data.

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
| settings | page | Settings | Edit settings.json, users.json | Required |
| logon | dialog | Logon | User login | Required |
| setup | dialog | Setup | User-specific data path setup | Required |
| tasks.task_ticket | state | Task Ticket | Task ticket creation | Required |
| tasks.analysis_targets | state | Analysis Targets | Sample list for analysis | Required |
| tasks.analysis | state | Analysis | Pre/post analysis info and checklists | Required |
| tasks.result_entry | state | Result Entry | Data entry | Required |
| tasks.result_verification | state | Result Verification | Data verification + anomaly detection | Required |
| tasks.submission | state | Submission | Circulation to reviewers | Required |
| tasks.completed | state | Completed | Task completed | Required |

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
  - Status breakdown by `tasks.{state}` name
- New task button (navigates to `tasks.task_ticket`)

**Actions**:
- "New Task" button -> navigate to `tasks.task_ticket`
- Double-click task row -> navigate to that task's current `tasks.{state}`

**Errors**:
- If active task not found: red warning banner + re-create button -> `tasks.task_ticket`

---

## [page] tasks

**Purpose**: Central page for task workflow management.
Initial view shows task list + new task button. Display latest 100 tasks.

**Content**:
- Task table columns: Created At, Holder Group, JOB Numbers, Status, Assignee, Last Updated, Actions
- Status filter (All / In Progress / Completed / Mine / By Assignee)
- "Load More" button for next 100 records

**Actions**:
- "New" button -> `tasks.task_ticket`
- Double-click row or Action button -> navigate to task's current state
- Filter toggle -> filter list
- "Load More" -> additional 100 records

### State Transition Flow

```
task_ticket -> analysis_targets -> analysis -> result_entry -> result_verification -> submission -> completed
```

**Navigation rules**:
- All states are navigable from any other state
- States except `task_ticket` and `analysis_targets` are editable when revisited
- `task_ticket` and `analysis_targets` require "Edit" button to enable editing; saving resets subsequent states (with warning dialog)
- After circulation to reviewer: `result_verification` and `submission` only are editable; others are read-only. Reviewer can send back to analyst for changes.

**Proxy circulation**:
- Available for non-completed tasks owned by other users
- Proxy user can advance the workflow on behalf of original user
- Proxy actions are recorded and visibly displayed

---

### [state] tasks.task_ticket

**Purpose**: Create new task ticket.

**Content**:
- Holder group dropdown
- JOB number input + add button (tag-style)
- News list (filtered by selected holder group)

**Data source**:
- File: `holder_groups.json`
- Holder groups: `holder_groups.json > items[].holder_group_name`

**Modes**:
- New: editable
- From another state: read-only, "Edit" button enables editing (saving resets subsequent states)
- After circulation: fully locked

**Actions**:
- "Create" button -> create task, navigate to `tasks.analysis_targets`
- "+" button -> add JOB number tag (default from admin settings)
- On creation: force-popup important news if not yet viewed

**Notes**:
- Task ID: `{creation_datetime}_{holder_group_code}`
- Task name: `{creation_datetime}_{holder_group_name}`
- Persist selected `holder_group_code` from `holder_groups.json::holder_group_code`

---

### [state] tasks.analysis_targets

**Purpose**: View/edit sample list for this task.

**Modes**:
- **View mode** (default): read-only
- **Edit mode**: "Edit" button enables add/delete samples (marked as edited). Editing from another state resets subsequent states with warning. Locked after circulation.

**Content**:
- Task name (header)
- Sample table: JOB Number, Sampling DateTime, Sample Name, Data Number, Median, Max, Min

**Actions**:
- "Add" -> dropdown or free-text entry (free-text creates temporary ID, no calculation)
- "Delete" -> remove sample record
- "Print" -> landscape print, fit columns to page width
- "Next" -> `tasks.analysis`
- "Back" -> `tasks.task_ticket` (view mode)

**Data source**:
- Sample table file: `bunseki.csv`
  - Filter: `holder_group_code` matches selected + `job_number` in selected list (OR) + no duplicates
  - Aggregation data: matching `valid_sample_set_code`, `trend_enabled` = true, `sample_sampling_date` within last 5 years (AND)
- Sample add dropdown file: `valid_samples.json`
  - Filter: `items[].is_active` = true, sorted by `sort_order`, display `display_name`

**Notes**:
- Persist `bunseki.csv::valid_sample_set_code` for selected samples
- If `bunseki.csv` has no data number column, default all to 0

---

### [state] tasks.analysis

**Purpose**: Provide analysis info (manuals, tools, checklists) and wait for user to complete analysis.

**Content**:
- Pre-analysis:
  - Links: analysis standards, related manuals, work tools
  - Checklist (may not exist for some analysis types)
- Post-analysis:
  - Logs: equipment, reagents (may not exist for some types)
  - Checklist (may not exist for some types)

**Actions**:
- Links: switch between web URL and file path as needed
- Log entry (same as log page; required if log exists for this analysis type)
- Checklists: checkboxes, all must be checked to proceed. Bulk-check button available. Locked after circulation.
- "Next" -> `tasks.result_entry`
- "Back" -> `tasks.analysis_targets` (view mode)

---

### [state] tasks.result_entry

**Purpose**: Data entry after analysis. (Minimal implementation for now)

**Content**:
- Message: "Please perform standard data entry."

**Actions**:
- "Launch Lab-Aid" button -> start Lab-Aid application
- "Entry Complete" -> `tasks.result_verification`

---

### [state] tasks.result_verification

**Purpose**: Verify entered data with automatic anomaly detection.

**Content**:
- Tabs per `valid_holder_display_name`, each showing:
  - Data table (read-only):

| Column | Display Name | Notes |
|--------|-------------|-------|
| valid_sample_display_name | Sample Name | holds valid_sample_set_code |
| valid_test_display_name | Test Item | holds valid_test_display_name |
| test_raw_data | Data | |
| test_unit_name | Unit | |
| - | Upper Limit | min of test_upper_limit_spec_1~4 |
| - | Lower Limit | max of test_lower_limit_spec_1~4 |
| test_judgment | Anomaly Flag | if NN: show calculated result (trend_enabled=true only); else show as-is |
| - | Trend | trend graph button |

  - Color-coded anomaly detection results
  - Highlighted anomaly flags
- Confirmation checkboxes

**Data source**:
- File: `bunseki.csv`
- Analysis result data (OR): `holder_group_code` match + `job_number` match + no duplicates
- Calculation data (AND): `holder_group_code` + `trend_enabled` = true + `valid_sample_set_code` match + `sample_sampling_date` last 5 years + numeric-only from `test_raw_data`
- Graph data (AND): same as calculation + `valid_test_code` match

**Chart requirements**:
- No font garbling (JP font support)
- No plain image paste — interactive charts
- Tooltip showing data at cursor position
- Upper/lower limits (red dashed) + mean +/- 2 sigma (orange dashed)
- Data table below chart (anomalous data highlighted)

| Column | Display | Notes |
|--------|---------|-------|
| sample_sampling_date | DateTime | |
| test_raw_data | Data | |
| test_unit_name | Unit | |
| test_judgment | Judgment | NN -> OK, else show as-is |

**Actions**:
- Trend graph button -> popup dialog
- "To Circulation" -> verify checkboxes, navigate to `tasks.submission`

---

### [state] tasks.submission

**Purpose**: Circulate results with attachments to reviewers.

**Content**:
- Attachment field (drag & drop or dialog; files saved in `{app_data}` keyed by task ID)
- Circulation flow (analyst -> reviewer(s), variable number of reviewers)
- Comment field

**Circulation**:
- No direct SMTP — use Outlook via pywin32 (create + display email, user sends)
- HTML-designed notification email (professional appearance)
- Status changes when email is created
- If anomalies exist: warning-style email with anomaly table (filtered from result_verification table)
- Items exceeding mean +/- 2 sigma: record to anomaly list for `[page] data` display. Save from `bunseki.csv`: `sample_request_number`, `sample_job_number`, `valid_sample_set_code`, `valid_holder_set_code`, `valid_test_set_code`

**Actions**:
- Role: Creator -> "Send" button (notifies reviewer, creator's work is done)
- Role: Reviewer -> "Forward" (select next reviewer) or "Complete" -> `tasks.completed`

---

### [state] tasks.completed

**Purpose**: Display task completion status.

**Content**: Completion message + summary.

**Actions**: "Back to Tasks" -> tasks page

---

## [page] data

**Purpose**: View/search historical analysis data.

**Content table**:

| Column | Display Name | Notes |
|--------|-------------|-------|
| sample_request_number | Request Number | |
| sample_sampling_date | Sampling DateTime | |
| sample_job_number | JOB Number | |
| valid_sample_display_name | Sample Name | |
| valid_holder_display_name | Holder Name | |
| valid_test_display_name | Test Item | |
| test_raw_data | Data | |
| test_reported_data | Reported Data | |
| test_unit_name | Unit | |
| test_upper_limit_spec_1~4 | Upper Limit 1~4 | |
| test_lower_limit_spec_1~4 | Lower Limit 1~4 | |
| test_judgment | Judgment | NN: show 2-sigma exceedance from saved list; non-NN takes priority |
| - | Action | Chart button |

**Filters**: date range (calendar), request number (partial), JOB number (partial), sample name (multi-select dropdown), holder name (multi-select), test item (multi-select), judgment (multi-select)

**Actions**:
- Chart button: same as `tasks.result_verification` chart
- CSV export (prompt: all data or filtered; save to Downloads; show "open folder" button)

---

## [page] news

**Purpose**: Post/view work-related announcements.

**Content**:
- Fields: checkbox, ID, posted date, title, content, target holder groups (tags), important flag, forced display period (if flagged), action (edit)
- Features: file attachment (saved in `{app_data}`), link input
- List actions: delete selected (with warning), email selected (HTML email via Outlook to all active users)

**Filters**: Standard news/bulletin board filters.

---

## [page] library

**Purpose**: Browse/manage documents attached during task circulation.

**Content**: Attachments listed by task ID.

**Filters**: holder group, date range, user.

**Actions**: Bulk download by task, open read-only, download file.

---

## [page] log

**Purpose**: Record/view equipment and reagent usage logs.

**Content**:
- Equipment log: select equipment; configurable columns per equipment (all string, variable). Config: columns, holder group code, manager, phone number. Example fields: ID, datetime, usage time (min), user, notes.
- Reagent log: configurable per holder group. Config: ID, reagent name, expiry period (monthly), notes. Display: ID, reagent name, creator, storage expiry (calculated), last creation date, expiry period, status. Yellow if expiring within 1 month, red if expired.

**Actions**: Add/edit log entries, add/delete equipment and reagents.

---

## [page] job

**Purpose**: Manage JOB numbers for analysis.

**Content**: ID, JOB number (single), start date, end date.

**Actions**: Add, delete, edit.

---

## [page] settings

**Purpose**: Edit application settings. (Admin only)

**Content**:
- settings.json edit form
- users.json edit table (add/delete/edit users)

**Configurable items**:
- User settings
- Per holder group:
  - `tasks.analysis`: standard doc links, manual links, tool links, pre/post checklists (all variable count)
  - `tasks.result_entry`: Lab-Aid link
  - Other user-configurable items (implement as appropriate)
- `{app_data}` path

**Actions**: "Save" -> write to file; "Cancel" -> discard changes.

---

## [dialog] logon

**Purpose**: User authentication on startup.

**Content**: ID, password fields.

**Actions**: "Login" -> show main window on success; error message on failure; cancel/close -> exit app.

---

## [dialog] setup

**Purpose**: Set user-specific data paths (SharePoint sync folder).

**Content**: SharePoint root path input (folder picker), output folder input (folder picker).

**Actions**: Folder picker -> OS native dialog; "Save" -> write to settings.json; "Cancel" -> discard (exit app if first-time).

---

## 4. Common UI Specs

### Sidebar
- Show only `kind=page` screens (no states or dialogs)
- Highlight current page
- Icon-based navigation

### Task State Header (`tasks.{state}`)
- State icons centered at top with left/right navigation buttons
- Active state shows its display name
- States are clickable links
- Task name on left, user name on right
- Non-task pages: greyed-out icons
- Content may be vertically scrollable
- "Next" and "Back" buttons at bottom center

### Status Bar (main window bottom)
- Shows current processing state (e.g., "Loading...", "Ready")

### Error Dialog
- Unexpected errors: `QMessageBox.critical` with stack trace
- Error log: `{app_data}/bunseki/logs/app.log`

### Error Handling
- SharePoint folder not found: red warning banner + setup button -> `setup` dialog -> reload data
- Errors: red warning banner with error details + "contact admin" message + error log download button
