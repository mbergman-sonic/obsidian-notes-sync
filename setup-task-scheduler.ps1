# Obsidian Daily Sync - PowerShell Task Scheduler Setup Helper
# Run this script to automatically create a Windows Task Scheduler task

# Requires Admin - check and request if needed
$isAdmin = [Security.Principal.WindowsIdentity]::GetCurrent().Groups -contains (New-Object Security.Principal.SecurityIdentifier([Security.Principal.WellKnownSidType]::BuiltinAdministratorsSid,[Security.Principal.SecurityIdentifier]::Null)).Value
if (-not $isAdmin) {
    Write-Host "❌ This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

param(
    [string]$ScheduleTime = "08:00"  # Default 8:00 AM
)

$TaskName = "Obsidian Daily Sync"
$TaskDescription = "Sync Todoist tasks and Exchange calendar to Obsidian daily notes (M-F only)"
$ScriptPath = "C:\Users\michael.bergman\Projects\obsidian-daily-sync\run-sync.bat"
$WorkingDir = "C:\Users\michael.bergman\Projects\obsidian-daily-sync"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     OBSIDIAN DAILY SYNC - TASK SCHEDULER SETUP                 ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "⚠️  Task '$TaskName' already exists!" -ForegroundColor Yellow
    $remove = Read-Host "Remove and recreate? (y/n)"
    if ($remove -eq "y") {
        Write-Host "Removing existing task..."
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    } else {
        Write-Host "Setup cancelled."
        exit
    }
}

# Parse schedule time
try {
    $time = [TimeSpan]::Parse($ScheduleTime)
    Write-Host "✓ Schedule time: $ScheduleTime (M-F only)" -ForegroundColor Green
} catch {
    Write-Host "✗ Invalid time format. Use HH:MM (24-hour format)" -ForegroundColor Red
    exit
}

# Create trigger for M-F (weekdays only)
$trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday `
    -At $ScheduleTime

Write-Host "✓ Weekly trigger created (M-F)" -ForegroundColor Green

# Create action to run batch file
$action = New-ScheduledTaskAction `
    -Execute $ScriptPath `
    -WorkingDirectory $WorkingDir

Write-Host "✓ Task action created" -ForegroundColor Green

# Create task settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Write-Host "✓ Task settings configured" -ForegroundColor Green

# Get current user
$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -RunLevel Highest

# Register the task
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Trigger $trigger `
        -Action $action `
        -Settings $settings `
        -Principal $principal `
        -Description $TaskDescription `
        -Force | Out-Null
    
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  ✅ TASK CREATED SUCCESSFULLY!                               ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "📋 Task Details:" -ForegroundColor Cyan
    Write-Host "  Name:       $TaskName"
    Write-Host "  Schedule:   Weekdays (M-F) at $ScheduleTime"
    Write-Host "  Batch File: $ScriptPath"
    Write-Host ""
    
    Write-Host "📖 Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Complete .env file with your credentials"
    Write-Host "  2. Test the script manually:"
    Write-Host "     • Double-click:  run-sync.bat"
    Write-Host "     • Or PowerShell: python sync_daily_notes.py"
    Write-Host "  3. Test connectivity:"
    Write-Host "     • PowerShell: python sync_daily_notes.py --test"
    Write-Host "  4. Task will run automatically M-F at $ScheduleTime"
    Write-Host ""
    
    Write-Host "🎯 Manual Runs:" -ForegroundColor Cyan
    Write-Host "  • Double-click run-sync.bat for interactive menu"
    Write-Host "  • Or use PowerShell commands:"
    Write-Host "    - python sync_daily_notes.py           (normal sync)"
    Write-Host "    - python sync_daily_notes.py --test    (connectivity test)"
    Write-Host "    - python sync_daily_notes.py --verbose (debug output)"
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "✗ Error creating task: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Press Enter to close this window..."
Read-Host

