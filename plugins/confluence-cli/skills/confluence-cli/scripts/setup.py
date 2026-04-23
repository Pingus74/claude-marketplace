#!/usr/bin/env python3
"""Interactive credential setup for the confluence-cli skill.

Prompts for Atlassian email, site, and API token (hidden input), validates
them with a test API call (`/wiki/api/v2/spaces?limit=1`), and writes them
to ~/.atlassian-token with chmod 600 (POSIX) / user-only ACL (Windows).

No external dependencies; uses Python stdlib only.
"""
from __future__ import annotations

import base64
import getpass
import json
import os
import platform
import stat
import sys
import urllib.error
import urllib.request
from pathlib import Path

TOKEN_FILE = Path.home() / ".atlassian-token"
DEFAULT_SITE = "coverzen.atlassian.net"
VALIDATE_URL_TEMPLATE = "https://{site}/wiki/api/v2/spaces?limit=1"
WHOAMI_URL_TEMPLATE = "https://{site}/wiki/rest/api/user/current"


def prompt(label: str, default: str | None = None, secret: bool = False) -> str:
    if secret:
        return getpass.getpass(f"{label}: ").strip()
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or (default or "")


def _auth_header(email: str, token: str) -> str:
    encoded = base64.b64encode(f"{email}:{token}".encode("utf-8")).decode("ascii")
    return f"Basic {encoded}"


def _http_get(url: str, email: str, token: str, timeout: int = 15):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": _auth_header(email, token),
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def validate_credentials(email: str, site: str, token: str) -> tuple[bool, str]:
    try:
        _http_get(VALIDATE_URL_TEMPLATE.format(site=site), email, token)
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        return False, f"HTTP {e.code} {e.reason}. {detail}".strip()
    except urllib.error.URLError as e:
        return False, f"Network error: {e.reason}"
    except Exception as e:
        return False, f"Unexpected error: {e}"

    # Try whoami for a friendlier confirmation message
    try:
        me = _http_get(WHOAMI_URL_TEMPLATE.format(site=site), email, token)
        name = me.get("displayName") or me.get("publicName") or email
        return True, f"connected as {name}"
    except Exception:
        return True, "connected"


def write_token_file(email: str, site: str, token: str) -> None:
    content = (
        f"ATLASSIAN_EMAIL={email}\n"
        f"ATLASSIAN_SITE={site}\n"
        f"ATLASSIAN_API_TOKEN={token}\n"
    )
    TOKEN_FILE.write_text(content, encoding="utf-8")
    if platform.system() != "Windows":
        os.chmod(TOKEN_FILE, stat.S_IRUSR | stat.S_IWUSR)
    else:
        # Best-effort: restrict to current user via icacls; ignore failures
        try:
            import subprocess

            user = os.environ.get("USERNAME", "")
            if user:
                subprocess.run(
                    ["icacls", str(TOKEN_FILE), "/inheritance:r",
                     "/grant:r", f"{user}:F"],
                    check=False,
                    capture_output=True,
                )
        except Exception:
            pass


def main() -> int:
    print("Confluence CLI skill — credential setup")
    print(f"Target file: {TOKEN_FILE}")
    print()

    if TOKEN_FILE.exists():
        print(f"Note: {TOKEN_FILE} already exists. Continuing will overwrite it.")
        answer = input("Overwrite? [y/N]: ").strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted. No changes.")
            return 1
        print()

    email = prompt("Atlassian email")
    if not email:
        print("Email is required.", file=sys.stderr)
        return 1

    site = prompt("Atlassian site", DEFAULT_SITE)
    if not site:
        print("Site is required.", file=sys.stderr)
        return 1

    print("Paste your API token (input hidden). Generate one at:")
    print("  https://id.atlassian.com/manage-profile/security/api-tokens")
    token = prompt("API token", secret=True)
    if not token:
        print("Token is required.", file=sys.stderr)
        return 1

    print()
    print("Validating credentials...", end=" ", flush=True)
    ok, info = validate_credentials(email, site, token)
    if not ok:
        print("FAILED")
        print(f"  Reason: {info}", file=sys.stderr)
        print("Double-check email, site, and token. Token must be unrevoked.",
              file=sys.stderr)
        return 2
    print(f"OK — {info}")

    write_token_file(email, site, token)
    print(f"Saved to {TOKEN_FILE}")
    if platform.system() != "Windows":
        print("Permissions: 0600 (user read/write only).")
    print()
    print("Done. You can now use the confluence-cli skill.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(130)
