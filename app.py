import os
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
from datetime import time, datetime
import src.database as db
from src.models import FixedEvent, FlexibleTask
from src.engine import generate_daily_schedule

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("S")
# Initialize the database schema on web server startup
db.init_db()

@app.route("/")
def index():
    """Unified Single-Page App router."""
    # Get all existing schedule profiles to populate selection lists
    all_schedules = db.get_all_schedules()
    
    # Check if a specific schedule is currently active in the user's browser session
    active_schedule = session.get("active_schedule")
    
    if not active_schedule:
        # Startup View (Choose or create a profile)
        return render_template("dashboard.html", state="startup", schedules=all_schedules)
    
    # Core Dashboard View
    # Fetch boundaries and items from database
    day_start, day_end = db.get_schedule_bounds(active_schedule)
    db_fixed_events = db.load_fixed_events(active_schedule)  # returns List[Tuple[id, FixedEvent]]
    db_flexible_tasks = db.load_flexible_tasks(active_schedule)  # returns List[Tuple[id, FlexibleTask]]
    scratchpad_notes = db.get_scratchpad(active_schedule)
    
    # Extract dataclass lists for schedule generation algorithm
    fixed_events_list = [item[1] for item in db_fixed_events]
    flexible_tasks_list = [item[1] for item in db_flexible_tasks]
    
    # Compute the automated time blocks and any overflow tasks using the engine
    computed_timeline, overflow_tasks = generate_daily_schedule(
        day_start, day_end, fixed_events_list, flexible_tasks_list
    )
    
    return render_template(
        "dashboard.html",
        state="workspace",
        schedules=all_schedules,
        active_schedule=active_schedule,
        day_start=day_start.strftime("%I:%M %p"),
        day_end=day_end.strftime("%I:%M %p"),
        fixed_events=db_fixed_events,
        flexible_tasks=db_flexible_tasks,
        timeline=computed_timeline,
        overflow=overflow_tasks,
        notes=scratchpad_notes
    )

# SCHEDULE SESSION OVERRIDES

@app.route("/schedule/select", methods=["POST"])
def select_schedule():
    """Locks a chosen profile name into the session cookie."""
    name = request.form.get("name")
    if name:
        session["active_schedule"] = name
    return redirect(url_for("index"))

@app.route("/schedule/create", methods=["POST"])
def create_schedule():
    """Creates a brand new schedule with bound time configurations."""
    name = request.form.get("name", "").strip()
    start_str = request.form.get("day_start", "08:00")
    end_str = request.form.get("day_end", "22:00")
    
    if name:
        db.create_schedule(name, start_str, end_str)
        session["active_schedule"] = name  # Auto-select the newly created schedule
    return redirect(url_for("index"))

@app.route("/schedule/clear-session")
def clear_session():
    """Logs out and returns to the startup view."""
    session.pop("active_schedule", None)
    return redirect(url_for("index"))

@app.route("/schedule/delete-profile", methods=["POST"])
def delete_profile():
    """Wipes an entire named schedule profile along with its contents from the DB."""
    active_schedule = session.get("active_schedule")
    if active_schedule:
        db.delete_entire_schedule(active_schedule)
        session.pop("active_schedule", None)
    return redirect(url_for("index"))

# ITEM DATA CONTROLLERS

@app.route("/event/add", methods=["POST"])
def add_fixed_event():
    active_schedule = session.get("active_schedule")
    if active_schedule:
        name = request.form.get("name")
        start_str = request.form.get("start_time")
        end_str = request.form.get("end_time")
        
        if name and start_str and end_str:
            start_time = time.fromisoformat(start_str)
            end_time = time.fromisoformat(end_str)
            event = FixedEvent(name=name, start_time=start_time, end_time=end_time)
            db.save_fixed_event(active_schedule, event)
    return redirect(url_for("index"))

@app.route("/task/add", methods=["POST"])
def add_flexible_task():
    active_schedule = session.get("active_schedule")
    if active_schedule:
        name = request.form.get("name")
        duration = request.form.get("duration_minutes")
        priority = request.form.get("priority")
        
        if name and duration and priority:
            task = FlexibleTask(name=name, duration_minutes=int(duration), priority=int(priority))
            db.save_flexible_task(active_schedule, task)
    return redirect(url_for("index"))

# TARGETED DELETION CONTROLLERS

@app.route("/delete/fixed/<int:item_id>", methods=["POST"])
def remove_fixed_event(item_id):
    db.delete_fixed_event(item_id)
    return redirect(url_for("index"))

@app.route("/delete/flexible/<int:item_id>", methods=["POST"])
def remove_flexible_task(item_id):
    db.delete_flexible_task(item_id)
    return redirect(url_for("index"))

@app.route("/schedule/clear-all", methods=["POST"])
def clear_all_content():
    """Clears all events, tasks, and notes inside the active schedule profile."""
    active_schedule = session.get("active_schedule")
    if active_schedule:
        db.clear_schedule_contents(active_schedule)
    return redirect(url_for("index"))

# SCRATCHPAD NOTEPAD CONTROLLER

@app.route("/scratchpad/update", methods=["POST"])
def save_notes():
    active_schedule = session.get("active_schedule")
    if active_schedule:
        notes_text = request.form.get("notes", "")
        db.update_scratchpad(active_schedule, notes_text)
    return redirect(url_for("index"))

if __name__ == "__main__":
    # Run the local server in debug mode for immediate code reload updates
    app.run(debug=True)