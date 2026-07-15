# Obsidian Daily Sync (agenda.py)

Automatically generate daily work agenda notes by syncing Todoist tasks and Microsoft Exchange calendar to Obsidian.

## ✨ Features

- ✅ **Manual or Scheduled:** Run anytime or automatically M-F at 8:00 AM
- 🧪 **Connectivity Testing:** Verify Todoist & Exchange access before sync
- 🔍 **Debug Mode:** Verbose output for troubleshooting changes
- ✅ **Checked agenda sync:** Completed `- [x]` items in the agenda are marked complete in Todoist
- 📋 **Smart Task Filtering:** Overdue, today, this week (with due dates)
- 📅 **Smart Calendar Filtering:** Only relevant meetings (skips all-day, short events, noise)
- 🛡️ **Resilient:** Tasks sync even if calendar is unavailable (token expired, offline, etc.)
- 🎯 **Config-Driven:** Easy to customize for different roles/companies
- 🔐 **Secure:** Credentials stored in `.env` (not committed to git)

## What It Does

This script:

1. **Pulls Todoist tasks** organized by due date:
   - Overdue (with due dates shown in parentheses)
   - Due today
   - Due this week (with due dates shown)

2. **Fetches Exchange calendar events** with intelligent filtering:
   - Skips all-day events
   - Skips short meetings (< 30 minutes)
   - Skips noise patterns: lunch, focus time, breaks, ooo, protected time
   - Extracts Teams/Zoom links and room locations

3. **Generates meeting note stubs** with time and title

4. **Writes to Obsidian** at: `Work/Sonic/Daily/YYYY-MM-DD_Agenda.md`

The script runs independently of Obsidian — Obsidian just reads the finished file.

## �️ Resilience & Fault Tolerance

The sync process is designed to complete even when some services are unavailable:

- **Tasks always sync:** Todoist task refresh completes even if calendar is unavailable
- **Calendar is optional:** If your Microsoft Graph token expires or the connection fails, tasks still refresh and update your note
- **Checked items always complete:** Marked-complete tasks in your agenda are synced to Todoist even if calendar fetch fails
- **Graceful degradation:** The note will show `⚠️ (unavailable - token expired or offline)` for calendar events when they can't be fetched

This means you can rely on the sync to keep your tasks current throughout the day, regardless of calendar auth issues.

## �🚀 Quick Start

### 1. Install Dependencies
```bash
cd C:\Users\michael.bergman\Projects\obsidian-daily-sync
pip install -r requirements.txt
```

