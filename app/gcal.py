"""Booking straight onto the operator's Google Calendar (Calendar API, scope calendar.events only).
Set up once with scripts/google_auth.py: it saves GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET and GOOGLE_REFRESH_TOKEN in .env.
Without them the agent falls back to emailing an .ics invite."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta, timezone

import calendar_ics as cal

TOKEN_URL = "https://oauth2.googleapis.com/token"
EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


def configured():
    return all(os.environ.get(k) for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN"))


def _open(req):
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, json.loads(r.read() or b"{}")


def event_id(app_id):
    """Fixed per company, so a retried booking can never create a second event (Google answers 409)."""
    return "aic" + app_id.encode().hex()  # Google allows a-v and 0-9; hex fits


def create_event(app_id, start, summary, description, attendee=None, send_updates=False, opener=None):
    """Creates the event; returns its link. A 401/403 is permanent (CalendarPermission); a timeout or 5xx is retried
    once, then CalendarTimeout. An event that already exists for this company counts as booked."""
    open_ = opener or _open
    fmt = lambda d: d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    body = {"id": event_id(app_id), "summary": summary, "description": description,
            "start": {"dateTime": fmt(start)}, "end": {"dateTime": fmt(start + timedelta(minutes=cal.SLOT_MIN))}}
    if attendee:
        body["attendees"] = [{"email": attendee}]
    for attempt in (1, 2):
        try:
            _, tok = open_(urllib.request.Request(TOKEN_URL, data=urllib.parse.urlencode({
                "client_id": os.environ["GOOGLE_CLIENT_ID"], "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                "refresh_token": os.environ["GOOGLE_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()))
            url = EVENTS_URL + "?sendUpdates=" + ("all" if send_updates else "none")
            _, ev = open_(urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                                 headers={"Authorization": "Bearer " + tok["access_token"], "Content-Type": "application/json"}))
            return ev.get("htmlLink", "")
        except urllib.error.HTTPError as e:
            if e.code == 409:
                return ""  # already booked by an earlier attempt
            if e.code in (400, 401, 403):  # 400 here is invalid_grant: the sign-in was revoked
                raise cal.CalendarPermission("Google Calendar refused the booking (HTTP %d). Run scripts/google_auth.py again." % e.code)
            if attempt == 2:
                raise cal.CalendarTimeout("Google Calendar answered HTTP %d twice." % e.code)
        except Exception as e:
            if attempt == 2:
                raise cal.CalendarTimeout("Could not reach Google Calendar (%s) twice." % type(e).__name__)
