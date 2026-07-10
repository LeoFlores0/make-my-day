from datetime import time, datetime
from src.engine import generate_daily_schedule
from src.models import FixedEvent, FlexibleTask

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
            print(f"Please enter a valid number.")

def main():
    print("=========================================")
    print("      Welcome to Auto Schedule Builder    ")
    print("=========================================\n")
    
    print("First, let's establish your day's boundaries.")
    day_start = get_time_input("Enter day start time (e.g., 8:00 AM): ")
    day_end = get_time_input("Enter day end time (e.g., 10:00 PM): ")
    
    fixed_events = []
    flexible_tasks = []
    
    while True:
        print("\n--- MENU OPTIONS ---")
        print("1. Add Fixed Event (e.g., Class, Lunch, Gym)")
        print("2. Add Flexible Task (e.g., Homework, Laundry)")
        print("3. Generate and View Schedule")
        print("4. Exit")
        
        choice = input("\nSelect an option (1-4): ").strip()
        
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
                
            fixed_events.append(FixedEvent(name=name, start_time=start, end_time=end))
            print(f"Fixed event '{name}' added successfully.")
            
        elif choice == "2":
            print("\n[Adding Flexible Task]")
            name = input("Task Name: ").strip()
            if not name:
                print("Name cannot be empty.")
                continue
            duration = get_int_input("Estimated Duration (in minutes): ", min_val=1, max_val=1440)
            priority = get_int_input("Priority (1 = Highest, 2 = Medium, 3 = Lowest): ", min_val=1, max_val=3)
            
            flexible_tasks.append(FlexibleTask(name=name, duration_minutes=duration, priority=priority))
            print(f"Flexible task '{name}' added successfully.")
            
        elif choice == "3":
            if not fixed_events and not flexible_tasks:
                print("\nYou haven't added any events or tasks yet!")
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
                print("\nOVERSCHEDULED TASKS (Did not fit in the day):")
                for task in overflow:
                    print(f"- {task.name} ({task.duration_minutes} mins)")
            else:
                print("\nSuccess! All tasks were successfully scheduled.")
                
        elif choice == "4":
            print("\nThanks for using Create Your Day!")
            break
        else:
            print("Invalid option. Please type 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()