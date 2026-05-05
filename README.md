# Obsidian Daily Sync (agenda.py)

Automatically generate daily work agenda notes by syncing Todoist tasks and Microsoft Exchange calendar to Obsidian.

## ✨ Features

- ✅ **Manual or Scheduled:** Run anytime or automatically M-F at 8:00 AM
- 🧪 **Connectivity Testing:** Verify Todoist & Exchange access before sync
- 🔍 **Debug Mode:** Verbose output for troubleshooting changes
- 📋 **Smart Task Filtering:** Overdue, today, this week (with due dates)
- 📅 **Smart Calendar Filtering:** Only relevant meetings (skips all-day, short events, noise)
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

## 🚀 Quick Start

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

# Test connectivity to Todoist & Exchange
python sync_daily_notes.py --test

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
