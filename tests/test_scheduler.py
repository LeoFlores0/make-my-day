import unittest
import sqlite3
from datetime import time
import src.database as db
from src.models import FixedEvent, FlexibleTask
from src.engine import generate_daily_schedule

class TestDatabaseAndEngine(unittest.TestCase):

    def setUp(self):
        """Runs before every single test. Sets up an isolated in-memory database."""
        # Override the production DB path with an in-memory instance for testing
        db.DB_PATH = ":memory:"
        db.init_db()
        
        # Seed a default schedule profile to use across database tests
        db.create_schedule("Weekday")

    def tearDown(self):
        """Runs after every single test. Disposes of the in-memory connection safely."""
        if db._test_conn:
            db._test_conn.close()
            db._test_conn = None

    # DATABASE LAYER TESTS

    def test_create_and_get_schedules(self):
        """Test that multi-schedule profiles can be created and listed."""
        db.create_schedule("Weekday", "08:00", "22:00")
        db.create_schedule("Weekend", "09:00", "23:00")
        
        schedules_data = db.get_all_schedules()
        schedule_names = [s["name"] for s in schedules_data]
        
        self.assertIn("Weekday", schedule_names)
        self.assertIn("Weekend", schedule_names)

    def test_save_and_load_fixed_events(self):
        """Test that fixed events save correctly to a specific profile and retain attributes."""
        event = FixedEvent(name="Lecture", start_time=time(9, 0), end_time=time(10, 30))
        db.save_fixed_event("Weekday", event)
        
        loaded = db.load_fixed_events("Weekday")
        self.assertEqual(len(loaded), 1)
        
        # Verify structure: load_fixed_events returns List[Tuple[db_id, FixedEvent]]
        db_id, loaded_event = loaded[0]
        self.assertEqual(loaded_event.name, "Lecture")
        self.assertEqual(loaded_event.start_time, time(9, 0))

    def test_cascade_delete_schedule(self):
        """Test that dropping a schedule deletes all its related events and tasks using Foreign Keys."""
        event = FixedEvent(name="Gym", start_time=time(17, 0), end_time=time(18, 0))
        db.save_fixed_event("Weekday", event)
        
        # Dropping the profile should trigger ON DELETE CASCADE
        db.delete_entire_schedule("Weekday")
        
        # Re-creating an empty profile should show 0 elements, proving old records were removed
        db.create_schedule("Weekday")
        self.assertEqual(len(db.load_fixed_events("Weekday")), 0)

    def test_targeted_item_deletion(self):
        """Test picking and choosing specific items to delete out of a profile."""
        task1 = FlexibleTask(name="Homework", duration_minutes=60, priority=1)
        task2 = FlexibleTask(name="Laundry", duration_minutes=30, priority=3)
        db.save_flexible_task("Weekday", task1)
        db.save_flexible_task("Weekday", task2)
        
        loaded_tasks = db.load_flexible_tasks("Weekday")
        self.assertEqual(len(loaded_tasks), 2)
        
        # Delete only the first task using its database row ID
        target_id = loaded_tasks[0][0]
        db.delete_flexible_task(target_id)
        
        remaining_tasks = db.load_flexible_tasks("Weekday")
        self.assertEqual(len(remaining_tasks), 1)
        self.assertEqual(remaining_tasks[0][1].name, "Laundry")

    # ALGORITHM ENGINE TESTS

    def test_engine_schedules_tasks_by_priority(self):
        """Verify engine places priority 1 tasks ahead of priority 3 tasks in open blocks."""
        day_start = time(8, 0)
        day_end = time(12, 0)
        
        fixed_events = []
        flexible_tasks = [
            FlexibleTask(name="Low Priority Item", duration_minutes=60, priority=3),
            FlexibleTask(name="High Priority Item", duration_minutes=60, priority=1)
        ]
        
        schedule, overflow = generate_daily_schedule(day_start, day_end, fixed_events, flexible_tasks)
        
        # The first non-fixed block generated should match our high-priority task
        self.assertEqual(schedule[0].name, "High Priority Item")
        self.assertEqual(schedule[1].name, "Low Priority Item")
        self.assertEqual(len(overflow), 0)

    def test_engine_identifies_overflow(self):
        """Verify tasks that do not fit within the day boundaries end up in the overflow pool."""
        day_start = time(9, 0)
        day_end = time(10, 0) 
        
        fixed_events = []
        flexible_tasks = [
            FlexibleTask(name="Huge Task", duration_minutes=120, priority=1)
        ]
        
        schedule, overflow = generate_daily_schedule(day_start, day_end, fixed_events, flexible_tasks)
        
        self.assertEqual(len(schedule), 0)
        self.assertEqual(len(overflow), 1)
        self.assertEqual(overflow[0].name, "Huge Task")

if __name__ == "__main__":
    unittest.main()