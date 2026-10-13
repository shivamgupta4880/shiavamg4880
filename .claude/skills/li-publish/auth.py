#!/usr/bin/env python3
"""
auth.py - one-time LinkedIn sign-in that gets an access token for post.py.

Run it on your own computer (it opens a browser and listens on localhost).
Needs your developer app's credentials in the environment:

  export LINKEDIN_CLIENT_ID=...
  export LINKEDIN_CLIENT_SECRET=...
  python3 auth.py

Your app must list this exact redirect URL under Auth -> Authorized redirect
URLs:  http://localhost:8765/callback

The token is saved to ~/.claude/linkedin/token (readable only by you) and
lasts 60 days. Rerun this when post.py says the token expired.
"""

import http.server
import json
import os
import secrets
import sys
import urllib.parse
import urllib.request
import webbrowser

PORT = 8765
REDIRECT = f"http://localhost:{PORT}/callback"
SCOPES = "openid profile w_member_social"
TOKEN_FILE = os.path.expanduser("~/.claude/linkedin/token")


def main():
    cid = os.environ.get("LINKEDIN_CLIENT_ID")
    secret = os.environ.get("LINKEDIN_CLIENT_SECRET")
    if not cid or not secret:
        sys.exit("Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET first.")

    state = secrets.token_urlsafe(16)
    url = "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode({
        "response_type": "code", "client_id": cid, "redirect_uri": REDIRECT,
        "state": state, "scope": SCOPES})

    got = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            got.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Done. You can close this tab and go back to the terminal.")

        def log_message(self, *a):
            pass

    print("Opening LinkedIn sign-in. If no browser opens, visit:\n" + url)
    webbrowser.open(url)
    with http.server.HTTPServer(("127.0.0.1", PORT), Handler) as srv:
        while "code" not in got and "error" not in got:
            srv.handle_request()

    if "error" in got:
        sys.exit(f"LinkedIn said: {got['error']} - {got.get('error_description', '')}")
    if got.get("state") != state:
        sys.exit("State mismatch - sign-in response was not ours. Try again.")

    data = urllib.parse.urlencode({
        "grant_type": "authorization_code", "code": got["code"],
        "redirect_uri": REDIRECT, "client_id": cid,
        "client_secret": secret}).encode()
    req = urllib.request.Request("https://www.linkedin.com/oauth/v2/accessToken",
                                 data=data, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        tok = json.load(resp)

    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(tok["access_token"])
    days = tok.get("expires_in", 0) // 86400
    print(f"Saved token to {TOKEN_FILE} (valid ~{days} days).")


if __name__ == "__main__":
    main()
