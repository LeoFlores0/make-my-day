from datetime import time, datetime, timedelta
from typing import List, Tuple
from src.models import FixedEvent, FlexibleTask, ScheduleBlock

def generate_daily_schedule(
    day_start: time, 
    day_end: time, 
    fixed_events: List[Tuple[int, FixedEvent]], 
    flexible_tasks: List[Tuple[int, FlexibleTask]]
) -> Tuple[List[ScheduleBlock], List[FlexibleTask]]:
    
    today = datetime.today()
    current_time = datetime.combine(today, day_start)
    end_datetime = datetime.combine(today, day_end)
    
    # Sort fixed events by start_time (item[1] is the FixedEvent object)
    sorted_fixed = sorted(fixed_events, key=lambda item: item[1].start_time)
    
    final_schedule: List[ScheduleBlock] = []
    
    # Sort flexible tasks by priority
    task_pool = sorted(flexible_tasks, key=lambda item: item[1].priority)
    
    fixed_index = 0
    
    while current_time < end_datetime:
        
        # Handle Fixed Events
        if fixed_index < len(sorted_fixed):
            event_id, next_fixed = sorted_fixed[fixed_index]
            fixed_start_dt = datetime.combine(today, next_fixed.start_time)
            fixed_end_dt = datetime.combine(today, next_fixed.end_time)
            
            if current_time >= fixed_start_dt:
                final_schedule.append(ScheduleBlock(
                    id=event_id,
                    name=next_fixed.name,
                    start_time=next_fixed.start_time,
                    end_time=next_fixed.end_time,
                    is_fixed=True
                ))
                current_time = fixed_end_dt
                fixed_index += 1
                continue

        # Calculate available time gap before next fixed event
        if fixed_index < len(sorted_fixed):
            next_fixed_start = datetime.combine(today, sorted_fixed[fixed_index][1].start_time)
            available_gap = int((next_fixed_start - current_time).total_seconds() / 60)
        else:
            available_gap = int((end_datetime - current_time).total_seconds() / 60)
            
        chosen_item = None
        if task_pool:
            for task_tuple in task_pool:
                task_id, task = task_tuple
                if task.duration_minutes <= available_gap:
                    chosen_item = task_tuple
                    break  
                
        # Schedule the chosen flexible task
        if chosen_item:
            task_id, chosen_task = chosen_item
            task_start = current_time.time()
            current_time += timedelta(minutes=chosen_task.duration_minutes)
            task_end = current_time.time()
            
            chosen_task.scheduled_start = task_start
            chosen_task.scheduled_end = task_end
            
            final_schedule.append(ScheduleBlock(
                id=task_id,
                name=chosen_task.name,
                start_time=task_start,
                end_time=task_end,
                is_fixed=False
            ))
            task_pool.remove(chosen_item)
        else:
            # Advance time pointer if nothing fits
            if fixed_index < len(sorted_fixed):
                current_time = datetime.combine(today, sorted_fixed[fixed_index][1].start_time)
            else:
                break
                
    overflow = [task for _, task in task_pool]
    return final_schedule, overflow