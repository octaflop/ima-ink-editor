import marimo

__generated_with = "0.10.0"
app = marimo.App(width="full")


@app.cell
def _imports():
    import marimo as mo
    import httpx
    import yaml
    import os
    import base64
    from datetime import date

    GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
    GITHUB_REPO = os.environ.get("GITHUB_REPO", "octaflop/ima.ink")
    GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")
    API = f"https://api.github.com/repos/{GITHUB_REPO}"
    HEADERS = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    return (
        mo,
        httpx,
        yaml,
        os,
        base64,
        date,
        GITHUB_TOKEN,
        GITHUB_REPO,
        GITHUB_BRANCH,
        API,
        HEADERS,
    )


@app.cell
def _helpers(httpx, base64, API, HEADERS, GITHUB_BRANCH):
    TIMEOUT = 30.0

    def gh_get(path: str) -> dict:
        r = httpx.get(
            f"{API}/{path}",
            headers=HEADERS,
            params={"ref": GITHUB_BRANCH},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()

    def gh_get_file(path: str) -> tuple[str, str]:
        """Returns (decoded_content, sha)."""
        data = gh_get(f"contents/{path}")
        content = base64.b64decode(data["content"]).decode()
        return content, data["sha"]

    def gh_put_file(path: str, content: str, sha: str, message: str) -> dict:
        encoded = base64.b64encode(content.encode()).decode()
        body = {
            "message": message,
            "content": encoded,
            "branch": GITHUB_BRANCH,
        }
        if sha:
            body["sha"] = sha
        r = httpx.put(
            f"{API}/contents/{path}",
            headers=HEADERS,
            json=body,
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()

    def gh_list_dir(path: str) -> list[dict]:
        data = gh_get(f"contents/{path}")
        return data if isinstance(data, list) else []

    def gh_dispatch() -> None:
        """Trigger a repository_dispatch to force a Pages redeploy."""
        r = httpx.post(
            f"{API}/dispatches",
            headers=HEADERS,
            json={"event_type": "data-updated"},
            timeout=TIMEOUT,
        )
        r.raise_for_status()

    return gh_get, gh_get_file, gh_put_file, gh_list_dir, gh_dispatch, TIMEOUT


@app.cell
def _posts_tab(mo, gh_list_dir):
    # ── Posts tab ─────────────────────────────────────────────────────────────
    try:
        entries = gh_list_dir("posts")
        post_dirs = [
            e["name"] for e in entries if e["type"] == "dir" and e["name"] != "template"
        ]
        posts_load_err = mo.md("")
    except Exception as e:
        post_dirs = []
        posts_load_err = mo.callout(mo.md(f"Error listing posts: {e}"), kind="danger")

    post_select = mo.ui.dropdown(options=post_dirs, label="Select post")

    return post_select, post_dirs, posts_load_err


@app.cell
def _post_editor(mo, post_select, gh_get_file):
    if not post_select.value:
        editor = mo.ui.code_editor(value="", language="markdown")
        save_btn = mo.ui.button(label="Save & commit")
        sha = ""
        post_path = ""
        post_load_status = mo.md("")
    else:
        post_path = f"posts/{post_select.value}/index.qmd"
        try:
            content, sha = gh_get_file(post_path)
            post_load_status = mo.md("")
        except Exception as e:
            content = ""
            sha = ""
            post_load_status = mo.callout(
                mo.md(f"Error loading post: {e}"), kind="danger"
            )
        editor = mo.ui.code_editor(value=content, language="markdown")
        save_btn = mo.ui.button(label="Save & commit")
    return editor, save_btn, sha, post_path, post_load_status


@app.cell
def _post_save_action(
    mo,
    GITHUB_REPO,
    GITHUB_BRANCH,
    post_select,
    editor,
    save_btn,
    sha,
    post_path,
    gh_put_file,
):
    post_status = mo.md("")
    if save_btn.value and post_path:
        try:
            _result = gh_put_file(
                post_path, editor.value, sha, f"edit: update {post_select.value}"
            )
            _commit_url = _result.get("commit", {}).get("html_url", "")
            _gh_url = f"https://github.com/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{post_path}"
            _links = (
                f" — [commit]({_commit_url}) · [GitHub]({_gh_url})"
                if _commit_url
                else f" — [GitHub]({_gh_url})"
            )
            post_status = mo.callout(
                mo.md(f"✅ Saved `{post_path}`{_links}"),
                kind="success",
            )
        except Exception as e:
            post_status = mo.callout(mo.md(f"❌ Save failed: {e}"), kind="danger")
    return (post_status,)


@app.cell
def _data_tab(mo):
    # ── Data tab ───────────────────────────────────────────────────────────────
    DATA_FILES = {
        "projects": "_data/projects.yml",
        "talks": "_data/talks.yml",
        "sites": "_data/sites.yml",
    }
    data_select = mo.ui.dropdown(
        options=list(DATA_FILES.keys()), label="Select data file"
    )
    return data_select, DATA_FILES


@app.cell
def _data_editor(mo, data_select, DATA_FILES, gh_get_file):
    if not data_select.value:
        data_editor = mo.ui.code_editor(value="", language="yaml")
        data_save = mo.ui.button(label="Save & commit")
        data_sha = ""
        data_path = ""
        data_load_status = mo.md("")
    else:
        data_path = DATA_FILES[data_select.value]
        try:
            _content, data_sha = gh_get_file(data_path)
            data_load_status = mo.md("")
        except Exception as e:
            _content = ""
            data_sha = ""
            data_load_status = mo.callout(
                mo.md(f"Error loading {data_select.value}: {e}"), kind="danger"
            )
        data_editor = mo.ui.code_editor(value=_content, language="yaml")
        data_save = mo.ui.button(label="Save & commit")
    return data_editor, data_save, data_sha, data_path, data_load_status


@app.cell
def _data_save_action(
    mo,
    GITHUB_REPO,
    GITHUB_BRANCH,
    data_select,
    data_editor,
    data_save,
    data_sha,
    data_path,
    gh_put_file,
):
    data_status = mo.md("")
    if data_save.value and data_path:
        try:
            _result = gh_put_file(
                data_path,
                data_editor.value,
                data_sha,
                f"data: update {data_select.value}",
            )
            _commit_url = _result.get("commit", {}).get("html_url", "")
            _gh_url = f"https://github.com/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{data_path}"
            _links = (
                f" — [commit]({_commit_url}) · [GitHub]({_gh_url})"
                if _commit_url
                else f" — [GitHub]({_gh_url})"
            )
            data_status = mo.callout(
                mo.md(f"✅ Saved `{data_path}`{_links}"), kind="success"
            )
        except Exception as e:
            data_status = mo.callout(mo.md(f"❌ Save failed: {e}"), kind="danger")
    return (data_status,)


@app.cell
def _new_post_tab(mo):
    # ── New post tab ───────────────────────────────────────────────────────────
    title_in = mo.ui.text(label="Title", placeholder="My Post Title")
    slug_in = mo.ui.text(label="Slug", placeholder="my-post-title")
    cats_in = mo.ui.text(
        label="Categories (comma-separated)", placeholder="python, data"
    )
    desc_in = mo.ui.text(label="Description", placeholder="One-line summary")
    create_btn = mo.ui.button(label="Create post")

    return title_in, slug_in, cats_in, desc_in, create_btn


@app.cell
def _new_post_action(
    mo,
    GITHUB_REPO,
    GITHUB_BRANCH,
    gh_get_file,
    gh_put_file,
    date,
    title_in,
    slug_in,
    cats_in,
    desc_in,
    create_btn,
):
    new_post_status = mo.md("")
    if create_btn.value and title_in.value and slug_in.value:
        slug = slug_in.value.strip().lower().replace(" ", "-")
        cats = [c.strip() for c in cats_in.value.split(",") if c.strip()]
        today = date.today().isoformat()
        _template_content = f"""---
title: "{title_in.value}"
date: {today}
categories: {cats}
description: "{desc_in.value}"
publish: false
---

Write the public body here.

::: {{.content-visible when-profile="internal"}}
## Internal context

Internal details for Confluence review.
:::
"""
        _path = f"posts/{slug}/index.qmd"
        _exists = False
        try:
            gh_get_file(_path)
            _exists = True
        except Exception:
            pass  # 404 expected — good

        if _exists:
            new_post_status = mo.callout(
                mo.md(f"⚠️ Post `{slug}` already exists — edit it in the Posts tab"),
                kind="warn",
            )
        else:
            try:
                _result = gh_put_file(
                    _path, _template_content, "", f"post: create {slug}"
                )
                _commit_url = _result.get("commit", {}).get("html_url", "")
                _gh_url = f"https://github.com/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{_path}"
                _links = (
                    f" — [commit]({_commit_url}) · [GitHub]({_gh_url})"
                    if _commit_url
                    else f" — [GitHub]({_gh_url})"
                )
                new_post_status = mo.callout(
                    mo.md(f"✅ Created `{_path}` — edit it in the Posts tab{_links}"),
                    kind="success",
                )
            except Exception as e:
                new_post_status = mo.callout(mo.md(f"❌ Error: {e}"), kind="danger")
    return (new_post_status,)


@app.cell
def _deploy_btn(mo):
    # ── Force redeploy ─────────────────────────────────────────────────────────
    deploy_btn = mo.ui.button(label="Force redeploy ima.ink", kind="danger")
    return (deploy_btn,)


@app.cell
def _deploy_action(mo, gh_dispatch, deploy_btn):
    deploy_status = mo.md("")
    if deploy_btn.value:
        try:
            gh_dispatch()
            deploy_status = mo.callout(
                mo.md("✅ Dispatch sent — GHA will rebuild ima.ink in ~60s"),
                kind="success",
            )
        except Exception as e:
            deploy_status = mo.callout(mo.md(f"❌ Error: {e}"), kind="danger")
    return (deploy_status,)


@app.cell
def _layout(
    mo,
    posts_load_err,
    post_select,
    post_load_status,
    editor,
    save_btn,
    post_status,
    data_select,
    data_load_status,
    data_editor,
    data_save,
    data_status,
    title_in,
    slug_in,
    cats_in,
    desc_in,
    create_btn,
    new_post_status,
    deploy_btn,
    deploy_status,
):
    mo.vstack(
        [
            mo.md("# ima.ink editor"),
            mo.ui.tabs(
                {
                    "Posts": mo.vstack(
                        [
                            posts_load_err,
                            post_select,
                            post_load_status,
                            editor,
                            save_btn,
                            post_status,
                        ]
                    ),
                    "Data": mo.vstack(
                        [
                            data_select,
                            data_load_status,
                            data_editor,
                            data_save,
                            data_status,
                        ]
                    ),
                    "New post": mo.vstack(
                        [
                            title_in,
                            slug_in,
                            cats_in,
                            desc_in,
                            create_btn,
                            new_post_status,
                        ]
                    ),
                }
            ),
            mo.md("---"),
            mo.hstack([deploy_btn, deploy_status], align="center"),
        ]
    )
