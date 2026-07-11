import sqlite3
from datetime import time
from typing import List
from src.models import FixedEvent, FlexibleTask

DB_PATH = "schedule.db"

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if tables don't exist yet."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fixed_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flexible_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                priority INTEGER NOT NULL
            )
        """)
        conn.commit()

def save_fixed_event(event: FixedEvent):
    """Inserts a new fixed event into the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO fixed_events (name, start_time, end_time) VALUES (?, ?, ?)",
            (event.name, event.start_time.isoformat(), event.end_time.isoformat())
        )
        conn.commit()

def save_flexible_task(task: FlexibleTask):
    """Inserts a new flexible task into the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO flexible_tasks (name, duration_minutes, priority) VALUES (?, ?, ?)",
            (task.name, task.duration_minutes, task.priority)
        )
        conn.commit()

def load_fixed_events() -> List[FixedEvent]:
    """Retrieves all fixed events from the database and converts strings back to time objects."""
    events = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, start_time, end_time FROM fixed_events")
        for row in cursor.fetchall():
            start_t = time.fromisoformat(row["start_time"])
            end_t = time.fromisoformat(row["end_time"])
            events.append(FixedEvent(name=row["name"], start_time=start_t, end_time=end_t))
    return events

def load_flexible_tasks() -> List[FlexibleTask]:
    """Retrieves all flexible tasks from the database."""
    tasks = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, duration_minutes, priority FROM flexible_tasks")
        for row in cursor.fetchall():
            tasks.append(FlexibleTask(
                name=row["name"], 
                duration_minutes=row["duration_minutes"], 
                priority=row["priority"]
            ))
    return tasks

def clear_all_data():
    """Wipes tables clean so users can start fresh daily if they want."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fixed_events")
        cursor.execute("DELETE FROM flexible_tasks")
        conn.commit()