#!/usr/bin/env python3
"""
post.py - publish an approved draft to the user's own LinkedIn feed through
LinkedIn's official Posts API (product: "Share on LinkedIn", scope
w_member_social). No browser automation, no scraping.

It always shows the exact text and asks for a typed "yes" before sending,
unless --yes is passed. --dry-run never touches the network.

Token lookup, first hit wins:
  1. $LINKEDIN_ACCESS_TOKEN
  2. ~/.claude/linkedin/token   (written by auth.py)

Usage
  python3 post.py draft.txt --dry-run
  python3 post.py draft.txt
  python3 post.py draft.txt --visibility CONNECTIONS
  cat draft.txt | python3 post.py -
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request

API = "https://api.linkedin.com"
TOKEN_FILE = os.path.expanduser("~/.claude/linkedin/token")
MAX_CHARS = 3000

# Reserved characters in LinkedIn's "little text format". Unescaped, they
# make the API reject or silently truncate the commentary.
RESERVED = set("\\|{}@[]()<>#*_~")
HASHTAG_RE = re.compile(r"#(\w+)")


def api_version():
    """LinkedIn-Version header (YYYYMM). Versions ship monthly and live for
    about a year, so last month is always a safe default."""
    if os.environ.get("LINKEDIN_VERSION"):
        return os.environ["LINKEDIN_VERSION"]
    first = datetime.date.today().replace(day=1)
    return (first - datetime.timedelta(days=1)).strftime("%Y%m")


def escape(text):
    """Escape reserved chars; keep #tags clickable as hashtag templates."""
    out, pos = [], 0
    for m in HASHTAG_RE.finditer(text):
        out.append("".join("\\" + c if c in RESERVED else c
                           for c in text[pos:m.start()]))
        out.append("{hashtag|\\#|%s}" % m.group(1))
        pos = m.end()
    out.append("".join("\\" + c if c in RESERVED else c for c in text[pos:]))
    return "".join(out)


def load_token():
    tok = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip()
    if not tok and os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, encoding="utf-8") as fh:
            tok = fh.read().strip()
    if not tok:
        sys.exit("No token. Run auth.py first, or set LINKEDIN_ACCESS_TOKEN.")
    return tok


def call(method, path, token, body=None, rest=False):
    headers = {"Authorization": "Bearer " + token}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if rest:
        headers["LinkedIn-Version"] = api_version()
        headers["X-Restli-Protocol-Version"] = "2.0.0"
    req = urllib.request.Request(API + path, data=data, headers=headers,
                                 method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8") or "{}"
            return resp.status, dict(resp.headers), json.loads(raw)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        hint = {401: "token expired or wrong - rerun auth.py",
                403: "app is missing 'Share on LinkedIn' / w_member_social",
                426: "LinkedIn-Version is retired - set LINKEDIN_VERSION=YYYYMM"
                }.get(e.code, "")
        sys.exit(f"LinkedIn API {e.code} on {path}: {detail}\n{hint}".rstrip())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="draft file, or - for stdin")
    ap.add_argument("--visibility", choices=["PUBLIC", "CONNECTIONS"],
                    default="PUBLIC")
    ap.add_argument("--dry-run", action="store_true",
                    help="show the request body, send nothing")
    ap.add_argument("--yes", action="store_true",
                    help="skip the typed confirmation")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    text = raw.strip()
    if not text:
        sys.exit("Draft is empty.")
    if len(text) > MAX_CHARS:
        sys.exit(f"Draft is {len(text)} chars; LinkedIn's limit is {MAX_CHARS}.")
    if "{{" in text:
        sys.exit("Draft still has a {{placeholder}}. Fill it in first.")

    print("=" * 62)
    print(text)
    print("=" * 62)
    print(f"{len(text)} chars  |  visibility {args.visibility}")

    body = {
        "author": None,
        "commentary": escape(text),
        "visibility": args.visibility,
        "distribution": {"feedDistribution": "MAIN_FEED",
                         "targetEntities": [],
                         "thirdPartyDistributionChannels": []},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    if args.dry_run:
        body["author"] = "urn:li:person:<you>"
        print("\nDRY RUN - would POST /rest/posts "
              f"(LinkedIn-Version {api_version()}):")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        return

    if not args.yes:
        if input("\nType yes to publish this to LinkedIn: ").strip().lower() != "yes":
            sys.exit("Not posted.")

    token = load_token()
    _, _, me = call("GET", "/v2/userinfo", token)
    body["author"] = "urn:li:person:" + me["sub"]

    _, headers, _ = call("POST", "/rest/posts", token, body, rest=True)
    urn = {k.lower(): v for k, v in headers.items()}.get("x-restli-id", "")
    print("\nPosted." + (f"  https://www.linkedin.com/feed/update/{urn}/" if urn else ""))


if __name__ == "__main__":
    main()
