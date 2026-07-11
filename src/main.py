from datetime import time, datetime
from src.engine import generate_daily_schedule
from src.models import FixedEvent, FlexibleTask
from src.database import (
    init_db, 
    save_fixed_event, 
    save_flexible_task, 
    load_fixed_events, 
    load_flexible_tasks,
    clear_all_data
)

def get_time_input(prompt: str) -> time:
    """Helper to ensure the user inputs a valid standard time format (e.g., 8:00 AM or 2:30 PM)."""
    while True:
        try:
            time_str = input(prompt).strip()
            parsed_dt = datetime.strptime(time_str, "%I:%M %p")
            return parsed_dt.time()
        except ValueError:
            print("Invalid format. Please enter time as HH:MM AM/PM (e.g., 8:00 AM, 2:30 PM).")

def get_int_input(prompt: str, min_val: int, max_val: int) -> int:
    """Helper to ensure valid integer input within a specific range."""
    while True:
        try:
            val = int(input(prompt).strip())
            if min_val <= val <= max_val:
                return val
            print(f"Value must be between {min_val} and {max_val}.")
        except ValueError:
            print("Please enter a valid number.")

def main():
    # Initialize or connect to the SQLite DB schema
    init_db()
    
    print("=========================================")
    print("      Welcome to Auto Schedule Builder    ")
    print("=========================================\n")
    
    print("First, let's establish your day's boundaries.")
    day_start = get_time_input("Enter day start time (e.g., 8:00 AM): ")
    day_end = get_time_input("Enter day end time (e.g., 10:00 PM): ")
    
    while True:
        # Pull what's currently saved in the SQL DB
        fixed_events = load_fixed_events()
        flexible_tasks = load_flexible_tasks()
        
        print("\n--- MENU OPTIONS ---")
        print(f"1. Add Fixed Event (Current count: {len(fixed_events)})")
        print(f"2. Add Flexible Task (Current count: {len(flexible_tasks)})")
        print("3. Generate and View Schedule")
        print("4. Clear All Saved Data")
        print("5. Exit")
        
        choice = input("\nSelect an option (1-5): ").strip()
        
        if choice == "1":
            print("\n[Adding Fixed Event]")
            name = input("Event Name: ").strip()
            if not name:
                print("Name cannot be empty.")
                continue
            start = get_time_input("Start Time (e.g., 10:00 AM): ")
            end = get_time_input("End Time (e.g., 11:30 AM): ")
            
            if start >= end:
                print("End time must be after start time.")
                continue
                
            new_event = FixedEvent(name=name, start_time=start, end_time=end)
            save_fixed_event(new_event)
            print(f"Fixed event '{name}' saved to database.")
            
        elif choice == "2":
            print("\n[Adding Flexible Task]")
            name = input("Task Name: ").strip()
            if not name:
                print("Name cannot be empty.")
                continue
            duration = get_int_input("Estimated Duration (in minutes): ", min_val=1, max_val=1440)
            priority = get_int_input("Priority (1 = Highest, 2 = Medium, 3 = Lowest): ", min_val=1, max_val=3)
            
            new_task = FlexibleTask(name=name, duration_minutes=duration, priority=priority)
            save_flexible_task(new_task)
            print(f"Flexible task '{name}' saved to database.")
            
        elif choice == "3":
            if not fixed_events and not flexible_tasks:
                print("\nError: You don't have any items saved in the database yet!")
                continue
                
            schedule, overflow = generate_daily_schedule(day_start, day_end, fixed_events, flexible_tasks)
            
            print("\n========================================")
            print("       YOUR AUTOMATED DAILY SCHEDULE     ")
            print("========================================")
            for block in schedule:
                type_tag = "[FIXED]" if block.is_fixed else "[TASK ]"
                print(f"{block.start_time.strftime('%I:%M %p')} - {block.end_time.strftime('%I:%M %p')} | {type_tag} {block.name}")
            print("========================================")
            
            if overflow:
                print("\nWarning: OVERSCHEDULED TASKS (Did not fit in the day):")
                for task in overflow:
                    print(f"- {task.name} ({task.duration_minutes} mins)")
            else:
                print("\nSuccess! All tasks were successfully scheduled.")
                
        elif choice == "4":
            confirm = input("Are you sure you want to wipe the database? (y/n): ").strip().lower()
            if confirm == 'y':
                clear_all_data()
                print("Database cleared successfully.")
                
        elif choice == "5":
            print("\nThanks for using Auto Schedule Builder! Goodbye.")
            break
        else:
            print("Invalid option. Please type a number from 1 to 5.")

if __name__ == "__main__":
    main()