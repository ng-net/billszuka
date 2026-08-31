#!/usr/bin/env python3
"""Per-user identity for BILLSzuka.

Layered on top of Basic Auth: anyone with the team password can hit /api/*,
but per-user features (bookmarks, soft-delete, knowledge attribution,
activity) require a logged-in session.

Login model: username-only. The allowlist of accepted usernames lives in the
TEAM_USERS env var (comma-separated, e.g. "marceli,kolega"). On first login
we create a `users` row; subsequent logins reuse it. No invite code, no
email, no external service.

Session model: random 32-byte token, stored in `sessions` table, returned
to the browser as the `bsz_sid` HttpOnly cookie. Sliding 30-day expiry
(touched on every request that has a valid session).
"""
from __future__ import annotations

import json
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Request

import db

COOKIE_NAME = "bsz_sid"
SESSION_TTL_DAYS = 30
USER_AGENT_MAX = 200


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _expires() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def allowed_usernames() -> set[str]:
    """Read TEAM_USERS env var. Empty -> no one can log in (safe default)."""
    raw = os.environ.get("TEAM_USERS", "")
    return {u.strip().lower() for u in raw.split(",") if u.strip()}


def normalize_username(name: str) -> str:
    return (name or "").strip().lower()


def is_allowed(name: str) -> bool:
    return normalize_username(name) in allowed_usernames()


def get_or_create_user(conn: sqlite3.Connection, username: str) -> dict:
    """Return the user row, creating it on first login. Case-insensitive
    username, but the stored form is the lowercased version."""
    u = normalize_username(username)
    if not u:
        raise ValueError("username is empty")
    row = conn.execute(
        "SELECT id, username, display_name, role, created_at, last_seen_at, disabled_at "
        "FROM users WHERE username = ?",
        (u,),
    ).fetchone()
    if row is not None:
        if row["disabled_at"]:
            raise PermissionError("user is disabled")
        return dict(row)
    cur = conn.execute(
        "INSERT INTO users (username, display_name, role, created_at) "
        "VALUES (?, ?, 'member', ?)",
        (u, u, _now()),
    )
    return {
        "id": cur.lastrowid,
        "username": u,
        "display_name": u,
        "role": "member",
        "created_at": _now(),
        "last_seen_at": None,
        "disabled_at": None,
    }


def create_session(user_id: int, user_agent: str = "") -> str:
    """Mint a session token, persist it, return the token string."""
    token = secrets.token_urlsafe(32)
    ua = (user_agent or "")[:USER_AGENT_MAX]
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO sessions (id, user_id, created_at, last_seen_at, expires_at, user_agent) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (token, user_id, _now(), _now(), _expires(), ua),
        )
        conn.execute(
            "UPDATE users SET last_seen_at = ? WHERE id = ?", (_now(), user_id)
        )
    return token


def lookup_session(token: str) -> Optional[dict]:
    """Return the session + user dict if the token is valid and not expired.
    Touches `last_seen_at` (sliding window). Returns None otherwise."""
    if not token:
        return None
    with db.connect() as conn:
        row = conn.execute(
            "SELECT s.id AS sid, s.user_id, s.expires_at, "
            "       u.username, u.display_name, u.role, u.disabled_at "
            "FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.id = ?",
            (token,),
        ).fetchone()
        if row is None:
            return None
        if row["disabled_at"]:
            return None
        if row["expires_at"] < _now():
            return None
        # Touch sliding expiry + last_seen_at
        new_expires = _expires()
        conn.execute(
            "UPDATE sessions SET last_seen_at = ?, expires_at = ? WHERE id = ?",
            (_now(), new_expires, token),
        )
        conn.execute(
            "UPDATE users SET last_seen_at = ? WHERE id = ?", (_now(), row["user_id"])
        )
        return {
            "session_id": row["sid"],
            "user_id": row["user_id"],
            "username": row["username"],
            "display_name": row["display_name"] or row["username"],
            "role": row["role"],
        }


def destroy_session(token: str) -> None:
    if not token:
        return
    with db.connect() as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (token,))


def log_activity(
    user_id: int,
    kind: str,
    *,
    session_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    target_kind: Optional[str] = None,
    target_id: Optional[str] = None,
    payload: Optional[dict] = None,
) -> None:
    """Append a row to user_activity. Best-effort: failures here must not
    break the calling request, so we swallow exceptions."""
    try:
        payload_str = json.dumps(payload, ensure_ascii=False) if payload is not None else None
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO user_activity "
                "(ts, user_id, session_id, kind, lead_id, target_kind, target_id, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (_now(), user_id, session_id, kind, lead_id, target_kind, target_id, payload_str),
            )
    except Exception:
        pass  # never let activity logging break a user action


def current_user(request: Request) -> Optional[dict]:
    """Read the bsz_sid cookie and resolve it. Cached on request.state
    so multiple lookups in one request are cheap."""
    if hasattr(request.state, "user"):
        return request.state.user
    token = request.cookies.get(COOKIE_NAME)
    user = lookup_session(token) if token else None
    request.state.user = user
    return user


def require_user(request: Request) -> dict:
    """Raise HTTPException(401) if no valid session. Use as a dependency."""
    from fastapi import HTTPException

    u = current_user(request)
    if not u:
        raise HTTPException(status_code=401, detail="login required")
    return u
