from datetime import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class FixedEvent:
    name: str
    start_time: time
    end_time: time

@dataclass
class FlexibleTask:
    name: str
    duration_minutes: int
    priority: int
    scheduled_start: Optional[time] = None
    scheduled_end: Optional[time] = None

@dataclass
class ScheduleBlock:
    name: str
    start_time: time
    end_time: time
    is_fixed: bool