### 2. Configure Credentials
```bash
copy .env.example .env
```
Edit `.env` with your:
- Todoist API token (from https://todoist.com/app/settings/integrations/developer)
- Exchange email and password
- Obsidian vault path

### 3. Test Connectivity
```bash
python sync_daily_notes.py --test
```

### 4. Run Your First Sync
```bash
python sync_daily_notes.py
```

Plan tomorrow tonight:
```bash
python sync_daily_notes.py --date 2026-06-02
```

### 5. Schedule for M-F 8:00 AM
```powershell
# Open PowerShell as Administrator
.\setup-task-scheduler.ps1 -ScheduleTime "08:00"
```

## 📖 Usage

### Three Ways to Run

#### 1. Easy Interactive Menu (Recommended for Manual Runs)
```
Double-click: run-sync.bat
```

Menu options:
1. Run sync now
2. Test connectivity
3. Run sync with verbose output
4. Exit

#### 2. PowerShell Commands
```bash
# Normal sync
python sync_daily_notes.py

# Sync a specific date (useful for planning tomorrow the night before)
python sync_daily_notes.py --date 2026-06-02

# Test connectivity to Todoist & Exchange
python sync_daily_notes.py --test

# Print all raw Todoist tasks for debugging
python sync_daily_notes.py --test-tasks

# Sync with detailed debug output
python sync_daily_notes.py --verbose

# Show all options
python sync_daily_notes.py --help
```

#### 3. Automated Schedule
```powershell
# Create M-F 8:00 AM schedule (Admin PowerShell)
.\setup-task-scheduler.ps1 -ScheduleTime "08:00"

# Remove schedule
Unregister-ScheduledTask -TaskName "Obsidian Daily Sync" -Confirm:$false

# Check schedule status
Get-ScheduledTask -TaskName "Obsidian Daily Sync"
```

## 🧪 Testing & Debugging

### Connectivity Test
```bash
python sync_daily_notes.py --test
```

Checks:
- ✅ Todoist API connection and task count
- ✅ Exchange/Outlook connection and calendar access
- ✅ Obsidian vault path exists
- ✅ Daily note file exists/path correct

### Raw Todoist Task Debugging
```bash
python sync_daily_notes.py --test-tasks
```

This prints the raw Todoist task payloads returned from the API so you can verify what is being pulled in.

Expected output:
```
✅ Todoist connected! Found 23 tasks
✅ Exchange connected! Found 3 events today
✅ Vault path exists: C:\Users\michael.bergman\Command
✅ Daily note exists: ...YYYY-MM-DD_Agenda.md

✅ All systems ready! You can now run manual syncs.
```

### Verbose Output
```bash
python sync_daily_notes.py --verbose
```

Shows:
- Every step being executed
- Detailed error messages
- All data being processed
- Timing information

**Use this when:**
- Making changes to the script
- Debugging issues
- Understanding the sync process

## 📋 Configuration

Edit top of `sync_daily_notes.py` to customize:

```python
# Stakeholders and team members (shown in template guide comments)
STAKEHOLDER_NAMES = ["Gabe", "Stephen"]
DELEGATION_TARGETS = ["Thayra", "Raj", "Jim"]
COMPANY_NAME = "Sonic Automotive"

# Calendar filtering
SKIP_PATTERNS = [
    "lunch", "focus time", "break",
    "ooo", "out of office", "protected"
]
MIN_EVENT_DURATION_MINUTES = 30
```

## 📁 Output Format

```markdown
---
date: 2026-04-29
week: 2026-W18
tags: [daily, sonic]
---

# 2026-04-29 — Sonic Automotive

---

## 🎯 Director focus
[Your manual input - never overwritten]

---

## ✅ Today's tasks

### Overdue
- [ ] Fix bug (due: 2026-04-27) 🔴
- [ ] Review forecast (due: 2026-04-28)

### Due today
- [ ] Standup prep
- [ ] Approve budget

### Due this week
- [ ] Quarterly review (due: 2026-05-02)

---

## 📅 Calendar

| Time | Event | Location/Link |
|---|---|---|
| 09:00 AM | Leadership sync | Teams |
| 02:00 PM | Client call | Zoom |

---

## 📝 Meeting notes

### 09:00 AM — Leadership sync

### 02:00 PM — Client call

---

## 🚦 Blockers & next steps
[Your manual input - never overwritten]

---

## 📤 End of day
[Your manual input - never overwritten]
```

## 🎯 How It Works

### Task Filtering Logic
```
Fetches all incomplete tasks from Todoist
↓
Organizes by due date:
  • Overdue: Due before today
  • Today: Due today
  • This week: Due within 7 days
  • (Excludes: no due date, > 7 days out)
↓
Includes due dates for overdue and this-week categories
↓
Adds priority emojis (🔴 High, 🟠 Medium, 🟡 Low)
```

### Calendar Filtering Logic
```
Fetches all events for today from Exchange
↓
Filters OUT:
  ✗ All-day events
  ✗ Events < 30 minutes
  ✗ Titles matching: lunch, focus, break, ooo, protected
↓
Includes only RELEVANT meetings:
  ✓ 30+ minutes
  ✓ Has time slot (not all-day)
  ✓ Not a noise pattern
↓
Generates meeting note stubs only for included events
```

## 🛠️ Troubleshooting

### Connectivity Test Fails
```bash
python sync_daily_notes.py --test
```

**Todoist Error:**
- Get token: https://todoist.com/app/settings/integrations/developer
- Ensure token hasn't expired

**Exchange Error:**
- Verify email and password correct
- If 2FA enabled, use app password instead
- Check network access to Outlook

**Vault Path Error:**
- Check `OBSIDIAN_VAULT_PATH` in `.env`
- Ensure path exists and is accessible

**Daily Note Missing:**
- Create the daily note in Obsidian first
- Then run sync to populate it

### Sync Fails But Test Passes
```bash
# Debug with verbose output
python sync_daily_notes.py --verbose

# Check if daily note template path is correct
# Ensure note exists at: Work/Sonic/Daily/YYYY-MM-DD_Agenda.md
```

### Task Scheduler Doesn't Run
```powershell
# Enable PowerShell scripts (as Admin):
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Verify task exists:
Get-ScheduledTask | Where-Object { $_.TaskName -like "*Obsidian*" }

# Check Task Scheduler history:
# → Open Task Scheduler → Obsidian Daily Sync → History tab
```

### Python Command Not Found
- Ensure Python installed: `python --version`
- If not found, reinstall Python and check "Add to PATH"
- Try `python3` instead of `python`

## 📚 Full Documentation

- **QUICK_START.md** — 5-minute setup guide
- **MANUAL_RUN_GUIDE.md** — Running, testing, debugging in detail
- **IMPLEMENTATION.md** — Technical details of spec implementation
- **README.md** — This file

## 🔎 Clarity classification

This repository includes a reusable classification skill that maps events in a daily agenda to Clarity task codes (TSK IDs). The core functions are pure (no side effects) so they are easy to test and reuse programmatically or via the CLI.

- Package: `classification/` (pure core)
  - `classification/parsers.py` — agenda and CSV parsers (pure)
  - `classification/classifier.py` — rule-based mapping and per-event output (pure)
  - `classification/formatters.py` — markdown formatter
  - `classification/__init__.py` — public API (`classify_text`, `classify_day`, helpers)
- CLI: `classify.py` — convenience wrapper that reads agenda files, runs classification, writes one JSON file per day to `Work/Sonic/Clarity Processing`, and optionally appends a Markdown summary to the agenda file when `--append` is passed.

Programmatic example (pure):
```python
from classification import classify_text, format_summary_markdown

agenda_text = open('Work/Sonic/Daily/2026-05-28_Agenda.md', encoding='utf-8').read()
clarity_csv = open('resources/Clarity-definitions.csv', encoding='utf-8').read()

summary = classify_text(agenda_text, clarity_csv, '2026-05-28')  # pure, no IO
print(summary)
print(format_summary_markdown(summary))
```

CLI usage:
```bash
python classify.py --date 2026-05-28
python classify.py --date 2026-05-28 --append            # optional: append human-readable table to agenda
python classify.py --date 2026-05-28 --corrections-csv resources/clarity-corrections.csv
python classify.py --date 2026-05-28 --clean-legacy-clarity
python classify.py --date 2026-05-28 --output-md
python classify.py --date 2026-05-28 --clarity-csv resources/Clarity-definitions.csv --vault-path "C:\Users\michael.bergman\Command"
python classify.py --date 2026-05-28 --output-json out.json
python classify.py --start-date 2026-05-26 --end-date 2026-05-29
python classify.py --start-date 2026-05-26 --end-date 2026-05-29 --clean-legacy-clarity
```

Summary JSON shape (example):
```json
{
  "date": "YYYY-MM-DD",
  "entries": [
    {
      "task_name": "...",
      "task_code": "...",
      "project": "...",
      "hours": 2.5,
      "source_event": "Meeting 1"
    }
  ],
  "event_count": 5
}
```

Notes:
- By default the CLI does not modify agenda files.
- Use `--append` if you want a human-readable Markdown table added to the end of the agenda file.
- Use `--clean-legacy-clarity` to remove previously appended legacy Clarity summary blocks from agenda files.
- Each processed day writes a JSON file to `Work/Sonic/Clarity Processing/YYYY-MM-DD_clarity.json`.
- Use `--output-md` to also write `Work/Sonic/Clarity Processing/YYYY-MM-DD_clarity.md` for Obsidian-friendly review.
- Optional feedback loop: maintain `resources/clarity-corrections.csv` and rerun classification to force corrected mappings for matching `source_event` (and optional `date`).
- `--vault-path` is optional only when `OBSIDIAN_VAULT_PATH` is set in `.env`; otherwise `--vault-path` is required.
- Range mode (`--start-date` + `--end-date`) runs each date inclusively and returns JSON grouped by day.
- In range mode, missing agenda files are reported in `skipped_dates` and do not fail the run.
- The pure function `classify_text(agenda_text, clarity_csv_text, date_str, llm_classifier=None, corrections_csv_text=None)` accepts an optional `llm_classifier(event)` hook that should return `(project, task_name, task_code)` for a given event and optional corrections CSV text for deterministic overrides.
- No additional dependencies were added. See `classify_test.py` for a minimal example test.

TODO (Payroll Rollup):
- Add a payroll-period rollup mode that accepts `--start-date` and `--end-date` for a 15-day window.
- Produce an additional consolidated rollup JSON file for the selected payroll period (while keeping per-day files).

Corrections CSV format:
```csv
date,source_event,project,task_name,task_code,hours
2026-05-28,Team Sync,Administration,Internal Meetings,TSK001172,1.0
```
- `source_event`, `project`, `task_name`, and `task_code` are required.
- `date` is optional; include it to scope a correction to one day.
- `hours` is optional and ignored for override matching.

## 🔄 Workflow

### Daily Automated Schedule (M-F 8:00 AM)
```
Task Scheduler triggers at 8:00 AM
→ Runs run-sync.bat
→ Executes sync_daily_notes.py
→ Updates daily note with new tasks/calendar
→ You open Obsidian and refresh if needed
```

### Manual Run (Laptop Was Off)
```
You turn on laptop at 10:00 AM
→ Task Scheduler runs "start when available"
→ Or you manually run: python sync_daily_notes.py
→ Daily note updates
```

### Testing Changes
```
Make change to sync_daily_notes.py
→ Run: python sync_daily_notes.py --verbose
→ Check output for errors
→ Run again: python sync_daily_notes.py
→ Verify daily note updated correctly
```

## 🔒 Security

- ⚠️ **Never commit `.env` to git** — it contains sensitive credentials
- Consider using app passwords for Exchange (not your main password)
- Keep Todoist API token private
- `.env` is in `.gitignore` by default

## 💡 Tips

- **Manual edits preserved:** Director focus, Blockers, End of day sections are never overwritten
- **Task priorities visible:** 🔴 High, 🟠 Medium, 🟡 Low emojis show importance
- **Meeting locations extracted:** Teams links, Zoom URLs, and room names automatically included
- **Easy to customize:** Change stakeholder names, skip patterns, or output folder via config constants

## 📞 Common Scenarios

### Laptop Was Off at 8:00 AM?
No problem! Task Scheduler has "Start when available" enabled. It will run when you turn on your laptop.

Or just run manually:
```bash
python sync_daily_notes.py
```

### Updated Script, Want to Test?
```bash
python sync_daily_notes.py --verbose
```

Then run normal sync to verify:
```bash
python sync_daily_notes.py
```

### Want Different Schedule?
```powershell
# Remove old task
Unregister-ScheduledTask -TaskName "Obsidian Daily Sync" -Confirm:$false

# Create new one
.\setup-task-scheduler.ps1 -ScheduleTime "06:30"
```

### Changed Password/Token?
```bash
# Edit .env with new credentials
# Test connectivity
python sync_daily_notes.py --test

# If test passes, run sync
python sync_daily_notes.py
```

## 📊 File Structure

```
obsidian-daily-sync/
├── sync_daily_notes.py         # Main script
├── run-sync.bat                # Easy interactive menu
├── setup-task-scheduler.ps1    # Schedule setup
├── requirements.txt            # Python dependencies
├── .env.example                # Credentials template
├── .gitignore                  # Git configuration
├── README.md                   # This file
├── QUICK_START.md              # 5-minute setup
├── MANUAL_RUN_GUIDE.md         # Detailed manual run guide
├── IMPLEMENTATION.md           # Technical details
└── legacy_notes/               # Your original specs
```

## 📄 License

Personal use.
