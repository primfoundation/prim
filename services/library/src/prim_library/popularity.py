"""Operator-only signed signal ingestion. There is deliberately no public vote tool.

Issuers are trusted authenticated collection services, NOT end-user API keys.
No instance content, search text, IP address or raw subject is retained.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import math
from pathlib import Path
import sqlite3
from typing import Any

from .library import ID, LibraryError, canonical, fingerprint

POLICY = {"id": "prim-popularity-v1", "minimum_cohort": 5,
          "popular": "2*ln(1+active_stars)+ln(1+distinct_adoptions_30d)",
          "trending": "ln(1+distinct_adoptions_7d)*min(4,(week+5)/(previous_week+5))",
          "note": "Popularity is adoption, not quality, factual truth, conformance, or security."}


def sign(event: dict, secret: bytes) -> str:
    return hmac.new(secret, canonical(event), hashlib.sha256).hexdigest()


def instant(text: str) -> datetime:
    try:
        result = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError()
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError) as exc:
        raise LibraryError("expected a timezone-aware event time") from exc


class Signals:
    """Private operator database. External identity/consent verification is an issuer obligation."""
    def __init__(self, path: Path, issuer_keys: dict[str, bytes], subject_secret: bytes):
        if len(subject_secret) < 32 or any(len(k) < 32 for k in issuer_keys.values()):
            raise LibraryError("signal secrets must be at least 32 bytes")
        if path.is_symlink():
            raise LibraryError("signal database cannot be a symlink")
        self.keys, self.secret = issuer_keys, subject_secret
        self.db = sqlite3.connect(path, timeout=10)
        path.chmod(0o600)
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS processed (id TEXT PRIMARY KEY, at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS adoption (profile TEXT, subject TEXT, day TEXT,
          PRIMARY KEY(profile, subject, day));
        CREATE TABLE IF NOT EXISTS stars (profile TEXT, subject TEXT, active INTEGER, at TEXT,
          PRIMARY KEY(profile, subject));
        """)

    def close(self) -> None:
        self.db.close()

    def ingest(self, event: dict, known_ids: set[str], now: datetime | None = None) -> str:
        now = now or datetime.now(timezone.utc)
        expected = {"issuer", "subject", "profile_id", "kind", "event_id", "occurred_at", "consent", "signature"}
        if set(event) != expected or len(canonical(event)) > 4096:
            raise LibraryError("unexpected event fields or size")
        if event["consent"] is not True:
            raise LibraryError("explicit consent is required")
        for key in ("issuer", "subject", "event_id", "signature", "profile_id", "kind", "occurred_at"):
            if not isinstance(event[key], str) or not 1 <= len(event[key]) <= 256:
                raise LibraryError("invalid event identifier")
        issuer_key = self.keys.get(event["issuer"])
        body = {k: v for k, v in event.items() if k != "signature"}
        if issuer_key is None or not hmac.compare_digest(sign(body, issuer_key), event["signature"]):
            raise LibraryError("untrusted signal issuer/signature")
        if event["profile_id"] not in known_ids or not ID.fullmatch(event["profile_id"]):
            raise LibraryError("unknown public profile")
        if event["kind"] not in {"star", "unstar", "adoption"}:
            raise LibraryError("unsupported signal; reads and raw downloads are not votes")
        at = instant(event["occurred_at"])
        if at > now + timedelta(minutes=5) or at < now - timedelta(days=7):
            raise LibraryError("signal outside acceptance window")
        subject = sign({"issuer": event["issuer"], "subject": event["subject"]}, self.secret)
        event_id = sign({"issuer": event["issuer"], "event_id": event["event_id"]}, self.secret)
        profile, stamp = event["profile_id"], at.isoformat()
        with self.db:
            if self.db.execute("SELECT 1 FROM processed WHERE id=?", (event_id,)).fetchone():
                return "duplicate"
            self.db.execute("INSERT INTO processed VALUES (?,?)", (event_id, stamp))
            if event["kind"] == "adoption":
                self.db.execute("INSERT OR IGNORE INTO adoption VALUES (?,?,?)", (profile, subject, at.date().isoformat()))
            else:
                self.db.execute("""INSERT INTO stars VALUES (?,?,?,?) ON CONFLICT(profile,subject)
                DO UPDATE SET active=excluded.active,at=excluded.at WHERE excluded.at > stars.at""",
                                (profile, subject, int(event["kind"] == "star"), stamp))
            cutoff = (now - timedelta(days=90)).isoformat()
            self.db.execute("DELETE FROM processed WHERE at < ?", (cutoff,))
            self.db.execute("DELETE FROM adoption WHERE day < ?", (cutoff[:10],))
        return "accepted"

    def forget(self, issuer: str, subject: str) -> None:
        pseudonym = sign({"issuer": issuer, "subject": subject}, self.secret)
        with self.db:
            self.db.execute("DELETE FROM adoption WHERE subject=?", (pseudonym,))
            self.db.execute("DELETE FROM stars WHERE subject=?", (pseudonym,))

    def export(self, known_ids: set[str], now: datetime | None = None) -> dict:
        now = now or datetime.now(timezone.utc)
        # Only COMPLETE UTC days contribute, so the windows are deterministic.
        today = now.date()
        current = today.isoformat()
        week = (today - timedelta(days=7)).isoformat()
        previous = (today - timedelta(days=14)).isoformat()
        month = (today - timedelta(days=30)).isoformat()
        rows = {}
        for identity in sorted(known_ids):
            def count(start, end):
                return self.db.execute("SELECT COUNT(DISTINCT subject) FROM adoption WHERE profile=? AND day>=? AND day<?",
                                       (identity, start, end)).fetchone()[0]
            values = {"stars": self.db.execute("SELECT COUNT(*) FROM stars WHERE profile=? AND active=1", (identity,)).fetchone()[0],
                      "adoptions_30d": count(month, current), "adoptions_7d": count(week, current),
                      "adoptions_previous_7d": count(previous, week)}
            suppressed = [k for k, n in values.items() if n < POLICY["minimum_cohort"]]
            rows[identity] = {**{k: n if n >= POLICY["minimum_cohort"] else 0 for k, n in values.items()},
                              "status": "measured" if len(suppressed) < len(values) else "insufficient_data",
                              "suppressed_metrics": suppressed}
        return {"format": "prim-popularity", "version": 1, "as_of": current,
                "policy": POLICY, "profiles": rows,
                "limits": "Trusted-issuer assertions, not independently verified people. Cohort suppression is not a full anonymity guarantee. No public vote submission is enabled."}
