"""One-time Google sign-in so the scheduling agent can put meetings on your calendar.
Reads the "Desktop app" OAuth client from its downloaded JSON in Downloads (or from .env); see docs/mesa/google-calendar.md.
Run: python3 scripts/google_auth.py   It opens Google's consent page, waits for you on 127.0.0.1, and saves
GOOGLE_REFRESH_TOKEN in .env. Nothing secret is printed. Access asked for: calendar events only."""
import http.server
import json
import os
import re
import secrets
import sys
import time
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

ENV = Path(__file__).resolve().parent.parent / ".env"
SCOPE = "https://www.googleapis.com/auth/calendar.events"


def env():
    out = {}
    for line in (ENV.read_text() if ENV.exists() else "").splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip("\"'")
    return out


def save(name, value):
    text = ENV.read_text()
    line = "%s=%s" % (name, value)
    text = re.sub(r"(?m)^%s=.*$" % name, lambda m: line, text) if re.search(r"(?m)^%s=" % name, text) else text.rstrip("\n") + "\n" + line + "\n"
    ENV.write_text(text)
    os.chmod(ENV, 0o600)


def from_download():
    """The client file Google offers as "Download JSON": a path given on the command line, else the newest
    client_secret_*.json in Downloads. Its two values are saved in .env; the file itself is left where it is."""
    paths = [Path(a).expanduser() for a in sys.argv[1:]] or sorted(Path.home().joinpath("Downloads").glob("client_secret_*.json"), key=lambda p: p.stat().st_mtime)
    if not paths:
        return
    c = json.loads(paths[-1].read_text())
    c = c.get("installed") or c.get("web") or {}
    if c.get("client_id") and c.get("client_secret"):
        save("GOOGLE_CLIENT_ID", c["client_id"])
        save("GOOGLE_CLIENT_SECRET", c["client_secret"])
        print("Read the client from %s and saved GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET." % paths[-1].name)


e = env()
if not e.get("GOOGLE_CLIENT_ID") or not e.get("GOOGLE_CLIENT_SECRET"):
    from_download()
    e = env()
cid, csec = e.get("GOOGLE_CLIENT_ID"), e.get("GOOGLE_CLIENT_SECRET")
if not cid or not csec:
    sys.exit("No Google client found. On the client's page in Google Cloud Console click Download JSON, then run this again.")
state, got = secrets.token_urlsafe(16), {}


class Back(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
        if q.get("state") != state:  # not our sign-in: ignore
            self.send_response(400); self.end_headers(); return
        got.update(q)
        self.send_response(200); self.send_header("Content-Type", "text/plain; charset=utf-8"); self.end_headers()
        self.wfile.write(("Signed in. You can close this tab." if "code" in q else "Sign-in cancelled.").encode())

    def log_message(self, *a):
        pass


srv = http.server.HTTPServer(("127.0.0.1", 0), Back)
redirect = "http://127.0.0.1:%d" % srv.server_port
url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": SCOPE,
    "access_type": "offline", "prompt": "consent", "state": state})
print("Opening Google sign-in in your browser. If it does not open, paste this link into it:\n" + url)
webbrowser.open(url)
srv.timeout, deadline = 30, time.time() + 300
while not got and time.time() < deadline:
    srv.handle_request()  # a stray request (favicon, wrong state) is ignored and we keep waiting
if not got:
    sys.exit("No answer from Google within 5 minutes. Run it again.")
if "code" not in got:
    sys.exit("Sign-in cancelled (%s). Nothing saved." % got.get("error", "no code"))
req = urllib.request.Request("https://oauth2.googleapis.com/token", data=urllib.parse.urlencode({
    "code": got["code"], "client_id": cid, "client_secret": csec, "redirect_uri": redirect, "grant_type": "authorization_code"}).encode())
tok = json.loads(urllib.request.urlopen(req, timeout=20).read())
if "refresh_token" not in tok:
    sys.exit("Google gave no refresh token. Remove the app's access at myaccount.google.com/permissions and run again.")
save("GOOGLE_REFRESH_TOKEN", tok["refresh_token"])
print("Saved GOOGLE_REFRESH_TOKEN. The scheduling agent now books straight onto your Google Calendar.")
