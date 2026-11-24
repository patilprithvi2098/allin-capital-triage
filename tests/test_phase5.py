"""Phase 5: email safety (allowlist, suppression), Riya's edits stored, and the scheduling agent's rules at their
boundaries (lecture 7 decisions 6 to 8). No network: mail, calendar and models are faked."""
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
os.environ.update(OPERATOR_EMAIL="operator@example.com", TEST_MODE="1", ALLOWLIST="", GMAIL_APP_PASSWORD="x")
os.environ.pop("DATABASE_URL", None)
import store  # noqa: E402

store.STORE.root = Path(tempfile.mkdtemp())
import calendar_ics as cal  # noqa: E402
import mailer  # noqa: E402
import outreach  # noqa: E402
import gcal  # noqa: E402
import json  # noqa: E402
import urllib.error  # noqa: E402

T0 = datetime(2026, 11, 23, 4, 0, tzinfo=timezone.utc)  # Monday 09:30 IST
APP = {"id": "grainkind", "company": "GrainKind", "sector_label": "Consumer brands",
       "form_text": "Website www.grainkind.example Founders Founder 1 Ritu Hegde, CEO", "deck_text": "d"}


def state(**kw):
    s = {"id": "grainkind", "company": "GrainKind", "founder": "Ritu", "founder_email": "ritu@grainkind.example", "deeptech": False,
         "status": "sent", "slots": [outreach.iso(datetime(2026, 11, 26, 9, 0, tzinfo=timezone.utc))], "round": 0, "followups": 0,
         "seen": [], "history": [], "sent": {"subject": "Call? [AIC-grainkind]", "body": "b"}, "thread": "<t@x>",
         "sent_at": outreach.iso(T0), "last_contact": outreach.iso(T0)}
    s.update(kw)
    return s


class Safety(unittest.TestCase):
    def test_test_mode_sends_only_to_operator(self):  # K4
        self.assertEqual(mailer.route("ritu@grainkind.example"), "operator@example.com")

    def test_outside_allowlist_refused_when_live(self):  # K4
        os.environ["TEST_MODE"] = "0"
        try:
            with self.assertRaises(mailer.Refused):
                mailer.route("ritu@grainkind.example")
        finally:
            os.environ["TEST_MODE"] = "1"

    def test_suppressed_address_refused(self):  # K8
        mailer.suppress("no@thanks.example", "not interested")
        with self.assertRaises(mailer.Refused):
            mailer.route("No@Thanks.example")

    def test_refused_before_connecting(self):
        mailer.suppress("blocked@x.example", "not interested")
        with self.assertRaises(mailer.Refused):
            mailer.send("blocked@x.example", "s", "b", smtp_factory=lambda: self.fail("must not connect"))


class Invite(unittest.TestCase):
    def test_invite_is_an_inline_calendar_part_not_a_file(self):
        sent = []

        class FakeSMTP:
            def login(self, *a): pass
            def send_message(self, m): sent.append(m)
            def quit(self): pass
        os.environ.setdefault("GMAIL_APP_PASSWORD", "x")
        mailer.send("ritu@grainkind.example", "Invitation", "Booked.", ics="BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n", smtp_factory=FakeSMTP)
        m = sent[0]
        self.assertEqual(m.get_content_type(), "multipart/alternative")
        part = [p for p in m.walk() if p.get_content_type() == "text/calendar"][0]
        self.assertEqual(part.get_param("method"), "REQUEST")
        self.assertIsNone(part.get_content_disposition())


