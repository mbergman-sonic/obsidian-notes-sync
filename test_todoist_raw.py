    def test_todoist_raw_tasks(self):
        """Test: Print all raw tasks returned from Todoist (for debugging)."""
        print("\n" + "="*70)
        print("🧪 TODOIST RAW TASKS TEST")
        print("="*70 + "\n")
        if not self.todoist:
            print("  ❌ Todoist client not initialized.")
            return
        try:
            tasks_paginator = self.todoist.get_tasks()
            paginator_list = list(tasks_paginator)
            tasks = paginator_list[0] if paginator_list else []
            print(f"Found {len(tasks)} tasks (raw):\n")
            for task in tasks:
                print(json.dumps(task.to_dict() if hasattr(task, 'to_dict') else task.__dict__, indent=2, default=str))
            print("\nDone.")
        except Exception as e:
            print(f"  ❌ Error fetching raw Todoist tasks: {e}")
