---
name: confluence-cli
description: Read, create, update, search, and attach files to Confluence Cloud pages via the v2 REST API. Use whenever the user mentions Confluence, an atlassian.net/wiki URL, wiki pages, publishing/updating documentation on the wiki, or references a Confluence space/folder/page by ID or title. Cross-platform (Python 3 stdlib only).
---

# Confluence CLI skill

All operations go through two Python scripts shipped with the skill:

- `~/.claude/skills/confluence-cli/scripts/setup.py` — one-time interactive credential setup.
- `~/.claude/skills/confluence-cli/scripts/confluence.py` — the actual CLI (read/write/search/attachments).

Both are Python 3, stdlib only, so they run on macOS, Linux, and Windows without extra dependencies.

## Prerequisites & first-time setup

Before the first Confluence operation, credentials must be configured. Check with:

```bash
python3 ~/.claude/skills/confluence-cli/scripts/confluence.py whoami
```

- On success: JSON with the current user → proceed.
- On failure with `Credentials missing`: **STOP. Do not ask the user for the token in chat.** Instead tell the user:

> "Credenziali Confluence non configurate. Lancia nel tuo terminale:
> `python3 ~/.claude/skills/confluence-cli/scripts/setup.py`
> Lo script chiede email, site e API token (input nascosto), valida contro l'API, e salva in `~/.atlassian-token` con chmod 600. Fammi sapere quando hai finito e riprovo."

Wait for the user to confirm before retrying. On Windows the user may need `python` instead of `python3`.

If a call returns HTTP 401/403, credentials are expired or wrong: instruct the user to re-run `setup.py`.

## Commands reference

Always invoke via `python3 ~/.claude/skills/confluence-cli/scripts/confluence.py <cmd>`.

### Read

- `whoami` — current user (also used as health check).
- `get-space <spaceKey>` — resolve a space key (e.g. `CS`) to its space id.
- `get-page <pageId> [--body-format storage|view|atlas_doc_format]` — fetch a page. `storage` is the XHTML subset used for writes; `view` is the rendered HTML for human reading.
- `list-children <pageId> [--limit N]` — direct children pages of a page.
- `list-folder <folderId> [--limit N]` — children of a folder (folders have their own endpoint in v2).
- `search "<CQL>" [--limit N]` — CQL search. Example: `search 'space=CS AND title ~ "Gross Negligence"'`.
- `list-attachments <pageId> [--limit N]` — attachments of a page.

### Write (user confirmation required — see "Safety" below)

- `create-page "<title>" --space-key CS --parent-id <id> --body-file path.xml` — create a new page under a parent.
- `update-page <pageId> --title "<t>" --body-file path.xml` — replace body. Version auto-increments.
- `delete-page <pageId>` — irreversible.
- `upload-attachment <pageId> <file> [--comment "..."]` — upload an image/file to a specific page.

### Body file format

Write body content to a temp file in **storage format** (XHTML subset) and pass it via `--body-file`. Storage format is what the v2 API expects when `--representation storage` (default) is used. For small bodies use `--body '<p>...</p>'` inline.

See `~/.claude/skills/confluence-cli/references/storage-format.md` for a cheatsheet (code blocks, tables, panels, links, images, TOC).

### Templates

`~/.claude/skills/confluence-cli/templates/` contains starter storage-format skeletons:

- `spec-api.xml` — REST endpoint spec (Overview, Endpoint, Request, Response, Errors, Note).
- `flow-doc.xml` — end-to-end flow / technical documentation.
- `adr.xml` — Architecture Decision Record.

Copy to a temp file, fill placeholders (`{{TITLE}}`, `{{OVERVIEW}}`, etc.), then `create-page`.

## Workflows

### Create a new page

1. Ask the user: space key (default `CS`), parent page (ID or title — if title, resolve with `search` first), title of the new page.
2. Pick a template from `templates/` or draft the body inline in storage format.
3. Save the body to a tmp file: `/tmp/conf-body-$$.xml` (on Windows: `%TEMP%\conf-body.xml`).
4. **Show the body preview to the user and ask for explicit approval before posting.**
5. `create-page "<title>" --space-key CS --parent-id <id> --body-file /tmp/conf-body-$$.xml`.
6. Capture the returned `id` and `_links.webui`; report the full URL to the user.

### Update an existing page

1. `get-page <id> --body-format storage` to fetch current body + version.
2. Compute the new body (edit, add section, etc.). Don't silently drop existing content: if in doubt, show a diff first.
3. Save to tmp file. Show preview. Wait for approval.
4. `update-page <id> --title "..." --body-file /tmp/conf-body-$$.xml`. The script GETs the page again to read `version.number` and increments.

### Upload and embed an image

1. User provides an image path (or drops the file in chat — save with Write tool to a local path).
2. `upload-attachment <pageId> /path/to/image.png`.
3. In the page body insert:
   ```xml
   <ac:image><ri:attachment ri:filename="image.png" /></ac:image>
   ```
   Or sized: `<ac:image ac:width="600"><ri:attachment ri:filename="image.png"/></ac:image>`.
4. Update the page with the new body.

### Import an existing markdown file

Confluence does not accept Markdown natively. Two paths:

- If `pandoc` is available: `pandoc input.md -f gfm -t html -o out.html`, wrap in page body (add `<ac:structured-macro>` for code blocks if needed, since pandoc's `<pre><code>` renders but not with syntax highlight).
- If not: convert manually using the cheatsheet in `references/storage-format.md`.

## Safety rules (MANDATORY)

- **Never ask for tokens in chat.** Always redirect to `setup.py`.
- **Never commit** the token file or any credential into git.
- **Writes require confirmation.** Before `create-page`, `update-page`, `delete-page`, or `upload-attachment`, show the user the full preview (body content, target page/space, action summary) and wait for explicit approval in the current turn.
- **`delete-page` is irreversible.** Require the user to say "delete" or equivalent explicit intent, not just "ok".
- **Never retry a 401/403 with a different token guess.** Tell the user to re-run `setup.py`.
- **Respect rate limits.** On HTTP 429, back off and report to the user.
- **Do not dump long page bodies into chat.** Summarize or ask which sections the user wants to see.

## Environment variables (fallback to file)

The script prefers `~/.atlassian-token` but falls back to env vars if set:

- `ATLASSIAN_EMAIL`
- `ATLASSIAN_SITE` (e.g. `coverzen.atlassian.net`)
- `ATLASSIAN_API_TOKEN`

Useful for CI or when the user stores the token in a password manager and exports it per-session.

## Troubleshooting

- `Credentials missing` → run `setup.py`.
- `HTTP 401 Unauthorized` → token wrong or revoked; re-run `setup.py`.
- `HTTP 403 Forbidden` → token valid but user has no permission on that space/page; ask the user to check with an admin.
- `HTTP 404 Not Found` on a page ID → the ID is wrong, or the page was deleted, or the user doesn't have access. Don't guess IDs.
- `HTTP 409 Conflict` on `update-page` → version race condition; re-fetch and retry once.
- `HTTP 429 Too Many Requests` → back off; the skill does not auto-retry.
