# Execution Hub — Tab Navigation Design

**Date:** 2026-05-23
**Status:** Approved

## Overview

Replace the current Execution Hub sub-tile index page with a unified tabbed view. Test Runs, Bugs, and Deployments are presented as URL-based underline tabs on a single persistent layout — no more intermediate landing page with tiles.

## Tab Style

Underline tabs: a horizontal strip with a `2px` bottom border on the active tab, using the app's primary brown (`#8B7355`). Inactive tabs are muted grey; hover state transitions to brown. CSS goes in `main.css` so the pattern is reusable across other modules.

## Navigation Model

URL-based: each tab is a distinct Flask route. Clicking a tab navigates to its route; the browser URL changes and each tab is bookmarkable.

| Tab | Route |
|-----|-------|
| Test Runs | `/execution/runs` |
| Bugs | `/execution/bugs` |
| Deployments | `/execution/deployments` |

`/execution/` redirects to `/execution/runs` (the default tab). The sub-tile index template (`execution/index.html`) is removed.

## Layout Structure

Every Execution Hub sub-page shares the same top section:

1. **Module header** — icon + "Execution Hub" title + subtitle (already present on sub-pages, needs to be consistent)
2. **Tab bar** — underline tabs for Test Runs | Bugs | Deployments, active tab determined by current route
3. **Page content** — existing content for that sub-page, unchanged

The active tab is determined server-side: each template passes a `active_tab` value (`'runs'`, `'bugs'`, `'deployments'`) and the tab bar macro uses it to apply the active class.

## Implementation

### Jinja2 Macro

A `{% macro tab_bar(active) %}` is defined in a new partial `app/templates/execution/_tabs.html`. Each of the 3 sub-templates includes it with `{% from 'execution/_tabs.html' import tab_bar %}` and calls `{{ tab_bar('runs') }}` etc. This keeps the tab bar written once.

### Route Change

`execution/index` route changes from `render_template` to `redirect(url_for('execution.runs'))`.

### Templates Modified

- `execution/runs.html` — add module header + `{{ tab_bar('runs') }}`
- `execution/bugs.html` — add module header + `{{ tab_bar('bugs') }}`
- `execution/deployments.html` — add module header + `{{ tab_bar('deployments') }}`
- `execution/index.html` — deleted (replaced by redirect)

### CSS

Tab bar styles added to `app/static/css/main.css` under a `.exec-tabs` block:

```css
.exec-tabs { display: flex; border-bottom: 2px solid var(--color-surface-subtle); margin-bottom: 20px; }
.exec-tab  { padding: 9px 20px; font-size: 13px; font-weight: 500; color: var(--color-text-muted);
             border-bottom: 2px solid transparent; margin-bottom: -2px; text-decoration: none; }
.exec-tab:hover { color: var(--color-primary); }
.exec-tab.active { color: var(--color-primary); border-bottom-color: var(--color-primary); font-weight: 700; }
```

## What Does Not Change

- Flask routes for `/execution/runs`, `/execution/bugs`, `/execution/deployments` — logic untouched
- Data queries inside each route — untouched
- `run_detail` route and template — untouched
- Breadcrumb in topbar — changed to "Execution Hub" on all 3 sub-pages (currently each says its own name e.g. "Test Runs"; the `page_title` block in each template is updated to "Execution Hub")
- Grid nav dropdown link to Execution Hub — still points to `/execution/` (which now redirects to runs)

## Out of Scope

- Content changes inside any tab (data, actions, filtering)
- Adding tabs to other modules
