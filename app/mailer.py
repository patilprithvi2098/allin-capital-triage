"""Email for the outreach agent (adapted from the Sprinto build). Gmail SMTP sends; Gmail IMAP reads replies.
Safety (kill criteria K4 and K8):
- TEST_MODE=1 (the default): every message goes to OPERATOR_EMAIL only; the founder's address is named in the subject.
- Any recipient outside the allowlist (OPERATOR_EMAIL plus ALLOWLIST) is refused before connecting, in every mode.
- A suppressed address (said "not interested") is refused before connecting."""
import email
import imaplib
import os
import re
import smtplib
import time
from email.message import EmailMessage
from email.utils import make_msgid

from store import STORE

RETRY_WAIT = 2


class Refused(Exception):
    """The message was not sent because a safety rule forbids it."""


class PermanentError(Exception):
    """A failure that will not pass on retry (bad login, rejected address)."""


def test_mode():
    return os.environ.get("TEST_MODE", "1") == "1"


def allowlist():
    extra = [a.strip().lower() for a in (os.environ.get("ALLOWLIST") or "").split(",") if a.strip()]
    return {os.environ.get("OPERATOR_EMAIL", "").strip().lower(), *extra} - {""}


def suppressed(addr):
    return bool(STORE.get("suppression", _key(addr)))


def suppress(addr, reason):
    STORE.put("suppression", _key(addr), {"email": addr.strip().lower(), "reason": reason, "at": time.strftime("%Y-%m-%dT%H:%M:%S")})


def _key(addr):
    return re.sub(r"[^a-z0-9]", "_", (addr or "").strip().lower())[:120] or "blank"


def route(founder):
    """Who actually receives a message meant for `founder`. Raises Refused when no safe recipient exists."""
    founder = (founder or "").strip().lower()
    if founder and suppressed(founder):
        raise Refused("%s asked not to be contacted." % founder)
    to = os.environ.get("OPERATOR_EMAIL", "").strip().lower() if test_mode() else founder
    if not to or to not in allowlist():
        raise Refused("%s is not on the allowlist." % (to or "No address"))
    return to


def send(founder, subject, body, thread=None, ics=None, smtp_factory=None):
    """Send one message; returns its Message-ID. `thread` keeps replies in one conversation. Never retried after the
    message was handed over (a retry then would send it twice); only connecting and logging in are retried."""
    to = route(founder)
    sender = os.environ.get("GMAIL_SENDER") or os.environ["OPERATOR_EMAIL"]
    msg = EmailMessage()
    msg["From"], msg["To"] = sender, to
    msg["Subject"] = ("[TEST → %s] " % founder if test_mode() else "") + subject
    msg["Message-ID"] = make_msgid(domain="allin-triage.local")
    if thread:
        msg["In-Reply-To"] = msg["References"] = thread
    msg.set_content(body)
    if ics:
        msg.add_alternative(ics, subtype="calendar", params={"method": "REQUEST"})  # inline part: Gmail shows a Yes/No invite card, not a file
    factory = smtp_factory or (lambda: smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20))
    for attempt in (1, 2):
        try:
            smtp = factory()
            smtp.login(sender, os.environ["GMAIL_APP_PASSWORD"].replace(" ", ""))
            break
        except smtplib.SMTPAuthenticationError:
            raise PermanentError("Gmail rejected the login.")
        except Exception:
            if attempt == 2:
                raise
            time.sleep(RETRY_WAIT)
    try:
        smtp.send_message(msg)
    except smtplib.SMTPRecipientsRefused:
        raise PermanentError("Gmail refused the address.")
    finally:
        try:
            smtp.quit()
        except Exception:
            pass
    return msg["Message-ID"]


def replies(token, since_ids=(), imap_factory=None):
    """New messages in the operator's inbox whose subject carries `token` and that this app did not send.
    Returns [{"id", "from", "subject", "text", "in_reply_to"}]. Read-only: marks nothing, deletes nothing."""
    factory = imap_factory or (lambda: imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=20))
    box = factory()
    try:
        box.login(os.environ.get("GMAIL_SENDER") or os.environ["OPERATOR_EMAIL"], os.environ["GMAIL_APP_PASSWORD"].replace(" ", ""))
        box.select("INBOX", readonly=True)
        _, data = box.search(None, '(SUBJECT "%s")' % token.replace('"', ""))
        out = []
        for num in (data[0] or b"").split()[-30:]:
            _, parts = box.fetch(num, "(RFC822)")
            m = email.message_from_bytes(parts[0][1])
            mid = (m.get("Message-ID") or "").strip()
            if not mid or mid in since_ids or "allin-triage.local" in mid:  # skip our own sent messages
                continue
            out.append({"id": mid, "from": m.get("From", ""), "subject": m.get("Subject", ""), "text": _text(m)[:4000],
                        "in_reply_to": (m.get("In-Reply-To") or "").strip()})
        return out
    finally:
        try:
            box.logout()
        except Exception:
            pass


def _text(m):
    part = next((p for p in m.walk() if p.get_content_type() == "text/plain"), None) if m.is_multipart() else m
    raw = part.get_payload(decode=True) if part else b""
    text = (raw or b"").decode(part.get_content_charset() or "utf-8", "replace") if part else ""
    return re.split(r"\n\s*On .{5,120}wrote:\s*\n|\n>", text, maxsplit=1)[0].strip()  # the reply, without the quoted thread
