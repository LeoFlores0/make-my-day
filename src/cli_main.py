from datetime import time, datetime
from src.engine import generate_daily_schedule
from src.models import FixedEvent, FlexibleTask
from src.database import (
    init_db, get_all_schedules, create_schedule, delete_entire_schedule,
    save_fixed_event, save_flexible_task, load_fixed_events, load_flexible_tasks,
    delete_fixed_event, delete_flexible_task, clear_schedule_contents
)

def get_time_input(prompt: str) -> time:
    while True:
        try:
            time_str = input(prompt).strip()
            parsed_dt = datetime.strptime(time_str, "%I:%M %p")
            return parsed_dt.time()
        except ValueError:
            print("Invalid format. Please enter time as HH:MM AM/PM (e.g., 8:00 AM, 2:30 PM).")

def get_int_input(prompt: str, min_val: int, max_val: int) -> int:
    while True:
        try:
            val = int(input(prompt).strip())
            if min_val <= val <= max_val:
                return val
            print(f"Value must be between {min_val} and {max_val}.")
        except ValueError:
            print("Please enter a valid number.")

def pick_schedule_flow() -> str:
    """Handles choosing an existing schedule or naming a brand new one."""
    while True:
        schedules = get_all_schedules()
        print("\n=== AVAILABLE SCHEDULES ===")
        if not schedules:
            print("(No schedules found)")
        else:
            for i, name in enumerate(schedules, 1):
                print(f"{i}. {name}")
        
        print("\nOptions:")
        print("1. Select an existing schedule" if schedules else "[1. Create a schedule first!]")
        print("2. Create a new custom-named schedule")
        print("3. Delete a schedule")
        
        choice = input("Choice (1-3): ").strip()
        
        if choice == "1" and schedules:
            idx = get_int_input("Enter schedule number: ", 1, len(schedules))
            return schedules[idx - 1]
            
        elif choice == "2":
            name = input("Name for this schedule:").strip()
            if not name:
                print("Enter a name!")
                continue
            create_schedule(name)
            return name
            
        elif choice == "3" and schedules:
            idx = get_int_input("Select schedule number to delete: ", 1, len(schedules))
            target = schedules[idx - 1]
            confirm = input(f"Are you sure you want to delete '{target}'? (y/n): ").strip().lower()
            if confirm == 'y':
                delete_entire_schedule(target)
                print(f"Profile '{target}' deleted.")
        else:
            print("Invalid selection.")

def handle_deletion_flow(schedule_name: str):
    """Sub-menu allowing targeted item removals or a full clear."""
    while True:
        fixed_tuples = load_fixed_events(schedule_name)
        task_tuples = load_flexible_tasks(schedule_name)
        
        print(f"\n--- Manage Data for [{schedule_name}] ---")
        print("1. Remove a specific Fixed Event")
        print("2. Remove a specific Flexible Task")
        print("3. Clear all data inside this schedule")
        print("4. Cancel (Back to main menu)")
        
        choice = input("Select a modification option (1-4): ").strip()
        
        if choice == "1":
            if not fixed_tuples:
                print("No fixed events to delete.")
                continue
            for i, (db_id, item) in enumerate(fixed_tuples, 1):
                print(f"{i}. {item.name} ({item.start_time.strftime('%I:%M %p')})")
            print(f"{len(fixed_tuples) + 1}. Cancel")
            
            target = get_int_input("Select item to delete: ", 1, len(fixed_tuples) + 1)
            if target == len(fixed_tuples) + 1:
                print("Deletion canceled.")
            else:
                delete_fixed_event(fixed_tuples[target - 1][0])
                print("Fixed event removed.")
                
        elif choice == "2":
            if not task_tuples:
                print("No flexible tasks to delete.")
                continue
            for i, (db_id, item) in enumerate(task_tuples, 1):
                print(f"{i}. {item.name} ({item.duration_minutes} mins)")
            print(f"{len(task_tuples) + 1}. Cancel")
            
            target = get_int_input("Select item to delete: ", 1, len(task_tuples) + 1)
            if target == len(task_tuples) + 1:
                print("Deletion canceled.")
            else:
                delete_flexible_task(task_tuples[target - 1][0])
                print("Flexible task removed.")
                
        elif choice == "3":
            confirm = input("Wipe all events and tasks out of this schedule? (y/n): ").strip().lower()
            if confirm == 'y':
                clear_schedule_contents(schedule_name)
                print("Schedule contents removed.")
                break
        elif choice == "4":
            break

