# Execution Hub Tab Navigation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Execution Hub sub-tile index page with a persistent underline tab bar (Test Runs | Bugs | Deployments) using URL-based navigation.

**Architecture:** The `/execution/` index route redirects to `/execution/runs`. A shared Jinja2 macro (`_tabs.html`) renders the module header and tab bar; each sub-template imports it and passes its active tab name. Active state is determined server-side — no JS needed.

**Tech Stack:** Flask/Jinja2, vanilla CSS, pytest + pytest-flask

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `app/templates/execution/_tabs.html` | Jinja2 macro: module header + tab bar |
| Modify | `app/static/css/main.css` | Append `.exec-tabs` / `.exec-tab` styles |
| Modify | `app/blueprints/execution/routes.py` | `index()` returns redirect to `execution.runs` |
| Modify | `app/templates/execution/runs.html` | Import macro, fix page_title, add tab bar |
| Modify | `app/templates/execution/bugs.html` | Import macro, fix page_title, add tab bar |
| Modify | `app/templates/execution/deployments.html` | Import macro, fix page_title, add tab bar |
| Delete | `app/templates/execution/index.html` | Replaced by redirect |
| Create | `tests/__init__.py` | Makes tests/ a package |
| Create | `tests/conftest.py` | App + client fixtures |
| Create | `tests/test_execution_tabs.py` | Redirect + tab bar presence tests |

---

## Task 1: Add tab bar CSS

**Files:**
- Modify: `app/static/css/main.css` (append at end of file)

- [ ] **Step 1: Append `.exec-tabs` styles to `main.css`**

Add at the very end of `app/static/css/main.css`:

```css
/* ─── Module Tab Bar ─────────────────────────── */
.exec-tabs {
  display: flex;
  border-bottom: 2px solid var(--color-surface-subtle);
  margin-bottom: 24px;
}

.exec-tab {
  padding: 9px 22px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-muted);
  text-decoration: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: color 0.15s;
}

.exec-tab:hover { color: var(--color-primary); text-decoration: none; }

.exec-tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  font-weight: 700;
}
```

- [ ] **Step 2: Commit**

```bash
git add app/static/css/main.css
git commit -m "feat: add exec-tabs CSS for Execution Hub tab bar"
```

---

## Task 2: Create the `_tabs.html` macro

**Files:**
- Create: `app/templates/execution/_tabs.html`

- [ ] **Step 1: Create the file with the `tab_bar` macro**

Create `app/templates/execution/_tabs.html` with this exact content:

```html
{% macro tab_bar(active) %}
<div class="module-header">
  <div class="module-header-icon">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="2 12 6 12 8 4 10 20 12 11 14 15 16 12 22 12"/>
    </svg>
  </div>
  <div>
    <div class="module-header-title">Execution Hub</div>
    <div class="module-header-desc">Runs, bugs and deployments</div>
  </div>
</div>
<nav class="exec-tabs">
  <a href="{{ url_for('execution.runs') }}"
     class="exec-tab{% if active == 'runs' %} active{% endif %}">Test Runs</a>
  <a href="{{ url_for('execution.bugs') }}"
     class="exec-tab{% if active == 'bugs' %} active{% endif %}">Bugs</a>
  <a href="{{ url_for('execution.deployments') }}"
     class="exec-tab{% if active == 'deployments' %} active{% endif %}">Deployments</a>
</nav>
{% endmacro %}
```

- [ ] **Step 2: Commit**

```bash
git add app/templates/execution/_tabs.html
git commit -m "feat: add Execution Hub tab bar Jinja2 macro"
```

---

## Task 3: Test infrastructure + index redirect (TDD)

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_execution_tabs.py`
- Modify: `app/blueprints/execution/routes.py`

- [ ] **Step 1: Create `tests/__init__.py`**

Create `tests/__init__.py` as an empty file.

- [ ] **Step 2: Create `tests/conftest.py`**

```python
import pytest
from app import create_app
from app.extensions import db as _db
from app.models.user import User
from app.models.organization import Organization


@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
        org = Organization(name='Test Org', slug='test-org')
        _db.session.add(org)
        _db.session.flush()
        user = User(
            email='test@test.com',
            full_name='Test User',
            org_id=org.id,
            role='qa_engineer',
        )
        user.set_password('password123')
        _db.session.add(user)
        _db.session.commit()
        yield app
        _db.drop_all()


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()
```

- [ ] **Step 3: Write failing test for the redirect**

Create `tests/test_execution_tabs.py`:

```python
def test_index_redirects_to_runs(client):
    r = client.get('/execution/', follow_redirects=False)
    assert r.status_code == 302
    assert '/execution/runs' in r.headers['Location']
