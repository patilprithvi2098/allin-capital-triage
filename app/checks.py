"""Setup check: prove each credential works without spending anything (list or usage calls only)."""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
_UA = {"User-Agent": "allin-capital-triage/0.1"}


def load_env():
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.split(" #")[0].strip()  # .env.example style trailing comments
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))  # real environment wins (Vercel)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):  # calls that carry an API key must not follow a redirect to another host
        return None


def get_json(url, headers=None, timeout=10):
    request = urllib.request.Request(url, headers=dict(_UA, **(headers or {})))
    with urllib.request.build_opener(_NoRedirect).open(request, timeout=timeout) as response:
        return json.load(response)


def _result(ok, detail, **extra):
    return dict(ok=ok, detail=detail, **extra)


def _http_check(name, call):
    # Error text never includes the URL or the key: Gemini's key travels in the query string.
    try:
        return call()
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return _result(False, "%s rejected the key (HTTP %d)." % (name, e.code))
        return _result(False, "%s answered HTTP %d." % (name, e.code))
    except Exception as e:
        return _result(False, "Could not reach %s (%s)." % (name, type(e).__name__))


def _need(var, label):
    return None if os.environ.get(var) else _result(False, "Not set. Add %s to .env (%s)." % (var, label))


def check_claude():
    return _need("ANTHROPIC_API_KEY", "your Claude key") or _http_check("The Claude API", lambda: (
        get_json("https://api.anthropic.com/v1/models?limit=1",
                 {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"}),
        _result(True, "Key accepted."))[1])


def check_judge():
    provider = (os.environ.get("JUDGE_PROVIDER") or "").lower()
    if provider == "anthropic":  # operator's choice: the Claude key, with a different model from the agent's
        return _need("ANTHROPIC_API_KEY", "your Claude key") or _result(True, "Uses the Claude key with Claude Opus (same family as the agent).")
    missing = _need("JUDGE_API_KEY", "a Gemini, OpenAI or OpenRouter key for the eval judge")
    if provider == "openrouter":
        return missing or _http_check("OpenRouter", lambda: (get_json("https://openrouter.ai/api/v1/key", {"Authorization": "Bearer " + os.environ["JUDGE_API_KEY"]}),
                                                           _result(True, "OpenRouter key accepted (judge model: Google Gemini)."))[1])
    if provider not in ("gemini", "openai"):
        return _result(False, "Not set. Put JUDGE_PROVIDER=gemini or JUDGE_PROVIDER=openai in .env (needed by Phase 3).")
    if missing:
        return missing
    key = os.environ["JUDGE_API_KEY"]
    if provider == "gemini":
        call = lambda: (get_json("https://generativelanguage.googleapis.com/v1beta/models?pageSize=1", {"x-goog-api-key": key}),
                        _result(True, "Gemini key accepted."))[1]
    else:
        call = lambda: (get_json("https://api.openai.com/v1/models", {"Authorization": "Bearer " + key}),
                        _result(True, "OpenAI key accepted."))[1]
    return _http_check("The judge model", call)


def check_tavily():
    def call():
        usage = get_json("https://api.tavily.com/usage", {"Authorization": "Bearer " + os.environ["TAVILY_API_KEY"]})
        key = usage.get("key") or {}
        used, limit = key.get("usage"), key.get("limit")
        left = "" if used is None or limit is None else " %s of %s credits used." % (used, limit)
        return _result(True, "Key accepted." + left)
    return _need("TAVILY_API_KEY", "free at tavily.com") or _http_check("Tavily", call)


def check_resend():
    def call():
        get_json("https://api.resend.com/domains", {"Authorization": "Bearer " + os.environ["RESEND_API_KEY"]})
        return _result(True, "Key accepted. Test mode sends only to %s." % os.environ.get("OPERATOR_EMAIL", "OPERATOR_EMAIL"))
    if os.environ.get("TEST_MODE", "1") != "1":
        return _result(False, "TEST_MODE is off. Only the operator turns it off, and not before Phase 5.")
    return _need("OPERATOR_EMAIL", "your own inbox") or _need("RESEND_API_KEY", "free at resend.com") or \
        _http_check("Resend", call)


def check_storage():
    import store  # imported here: store picks files or Supabase when it loads
    if isinstance(store.STORE, store.FileStore):
        return _result(True, "Saved in files on this computer (Supabase used when DATABASE_URL is set).")
    try:
        store.STORE.get("meta", "ping")
    except ImportError:
        return _result(False, "The database driver is missing. Run: pip3 install -r requirements.txt")
    except Exception as e:  # the type only: a driver message can carry the connection string
        return _result(False, "Could not use Supabase (%s). Check DATABASE_URL and run db/schema.sql." % type(e).__name__)
    return _result(True, "Connected to Supabase.")


def run_all():
    load_env()
    return {"claude": check_claude(), "judge": check_judge(), "tavily": check_tavily(), "resend": check_resend(),
            "storage": check_storage()}
