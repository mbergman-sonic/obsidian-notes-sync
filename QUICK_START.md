# Quick Start Guide

## Initial Setup (5 minutes)

### 1. Install Python Dependencies
```bash
cd C:\Users\michael.bergman\Projects\obsidian-daily-sync
pip install -r requirements.txt
```

### 2. Get Your API Credentials

**Todoist:**
- Visit https://todoist.com/app/settings/integrations/developer
- Click "Create token"
- Copy the token

**Microsoft Exchange/Outlook:**
- Use your email address
- For password, consider using an App Password if 2FA is enabled:
  - Go to https://account.microsoft.com/security
  - Create an app password for "Other (Windows)"

### 3. Create .env File
```bash
copy .env.example .env
```

Edit `.env` with your credentials:
```
TODOIST_API_TOKEN=paste_your_token_here
EXCHANGE_EMAIL=your.email@company.com
EXCHANGE_PASSWORD=your_password_here
EXCHANGE_SERVER=outlook.office365.com
OBSIDIAN_VAULT_PATH=C:\Users\michael.bergman\Command
```

### 4. Test Connectivity
```bash
python sync_daily_notes.py --test
```

Should output:
```
✅ Todoist connected! Found X tasks
✅ Exchange connected! Found X events today
✅ Vault path exists
✅ All systems ready!
```

### 5. Run Your First Sync

**Option A: Easy Menu (Recommended)**
```bash
run-sync.bat
```
Then choose option 1

**Option B: Command Line**
```bash
python sync_daily_notes.py
```

### 6. Schedule for M-F at 8:00 AM

Open PowerShell as Administrator:
```powershell
cd C:\Users\michael.bergman\Projects\obsidian-daily-sync
.\setup-task-scheduler.ps1 -ScheduleTime "08:00"
```

Change `08:00` to your preferred time.

## That's It! 🎉

Your daily notes will now sync:
- **Automatically:** M-F at 8:00 AM via Task Scheduler
- **Manually:** Anytime using `run-sync.bat` or `python sync_daily_notes.py`

## Manual Run Options

**Interactive Menu** (easiest):
```
Double-click: run-sync.bat
```

**PowerShell Commands:**
```bash
python sync_daily_notes.py              # Run sync
python sync_daily_notes.py --test       # Test connectivity
python sync_daily_notes.py --verbose    # Debug output
python sync_daily_notes.py --help       # Show all options
```

## Troubleshooting

**Test failing?**
```bash
python sync_daily_notes.py --test
```
- Fix the error shown
- Verify `.env` credentials

**Task Scheduler script won't run?**
- In PowerShell (as Admin): `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**Python not found?**
- In PowerShell: `python --version`
- If not found, reinstall Python and add to PATH

## Next Steps

See **MANUAL_RUN_GUIDE.md** for:
- Debugging workflow
- Task Scheduler management
- Detailed troubleshooting
- FAQ
