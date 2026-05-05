# Device setup checklist

Run this when opening the vault on a device for the first time after the March 2026 reorganization.

---

## Obsidian core settings

### Daily notes (core plugin)
Settings → Daily notes → Folder: `Daily`

If it still says `Daily Notes` — update it.

### Attachments
Settings → Files & Links → Default location for new attachments: `In the folder specified below` → `Resources/Attachments`

If it's set to vault root or something else — update it.

---

## Community plugins

### Templater
If not installed: Settings → Community plugins → Browse → search "Templater" → Install → Enable

Then configure:
1. Settings → Templater → Template folder location: `Resources/Templates`
2. Enable **Trigger Templater on new file creation**
3. Under **Folder templates**, add: folder `Daily` → template `Resources/Templates/personal-daily-template.md`

This makes "Open today's daily note" auto-populate the Victory Hour template on creation.

### Periodic Notes (if installed)
Settings → Periodic Notes → Daily Notes → Folder: `Daily`

---

## Python script (cron)
The daily work note output path should be:
- **RV (until late April 2026):** `~/Documents/Command/Work/RV/Daily/`
- **Sonic (after late April 2026):** `~/Documents/Command/Work/Sonic/Daily/`

If the script still points to `Daily Notes/` or the old vault path — update it.

---

*This file can be deleted once all devices are confirmed up to date.*
