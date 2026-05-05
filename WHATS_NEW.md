# What's New: Manual Run & Testing Features

## ✅ What Was Added

### 1. Connectivity Testing 🧪
**Command:** `python sync_daily_notes.py --test`

Tests:
- ✅ Todoist API connection (shows task count)
- ✅ Exchange/Outlook connection (shows event count)
- ✅ Obsidian vault path exists
- ✅ Daily note file path correct

Perfect for debugging setup issues before first run!

### 2. Interactive Runner Menu 🖱️
**File:** `run-sync.bat`

Double-click it for an easy menu:
```
1. Run sync now
2. Test connectivity
3. Run sync with verbose output
4. Exit
```

No command line needed!

### 3. Command-Line Arguments
**Usage:** `python sync_daily_notes.py [OPTIONS]`

Available options:
```
--test              # Test connectivity only
--verbose           # Detailed debug output
--no-backup         # Skip creating note backup
--help              # Show all options
```

### 4. Verbose Debug Mode 🔍
**Command:** `python sync_daily_notes.py --verbose`

Shows:
- Every step being executed
- Detailed error messages
- All data being processed
- Timing information

Great for:
- Debugging script changes
- Understanding what's happening
- Troubleshooting issues

### 5. M-F Weekday Schedule 📅
**Updated:** `setup-task-scheduler.ps1`

Now creates a **weekday-only** schedule:
- Runs M-F (skips Saturday/Sunday)
- Default 8:00 AM (customizable)
- "Start when available" enabled (catches up if laptop was off)

```powershell
.\setup-task-scheduler.ps1 -ScheduleTime "08:00"
```

### 6. Enhanced Documentation 📚
New guides:
- **MANUAL_RUN_GUIDE.md** — Complete manual run & debugging guide
- **Updated QUICK_START.md** — Now covers manual runs
- **Updated README.md** — Documents all new features

## 🎯 Three Ways to Run

### 1️⃣ Interactive Menu (Easiest)
```
Double-click run-sync.bat
```
Choose from: Sync, Test, Debug, Exit

### 2️⃣ Command Line (PowerShell/Terminal)
```bash
python sync_daily_notes.py              # Run sync
python sync_daily_notes.py --test       # Test connectivity
python sync_daily_notes.py --verbose    # Debug output
```

### 3️⃣ Automated (Task Scheduler)
```powershell
.\setup-task-scheduler.ps1 -ScheduleTime "08:00"
```
Runs M-F at 8:00 AM automatically

## 🧪 Testing Workflow

```bash
# Step 1: Test connectivity
python sync_daily_notes.py --test

# Step 2: If test passes, run sync
python sync_daily_notes.py

# Step 3: For debugging, use verbose
python sync_daily_notes.py --verbose

# Step 4: Once verified, schedule it
.\setup-task-scheduler.ps1 -ScheduleTime "08:00"
```

## 🐛 Debugging Your Changes

When you modify `sync_daily_notes.py`:

```bash
# Test with verbose output to see every step
python sync_daily_notes.py --verbose

# Check connectivity hasn't broken
python sync_daily_notes.py --test

# Run full sync to verify
python sync_daily_notes.py

# Then double-check the output in Obsidian
```

## 📊 Code Changes Made

### sync_daily_notes.py
- ✅ Added `argparse` for CLI arguments
- ✅ Added `test_connectivity()` method with detailed diagnostics
- ✅ Added `--test`, `--verbose`, `--help` support
- ✅ Enhanced logging configuration
- ✅ Improved main function with argument handling

### run-sync.bat
- ✅ Added interactive menu (1-4 options)
- ✅ User-friendly interface
- ✅ No command-line knowledge needed

### setup-task-scheduler.ps1
- ✅ Changed from daily to weekly (M-F only)
- ✅ Enhanced visual feedback
- ✅ Better error handling
- ✅ Admin check at start
- ✅ Improved documentation

### Documentation
- ✅ MANUAL_RUN_GUIDE.md (comprehensive manual run guide)
- ✅ Updated QUICK_START.md
- ✅ Updated README.md (now 300+ lines of detail)
- ✅ This document!

## 🚀 Quick Start with New Features

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
copy .env.example .env
# Edit .env with your credentials

# 3. Test
python sync_daily_notes.py --test

# 4. Run manually (choose one)
run-sync.bat                           # Interactive menu
python sync_daily_notes.py             # Command line

# 5. Schedule for M-F 8:00 AM
.\setup-task-scheduler.ps1 -ScheduleTime "08:00"
```

That's it! ✨

## 💡 Key Benefits

✅ **No script runs if laptop is off** — Task Scheduler will catch up when you turn it on

✅ **Easy debugging** — `--test` and `--verbose` flags make troubleshooting simple

✅ **Manual override anytime** — Run `run-sync.bat` or `python sync_daily_notes.py` whenever

✅ **Weekend protection** — Won't run on Saturday/Sunday (weekday schedule only)

✅ **Config-driven** — Easy to customize for different setups

✅ **Well documented** — Multiple guides for different workflows

## 📝 Notes

- The batch file menu is Windows-only, but Python commands work everywhere
- Test connectivity before relying on the scheduled task
- Verbose mode is great for first-time debugging
- All manual sections in your daily note are preserved (never overwritten)
- The task backs off on network errors automatically

## 🎓 Learning Resources

- **First time?** → Read QUICK_START.md
- **Want to run manually?** → Read MANUAL_RUN_GUIDE.md
- **Debugging issues?** → Run `python sync_daily_notes.py --test`
- **Want details?** → See README.md or MANUAL_RUN_GUIDE.md FAQ

---

**Summary:** You can now run the script manually anytime via `run-sync.bat` or command line, test connectivity with `--test`, debug with `--verbose`, and schedule it for M-F 8:00 AM via Task Scheduler. Easy debugging, full control! 🎉