class GoogleCalendar(unittest.TestCase):
    BOOK = dict(read_replies=lambda s: [{"id": "<r1@x>", "text": "Slot 1 works"}],
                classify_fn=lambda t, s: {"kind": "interested", "picked_slot": 1, "proposed": []})

    def test_booking_writes_event_without_guest_in_test_mode(self):
        calls, mails = [], []
        st = Tick.run_tick(self, state(), send=lambda to, s, b, **k: mails.append(k.get("ics")) or "<m@x>",
                           book_event=lambda *a, **k: calls.append((a, k)) or "https://calendar.google.com/e", **self.BOOK)
        self.assertEqual((st["status"], st["event_link"]), ("booked", "https://calendar.google.com/e"))
        (app_id, start, summary, desc, guest), kw = calls[0]
        self.assertEqual((app_id, guest, kw["send_updates"]), ("grainkind", None, False))  # nobody but the operator hears of it
        self.assertEqual(mails, [None])  # the confirmation email carries no .ics

    def test_permission_error_aborts_and_timeout_escalates(self):
        def denied(*a, **k):
            raise cal.CalendarPermission("403")

        def slow(*a, **k):
            raise cal.CalendarTimeout("twice")
        self.assertEqual(Tick.run_tick(self, state(), book_event=denied, **self.BOOK)["status"], "aborted")
        self.assertEqual(Tick.run_tick(self, state(), book_event=slow, **self.BOOK)["status"], "escalated")

    def test_create_event_body_retry_and_409(self):
        os.environ.update(GOOGLE_CLIENT_ID="c", GOOGLE_CLIENT_SECRET="s", GOOGLE_REFRESH_TOKEN="r")
        seen = []

        def opener(req):
            seen.append(req)
            if req.full_url.endswith("/token"):
                return 200, {"access_token": "a"}
            return 200, {"htmlLink": "L"}
        start = datetime(2026, 11, 26, 8, 30, tzinfo=timezone.utc)
        self.assertEqual(gcal.create_event("stocksathi", start, "S", "D", opener=opener), "L")
        body = json.loads(seen[1].data)
        self.assertEqual((body["start"]["dateTime"], body["end"]["dateTime"]), ("2026-11-26T08:30:00Z", "2026-11-26T09:00:00Z"))
        self.assertNotIn("attendees", body)
        self.assertTrue(seen[1].full_url.endswith("sendUpdates=none"))
        self.assertRegex(body["id"], r"^[a-v0-9]{5,1024}$")

        def exists(req):
            if req.full_url.endswith("/token"):
                return 200, {"access_token": "a"}
            raise urllib.error.HTTPError(req.full_url, 409, "dup", {}, None)
        self.assertEqual(gcal.create_event("stocksathi", start, "S", "D", opener=exists), "")  # a retry never double-books

        def revoked(req):
            raise urllib.error.HTTPError(req.full_url, 400, "invalid_grant", {}, None)
        with self.assertRaises(cal.CalendarPermission):
            gcal.create_event("stocksathi", start, "S", "D", opener=revoked)


class Draft(unittest.TestCase):
    def test_draft_uses_free_tue_thu_slots_and_records_riyas_edits(self):
        busy = [(datetime(2026, 11, 24, 8, 30, tzinfo=timezone.utc), datetime(2026, 11, 24, 12, 30, tzinfo=timezone.utc))]  # Tue afternoon IST
        st = outreach.create_draft(APP, {"what_it_does": "Millet snacks", "why_yes": []}, now=T0, busy=busy,
                                   ask=lambda s, u, sch: {"subject": "Call with All In Capital", "body": "Hi Ritu, ..."})
        self.assertEqual(st["status"], "draft")
        self.assertEqual(st["founder_email"], "ritu@grainkind.example")
        days = [outreach.parse(x).astimezone(cal.IST).strftime("%a") for x in st["slots"]]
        self.assertTrue(all(d in ("Tue", "Thu") for d in days))
        self.assertNotIn("Tue 24", " ".join(cal.label(outreach.parse(x)) for x in st["slots"]))  # busy Tuesday skipped
        sent = []
        outreach.send_first("grainkind", st["draft"]["subject"], "Hi Ritu, edited by Riya.", now=T0,
                            send=lambda to, subj, body, **k: sent.append((to, subj)) or "<m1@x>")
        self.assertEqual(sent[0][0], "ritu@grainkind.example")  # the mailer itself reroutes to the operator in test mode
        self.assertEqual(store.STORE.all("email_edits")[-1]["after"], "Hi Ritu, edited by Riya.")
        with self.assertRaises(ValueError):  # cannot send twice
            outreach.send_first("grainkind", "s", "b", send=lambda *a, **k: "<m2@x>")


