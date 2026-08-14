# Automated Daily Schedule Builder & Optimization Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-green?logo=flask)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3.0-lightgrey?logo=sqlite)](https://www.sqlite.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6%2B-yellow?logo=javascript)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Tests](https://img.shields.io/badge/Tests-PyUnittest-passing)](https://docs.python.org/3/library/unittest.html)

An algorithmic daily planner and scheduling engine that solves temporal constraint satisfaction problems by automatically scheduling flexible tasks around fixed, unmovable events within customizable time boundaries. Built with a decoupled core scheduling engine, a Flask web dashboard, interactive client-side drag-and-drop timeline reordering, and a terminal CLI interface.

## Key Features

- **Algorithmic Schedule Synthesis**: Automatically places flexible tasks into available time gaps between fixed events based on duration and priority ranking.
- **Dual Interface Parity**: Full functionality across both an interactive Flask web dashboard and a terminal CLI interface.
- **Interactive Drag-and-Drop Reordering**: Real-time client-side timeline reordering implemented using JavaScript with backend priority synchronization via AJAX.
- **Multi-Schedule Profile Management**: Supports creating, switching, deleting, and persisting multiple named daily schedules with individual start/end temporal boundaries.
- **Overflow Tracking**: Detects, isolates, and displays tasks that exceed daily time constraints rather than truncating or failing silently.
- **Relational Persistence & Scratchpads**: Built on SQLite with dynamic scratchpad note-taking exclusive to individual schedule profiles.

---

## Engineering Architecture & Design Choices

### Core Scheduling Algorithm (`src/engine.py`)

The engine implements a time-pointer traversal algorithm to place tasks into available time gaps:

- **Constraint Handling**: Fixed events (`FixedEvent`) take absolute precedence and anchor specific time blocks.
- **Greedy Gap Analysis**: The algorithm calculates available gap minutes (`available_gap`) between fixed events and evaluates flexible task candidates sorted by priority rank.
- **Priority Queue Fit**: The highest-priority flexible task whose duration fits within the current available gap is placed into the `ScheduleBlock` sequence.
- **Overflow Handling**: Any flexible tasks that cannot fit prior to reaching `day_end` are caught and isolated in an `overflow` collection for user visibility.

### Data Schema & Persistence Strategy (`src/database.py`, `src/models.py`)

- **Relational Schema**: Managed via SQLite with enforced foreign key constraints (`PRAGMA foreign_keys = ON;`) and cascading deletes (`ON DELETE CASCADE`) across schedules, fixed events, flexible tasks, and scratchpad notes.
- **Data Abstractions**: Built with Python `@dataclass` structures (`FixedEvent`, `FlexibleTask`, `ScheduleBlock`) ensuring strong typing across modules.
- **SQL Injection Prevention**: Uses parameterized query execution (`?` placeholders) across all read/write database operations.
- **Test Isolation**: Implements dynamic in-memory database switching (`DB_PATH = ":memory:"`) with persistent connection caching (`_test_conn`) to keep unit test suites isolated and fast.

### Decoupled System Architecture (`app.py` vs `cli_main.py`)

- **Separation of Concerns**: Core algorithmic scheduling (`src/engine.py`) and database persistence (`src/database.py`) have zero dependencies on web or CLI frameworks.
- **Interface Parity**: Both `app.py` (Flask web server) and `cli_main.py` (interactive command-line interface) consume the same underlying service layers.

### Interactive Frontend (`static/js/timeline-drag.js`, `static/css/style.css`)

- **Native HTML5 Drag-and-Drop**: Built with zero external JS frameworks, handling `dragstart`, `dragover`, and `drop` events.
- **Constraint Validation**: Includes client-side time parsing helper functions (`parseTimeToMinutes`) to prevent reordering actions that violate fixed schedule bounds.
- **AJAX Synchronization**: Sends reordered task arrays to `POST /reorder-timeline` to dynamically re-rank task priorities in SQLite.

---

## Automated Testing & Validation (`tests/test_scheduler.py`)

The repository includes an automated test suite built with `unittest`:

- **Database Layer Coverage**: Verifies schedule profile creation, fixed event insertion, flexible task insertion, and deletion cascades.
- **Algorithmic Correctness**: Validates priority execution order (ensuring priority 1 items schedule before priority 3 items) and tests overflow detection when total task durations exceed day boundaries.

To execute the test suite:

```bash
python -m unittest tests/test_scheduler.py
```

## Installation & Developer Setup

### Prerequisites

Python 3.10 or higher installed.

### Step-by-Step Setup

Clone the Repository:

```bash
git clone [https://github.com/LeoFlores0/make-my-day.git](https://github.com/LeoFlores0/make-my-day.git)
cd make-my-day
```

### Create and Activate Virtual Environment:

macOS/Linux:

bash
python3 -m venv venv
source venv/bin/activate

Windows:

DOS
python -m venv venv
venv\Scripts\activate

Install Dependencies:

pip install -r requirements.txt
Create a .env file in the root directory:

Code snippet
FLASK_SECRET_KEY=your_secret_key_here

### Web Dashboard:

Run the Application:

python app.py
Navigate to http://127.0.0.1:5000 in your web browser.

Terminal CLI:

Bash
python cli_main.py

## Project Structure

├── app.py # Flask web server routes & API endpoints
├── cli_main.py # Command-line interface entry point
├── src/
│ ├── database.py # SQLite schema, queries, and connection caching
│ ├── engine.py # Core interval scheduling algorithm
│ └── models.py # Dataclass definitions (FixedEvent, FlexibleTask, etc.)
├── static/
│ ├── css/
│ │ └── style.css # Custom styling and layout rules
│ └── js/
│ └── timeline-drag.js # Client-side HTML5 drag-and-drop reordering
├── templates/
│ ├── base.html # Master Jinja2 template skeleton
│ ├── dashboard.html # Main workspace layout
│ └── components/ # Reusable UI component templates
└── tests/
└── test_scheduler.py # Automated unit test suite
