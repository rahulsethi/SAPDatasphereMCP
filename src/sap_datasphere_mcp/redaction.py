# SAP Datasphere MCP Server
# File: redaction.py
# Version: v1 (1.0)

"""Best-effort scrubbing of secrets and tokens from tool returns.

Applied to every tool return when ``DATASPHERE_REDACTION_ENABLED=1`` (default
on for v1.0). Walks the result structure recursively. Conservative by default
— we'd rather miss an exotic secret than break legitimate enterprise data.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

__all__ = ["DEFAULT_PATTERNS", "scrub", "is_enabled"]


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def is_enabled() -> bool:
    """Whether redaction is on. Default: ``True`` in v1.0."""
    return _env_flag("DATASPHERE_REDACTION_ENABLED", default=True)


# Each pattern: (label, regex, applies-to-keys-named).
# - JWT-shaped strings anywhere.
# - Bearer/Basic header values in echoed errors.
# - Long base64-ish secrets in fields whose key name *looks* like a secret.
DEFAULT_PATTERNS: List[Tuple[str, re.Pattern, Optional[Tuple[str, ...]]]] = [
    (
        "jwt",
        re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"),
        None,
    ),
    (
        "bearer",
        re.compile(r"(?i)(bearer)\s+[A-Za-z0-9._\-+/=]{8,}"),
        None,
    ),
    (
        "basic_auth",
        re.compile(r"(?i)(basic)\s+[A-Za-z0-9+/=]{8,}"),
        None,
    ),
    (
        "long_secret_in_secret_field",
        re.compile(r"[A-Za-z0-9+/=_\-]{32,}"),
        ("client_secret", "secret", "password", "api_key", "apikey", "token", "auth"),
    ),
]


# Key names whose VALUES we always replace, regardless of pattern match.
ALWAYS_REDACT_KEYS = frozenset(
    {
        "client_secret",
        "client_secret_value",
        "secret",
        "password",
        "api_key",
        "apikey",
        "token",
        "access_token",
        "refresh_token",
        "id_token",
        "authorization",
        "auth_header",
    }
)

_PLACEHOLDER = "<redacted>"


def _redact_string(value: str, key_hint: Optional[str]) -> str:
    if not isinstance(value, str) or not value:
        return value
    result = value
    for label, pattern, restrict_keys in DEFAULT_PATTERNS:
        if restrict_keys is not None:
            if key_hint is None or key_hint.lower() not in restrict_keys:
                continue
        result = pattern.sub(f"<redacted:{label}>", result)
    return result


def _walk(value: Any, key_hint: Optional[str] = None) -> Any:
    if isinstance(value, dict):
        out: Dict[Any, Any] = {}
        for k, v in value.items():
            if isinstance(k, str) and k.lower() in ALWAYS_REDACT_KEYS:
                out[k] = _PLACEHOLDER
            else:
                out[k] = _walk(v, k if isinstance(k, str) else None)
        return out
    if isinstance(value, list):
        return [_walk(item, key_hint) for item in value]
    if isinstance(value, tuple):
        return tuple(_walk(item, key_hint) for item in value)
    if isinstance(value, str):
        return _redact_string(value, key_hint)
    return value


def scrub(value: Any) -> Any:
    """Return a redacted copy of ``value``.

    Cheap when redaction is disabled — returns the input unchanged.
    """
    if not is_enabled():
        return value
    return _walk(value)
