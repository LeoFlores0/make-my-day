import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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
    all_schedules = db.get_all_schedules()
    active_schedule = session.get("active_schedule")
    
    if not active_schedule:
        return render_template("dashboard.html", state="startup", schedules=all_schedules)
    
    day_start, day_end = db.get_schedule_bounds(active_schedule)
    db_fixed_events = db.load_fixed_events(active_schedule)  
    db_flexible_tasks = db.load_flexible_tasks(active_schedule)  
    scratchpad_notes = db.get_scratchpad(active_schedule)
    
    computed_timeline, overflow_tasks = generate_daily_schedule(
        day_start, day_end, db_fixed_events, db_flexible_tasks
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

@app.route("/schedule/return")
def change_schedule():
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

# DRAG AND DROP REORDER TASKS

@app.route("/reorder-timeline", methods=["POST"])
def reorder_timeline():
    """
    Receives updated timeline sequence from drag-and-drop JS.
    Updates flexible task priorities based on their new relative ordering.
    """
    active_schedule = session.get("active_schedule")
    if not active_schedule:
        return jsonify({"status": "error", "message": "No active schedule found"}), 400

    data = request.get_json()
    if not data or "order" not in data:
        return jsonify({"status": "error", "message": "Invalid request payload"}), 400

    new_order = data["order"]

    # Filter out flexible task IDs in the sequence they now appear
    # We assign higher priority numbers (or rank order) based on position
    flexible_priority = 1
    for item in new_order:
        if item.get("type") == "flexible":
            task_id = item.get("id")
            if task_id:
                # Update task priority in the database
                db.update_flexible_task_priority(task_id, flexible_priority)
                flexible_priority += 1

    return jsonify({"status": "success", "message": "Schedule reordered successfully"}), 200

if __name__ == "__main__":
    # Run the local server in debug mode for immediate code reload updates
    app.run(debug=True)