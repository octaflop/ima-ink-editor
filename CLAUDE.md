# ima-ink-editor

A minimal marimo-based web CMS for editing content in the [ima.ink](../ima.ink) GitHub Pages site.

## Project Overview

Single-file marimo app (`editor.py`) that connects to the `ima.ink` GitHub repo via API and provides a UI for:
- Editing existing posts (`.qmd` files in `posts/`)
- Managing YAML data files (`_data/projects.yml`, `_data/talks.yml`, `_data/sites.yml`)
- Creating new posts from the `posts/template/index.qmd` template
- Triggering site rebuilds via GitHub Actions (`repository_dispatch`)

Saves are committed directly to GitHub; GHA runs `quarto render --profile public` and deploys to Cloudflare Pages.

## Endpoint Repo: ima.ink

Located at `../ima.ink`. Key paths this editor reads/writes:

| Path | Purpose |
|------|---------|
| `posts/` | Blog posts as `.qmd` files with YAML frontmatter |
| `_data/projects.yml` | Projects registry |
| `_data/talks.yml` | Talks registry |
| `_data/sites.yml` | Sites registry |

### Post frontmatter schema
```yaml
---
title: "Post Title"
date: 2026-01-01
categories: [python, data]
description: "One-line summary for the public listing."
publish: false   # set to true when ready
---
```

### Data file schema (projects.yml example)
```yaml
- id: ducktiles
  title: "DuckTiles"
  description: "..."
  url: https://...
  repo: owner/repo
  tags: [python, duckdb]
  featured: true
  status: active  # active | archived
```

## Setup

```bash
cp .env.example .env
# Edit .env with real values
```

Required env vars:
- `GITHUB_TOKEN` — fine-grained PAT with contents read+write on the `ima.ink` repo
- `GITHUB_REPO` — e.g. `octaflop/ima.ink`
- `GITHUB_BRANCH` — e.g. `main`

## Running

```bash
uv run marimo run editor.py    # app mode (production)
uv run marimo edit editor.py   # edit mode (development)
```

## Stack

- **Python** 3.12+
- **marimo** — reactive notebook framework (UI)
- **httpx** — GitHub API HTTP client
- **PyYAML** — YAML parsing for data files
- **uv** — package manager (`uv run` prefix for all commands)
- **ruff** — linter/formatter

```bash
uv run ruff check editor.py
uv run ruff format editor.py
```

## Architecture

All logic lives in `editor.py` as marimo cells. Convention: `_<name>` prefix = private cell.

| Cell | Role |
|------|------|
| `_imports` | env config + imports |
| `_helpers` | GitHub API (`gh_get`, `gh_get_file`, `gh_put_file`, `gh_list_dir`, `gh_dispatch`) |
| `_posts_tab` / `_post_editor` / `_post_save_action` | posts CRUD |
| `_data_tab` / `_data_editor` / `_data_save_action` | YAML data files CRUD |
| `_new_post_tab` / `_new_post_action` | new post creation |
| `_deploy_btn` / `_deploy_action` | trigger GHA rebuild |
| `_layout` | final UI (tabs + deploy button) |

## marimo Gotchas

- `marimo.toml` must have `auto_instantiate = true` for app mode to work
- Return placeholder widgets instead of calling `mo.stop(False)` — marimo 0.22+ compatibility
- `mo.stop(condition, output)` halts cell execution when condition is truthy
- Cells return their last expression as output

## Container

```bash
docker build -f Containerfile -t ima-editor .
docker run -e GITHUB_TOKEN=$TOKEN -p 2719:2719 ima-editor
# Port 2719; auth handled upstream by oauth2-proxy
```
