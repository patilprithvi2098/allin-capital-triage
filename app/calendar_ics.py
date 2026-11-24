"""The operator's calendar, read-only, from its secret iCal address (CALENDAR_ICS_URL), and booking by calendar invite.
Slots: Tuesday or Thursday afternoons, 30 minutes, India time (the partners' rule in the meeting notes).
shortcut: recurring events (RRULE) are read only at their first occurrence; switch to the Calendar API if the operator's
calendar relies on repeating meetings for busy time."""
import os
import re
import urllib.error
import urllib.request
import uuid
from datetime import date, datetime, time, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
SLOT_MIN, DAYS = 30, (1, 3)  # Tuesday, Thursday
HOURS = [(14, 0), (14, 30), (15, 0), (15, 30), (16, 0), (16, 30), (17, 0), (17, 30)]


class CalendarTimeout(Exception):
    pass


class CalendarPermission(Exception):
    """Permanent: the link was revoked or is wrong. Never retried."""


def fetch(url=None, opener=None):
    """The ICS text. One retry on a timeout, then CalendarTimeout; a 401/403/404 is permanent (CalendarPermission)."""
    url = url or os.environ.get("CALENDAR_ICS_URL", "")
    if not url.startswith("https://"):
        raise CalendarPermission("CALENDAR_ICS_URL is not set to an https iCal address.")
    open_ = opener or (lambda u: urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "allin-triage/0.1"}), timeout=15).read().decode("utf-8", "replace"))
    for attempt in (1, 2):
        try:
            return open_(url)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404, 410):
                raise CalendarPermission("The calendar link answered HTTP %d (revoked or wrong)." % e.code)
            if attempt == 2:
                raise CalendarTimeout("The calendar answered HTTP %d twice." % e.code)
        except Exception as e:  # timeouts and connection errors
            if attempt == 2:
                raise CalendarTimeout("Could not read the calendar (%s) twice." % type(e).__name__)


def _dt(value, params):
    value = value.strip()
    if re.fullmatch(r"\d{8}", value):  # all-day: busy from midnight to midnight India time
        return datetime.strptime(value, "%Y%m%d").replace(tzinfo=IST)
    if value.endswith("Z"):
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    naive = datetime.strptime(value[:15], "%Y%m%dT%H%M%S")
    return naive.replace(tzinfo=IST)  # shortcut: a TZID other than India time is read as India time; fine for this operator


def busy(ics_text):
    """[(start, end)] for every event that is not marked free (TRANSP:TRANSPARENT) or cancelled."""
    text = re.sub(r"\r?\n[ \t]", "", ics_text)  # unfold long lines
    out = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, re.S):
        if re.search(r"^TRANSP:TRANSPARENT", block, re.M) or re.search(r"^STATUS:CANCELLED", block, re.M):
            continue
        s = re.search(r"^DTSTART([^:]*):(.+)$", block, re.M)
        e = re.search(r"^DTEND([^:]*):(.+)$", block, re.M)
        if not s:
            continue
        start = _dt(s.group(2), s.group(1))
        all_day = re.fullmatch(r"\d{8}", s.group(2).strip())
        end = _dt(e.group(2), e.group(1)) if e else start + (timedelta(days=1) if all_day else timedelta(minutes=30))
        out.append((start, end))
    return out


def free_slots(busy_times, now, days=14, limit=3):
    """The next free Tuesday or Thursday afternoon 30-minute slots, at least 24 hours ahead."""
    earliest, slots = now + timedelta(hours=24), []
    for d in range(days + 1):
        day = (now.astimezone(IST) + timedelta(days=d)).date()
        if day.weekday() not in DAYS:
            continue
        for h, m in HOURS:
            start = datetime.combine(day, time(h, m), IST)
            end = start + timedelta(minutes=SLOT_MIN)
            if start >= earliest and not any(s < end and start < e for s, e in busy_times):
                slots.append(start)
                break  # one slot per day keeps the email short; days give the founder the choice
        if len(slots) == limit:
            break
    return slots


def is_free(busy_times, start):
    end = start + timedelta(minutes=SLOT_MIN)
    return start.astimezone(IST).weekday() in DAYS and not any(s < end and start < e for s, e in busy_times)


def allowed(start, now, days=14):
    """A time the founder proposes must follow the same rule as the slots we offer: a Tue/Thu afternoon slot in India
    time, at least 24 hours ahead and within two weeks."""
    t = start.astimezone(IST)
    return (t.hour, t.minute) in HOURS and t.weekday() in DAYS and now + timedelta(hours=24) <= start <= now + timedelta(days=days)


def label(dt):
    return dt.astimezone(IST).strftime("%a %d %b, %-I:%M %p IST")


def invite(start, summary, description, organizer, attendees, uid=None):
    """An iCalendar REQUEST that Gmail and Google Calendar show as an invitation."""
    stamp = lambda d: d.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")  # noqa: E731
    lines = ["BEGIN:VCALENDAR", "PRODID:-//All In Capital triage//EN", "VERSION:2.0", "METHOD:REQUEST", "BEGIN:VEVENT",
             "UID:%s" % (uid or "%s@allin-triage.local" % uuid.uuid4()), "DTSTAMP:%s" % stamp(datetime.now(timezone.utc)),
             "DTSTART:%s" % stamp(start), "DTEND:%s" % stamp(start + timedelta(minutes=SLOT_MIN)),
             "SUMMARY:%s" % summary.replace("\n", " "), "DESCRIPTION:%s" % description.replace("\n", "\\n"),
             "ORGANIZER;CN=All In Capital:mailto:%s" % organizer]
    lines += ["ATTENDEE;RSVP=TRUE;PARTSTAT=NEEDS-ACTION:mailto:%s" % a for a in attendees]
    lines += ["STATUS:CONFIRMED", "END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(lines) + "\r\n"