def main():
    init_db()
    
    print("=========================================")
    print("      Welcome to Auto Schedule Builder    ")
    print("=========================================")
    
    active_schedule = pick_schedule_flow()
    print(f"\nCurrent Schedule: [{active_schedule}]")

    print("\nNext, let's establish your day's boundaries.")
    day_start = get_time_input("Enter day start time (e.g., 8:00 AM): ")
    day_end = get_time_input("Enter day end time (e.g., 10:00 PM): ")
    
    while True:
        # Unwrap data lists by throwing away the database integer IDs for calculation engine
        fixed_events = [item for db_id, item in load_fixed_events(active_schedule)]
        flexible_tasks = [item for db_id, item in load_flexible_tasks(active_schedule)]
        
        print(f"\n--- MENU OPTIONS [{active_schedule}] ---")
        print(f"1. Add Fixed Event (Current: {len(fixed_events)})")
        print(f"2. Add Flexible Task (Current: {len(flexible_tasks)})")
        print("3. Generate and View Schedule")
        print("4. Delete Items / Clear Schedule Data")
        print("5. Change Schedule Profile / Restart")
        print("6. Exit")
        
        choice = input("\nSelect an option (1-6): ").strip()
        
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
                
            save_fixed_event(active_schedule, FixedEvent(name=name, start_time=start, end_time=end))
            print(f"Fixed event '{name}' saved to [{active_schedule}].")
            
        elif choice == "2":
            print("\n[Adding Flexible Task]")
            name = input("Task Name: ").strip()
            if not name:
                print("Name cannot be empty.")
                continue
            duration = get_int_input("Estimated Duration (in minutes): ", min_val=1, max_val=1440)
            priority = get_int_input("Priority (1 = High, 2 = Med, 3 = Low): ", min_val=1, max_val=3)
            
            save_flexible_task(active_schedule, FlexibleTask(name=name, duration_minutes=duration, priority=priority))
            print(f"Flexible task '{name}' saved to [{active_schedule}].")
            
        elif choice == "3":
            if not fixed_events and not flexible_tasks:
                print("\nError: You don't have any items saved in this profile yet!")
                continue
                
            schedule, overflow = generate_daily_schedule(day_start, day_end, fixed_events, flexible_tasks)
            
            print(f"\n========================================")
            print(f"   AUTOMATED SCHEDULE: {active_schedule.upper()}  ")
            print("========================================")
            for block in schedule:
                type_tag = "[FIXED]" if block.is_fixed else "[TASK ]"
                print(f"{block.start_time.strftime('%I:%M %p')} - {block.end_time.strftime('%I:%M %p')} | {type_tag} {block.name}")
            print("========================================")
            
            if overflow:
                print("\nWarning: OVERSCHEDULED TASKS:")
                for task in overflow:
                    print(f"- {task.name} ({task.duration_minutes} mins)")
            else:
                print("\nSuccess! All tasks were successfully scheduled.")
                
        elif choice == "4":
            handle_deletion_flow(active_schedule)
            
        elif choice == "5":
            print("\nReturning to Select Menu...")
            active_schedule = pick_schedule_flow()
            print(f"\nCurrent Schedule: [{active_schedule}]")
            day_start = get_time_input("Enter day start time (e.g., 8:00 AM): ")
            day_end = get_time_input("Enter day end time (e.g., 10:00 PM): ")
            
        elif choice == "6":
            print("\nThanks for using Auto Schedule Builder! Goodbye.")
            break
        else:
            print("Invalid option. Please type a number from 1 to 6.")

if __name__ == "__main__":
    main()