class Decide(unittest.TestCase):
    """Decision 7 boundaries: test the edge, not the middle."""

    def test_silence_just_inside_followup_window_waits(self):
        self.assertEqual(outreach.decide(state(), T0 + timedelta(days=3) - timedelta(minutes=1))[1], "none")

    def test_followup_at_exactly_three_days(self):
        self.assertEqual(outreach.decide(state(), T0 + timedelta(days=3))[1], "followup")

    def test_times_out_at_the_hour_after_two_followups(self):
        st = state(followups=2, last_contact=outreach.iso(T0 + timedelta(days=6)))
        self.assertEqual(outreach.decide(st, T0 + timedelta(days=9) - timedelta(minutes=1))[0], "sent")
        self.assertEqual(outreach.decide(st, T0 + timedelta(days=9))[0], "timed_out")

    def test_counter_proposal_increments_round(self):
        st = state(round=3)
        status, action, _ = outreach.decide(st, T0, {"text": "x"}, {"kind": "other_time", "proposed": ["2026-11-26T16:00"]},
                                            busy=[(datetime(2026, 11, 26, 10, 0, tzinfo=timezone.utc), datetime(2026, 11, 26, 11, 30, tzinfo=timezone.utc))])
        self.assertEqual((status, action), ("counter_proposed", "counter"))

    def test_escalates_at_exactly_the_cap_not_after(self):  # K7
        self.assertEqual(outreach.decide(state(round=8), T0, {"text": "x"}, {"kind": "other_time", "proposed": []})[0], "counter_proposed")
        self.assertEqual(outreach.decide(state(round=9), T0, {"text": "x"}, {"kind": "other_time", "proposed": []})[0], "escalated")

    def test_confirms_free_picked_slot(self):
        status, action, when = outreach.decide(state(), T0, {"text": "1 works"}, {"kind": "interested", "picked_slot": 1, "proposed": []})
        self.assertEqual((status, action), ("confirmed", "book"))

    def test_free_founder_time_is_booked(self):
        status, action, when = outreach.decide(state(), T0, {"text": "x"}, {"kind": "other_time", "proposed": ["2026-11-26T16:00"]})
        self.assertEqual((status, action, when), ("confirmed", "book", "2026-11-26T10:30:00Z"))

    def test_not_interested_and_ambiguous(self):  # decision 6, K8
        self.assertEqual(outreach.decide(state(), T0, {"text": "x"}, {"kind": "not_interested"})[:2], ("closed_not_interested", "suppress"))
        self.assertEqual(outreach.decide(state(), T0, {"text": "x"}, {"kind": "ambiguous"})[:2], ("needs_human", "escalate"))

    def test_closed_conversation_does_nothing(self):
        self.assertEqual(outreach.decide(state(status="booked"), T0 + timedelta(days=30))[1], "none")


