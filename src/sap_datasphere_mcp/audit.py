# SAP Datasphere MCP Server
# File: audit.py
# Version: v1 (1.0)

"""Structured per-tool-call audit logging.

When enabled via ``DATASPHERE_AUDIT_ENABLED=1`` the server writes one JSON
object per tool call to a JSONL log (default ``~/.cache/sap-datasphere-mcp/audit.log``).

The schema is intentionally minimal:

    {
      "ts": "2026-05-30T15:42:01.314Z",
      "tool": "datasphere_query_relational",
      "duration_ms": 412,
      "outcome": "ok" | "error" | "denied",
      "args_fingerprint": "sha256:...",
      "rows_returned": 47,
      "tenant_url_hash": "sha256:...",
      "sub": "<oauth-client-id-or-mock>",
      "policy_strict": false
    }

Argument *values* are never logged in plaintext — only a deterministic
SHA-256 of the canonical-JSON encoding. The tenant URL is hashed for the
same reason.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional

__all__ = [
    "AuditRecord",
    "AuditLog",
    "get_default_log_path",
    "fingerprint",
    "hash_tenant_url",
]


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def get_default_log_path() -> Path:
    """Resolve the default audit log path.

    Respects ``DATASPHERE_AUDIT_LOG_PATH`` if set. Otherwise:

    - Windows: ``%LOCALAPPDATA%/sap-datasphere-mcp/audit.log``
    - POSIX:   ``~/.cache/sap-datasphere-mcp/audit.log``
    """
    override = os.environ.get("DATASPHERE_AUDIT_LOG_PATH")
    if override:
        return Path(os.path.expanduser(override)).resolve()

    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/AppData/Local")
        return (Path(base) / "sap-datasphere-mcp" / "audit.log").resolve()
    return (Path(os.path.expanduser("~")) / ".cache" / "sap-datasphere-mcp" / "audit.log").resolve()


def fingerprint(value: Any) -> str:
    """Return a deterministic SHA-256 fingerprint of ``value``.

    Used to log argument shapes without leaking values.
    """
    try:
        canonical = json.dumps(value, sort_keys=True, default=repr)
    except Exception:  # pragma: no cover — defensive
        canonical = repr(value)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


def hash_tenant_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    return "sha256:" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]


@dataclass
class AuditRecord:
    """In-progress audit record. Finalize with :py:meth:`commit`."""

    tool: str
    sub: Optional[str] = None
    tenant_url: Optional[str] = None
    policy_strict: bool = False
    args_fingerprint: Optional[str] = None
    _start_perf: float = field(default_factory=time.perf_counter)

    def to_json(self, *, outcome: str, rows: Optional[int] = None, error_code: Optional[str] = None) -> Dict[str, Any]:
        return {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "tool": self.tool,
            "duration_ms": int((time.perf_counter() - self._start_perf) * 1000),
            "outcome": outcome,
            "args_fingerprint": self.args_fingerprint,
            "rows_returned": rows,
            "tenant_url_hash": hash_tenant_url(self.tenant_url),
            "sub": self.sub,
            "policy_strict": self.policy_strict,
            **({"error_code": error_code} if error_code else {}),
        }


class AuditLog:
    """JSONL audit log writer.

    Thread-safe within a single process. Cheap when disabled — the ``write``
    method short-circuits without touching disk.
    """

    def __init__(self, *, path: Optional[Path] = None, enabled: Optional[bool] = None) -> None:
        self.path = path or get_default_log_path()
        self.enabled = _env_flag("DATASPHERE_AUDIT_ENABLED", default=False) if enabled is None else enabled
        self._lock = Lock()
        if self.enabled:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def start(self, *, tool: str, sub: Optional[str], tenant_url: Optional[str], policy_strict: bool, args: Any) -> AuditRecord:
        return AuditRecord(
            tool=tool,
            sub=sub,
            tenant_url=tenant_url,
            policy_strict=policy_strict,
            args_fingerprint=fingerprint(args) if args is not None else None,
        )

    def commit(self, record: AuditRecord, *, outcome: str, rows: Optional[int] = None, error_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        payload = record.to_json(outcome=outcome, rows=rows, error_code=error_code)
        line = json.dumps(payload, default=str, separators=(",", ":"))
        with self._lock:
            try:
                with self.path.open("a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
            except OSError:
                # Audit failures must never break the tool call. Swallow.
                return payload
        return payload

    def tail(self, *, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the last ``limit`` audit records (parsed)."""
        if not self.path.exists():
            return []
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                lines: Iterable[str] = fh.readlines()[-limit:]
        except OSError:
            return []
        out: List[Dict[str, Any]] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out


# Module-level singleton constructed on first access.
_LOG: Optional[AuditLog] = None
_LOG_LOCK = Lock()


def get_audit_log() -> AuditLog:
    global _LOG
    with _LOG_LOCK:
        if _LOG is None:
            _LOG = AuditLog()
        return _LOG


def reset_audit_log_for_tests() -> None:
    """Test helper — drop the module singleton so a fresh instance is built."""
    global _LOG
    with _LOG_LOCK:
        _LOG = None
