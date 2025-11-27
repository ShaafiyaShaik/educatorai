"""Conversation state store with optional Redis backend.

This module exposes the same synchronous API used elsewhere in the
codebase (`get_state`, `update_state`, `clear_state`) but will persist
small per-educator conversation memory in Redis when available. The
default key prefix is `convstate:`. If Redis is not reachable or the
backend is configured as `memory`, an in-memory dict with a Lock is used
as a safe fallback.

Stored structure (JSON):
{ "last_resolved_student": Optional[str], "last_action": Optional[dict], "pending_clarify": Optional[dict], "updated_at": <epoch> }
"""
from threading import Lock
from typing import Dict, Any, Optional
import time
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory fallback
_store: Dict[int, Dict[str, Any]] = {}
_lock = Lock()

# Redis client (lazy)
_redis = None
_use_redis = False

try:
    # Use explicit backend preference if set to 'redis', or use redis when
    # CONVERSATION_STATE_BACKEND is 'auto' and a REDIS_URL is configured.
    if settings.CONVERSATION_STATE_BACKEND.lower() == "redis" or (
        settings.CONVERSATION_STATE_BACKEND.lower() == "auto" and settings.REDIS_URL
    ):
        try:
            import redis as _redis_module

            _redis = _redis_module.from_url(settings.REDIS_URL, decode_responses=True)
            # quick connectivity check (non-blocking on import but will raise on first call)
            _use_redis = True
        except Exception as e:
            logger.warning("Redis connection not available for conversation_state: %s", e)
            _use_redis = False
except Exception:
    _use_redis = False


def _redis_key(educator_id: int) -> str:
    return f"convstate:{educator_id}"


def _default_state() -> Dict[str, Any]:
    return {"last_resolved_student": None, "last_action": None, "pending_clarify": None, "updated_at": time.time()}


def get_state(educator_id: int) -> Dict[str, Any]:
    """Return the conversation state dict for the given educator id.

    This is a synchronous API for compatibility with existing code. When
    Redis is enabled, the value is fetched from Redis and parsed as JSON.
    Otherwise the in-memory store is used.
    """
    if educator_id is None:
        return _default_state()

    if _use_redis and _redis:
        try:
            key = _redis_key(educator_id)
            val = _redis.get(key)
            if val:
                try:
                    return json.loads(val)
                except Exception:
                    logger.exception("Failed to parse JSON for conversation state key %s", key)
            # Initialize default state in redis
            st = _default_state()
            try:
                _redis.set(key, json.dumps(st))
            except Exception:
                logger.exception("Failed to write default conversation state to redis for %s", key)
            return st
        except Exception as e:
            logger.warning("Redis error in get_state, falling back to memory: %s", e)

    # Fallback to in-memory
    with _lock:
        st = _store.get(educator_id)
        if not st:
            st = _default_state()
            _store[educator_id] = st
        return st


def update_state(educator_id: int, **kwargs) -> None:
    """Update keys in the educator's conversation state.

    This will persist to Redis when available; otherwise updates the in-memory map.
    """
    if educator_id is None:
        return

    if _use_redis and _redis:
        try:
            key = _redis_key(educator_id)
            cur = None
            val = _redis.get(key)
            if val:
                try:
                    cur = json.loads(val)
                except Exception:
                    cur = _default_state()
            else:
                cur = _default_state()
            for k, v in kwargs.items():
                cur[k] = v
            cur["updated_at"] = time.time()
            try:
                _redis.set(key, json.dumps(cur))
            except Exception:
                logger.exception("Failed to write conversation state to redis for %s", key)
            return
        except Exception as e:
            logger.warning("Redis error in update_state, falling back to memory: %s", e)

    with _lock:
        st = _store.get(educator_id)
        if not st:
            st = _default_state()
            _store[educator_id] = st
        for k, v in kwargs.items():
            st[k] = v
        st["updated_at"] = time.time()


def clear_state(educator_id: int) -> None:
    if educator_id is None:
        return
    if _use_redis and _redis:
        try:
            key = _redis_key(educator_id)
            _redis.delete(key)
            return
        except Exception as e:
            logger.warning("Redis error in clear_state, falling back to memory delete: %s", e)
    with _lock:
        if educator_id in _store:
            del _store[educator_id]
