import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from sync_daily_notes import ObsidianDailySync


class FakeTodoist:
    def __init__(self):
        self.completed_ids = []
        self.created = []
        self.next_id = 900

    def complete_task(self, task_id):
        self.completed_ids.append(str(task_id))
        return True

    def add_task(self, content, due_date=None, priority=None):
        task = SimpleNamespace(
            id=str(self.next_id),
            content=content,
            due=SimpleNamespace(date=due_date) if due_date else None,
            priority=priority or 1,
        )
        self.next_id += 1
        self.created.append(task)
        return task


class TaskSyncTests(unittest.TestCase):
    def setUp(self):
        self.sync = ObsidianDailySync.__new__(ObsidianDailySync)
        self.sync.todoist = FakeTodoist()
        self.sync.vault_path = Path('/tmp/test-vault')
        self.sync.work_folder = 'Work'
        self.sync.company_folder = 'Sonic'
        self.sync.daily_notes_folder = 'Daily'

    def test_replace_task_section_updates_existing_section_body(self):
        content = """## ? Today's tasks

### Overdue
- [ ] Old task <!-- todoist-id:1 -->

### Due today
- [ ] Keep me

---
"""

        updated = self.sync.replace_task_section(content, 'Overdue', '- [ ] New task <!-- todoist-id:2 -->')

        self.assertIn('- [ ] New task <!-- todoist-id:2 -->', updated)
        self.assertNotIn('Old task', updated)
        self.assertIn('### Due today\n- [ ] Keep me', updated)

    def test_sync_note_tasks_to_todoist_creates_and_completes(self):
        existing = SimpleNamespace(id='123', content='Existing task', priority=1, due=None)
        self.sync.get_all_active_todoist_tasks = lambda: [existing]
        note = """### Overdue
- [x] Existing task <!-- todoist-id:123 -->

### Due today
- [ ] New task from Obsidian

### Due this week
*No tasks*
"""

        result = self.sync.sync_note_tasks_to_todoist(note, date(2026, 7, 9))

        self.assertEqual({'created': 1, 'completed': 1}, result)
        self.assertEqual(['123'], self.sync.todoist.completed_ids)
        self.assertEqual(1, len(self.sync.todoist.created))
        self.assertEqual('New task from Obsidian', self.sync.todoist.created[0].content)
        self.assertEqual(date(2026, 7, 9), self.sync.todoist.created[0].due.date)

    def test_load_calendar_events_from_file_accepts_connector_payload(self):
        payload = {
            'value': [
                {
                    'subject': 'Connector meeting',
                    'start': {'dateTime': '2026-07-14T14:00:00.0000000', 'timeZone': 'UTC'},
                    'end': {'dateTime': '2026-07-14T15:00:00.0000000', 'timeZone': 'UTC'},
                    'location': {'displayName': 'Microsoft Teams Meeting'},
                    'bodyPreview': 'Join: https://teams.microsoft.com/meet/example',
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'calendar.json'
            path.write_text(json.dumps(payload), encoding='utf-8')
            events = self.sync.load_calendar_events_from_file(path)

        self.assertEqual(1, len(events))
        self.assertEqual('Connector meeting', events[0]['subject'])
        self.assertEqual('Join: https://teams.microsoft.com/meet/example', events[0]['body_preview'])

    def test_sync_uses_external_calendar_events_without_graph_fetch(self):
        self.sync.get_todoist_tasks = lambda target_date=None: {'overdue': [], 'due_today': [], 'due_this_week': []}
        self.sync.get_exchange_calendar_events = lambda target_date=None: (_ for _ in ()).throw(AssertionError('should not fetch graph'))
        self.sync.read_daily_note = lambda path: """## ✅ Today's tasks

### Overdue
{{overdue_tasks}}

### Due today
{{due_today_tasks}}

### Due this week
{{due_this_week_tasks}}

---

## 📅 Calendar

{{calendar_table}}

---

## 📝 Meeting notes

{{meeting_notes}}
"""
        self.sync.write_daily_note = lambda path, content: True
        self.sync.sync_note_tasks_to_todoist = lambda content, target_date: {'created': 0, 'completed': 0}
        captured = {}

        def capture_update(content, tasks, events):
            captured['events'] = events
            return content

        self.sync.update_daily_note_content = capture_update

        result = self.sync.sync(
            target_date=date(2026, 7, 14),
            calendar_events=[{'subject': 'Injected', 'start': {'dateTime': '2026-07-14T14:00:00', 'timeZone': 'UTC'}, 'end': {'dateTime': '2026-07-14T15:00:00', 'timeZone': 'UTC'}}],
        )

        self.assertTrue(result)
        self.assertEqual('Injected', captured['events'][0]['subject'])

    def test_sync_note_tasks_to_todoist_requires_due_date_for_due_this_week(self):
        self.sync.get_all_active_todoist_tasks = lambda: []
        note = """### Overdue
*No tasks*

### Due today
*No tasks*

### Due this week
- [ ] Need explicit date
"""

        result = self.sync.sync_note_tasks_to_todoist(note, date(2026, 7, 9))

        self.assertEqual({'created': 0, 'completed': 0}, result)
        self.assertEqual([], self.sync.todoist.created)


if __name__ == '__main__':
    unittest.main()
