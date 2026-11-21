"""Two logins: Riya (decides, edits, sends) and Kushal (read-only outcomes, thesis approval). Each has a password in
RIYA_PASSWORD / KUSHAL_PASSWORD; a correct one gets a signed, expiring cookie that carries the role. No server state, so
it works on serverless. Locally, with neither password set, the app stays open on 127.0.0.1 as Riya."""
import hashlib
import hmac
import os
import time

COOKIE = "aic_session"
DAYS = 7
ROLES = {"riya": "RIYA_PASSWORD", "kushal": "KUSHAL_PASSWORD"}


def required():
    return any(os.environ.get(v) for v in ROLES.values()) or bool(os.environ.get("VERCEL"))


def configured():
    return all(os.environ.get(v) for v in ROLES.values())


def _secret():  # changing either password signs everyone out
    return hashlib.sha256(("aic-session:" + "|".join(os.environ.get(v, "") for v in ROLES.values())).encode()).digest()


def _sign(role, expiry):
    return hmac.new(_secret(), ("%s:%d" % (role, expiry)).encode(), hashlib.sha256).hexdigest()


def check_password(role, given):
    pw = os.environ.get(ROLES[role], "") if role in ROLES else ""
    return bool(pw) and isinstance(given, str) and hmac.compare_digest(given.encode(), pw.encode())


def new_cookie(role, secure):
    expiry = int(time.time()) + DAYS * 86400
    return "%s=%s.%d.%s; Path=/; Max-Age=%d; HttpOnly; SameSite=Strict%s" % (
        COOKIE, role, expiry, _sign(role, expiry), DAYS * 86400, "; Secure" if secure else "")


def clear_cookie(secure):
    return "%s=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict%s" % (COOKIE, "; Secure" if secure else "")


def role(cookie_header):
    """The signed-in role, or None. Open local mode (no passwords set) is Riya."""
    if not required():
        return "riya"
    if not configured():
        return None
    for part in (cookie_header or "").split(";"):
        name, _, value = part.strip().partition("=")
        if name == COOKIE and value.count(".") == 2:
            who, expiry, sig = value.split(".")
            if who in ROLES and expiry.isdigit() and int(expiry) > time.time() and hmac.compare_digest(sig, _sign(who, int(expiry))):
                return who
    return None
