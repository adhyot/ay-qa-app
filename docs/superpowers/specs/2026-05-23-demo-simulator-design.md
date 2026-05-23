# Demo Simulation Engine — Design Spec
**Date:** 2026-05-23  
**Status:** Approved

## Overview

A background simulation engine embedded in the Flask app that generates realistic QA team activity (test case writing, test runs, bug filing, automation) against the demo org's database. Controlled from a Settings page with a master toggle, per-job toggles, and a live activity log.

The goal is to make the app feel like a real company is actively using it — engineers writing cases, CI pipelines triggering runs, bugs getting filed and resolved — so the demo org always has fresh, believable data.

---

## Architecture

```
app/
  simulator/
    __init__.py       # start_scheduler() / stop_scheduler() called from app factory
    engine.py         # APScheduler instance, job registration, start/pause/resume per job
    jobs.py           # 5 job functions, each using app context + Faker
    seeder.py         # one-time seed: virtual users, suites, test cases
  blueprints/
    settings/
      __init__.py
      routes.py       # GET /settings/simulator, POST /settings/simulator/toggle, POST /settings/simulator/job/<name>
      templates/
        settings/
          simulator.html
  models/
    simulator.py      # SimulatorConfig + SimulatorLog models
```

The scheduler is started in `create_app()` after all extensions initialise. It starts in a paused state; only resumes jobs for orgs with `simulation_enabled=True`.

---

## Data Models

### SimulatorConfig
One row per org. Created on first visit to the settings page.

| Column | Type | Default | Notes |
|--------|------|---------|-------|
| id | String(36) PK | uuid | |
| org_id | String(36) FK | — | unique |
| enabled | Boolean | False | master toggle |
| seeded | Boolean | False | True after one-time seed runs |
| job_write_test_case | Boolean | True | |
| job_start_run | Boolean | True | |
| job_complete_run | Boolean | True | |
| job_file_bug | Boolean | True | |
| job_automation_run | Boolean | True | |
| created_at | DateTime | utcnow | |
| updated_at | DateTime | utcnow | |

### SimulatorLog
Append-only activity feed. Capped at 200 rows per org (oldest deleted when inserting past the cap).

| Column | Type | Notes |
|--------|------|-------|
| id | String(36) PK | uuid |
| org_id | String(36) FK | |
| job_type | String(30) | write_test_case, start_run, etc. |
| message | String(500) | Human-readable description of what happened |
| created_at | DateTime | utcnow |

---

## The 5 Jobs

Each job follows this pattern:
1. Load `SimulatorConfig` for the demo org — skip if not found or not enabled
2. Check its own per-job flag — skip if disabled
3. Execute within `app.app_context()`
4. Commit DB changes
5. Append a `SimulatorLog` entry
6. If log count > 200, delete the oldest rows down to 180

| Job ID | Interval | What it does |
|--------|----------|-------------|
| `write_test_case` | 45s | Picks a random suite owned by a virtual user, creates a TestCase with Faker-generated title/steps/priority/type |
| `start_run` | 2 min | Picks a random suite with test cases, creates a TestRun (status=running, trigger_type=manual or ci_cd), assigns a virtual user as triggerer |
| `complete_run` | 60s | Finds the oldest running TestRun, distributes pass/fail/skip counts across its test cases (80–95% pass rate), creates TestRunResult rows, marks run as passed/failed/partial |
| `file_bug` | 90s | Finds a failed TestRunResult with no existing bug, creates a Bug with Faker-generated title/description/severity (weighted: minor 40%, major 35%, critical 20%, blocker 5%), assigns to a virtual user |
| `automation_run` | 3 min | Creates a TestRun with trigger_type=ci_cd, branch=main or feature/*, 30–60 test cases, immediately queues it (status=queued); complete_run will finish it in the next cycle |

### Pass Rate Distribution
Completed runs use a weighted random pass rate:
- 60% chance: 90–100% pass (healthy sprint)
- 25% chance: 70–89% pass (some failures)
- 15% chance: 50–69% pass (bad deploy / flaky suite)

---

## One-Time Seeder

Runs once when simulation is first enabled (`seeded=False`). Creates all data under the demo org.

**Virtual users (5):**
- 2 QA Engineers, 1 QA Manager, 1 automation engineer, 1 viewer
- Names and emails generated with Faker, passwords set to `sim_user_XXXX` (never used for login)

**Test Suites (4):**
1. Login & Auth (pytest, GitHub repo: `acme/auth-service`)
2. Checkout & Payments (selenium, `acme/checkout`)
3. API Integration (pytest, `acme/api-gateway`)
4. Mobile Regression (playwright, `acme/mobile-app`)

**Test Cases (~30 total, 7–8 per suite):** Faker-generated titles using domain-specific templates (e.g. "Verify [action] when [condition]"), mix of manual/automated/hybrid, priorities weighted toward medium/high.

**Environments (2):** Staging, Production — if none exist for the org.

---

## Settings Page (`/settings/simulator`)

Route: `GET /settings/simulator`  
Access: `login_required`, role must be `admin` or `qa_manager`

**Layout:**
```
Demo Simulation                              [● ENABLED / ○ DISABLED]

Jobs
─────────────────────────────────────────────────────────
Write test cases        every 45s            [ON | OFF]
Start test runs         every 2 min          [ON | OFF]
Complete running runs   every 60s            [ON | OFF]
File bugs               every 90s            [ON | OFF]
Automation runs         every 3 min          [ON | OFF]

Live Activity Log                            [auto-refreshes every 10s]
─────────────────────────────────────────────────────────
14:32:01  write_test_case   Alice Chen added "Verify 2FA login works" → Login & Auth
14:31:20  automation_run    CI triggered run on main (52 tests) → API Integration
14:30:45  file_bug          Bug filed: Payment gateway timeout – MAJOR → assigned to Bob
14:29:10  complete_run      Run #38 completed: 43/47 passed (91.5%)
```

**Interactions:**
- Master toggle: `POST /settings/simulator/toggle` → flips `enabled`, starts/pauses all jobs
- Per-job toggle: `POST /settings/simulator/job/<job_id>` → flips individual flag, pauses/resumes that APScheduler job
- Log endpoint: `GET /settings/simulator/log` → returns last 30 entries as JSON, polled every 10s by vanilla JS

---

## APScheduler Integration

- Library: `APScheduler` (add to `requirements.txt`)
- Scheduler type: `BackgroundScheduler` with `MemoryJobStore` (simpler than SQLAlchemyJobStore, no separate connection needed)
- On startup, `start_scheduler(app)` registers all 5 jobs, then queries `SimulatorConfig` to resume or pause each job based on stored flags — restoring state after a restart
- Each job registered with `id`, `func`, `trigger='interval'`, `seconds=N`, `max_instances=1`, initial state `paused`
- The scheduler instance is a module-level singleton in `engine.py`, importable by settings routes to pause/resume jobs on toggle

---

## Error Handling

- Each job is wrapped in a `try/except`; exceptions are caught, logged to Python logger, and a SimulatorLog entry is written with `job_type='error'`
- DB session rollback on exception to avoid dirty state
- Jobs use `max_instances=1` to prevent overlapping execution

---

## Migrations

One new Alembic migration: creates `simulator_configs` and `simulator_logs` tables.

---

## Out of Scope

- Real-time push (SSE/WebSockets) — manual page refresh is sufficient
- Simulation of retros, allocations, initiatives — can be added later
- Multi-org simulation — targets demo org only for now
- Simulation statistics/counters — activity log is sufficient
