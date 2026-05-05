# Manual Run & Testing Guide

## 🚀 Three Ways to Run

### Option 1: Easy Interactive Menu (Recommended)
**Double-click:** `run-sync.bat`

Opens an interactive menu with options:
```
1. Run sync now
2. Test connectivity  
3. Run sync with verbose output
4. Exit
```

### Option 2: PowerShell Commands
Open PowerShell in the project directory and run:

```powershell
# Normal sync
python sync_daily_notes.py

# Test connectivity to Todoist & Exchange
python sync_daily_notes.py --test

# Sync with detailed debug output
python sync_daily_notes.py --verbose

# Show all options
python sync_daily_notes.py --help
```

### Option 3: Task Scheduler
Set up automatic M-F 8:00 AM execution:

```powershell
# Open PowerShell as Administrator and run:
cd "C:\Users\michael.bergman\Projects\obsidian-daily-sync"
.\setup-task-scheduler.ps1 -ScheduleTime "08:00"

# To change time (e.g., 6:30 AM):
.\setup-task-scheduler.ps1 -ScheduleTime "06:30"
```

---

## 🧪 Testing Connectivity

Before first run, test that everything is connected:

```powershell
python sync_daily_notes.py --test
```

### Expected Output
```
======================================================================
🧪 CONNECTIVITY TEST
======================================================================

Testing Todoist API...
  ✅ Todoist connected! Found 23 tasks

Testing Exchange/Outlook...
  ✅ Exchange connected! Found 3 events today

Testing Obsidian vault...
  ✅ Vault path exists: C:\Users\michael.bergman\Command

Testing daily note file...
  ✅ Daily note exists: C:\Users\michael.bergman\Command\Work\Sonic\Daily\2026-04-29_Agenda.md

======================================================================
📊 TEST SUMMARY
======================================================================

✅ Passed:   4
❌ Failed:   0
⚠️  Warnings: 0

✅ All systems ready! You can now run manual syncs.
```

### Troubleshooting

**Todoist Error:**
```
  ❌ TODOIST_API_TOKEN not set in .env
```
→ Get token from: https://todoist.com/app/settings/integrations/developer

**Exchange Error:**
```
  ❌ Exchange account not initialized (check credentials)
```
→ Verify `EXCHANGE_EMAIL` and `EXCHANGE_PASSWORD` in `.env`  
→ If using 2FA, use app password instead

**Vault Not Found:**
```
  ❌ Vault path not found: C:\Users\michael.bergman\Command
```
→ Check `OBSIDIAN_VAULT_PATH` in `.env`

**Daily Note Missing:**
```
  ⚠️  Daily note not found (will be created on first sync)
```
→ This is OK! Create a daily note in Obsidian first, then sync will update it.

---

## 🔍 Debugging Updates

When making changes to the script, test with verbose output:

```powershell
python sync_daily_notes.py --verbose
```

This shows:
- Every step being executed
- Time spent on each operation
- Detailed error messages
- All data being processed

### Example Workflow for Debugging

1. **Make a change** to `sync_daily_notes.py`
2. **Test with verbose:**
   ```powershell
   python sync_daily_notes.py --verbose
   ```
3. **Check connectivity:**
   ```powershell
   python sync_daily_notes.py --test
   ```
4. **Run full sync:**
   ```powershell
   python sync_daily_notes.py
   ```

---

## 📅 Schedule Management

### Check Scheduled Task Status
```powershell
# List all Obsidian tasks
Get-ScheduledTask | Where-Object { $_.TaskName -like "*Obsidian*" }

# View detailed task info
Get-ScheduledTask -TaskName "Obsidian Daily Sync" | Format-List *

# See last run result
Get-ScheduledTaskInfo -TaskName "Obsidian Daily Sync"
```

### Remove Scheduled Task
```powershell
Unregister-ScheduledTask -TaskName "Obsidian Daily Sync" -Confirm:$false
```

### Edit Scheduled Task Manually
1. Open **Task Scheduler** (search in Windows)
2. Find "Obsidian Daily Sync"
3. Right-click → **Properties**
4. Edit **Triggers**, **Actions**, or **Settings**

---

## 🛠️ Common Scenarios

### My Laptop Was Off at 8:00 AM
**No Problem!** Just run manually:
```powershell
python sync_daily_notes.py
```

Task Scheduler has "Start when available" enabled, so it will catch up if you turn on your laptop later in the day.

### I Made Changes to the Script
**Test them immediately:**
```powershell
python sync_daily_notes.py --verbose
```

Then re-run the sync to verify:
```powershell
python sync_daily_notes.py
```

### I Changed My Password/Token
1. Edit `.env` with new credentials
2. Test connectivity:
   ```powershell
   python sync_daily_notes.py --test
   ```
3. Run sync if test passes:
   ```powershell
   python sync_daily_notes.py
   ```

### I Want to Run at a Different Time
```powershell
# Remove old task
Unregister-ScheduledTask -TaskName "Obsidian Daily Sync" -Confirm:$false

# Create new one with different time
.\setup-task-scheduler.ps1 -ScheduleTime "07:00"
```

### I Want to Run on Weekends Too
```powershell
# Open Task Scheduler manually
# Edit "Obsidian Daily Sync" task
# In Triggers → Edit → Change to "Daily" instead of "Weekly"
```

---

## 📊 Task Scheduler Behavior

Once set up for M-F at 8:00 AM:

| Scenario | Behavior |
|----------|----------|
| Laptop ON at 8:00 AM | ✅ Runs automatically |
| Laptop OFF at 8:00 AM | Runs when you turn it on |
| Manually ran at 7:00 AM | 8:00 AM run still happens |
| Network down at 8:00 AM | Skips (due to RunOnlyIfNetworkAvailable) |
| Task runs, but fails | Logs error; task retries on next schedule |

---

## 💾 Backup Notes

The script preserves all your manual edits to:
- 🎯 Director focus section
- 🚦 Blockers & next steps section  
- 📤 End of day section

These are never overwritten by automated syncing!

---

## 🎯 Quick Command Reference

```bash
# Normal run
python sync_daily_notes.py

# Test only
python sync_daily_notes.py --test

# Debug/verbose
python sync_daily_notes.py --verbose

# Help menu
python sync_daily_notes.py --help

# Interactive menu (Windows)
run-sync.bat

# Create schedule (PowerShell as Admin)
.\setup-task-scheduler.ps1 -ScheduleTime "08:00"

# Check schedule status (PowerShell)
Get-ScheduledTask -TaskName "Obsidian Daily Sync"
```

---

## ❓ FAQ

**Q: Can I run the script while Obsidian is open?**
A: Yes! The script reads/writes directly to files, independent of Obsidian. Just reload the file in Obsidian if needed.

**Q: What if the sync fails?**
A: Your daily note is backed up. Errors are logged. Try again or check connectivity with `--test` mode.

**Q: How do I know if the scheduled task ran?**
A: Check your daily note — it will be updated with the latest tasks/calendar. Or check Task Scheduler history in Event Viewer.

**Q: Can I customize the schedule?**
A: Yes! Create a new schedule or edit the existing one in Task Scheduler (search "Task Scheduler" in Windows).

**Q: My daily note has manual sections that keep getting overwritten**
A: Only these are auto-updated:
- `{{overdue_tasks}}`
- `{{due_today_tasks}}`
- `{{due_this_week_tasks}}`
- `{{calendar_table}}`
- `{{meeting_notes}}`

Everything else (Director focus, Blockers, End of day) stays as-is.