class Tick(unittest.TestCase):
    """Decision 8: tool failures."""

    def run_tick(self, st, **kw):
        store.STORE.put("outreach", st["id"], st)
        args = dict(read_replies=lambda s: [], classify_fn=lambda t, s: {"kind": "ambiguous"}, fetch_busy=lambda: [],
                    send=lambda *a, **k: "<m@x>", book_event=False)
        args.update(kw)
        return outreach.tick(st["id"], now=T0 + timedelta(days=3), **args)

    def test_calendar_timeout_escalates(self):
        def slow():
            raise cal.CalendarTimeout("twice")
        self.assertEqual(self.run_tick(state(), fetch_busy=slow)["status"], "escalated")

    def test_calendar_permission_aborts_without_retry(self):
        calls = []

        def revoked():
            calls.append(1)
            raise cal.CalendarPermission("403")
        self.assertEqual(self.run_tick(state(), fetch_busy=revoked)["status"], "aborted")
        self.assertEqual(len(calls), 1)

    def test_bad_address_skipped_pipeline_continues(self):
        def bad(*a, **k):
            raise mailer.PermanentError("refused")
        self.assertEqual(self.run_tick(state(), send=bad)["status"], "skipped")

    def test_followup_sent_and_counted(self):
        sent = []
        st = self.run_tick(state(), send=lambda to, s, b, **k: sent.append(s) or "<m@x>")
        self.assertEqual((st["followups"], st["status"]), (1, "sent"))
        self.assertTrue(sent[0].startswith("Re: "))

    def test_booking_sends_invite_and_books(self):
        sent = []
        st = self.run_tick(state(), read_replies=lambda s: [{"id": "<r1@x>", "text": "Slot 1 works"}],
                           classify_fn=lambda t, s: {"kind": "interested", "picked_slot": 1, "proposed": []},
                           send=lambda to, s, b, **k: sent.append(k.get("ics")) or "<m@x>")
        self.assertEqual(st["status"], "booked")
        self.assertEqual(st["next"]["what"], "Meeting booked")
        self.assertIn("BEGIN:VEVENT", sent[0])
        self.assertIn("mailto:operator@example.com", sent[0])  # test mode: the invite goes to the operator only
        self.assertIn("ORGANIZER;CN=All In Capital:mailto:" + outreach.TEST_ORGANIZER, sent[0])  # not the operator inviting themself

    def test_record_failure_after_booking_escalates_and_alerts(self):
        def failing_save(s):
            if s["status"] == "booked":
                raise IOError("disk")
        st = self.run_tick(state(), read_replies=lambda s: [{"id": "<r2@x>", "text": "1"}],
                           classify_fn=lambda t, s: {"kind": "interested", "picked_slot": 1, "proposed": []},
                           send=lambda *a, **k: "<m@x>", save=failing_save)
        self.assertEqual(st["status"], "escalated")
        self.assertTrue(any("booked, but saving the record failed" in a["text"] for a in store.STORE.all("alerts")))

    def test_not_interested_suppresses(self):  # K8
        st = self.run_tick(state(founder_email="bye@nope.example"), read_replies=lambda s: [{"id": "<r3@x>", "text": "Not a fit, remove us"}],
                           classify_fn=lambda t, s: {"kind": "not_interested"})
        self.assertEqual(st["status"], "closed_not_interested")
        self.assertTrue(mailer.suppressed("bye@nope.example"))

    def test_reply_seen_once(self):
        r = [{"id": "<r4@x>", "text": "maybe"}]
        st = self.run_tick(state(), read_replies=lambda s: r)
        self.assertEqual(st["seen"], ["<r4@x>"])


class Calendar(unittest.TestCase):
    def test_parse_busy_and_skip_free_or_cancelled(self):
        ics = ("BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nDTSTART:20261124T090000Z\r\nDTEND:20261124T100000Z\r\nEND:VEVENT\r\n"
               "BEGIN:VEVENT\r\nDTSTART:20261126T090000Z\r\nDTEND:20261126T100000Z\r\nTRANSP:TRANSPARENT\r\nEND:VEVENT\r\n"
               "BEGIN:VEVENT\r\nDTSTART;VALUE=DATE:20261201\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n")
        b = cal.busy(ics)
        self.assertEqual(len(b), 2)
        self.assertEqual(b[1][1] - b[1][0], timedelta(days=1))

    def test_fetch_permission_is_permanent(self):
        import urllib.error
        calls = []

        def opener(u):
            calls.append(1)
            raise urllib.error.HTTPError(u, 404, "gone", {}, None)
        with self.assertRaises(cal.CalendarPermission):
            cal.fetch("https://calendar.example/x.ics", opener=opener)
        self.assertEqual(len(calls), 1)

    def test_fetch_timeout_retried_once(self):
        calls = []

        def opener(u):
            calls.append(1)
            raise TimeoutError()
        with self.assertRaises(cal.CalendarTimeout):
            cal.fetch("https://calendar.example/x.ics", opener=opener)
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
