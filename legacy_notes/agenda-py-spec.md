# agenda.py rewrite spec

**Read this before touching any code.** This document gives Claude full context
on what the script does, what the rewrite should produce, and where everything lives.

---

## What this script does

`agenda.py` is a Python cron job that runs each weekday morning. It:
1. Pulls tasks from Todoist via API
2. Pulls calendar events from Outlook via API
3. Combines them into a populated daily work note
4. Writes the file to the vault

It runs independently of Obsidian — Obsidian just reads the finished file.

---

## Vault location

The vault lives at: `C:\Users\michael.bergman\Command`

**Output path (Sonic, after late April 2026):**
```
C:\Users\michael.bergman\Command\Work\Sonic\Daily\YYYY-MM-DD_Agenda.md
```

File naming convention: `YYYY-MM-DD_Agenda.md` — the `_Agenda` suffix
distinguishes Python-generated work notes from personal daily notes
(`YYYY-MM-DD.md`) which live in `~/Documents/Command/Daily/`.

---

## Target output format

The rewritten script should produce exactly this structure:

```markdown
---
date: YYYY-MM-DD
week: YYYY-WWW
tags: [daily, sonic]
---

# YYYY-MM-DD — Red Ventures

---

## 🎯 Director focus
> Complete this before opening Microsoft Teams. 2 minutes.

**One Director-level move today:**

**What needs to be visible to Gabe, Stephen, or stakeholders?**

**What am I delegating to Thayra, Raj, or Jim that I'd normally hold?**

---

## ✅ Today's tasks

### Overdue
- [ ] task name (due: YYYY-MM-DD)

### Due today
- [ ] task name

### Due this week
- [ ] task name (due: YYYY-MM-DD)

---

## 📅 Calendar

| Time | Event | Location/Link |
|---|---|---|
| 9:00 AM | Meeting name | Teams link or room |

---

## 📝 Meeting notes

### 9:00 AM — Meeting name

---

## 🚦 Blockers & next steps

| Blocker | Next step | Owner | By when |
|---|---|---|---|
| | | | |

---

## 📤 End of day

**What I shipped or moved forward today:**

**What I would have held but delegated instead:**

**One thing Gabe should know from today:**

**Anything to carry into tomorrow:**
```

---

## What to remove from the current script

1. **Priorities & Focus section** — duplicate of Todoist tasks. Delete entirely.

2. **Deadlines section** — same data a third time. Delete entirely.

3. **"Needs Date" tasks** — tasks with no due date are backlog/maintenance.
   Remove from daily pull. (Phase 2: consider a separate weekly review pull.)

4. **"Items due in next 4 weeks"** — too far out to be actionable. Remove.
   Keep only: overdue, due today, due this week (by EOW).

5. **All-day events generating meeting note stubs** — if an event is all-day
   AND has no Zoom/Teams link, skip it entirely. Example: "Austin - OOO - Oregon"
   should not get a calendar row or notes section.

6. **Noise events generating meeting note stubs** — add a skip list:
   - "Lunch"
   - "Focus time"
   - Any pattern matching `protected.*time` (case-insensitive)
   - Any event under 30 minutes

---

## Todoist filter logic

```python
# Filter string for Todoist API:
# overdue | today | 7 days
#
# This produces three groups:
#   overdue  — anything past due
#   today    — due today
#   7 days   — due by end of this week (excludes overdue and today)
#
# Explicitly exclude:
#   - Tasks with no due date
#   - Tasks due more than 7 days out
```

---

## Calendar filter logic

```python
def should_include_event(event):
    """Return True if this event should appear in the note."""
    # Skip all-day events
    if event.is_all_day:
        return False
    # Skip noise by title
    skip_patterns = ["lunch", "focus time", "ooo", "out of office", "protected"]
    if any(p in event.title.lower() for p in skip_patterns):
        return False
    # Skip short events
    duration_minutes = (event.end - event.start).seconds / 60
    if duration_minutes < 30:
        return False
    return True

def should_generate_notes_stub(event):
    """Return True if this event should get a ## Meeting notes stub."""
    # Same filter as above — only events that pass inclusion get a stub
    return should_include_event(event)
```

---

## Director focus section

Hardcoded static block — no API call. Inject at top of note, above tasks:

```
## 🎯 Director focus
> Complete this before opening Slack. 2 minutes.

**One Director-level move today:**

**What needs to be visible to Gabe. Stephen or Stakeholders?**

**What am I delegating to Thayra, Ray, Jim that I'd normally hold?**
```

---

## Design goals for the rewrite

- **Config-driven** — vault path, output path, Todoist project, calendar source,
  and stakeholder names should all live in a config file or top-of-file constants,
  not scattered through the code. This makes the Sonic transition a config change,
  not a code change.
- **Portable** — should live on personal GitHub, not tied to RV infrastructure.
- **Single responsibility** — Todoist pull, calendar pull, and note assembly should
  be separate functions, easy to swap data sources independently.
- **No LLM calls** — everything is deterministic. Static prompts, pulled data,
  assembled output.

---

## Sonic transition checklist (late April 2026)

When starting at Sonic, duplicate the script and change only the config:

- [ ] Output path: `C:\Users\michael.bergman\Command\Work\Sonic\Daily\`
- [ ] Calendar source: Sonic calendar account
- [ ] Todoist project filter: update to Sonic project label
- [ ] Frontmatter tag: `[daily, sonic]`
- [ ] Note title: `YYYY-MM-DD — Sonic`
- [ ] Director focus prompts: replace Brandon/Gitesh/Jesse/Lachlan with Sonic equivalents
- [ ] RV script: leave in place but disable cron trigger after last RV day

The script structure stays identical. Only the config changes.

---

## Phase 2 (optional, do after rewrite is stable)

**Completed tasks from yesterday** — pull Todoist completed items from prior day,
inject under `### Completed yesterday` header in the tasks section. Useful context
for the end-of-day summary prompts.
