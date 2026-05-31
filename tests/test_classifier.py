import unittest

from classification.classifier import classify_event, classify_events


CLARITY_DEFS = [
    {'project': 'Internal', 'task_name': 'Internal Meetings', 'task_code': 'INTERNAL'},
    {'project': 'Learning', 'task_name': 'Training', 'task_code': 'TSK-TRAIN'},
    {'project': 'TURBO', 'task_name': 'Turbo Execution', 'task_code': 'TSK-TURBO'},
    {'project': 'Data Platform', 'task_name': 'Data Engineering', 'task_code': 'TSK-DATAENG'},
    {'project': 'Analytics', 'task_name': 'Data Analysis', 'task_code': 'TSK-ANALYSIS'},
    {'project': 'Delivery', 'task_name': 'Project Management', 'task_code': 'TSK-PM'},
]


class TestClassifyEvent(unittest.TestCase):
    def test_rule_bootcamp_training(self):
        result = classify_event({'title': 'Bootcamp: Python Foundations', 'notes': ''}, CLARITY_DEFS, '2026-05-28')
        self.assertEqual(result['task_name'], 'Training')
        self.assertEqual(result['task_code'], 'TSK-TRAIN')
        self.assertGreaterEqual(result['confidence'], 0.95)

    def test_rule_internal_1on1(self):
        result = classify_event({'title': '1:1 with Alice', 'notes': ''}, CLARITY_DEFS, '2026-05-28')
        self.assertEqual(result['task_name'], 'Internal Meetings')
        self.assertEqual(result['task_code'], 'INTERNAL')

    def test_rule_internal_cab(self):
        result = classify_event({'title': 'CAB review', 'notes': ''}, CLARITY_DEFS, '2026-05-28')
        self.assertEqual(result['task_code'], 'INTERNAL')

    def test_rule_turbo(self):
        result = classify_event({'title': 'Turbo sprint planning', 'notes': ''}, CLARITY_DEFS, '2026-05-28')
        self.assertEqual(result['task_code'], 'TSK-TURBO')

    def test_rule_data_engineering_from_notes(self):
        result = classify_event({'title': 'Daily sync', 'notes': 'Need SAP data mapping work'}, CLARITY_DEFS, '2026-05-28')
        self.assertEqual(result['task_code'], 'TSK-DATAENG')

    def test_rule_data_analysis(self):
        result = classify_event({'title': 'Weekly metrics review', 'notes': ''}, CLARITY_DEFS, '2026-05-28')
        self.assertEqual(result['task_code'], 'TSK-ANALYSIS')

    def test_rule_project_management(self):
        result = classify_event({'title': 'Catch up and planning', 'notes': ''}, CLARITY_DEFS, '2026-05-28')
        self.assertEqual(result['task_code'], 'TSK-PM')

    def test_fallback_scoring_when_no_rule_match(self):
        result = classify_event({'title': 'Management kickoff', 'notes': ''}, CLARITY_DEFS, '2026-05-28')
        self.assertEqual(result['task_code'], 'TSK-PM')
        self.assertGreaterEqual(result['confidence'], 0.5)
        self.assertLessEqual(result['confidence'], 0.85)

    def test_default_internal_when_ambiguous(self):
        result = classify_event({'title': '', 'notes': ''}, CLARITY_DEFS, '2026-05-28')
        self.assertEqual(result['task_code'], 'INTERNAL')
        self.assertEqual(result['confidence'], 0.5)


class TestClassifyEvents(unittest.TestCase):
    def test_per_event_entries(self):
        events = [
            {'title': '1:1 with Bob', 'notes': '', 'duration_hours': 0.5},
            {'title': 'CAB discussion', 'notes': '', 'duration_hours': 1.0},
            {'title': 'Bootcamp session', 'notes': '', 'duration_hours': 2.0},
        ]
        summary = classify_events(events, CLARITY_DEFS, '2026-05-28')

        self.assertEqual(summary['date'], '2026-05-28')
        self.assertEqual(summary['event_count'], 3)

        self.assertEqual(len(summary['entries']), 3)
        self.assertIn('source_event', summary['entries'][0])

    def test_corrections_override(self):
        events = [{'title': 'Team Sync', 'notes': '', 'duration_hours': 1.0}]
        corrections = [{
            'date': '2026-05-28',
            'source_event': 'Team Sync',
            'project': 'Administration',
            'task_name': 'Internal Meetings',
            'task_code': 'TSK001172',
        }]
        summary = classify_events(events, CLARITY_DEFS, '2026-05-28', corrections=corrections)
        self.assertEqual(summary['entries'][0]['task_code'], 'TSK001172')


if __name__ == '__main__':
    unittest.main()
