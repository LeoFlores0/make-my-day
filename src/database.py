import sqlite3
from datetime import time
from typing import List, Tuple
from src.models import FixedEvent, FlexibleTask

DB_PATH = "schedule.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the multi-schedule schema with foreign keys."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Table for named schedules
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                name TEXT PRIMARY KEY
            )
        """)
        
        # Fixed events linked to a schedule
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fixed_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_name TEXT NOT NULL,
                name TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                FOREIGN KEY (schedule_name) REFERENCES schedules(name) ON DELETE CASCADE
            )
        """)
        
        # Flexible tasks linked to a schedule
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flexible_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_name TEXT NOT NULL,
                name TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                priority INTEGER NOT NULL,
                FOREIGN KEY (schedule_name) REFERENCES schedules(name) ON DELETE CASCADE
            )
        """)
        conn.commit()

# Schedule Management

def get_all_schedules() -> List[str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM schedules")
        return [row["name"] for row in cursor.fetchall()]

def create_schedule(name: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO schedules (name) VALUES (?)", (name,))
        conn.commit()

def delete_entire_schedule(name: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schedules WHERE name = ?", (name,))
        conn.commit()

# Saving Data

def save_fixed_event(schedule_name: str, event: FixedEvent):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO fixed_events (schedule_name, name, start_time, end_time) VALUES (?, ?, ?, ?)",
            (schedule_name, event.name, event.start_time.isoformat(), event.end_time.isoformat())
        )
        conn.commit()

def save_flexible_task(schedule_name: str, task: FlexibleTask):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO flexible_tasks (schedule_name, name, duration_minutes, priority) VALUES (?, ?, ?, ?)",
            (schedule_name, task.name, task.duration_minutes, task.priority)
        )
        conn.commit()

# Loading Data (Returns IDs for deletion purposes) 

def load_fixed_events(schedule_name: str) -> List[Tuple[int, FixedEvent]]:
    events = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, start_time, end_time FROM fixed_events WHERE schedule_name = ?", (schedule_name,))
        for row in cursor.fetchall():
            start_t = time.fromisoformat(row["start_time"])
            end_t = time.fromisoformat(row["end_time"])
            events.append((row["id"], FixedEvent(name=row["name"], start_time=start_t, end_time=end_t)))
    return events

def load_flexible_tasks(schedule_name: str) -> List[Tuple[int, FlexibleTask]]:
    tasks = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, duration_minutes, priority FROM flexible_tasks WHERE schedule_name = ?", (schedule_name,))
        for row in cursor.fetchall():
            tasks.append((row["id"], FlexibleTask(name=row["name"], duration_minutes=row["duration_minutes"], priority=row["priority"])))
    return tasks

# Selective Deletions

def delete_fixed_event(event_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fixed_events WHERE id = ?", (event_id,))
        conn.commit()

def delete_flexible_task(task_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM flexible_tasks WHERE id = ?", (task_id,))
        conn.commit()

def clear_schedule_contents(schedule_name: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fixed_events WHERE schedule_name = ?", (schedule_name,))
        cursor.execute("DELETE FROM flexible_tasks WHERE schedule_name = ?", (schedule_name,))
        conn.commit()