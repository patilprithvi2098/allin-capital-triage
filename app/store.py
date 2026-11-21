"""Where reads, decisions and caches live: JSON files under data/ locally, Supabase Postgres when DATABASE_URL is set
(Vercel's disk is thrown away between requests). One small interface for both."""
import json
import os
import ssl
from pathlib import Path
from urllib.parse import unquote, urlparse

DATA = Path(__file__).resolve().parent.parent / "data" / "store"


def _safe(part):
    if not part or ".." in part or "/" in part or part.startswith("."):
        raise ValueError("bad key")
    return part


class FileStore:
    def __init__(self, root=DATA):
        self.root = Path(root)

    def _path(self, kind, key):
        return self.root / _safe(kind) / (_safe(key) + ".json")

    def get(self, kind, key):
        p = self._path(kind, key)
        return json.loads(p.read_text()) if p.exists() else None

    def put(self, kind, key, value):
        p = self._path(kind, key)
        p.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)  # founder details: owner only
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(value, indent=2))
        tmp.replace(p)  # readers never see a half-written file

    def all(self, kind):
        d = self.root / _safe(kind)
        return [json.loads(p.read_text()) for p in sorted(d.glob("*.json"))] if d.exists() else []


def _connect():
    import pg8000.dbapi
    u = urlparse(os.environ["DATABASE_URL"])
    return pg8000.dbapi.connect(user=unquote(u.username or ""), password=unquote(u.password or ""), host=u.hostname,
                                port=u.port or 5432, database=(u.path or "/postgres")[1:] or "postgres",
                                ssl_context=ssl.create_default_context(), timeout=10)


class PgStore:
    """Table `kv` (db/schema.sql). One short connection per call: serverless functions keep no state."""

    def _run(self, sql, args=(), fetch=False):
        conn = _connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, args)
            rows = cur.fetchall() if fetch else None
            conn.commit()
            return rows
        finally:
            conn.close()

    def get(self, kind, key):
        rows = self._run("SELECT value FROM kv WHERE kind = %s AND key = %s", (kind, key), fetch=True)
        return (json.loads(rows[0][0]) if isinstance(rows[0][0], str) else rows[0][0]) if rows else None

    def put(self, kind, key, value):
        self._run("INSERT INTO kv (kind, key, value) VALUES (%s, %s, %s::jsonb) ON CONFLICT (kind, key) "
                  "DO UPDATE SET value = EXCLUDED.value, updated_at = now()", (kind, key, json.dumps(value)))

    def all(self, kind):
        rows = self._run("SELECT value FROM kv WHERE kind = %s ORDER BY key", (kind,), fetch=True)
        return [json.loads(r[0]) if isinstance(r[0], str) else r[0] for r in rows]


STORE = PgStore() if os.environ.get("DATABASE_URL") else FileStore()
