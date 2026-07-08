from datetime import time
from src.engine import generate_daily_schedule
from src.models import FixedEvent, FlexibleTask

def main():
    
    # Define day boundaries
    day_start = time(8, 0)
    day_end = time(22, 0)
    
    # Add fixed events
    fixed_events = [
        FixedEvent(name="Data Structures Class", start_time=time(10, 0), end_time=time(11, 30)),
        FixedEvent(name="Lunch Break", start_time=time(12, 0), end_time=time(13, 0)),
        FixedEvent(name="Gym Session", start_time=time(16, 0), end_time=time(17, 30))
    ]
    
    # Add flexible tasks with durations and priorities (1 = Highest)
    flexible_tasks = [
        FlexibleTask(name="Coding Project HW", duration_minutes=120, priority=1),
        FlexibleTask(name="Read Calculus Chapter", duration_minutes=60, priority=2),
        FlexibleTask(name="Laundry", duration_minutes=45, priority=3),
        FlexibleTask(name="Review Resume", duration_minutes=30, priority=2)
    ]
    
    # Run the engine
    schedule, overflow = generate_daily_schedule(day_start, day_end, fixed_events, flexible_tasks)
    
    # Print the results out 
    print("\nYOUR AUTOMATED DAILY SCHEDULE:")
    print("=" * 40)
    for block in schedule:
        type_tag = "[FIXED]" if block.is_fixed else "[TASK ]"
        print(f"{block.start_time.strftime('%I:%M %p')} - {block.end_time.strftime('%I:%M %p')} | {type_tag} {block.name}")
    print("=" * 40)
    
    # Print anything that didn't fit
    if overflow:
        print("\n OVERSCHEDULED TASKS:")
        for task in overflow:
            print(f"- {task.name} ({task.duration_minutes} mins)")
    else:
        print("All tasks were successfully scheduled!")

if __name__ == "__main__":
    main()