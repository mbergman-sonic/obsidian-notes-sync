import unittest

from recap import DailyRecap, extract_blockers, extract_completed_tasks, extract_prompt_answer, render_daily_summary, render_weekly_summary


class RecapTests(unittest.TestCase):
    def test_extract_prompt_answer_supports_bullets(self):
        section = """**What I shipped or moved forward today:**
- Wrapped token refresh
- Added recap generator

**What I would have held but delegated instead:**
- Handed QA follow-up to Raj
"""
        self.assertEqual(
            ['Wrapped token refresh', 'Added recap generator'],
            extract_prompt_answer(section, 'What I shipped or moved forward today:'),
        )

    def test_extract_blockers_skips_empty_template_row(self):
        section = """| Blocker | Next step | Owner | By when |
|---|---|---|---|
| Graph auth expires | Refresh MSAL cache | Michael | Today |
| | | | |
"""
        self.assertEqual(
            ['Graph auth expires | Refresh MSAL cache | Michael | Today'],
            extract_blockers(section),
        )

    def test_extract_completed_tasks_cleans_suffixes(self):
        agenda = """- [x] Finish draft (due: 2026-07-14) 🔴 <!-- todoist-id:1 -->
- [ ] Not done
"""
        self.assertEqual(['Finish draft'], extract_completed_tasks(agenda))

    def test_render_daily_summary_falls_back_cleanly(self):
        recap = DailyRecap(date='2026-07-14', shipped=['Closed review'], blockers=['API token | Renew cache'])
        summary = render_daily_summary(recap)
        self.assertIn('# 2026-07-14 Daily Summary', summary)
        self.assertIn('- Closed review', summary)
        self.assertIn('- API token | Renew cache', summary)
        self.assertIn('*No delegation notes captured.*', summary)

    def test_render_weekly_summary_dedupes_items(self):
        recaps = [
            DailyRecap(date='2026-07-14', shipped=['Closed review'], gabe_updates=['Need sign-off']),
            DailyRecap(date='2026-07-15', shipped=['Closed review', 'Started rollout'], gabe_updates=['Need sign-off']),
        ]
        summary = render_weekly_summary(recaps, '2026-07-16')
        self.assertEqual(1, summary.count('- Closed review'))
        self.assertIn('- Started rollout', summary)
        self.assertIn('- Need sign-off', summary)


if __name__ == '__main__':
    unittest.main()
