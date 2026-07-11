from datetime import time, datetime, timedelta
from typing import List, Tuple
from src.models import FixedEvent, FlexibleTask, ScheduleBlock

def generate_daily_schedule(
    day_start: time, 
    day_end: time, 
    fixed_events: List[FixedEvent], 
    flexible_tasks: List[FlexibleTask]
) -> Tuple[List[ScheduleBlock], List[FlexibleTask]]:
    
    today = datetime.today()
    current_time = datetime.combine(today, day_start)
    end_datetime = datetime.combine(today, day_end)
    
    sorted_fixed = sorted(fixed_events, key=lambda e: e.start_time)
    
    final_schedule: List[ScheduleBlock] = []
    
    # Sort remaining tasks by priority (High to Low)
    task_pool = sorted(flexible_tasks, key=lambda t: t.priority)
    
    fixed_index = 0
    
    while current_time < end_datetime:
        
        # Handle Fixed Events
        if fixed_index < len(sorted_fixed):
            next_fixed = sorted_fixed[fixed_index]
            fixed_start_dt = datetime.combine(today, next_fixed.start_time)
            fixed_end_dt = datetime.combine(today, next_fixed.end_time)
            
            if current_time >= fixed_start_dt:
                final_schedule.append(ScheduleBlock(
                    name=next_fixed.name,
                    start_time=next_fixed.start_time,
                    end_time=next_fixed.end_time,
                    is_fixed=True
                ))
                current_time = fixed_end_dt
                fixed_index += 1
                continue
        
        # Calculate current available gap size
        if fixed_index < len(sorted_fixed):
            next_fixed_start = datetime.combine(today, sorted_fixed[fixed_index].start_time)
            available_gap = int((next_fixed_start - current_time).total_seconds() / 60)
        else:
            available_gap = int((end_datetime - current_time).total_seconds() / 60)
            
        chosen_task = None
        if task_pool:
            for task in task_pool:
                if task.duration_minutes <= available_gap:
                    chosen_task = task
                    break  
                
        # Schedule the chosen task, or advance time if nothing fits / no tasks left
        if chosen_task:
            task_start = current_time.time()
            current_time += timedelta(minutes=chosen_task.duration_minutes)
            task_end = current_time.time()
            
            chosen_task.scheduled_start = task_start
            chosen_task.scheduled_end = task_end
            
            final_schedule.append(ScheduleBlock(
                name=chosen_task.name,
                start_time=task_start,
                end_time=task_end,
                is_fixed=False
            ))
            task_pool.remove(chosen_task)
        else:
            # If nothing fits (or task_pool is empty), move pointer to the next fixed event
            if fixed_index < len(sorted_fixed):
                current_time = datetime.combine(today, sorted_fixed[fixed_index].start_time)
            else:
                break
                
    return final_schedule, task_pool