```

- [ ] **Step 4: Run the test — verify it fails**

```bash
cd /path/to/project && .venv/bin/pytest tests/test_execution_tabs.py::test_index_redirects_to_runs -v
```

Expected: FAIL — the index route currently renders a template, not a redirect, so status code will be 200.

- [ ] **Step 5: Update `routes.py` — make `index()` redirect**

In `app/blueprints/execution/routes.py`, replace the `index` route:

```python
from flask import render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.blueprints.execution import execution_bp
from app.models.test_run import TestRun, TestRunResult
from app.models.bug import Bug
from app.models.test_case import TestSuite


@execution_bp.route('/')
@login_required
def index():
    return redirect(url_for('execution.runs'))
```

(The rest of the routes file is unchanged.)

- [ ] **Step 6: Run the test — verify it passes**

```bash
.venv/bin/pytest tests/test_execution_tabs.py::test_index_redirects_to_runs -v
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add tests/__init__.py tests/conftest.py tests/test_execution_tabs.py app/blueprints/execution/routes.py
git commit -m "feat: redirect /execution/ to /execution/runs, add test infrastructure"
```

---

## Task 4: Add tab bar to `runs.html` (TDD)

**Files:**
- Modify: `app/templates/execution/runs.html`
- Modify: `tests/test_execution_tabs.py`

- [ ] **Step 1: Add failing test**

Append to `tests/test_execution_tabs.py`:

```python
def test_runs_page_has_tab_bar(client):
    r = client.get('/execution/runs')
    assert r.status_code == 200
    assert b'exec-tabs' in r.data
    assert b'Test Runs' in r.data
    assert b'Bugs' in r.data
    assert b'Deployments' in r.data
    assert b'Execution Hub' in r.data
```

- [ ] **Step 2: Run it — verify it fails**

```bash
.venv/bin/pytest tests/test_execution_tabs.py::test_runs_page_has_tab_bar -v
```

Expected: FAIL — `exec-tabs` not yet in the rendered HTML.

- [ ] **Step 3: Replace `runs.html` with this content**

Replace the entire file `app/templates/execution/runs.html`:

```html
{% extends "base.html" %}
{% block title %}Execution Hub — QA Platform{% endblock %}
{% block page_title %}Execution Hub{% endblock %}
{% from 'execution/_tabs.html' import tab_bar %}

{% block content %}
{{ tab_bar('runs') }}
<div class="module-card">
  <div class="flex justify-between items-center" style="margin-bottom:18px;">
    <h2 style="font-size:16px;font-weight:700;">Test Runs</h2>
    <a href="#" class="btn btn-primary btn-sm">&#9654;&nbsp; Trigger Run</a>
  </div>
  {% if runs %}
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <thead><tr style="border-bottom:2px solid var(--color-surface-subtle);">
      <th style="text-align:left;padding:8px 10px;color:var(--color-text-muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em;">Suite</th>
      <th style="text-align:left;padding:8px 10px;color:var(--color-text-muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em;">Status</th>
      <th style="text-align:left;padding:8px 10px;color:var(--color-text-muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em;">Pass Rate</th>
      <th style="text-align:left;padding:8px 10px;color:var(--color-text-muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em;">Started</th>
    </tr></thead>
    <tbody>{% for run in runs %}
    <tr style="border-bottom:1px solid var(--color-surface-subtle);">
      <td style="padding:10px;"><a href="{{ url_for('execution.run_detail', run_id=run.id) }}">{{ run.suite.name if run.suite else 'Run ' + run.id[:8] }}</a></td>
      <td style="padding:10px;"><span class="badge badge-{{ run.status }}">{{ run.status|title }}</span></td>
      <td style="padding:10px;">{{ run.pass_rate }}%</td>
      <td style="padding:10px;color:var(--color-text-muted);font-size:12px;">{{ run.started_at.strftime('%b %d, %H:%M') if run.started_at else '—' }}</td>
    </tr>{% endfor %}</tbody>
  </table>
  {% else %}
  <div class="empty-state" style="padding:60px;">No test runs yet. Trigger your first run to get started.</div>
  {% endif %}
</div>
{% endblock %}
```

- [ ] **Step 4: Run the test — verify it passes**

```bash
.venv/bin/pytest tests/test_execution_tabs.py::test_runs_page_has_tab_bar -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/templates/execution/runs.html tests/test_execution_tabs.py
git commit -m "feat: add tab bar to Test Runs page"
```

---

## Task 5: Add tab bar to `bugs.html` (TDD)

**Files:**
- Modify: `app/templates/execution/bugs.html`
- Modify: `tests/test_execution_tabs.py`

- [ ] **Step 1: Add failing test**

Append to `tests/test_execution_tabs.py`:

```python
def test_bugs_page_has_tab_bar(client):
    r = client.get('/execution/bugs')
    assert r.status_code == 200
    assert b'exec-tabs' in r.data
    assert b'Test Runs' in r.data
    assert b'Bugs' in r.data
    assert b'Deployments' in r.data
    assert b'Execution Hub' in r.data
