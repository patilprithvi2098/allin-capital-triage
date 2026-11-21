"""Save one secret into .env without it showing on screen or in shell history.
Run: python3 scripts/set_env.py TAVILY_API_KEY"""
import getpass
import os
import re
import sys
from pathlib import Path

ENV = Path(__file__).resolve().parent.parent / ".env"
name = sys.argv[1] if len(sys.argv) == 2 else ""
if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
    sys.exit("Usage: python3 scripts/set_env.py NAME")
value = getpass.getpass("Paste %s (nothing will show), then press Return: " % name).strip()
if not value or "\n" in value:
    sys.exit("Nothing saved: the value was empty.")
text = ENV.read_text() if ENV.exists() else ""
line = "%s=%s" % (name, value)
text = re.sub(r"(?m)^%s=.*$" % name, lambda m: line, text) if re.search(r"(?m)^%s=" % name, text) else text.rstrip("\n") + "\n" + line + "\n"
ENV.write_text(text)
os.chmod(ENV, 0o600)
print("Saved %s (%d characters)." % (name, len(value)))
