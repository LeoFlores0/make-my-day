import sqlite3
from datetime import time
from typing import List, Tuple
from src.models import FixedEvent, FlexibleTask

DB_PATH = "schedule.db"
_test_conn = None  # Cache connection to keep in-memory DB alive during test execution

def get_connection():
    global _test_conn
    if DB_PATH == ":memory:":
        if _test_conn is None:
            _test_conn = sqlite3.connect(":memory:")
            _test_conn.row_factory = sqlite3.Row
        return _test_conn
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the multi-schedule schema with boundary properties and scratchpads."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Table for named schedules
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            name TEXT PRIMARY KEY,
            day_start TEXT NOT NULL DEFAULT '08:00',
            day_end TEXT NOT NULL DEFAULT '22:00'
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

    # Text scratchpad for each profile view
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scratchpads (
            schedule_name TEXT PRIMARY KEY,
            notes TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (schedule_name) REFERENCES schedules(name) ON DELETE CASCADE
        )
    """)
    conn.commit()

# Schedule Management

def get_all_schedules() -> List[dict]:
    """Retrieves all schedules with their bound time configurations."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, day_start, day_end FROM schedules")
    return [dict(row) for row in cursor.fetchall()]

def get_schedule_bounds(name: str) -> Tuple[time, time]:
    """Fetches custom time limits parsed out as standard time objects."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT day_start, day_end FROM schedules WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        return (time.fromisoformat(row["day_start"]), time.fromisoformat(row["day_end"]))
    return (time(8, 0), time(22, 0))

def create_schedule(name: str, day_start: str = "08:00", day_end: str = "22:00"):
    """Inserts a brand new named workspace paired with time limits."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO schedules (name, day_start, day_end) VALUES (?, ?, ?)", 
        (name, day_start, day_end)
    )
    conn.commit()

def delete_entire_schedule(name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedules WHERE name = ?", (name,))
    conn.commit()

# Data Insertion

def save_fixed_event(schedule_name: str, event: FixedEvent):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO fixed_events (schedule_name, name, start_time, end_time) VALUES (?, ?, ?, ?)",
        (schedule_name, event.name, event.start_time.isoformat(), event.end_time.isoformat())
    )
    conn.commit()

def save_flexible_task(schedule_name: str, task: FlexibleTask):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO flexible_tasks (schedule_name, name, duration_minutes, priority) VALUES (?, ?, ?, ?)",
        (schedule_name, task.name, task.duration_minutes, task.priority)
    )
    conn.commit()

# Data Query Tools

def load_fixed_events(schedule_name: str) -> List[Tuple[int, FixedEvent]]:
    events = []
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, start_time, end_time FROM fixed_events WHERE schedule_name = ?", (schedule_name,))
    for row in cursor.fetchall():
        start_t = time.fromisoformat(row["start_time"])
        end_t = time.fromisoformat(row["end_time"])
        events.append((row["id"], FixedEvent(name=row["name"], start_time=start_t, end_time=end_t)))
    return events

def load_flexible_tasks(schedule_name: str) -> List[Tuple[int, FlexibleTask]]:
    tasks = []
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, duration_minutes, priority FROM flexible_tasks WHERE schedule_name = ?", (schedule_name,))
    for row in cursor.fetchall():
        tasks.append((row["id"], FlexibleTask(name=row["name"], duration_minutes=row["duration_minutes"], priority=row["priority"])))
    return tasks

# Scratchpad Notepad Logic

def get_scratchpad(schedule_name: str) -> str:
    """Loads the note block text. Creates one if missing."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT notes FROM scratchpads WHERE schedule_name = ?", (schedule_name,))
    row = cursor.fetchone()
    if row:
        return row["notes"]
    return ""

def update_scratchpad(schedule_name: str, text: str):
    """Saves changes written into the lower text section."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO scratchpads (schedule_name, notes) VALUES (?, ?) ON CONFLICT(schedule_name) DO UPDATE SET notes=excluded.notes",
        (schedule_name, text)
    )
    conn.commit()

def delete_fixed_event(event_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fixed_events WHERE id = ?", (event_id,))
    conn.commit()

def delete_flexible_task(task_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM flexible_tasks WHERE id = ?", (task_id,))
    conn.commit()

def clear_schedule_contents(schedule_name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fixed_events WHERE schedule_name = ?", (schedule_name,))
    cursor.execute("DELETE FROM flexible_tasks WHERE schedule_name = ?", (schedule_name,))
    cursor.execute("DELETE FROM scratchpads WHERE schedule_name = ?", (schedule_name,))
    conn.commit()