```

- [ ] **Step 2: Run it — verify it fails**

```bash
.venv/bin/pytest tests/test_execution_tabs.py::test_bugs_page_has_tab_bar -v
```

Expected: FAIL

- [ ] **Step 3: Replace `bugs.html` with this content**

Replace the entire file `app/templates/execution/bugs.html`:

```html
{% extends "base.html" %}
{% block title %}Execution Hub — QA Platform{% endblock %}
{% block page_title %}Execution Hub{% endblock %}
{% from 'execution/_tabs.html' import tab_bar %}

{% block content %}
{{ tab_bar('bugs') }}
<div class="module-card">
  <div class="flex justify-between items-center" style="margin-bottom:18px;">
    <h2 style="font-size:16px;font-weight:700;">Open Bugs</h2>
    <a href="#" class="btn btn-primary btn-sm">+ Log Bug</a>
  </div>
  {% if bugs %}
    {% for bug in bugs %}
    <div class="item-row">
      <span class="badge badge-{{ bug.severity }}">{{ bug.severity|title }}</span>
      <div class="item-name">{{ bug.title }}</div>
      <span class="badge badge-{{ 'warning' if bug.status == 'in_progress' else 'danger' }}">{{ bug.status|replace('_',' ')|title }}</span>
    </div>
    {% endfor %}
  {% else %}
  <div class="empty-state" style="padding:60px;">No open bugs. All clear!</div>
  {% endif %}
</div>
{% endblock %}
```

- [ ] **Step 4: Run the test — verify it passes**

```bash
.venv/bin/pytest tests/test_execution_tabs.py::test_bugs_page_has_tab_bar -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/templates/execution/bugs.html tests/test_execution_tabs.py
git commit -m "feat: add tab bar to Bugs page"
```

---

## Task 6: Add tab bar to `deployments.html` (TDD)

**Files:**
- Modify: `app/templates/execution/deployments.html`
- Modify: `tests/test_execution_tabs.py`

- [ ] **Step 1: Add failing test**

Append to `tests/test_execution_tabs.py`:

```python
def test_deployments_page_has_tab_bar(client):
    r = client.get('/execution/deployments')
    assert r.status_code == 200
    assert b'exec-tabs' in r.data
    assert b'Test Runs' in r.data
    assert b'Bugs' in r.data
    assert b'Deployments' in r.data
    assert b'Execution Hub' in r.data
```

- [ ] **Step 2: Run it — verify it fails**

```bash
.venv/bin/pytest tests/test_execution_tabs.py::test_deployments_page_has_tab_bar -v
```

Expected: FAIL

- [ ] **Step 3: Replace `deployments.html` with this content**

Replace the entire file `app/templates/execution/deployments.html`:

```html
{% extends "base.html" %}
{% block title %}Execution Hub — QA Platform{% endblock %}
{% block page_title %}Execution Hub{% endblock %}
{% from 'execution/_tabs.html' import tab_bar %}

{% block content %}
{{ tab_bar('deployments') }}
<div class="module-card">
  <div class="empty-state" style="padding:80px;">
    Connect GitHub to see CI/CD pipeline status here.
    <br/><a href="{{ url_for('automation.internal_tools') }}" class="btn btn-primary mt-3">Connect GitHub</a>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Run the test — verify it passes**

```bash
.venv/bin/pytest tests/test_execution_tabs.py::test_deployments_page_has_tab_bar -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/templates/execution/deployments.html tests/test_execution_tabs.py
git commit -m "feat: add tab bar to Deployments page"
```

---

## Task 7: Clean up — delete index template, run full suite

**Files:**
- Delete: `app/templates/execution/index.html`

- [ ] **Step 1: Delete the old index template**

```bash
git rm app/templates/execution/index.html
```

- [ ] **Step 2: Run the full test suite**

```bash
.venv/bin/pytest tests/test_execution_tabs.py -v
```

Expected output:
```
tests/test_execution_tabs.py::test_index_redirects_to_runs PASSED
tests/test_execution_tabs.py::test_runs_page_has_tab_bar PASSED
tests/test_execution_tabs.py::test_bugs_page_has_tab_bar PASSED
tests/test_execution_tabs.py::test_deployments_page_has_tab_bar PASSED

4 passed
```

- [ ] **Step 3: Final commit**

```bash
git commit -m "feat: remove Execution Hub index tile page (replaced by tab redirect)"
```
