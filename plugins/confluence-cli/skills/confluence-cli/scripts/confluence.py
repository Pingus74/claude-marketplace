#!/usr/bin/env python3
"""Confluence Cloud v2 CLI — Python stdlib only, cross-platform.

Credentials are read from ~/.atlassian-token (KEY=VALUE lines) or from
environment variables (ATLASSIAN_EMAIL, ATLASSIAN_SITE, ATLASSIAN_API_TOKEN).

Run `setup.py` first to create ~/.atlassian-token.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

TOKEN_FILE = Path.home() / ".atlassian-token"


# -------------------- credentials --------------------

def load_credentials() -> tuple[str, str, str]:
    creds: dict[str, str] = {}
    if TOKEN_FILE.exists():
        for line in TOKEN_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            creds[key.strip()] = value.strip()

    email = os.environ.get("ATLASSIAN_EMAIL") or creds.get("ATLASSIAN_EMAIL")
    site = os.environ.get("ATLASSIAN_SITE") or creds.get("ATLASSIAN_SITE")
    token = os.environ.get("ATLASSIAN_API_TOKEN") or creds.get("ATLASSIAN_API_TOKEN")

    missing = [n for n, v in (("ATLASSIAN_EMAIL", email),
                              ("ATLASSIAN_SITE", site),
                              ("ATLASSIAN_API_TOKEN", token)) if not v]
    if missing:
        sys.stderr.write(
            "Credentials missing: " + ", ".join(missing) + "\n"
            "Run: python3 ~/.claude/skills/confluence-cli/scripts/setup.py\n"
            "Or export the env vars for a one-off invocation.\n"
        )
        sys.exit(2)
    return email, site, token  # type: ignore[return-value]


def auth_header(email: str, token: str) -> str:
    return "Basic " + base64.b64encode(
        f"{email}:{token}".encode("utf-8")
    ).decode("ascii")


# -------------------- HTTP --------------------

def http_request(method: str, url: str, email: str, token: str,
                 json_body: Any = None,
                 raw_body: bytes | None = None,
                 extra_headers: dict[str, str] | None = None,
                 timeout: int = 30) -> Any:
    headers = {
        "Authorization": auth_header(email, token),
        "Accept": "application/json",
    }
    body: bytes | None = None
    if json_body is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(json_body).encode("utf-8")
    elif raw_body is not None:
        body = raw_body
    if extra_headers:
        headers.update(extra_headers)

    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            if not raw:
                return None
            content_type = resp.headers.get("Content-Type", "")
            if "json" in content_type:
                return json.loads(raw.decode("utf-8"))
            return raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        sys.stderr.write(
            f"HTTP {e.code} {e.reason} — {method} {url}\n{detail}\n"
        )
        sys.exit(1)
    except urllib.error.URLError as e:
        sys.stderr.write(f"Network error ({method} {url}): {e.reason}\n")
        sys.exit(1)


def print_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def read_body(args) -> str:
    if args.body_file:
        return Path(args.body_file).read_text(encoding="utf-8")
    return args.body  # type: ignore[return-value]


# -------------------- commands --------------------

def cmd_whoami(args, email: str, site: str, token: str) -> None:
    # v1 endpoint, still the canonical "current user" probe
    url = f"https://{site}/wiki/rest/api/user/current"
    print_json(http_request("GET", url, email, token))


def cmd_get_space(args, email: str, site: str, token: str) -> None:
    url = (f"https://{site}/wiki/api/v2/spaces?"
           f"keys={urllib.parse.quote(args.space_key)}&limit=1")
    print_json(http_request("GET", url, email, token))


def cmd_get_page(args, email: str, site: str, token: str) -> None:
    params = {"body-format": args.body_format}
    url = (f"https://{site}/wiki/api/v2/pages/{args.page_id}"
           f"?{urllib.parse.urlencode(params)}")
    print_json(http_request("GET", url, email, token))


def cmd_list_children(args, email: str, site: str, token: str) -> None:
    url = (f"https://{site}/wiki/api/v2/pages/{args.parent_id}/children"
           f"?limit={args.limit}")
    print_json(http_request("GET", url, email, token))


def cmd_list_folder(args, email: str, site: str, token: str) -> None:
    url = (f"https://{site}/wiki/api/v2/folders/{args.folder_id}/children"
           f"?limit={args.limit}")
    print_json(http_request("GET", url, email, token))


def cmd_search(args, email: str, site: str, token: str) -> None:
    # CQL search is a v1 endpoint
    params = {"cql": args.cql, "limit": str(args.limit)}
    if args.expand:
        params["expand"] = args.expand
    url = (f"https://{site}/wiki/rest/api/content/search?"
           f"{urllib.parse.urlencode(params)}")
    print_json(http_request("GET", url, email, token))


def _resolve_space_id(site: str, email: str, token: str,
                      space_key: str) -> str:
    url = (f"https://{site}/wiki/api/v2/spaces?"
           f"keys={urllib.parse.quote(space_key)}&limit=1")
    data = http_request("GET", url, email, token)
    results = data.get("results", []) if isinstance(data, dict) else []
    if not results:
        sys.stderr.write(f"Space {space_key!r} not found\n")
        sys.exit(1)
    return results[0]["id"]


def cmd_create_page(args, email: str, site: str, token: str) -> None:
    body_value = read_body(args)
    space_id = args.space_id or _resolve_space_id(
        site, email, token, args.space_key)

    payload: dict[str, Any] = {
        "spaceId": space_id,
        "status": "current",
        "title": args.title,
        "body": {"representation": args.representation, "value": body_value},
    }
    if args.parent_id:
        payload["parentId"] = args.parent_id

    url = f"https://{site}/wiki/api/v2/pages"
    print_json(http_request("POST", url, email, token, json_body=payload))


def cmd_update_page(args, email: str, site: str, token: str) -> None:
    body_value = read_body(args)

    current_url = f"https://{site}/wiki/api/v2/pages/{args.page_id}"
    current = http_request("GET", current_url, email, token)
    next_version = int(current["version"]["number"]) + 1

    payload = {
        "id": args.page_id,
        "status": "current",
        "title": args.title or current["title"],
        "body": {"representation": args.representation, "value": body_value},
        "version": {"number": next_version, "message": args.message or ""},
    }
    print_json(http_request("PUT", current_url, email, token, json_body=payload))


def cmd_delete_page(args, email: str, site: str, token: str) -> None:
    url = f"https://{site}/wiki/api/v2/pages/{args.page_id}"
    http_request("DELETE", url, email, token)
    print_json({"deleted": args.page_id})


def cmd_list_attachments(args, email: str, site: str, token: str) -> None:
    url = (f"https://{site}/wiki/api/v2/pages/{args.page_id}/attachments"
           f"?limit={args.limit}")
    print_json(http_request("GET", url, email, token))


def cmd_upload_attachment(args, email: str, site: str, token: str) -> None:
    file_path = Path(args.file_path)
    if not file_path.exists():
        sys.stderr.write(f"File not found: {file_path}\n")
        sys.exit(1)

    boundary = "----confluenceskill" + os.urandom(12).hex()
    crlf = b"\r\n"
    parts: list[bytes] = []

    # file part
    parts.append(f"--{boundary}".encode())
    parts.append(crlf)
    parts.append(
        f'Content-Disposition: form-data; name="file"; '
        f'filename="{file_path.name}"'.encode()
    )
    parts.append(crlf)
    parts.append(b"Content-Type: application/octet-stream")
    parts.append(crlf)
    parts.append(crlf)
    parts.append(file_path.read_bytes())
    parts.append(crlf)

    # comment part (optional)
    if args.comment:
        parts.append(f"--{boundary}".encode())
        parts.append(crlf)
        parts.append(b'Content-Disposition: form-data; name="comment"')
        parts.append(crlf)
        parts.append(crlf)
        parts.append(args.comment.encode("utf-8"))
        parts.append(crlf)

    # minorEdit part (optional, Confluence quirk)
    parts.append(f"--{boundary}".encode())
    parts.append(crlf)
    parts.append(b'Content-Disposition: form-data; name="minorEdit"')
    parts.append(crlf)
    parts.append(crlf)
    parts.append(b"true")
    parts.append(crlf)

    # closing boundary
    parts.append(f"--{boundary}--".encode())
    parts.append(crlf)

    body = b"".join(parts)

    url = (f"https://{site}/wiki/rest/api/content/"
           f"{args.page_id}/child/attachment")
    extra = {
        "X-Atlassian-Token": "nocheck",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    result = http_request("POST", url, email, token,
                          raw_body=body, extra_headers=extra, timeout=120)
    print_json(result if result is not None else {"uploaded": file_path.name})


# -------------------- CLI wiring --------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="confluence",
        description="Confluence Cloud CLI (stdlib only).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("whoami", help="Show the current authenticated user.")
    p.set_defaults(func=cmd_whoami)

    p = sub.add_parser("get-space", help="Resolve a space key to space details.")
    p.add_argument("space_key")
    p.set_defaults(func=cmd_get_space)

    p = sub.add_parser("get-page", help="Fetch a page by ID.")
    p.add_argument("page_id")
    p.add_argument(
        "--body-format", default="storage",
        choices=["storage", "atlas_doc_format", "view", "export_view", "wiki"],
    )
    p.set_defaults(func=cmd_get_page)

    p = sub.add_parser("list-children", help="List direct children of a page.")
    p.add_argument("parent_id")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_list_children)

    p = sub.add_parser("list-folder", help="List children of a folder.")
    p.add_argument("folder_id")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_list_folder)

    p = sub.add_parser("search", help="CQL search (v1 API).")
    p.add_argument("cql", help='e.g. \'space=CS AND title ~ "Gross Negligence"\'')
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--expand", help="Comma-separated expand fields.")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("create-page", help="Create a new page.")
    p.add_argument("title")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--space-id")
    g.add_argument("--space-key")
    p.add_argument("--parent-id")
    p.add_argument("--representation", default="storage",
                   choices=["storage", "atlas_doc_format", "wiki"])
    bg = p.add_mutually_exclusive_group(required=True)
    bg.add_argument("--body")
    bg.add_argument("--body-file")
    p.set_defaults(func=cmd_create_page)

    p = sub.add_parser("update-page", help="Update an existing page.")
    p.add_argument("page_id")
    p.add_argument("--title")
    p.add_argument("--representation", default="storage",
                   choices=["storage", "atlas_doc_format", "wiki"])
    p.add_argument("--message", help="Version message (changelog).")
    bg = p.add_mutually_exclusive_group(required=True)
    bg.add_argument("--body")
    bg.add_argument("--body-file")
    p.set_defaults(func=cmd_update_page)

    p = sub.add_parser("delete-page", help="Delete a page (IRREVERSIBLE).")
    p.add_argument("page_id")
    p.set_defaults(func=cmd_delete_page)

    p = sub.add_parser("list-attachments", help="List attachments of a page.")
    p.add_argument("page_id")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_list_attachments)

    p = sub.add_parser("upload-attachment",
                       help="Upload an attachment (multipart) to a page.")
    p.add_argument("page_id")
    p.add_argument("file_path")
    p.add_argument("--comment")
    p.set_defaults(func=cmd_upload_attachment)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    email, site, token = load_credentials()
    args.func(args, email, site, token)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
