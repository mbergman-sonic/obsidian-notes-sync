import os
import unittest


@unittest.skipUnless(
    os.getenv('RUN_TODOIST_INTEGRATION_TESTS') == '1',
    'Set RUN_TODOIST_INTEGRATION_TESTS=1 to run Todoist integration tests.',
)
class TestTodoistRaw(unittest.TestCase):
    def test_todoist_raw_tasks(self):
        token = os.getenv('TODOIST_API_TOKEN')
        self.assertTrue(token, 'TODOIST_API_TOKEN must be set to run this integration test.')

        try:
            from todoist_api_python.api import TodoistAPI
        except Exception as exc:
            self.skipTest(f'todoist_api_python is not available: {exc}')

        api = TodoistAPI(token)
        tasks = api.get_tasks()

        # Integration smoke assertion: API should return a list-like object.
        self.assertIsInstance(tasks, list)


if __name__ == '__main__':
    unittest.main()
