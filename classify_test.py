from classification import classify_text

agenda = '''---
date: 2026-05-28

## 📅 Calendar

| Time | Event | Location/Link |
|---|---|---|
| 9:00 AM | Team Sync | Teams |
| 10:30 AM | Project A Planning | Teams |
| 1:00 PM | 1:1 with Alice | Teams |

## 📝 Meeting notes

### 9:00 AM — Team Sync

Notes for team sync

### 10:30 AM — Project A Planning

Planning notes
'''

clarity_csv = '''Internal Meetings (TSK001172)
Project A (PRJ-130)
Project Planning (TSK001176)
'''

res = classify_text(agenda, clarity_csv, '2026-05-28')
import json
print(json.dumps(res, indent=2))
