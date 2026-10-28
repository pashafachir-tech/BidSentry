"""Append-only metadata audit log. Document text is deliberately excluded."""

from __future__ import annotations

import json
import os
import threading
import uuid
from collections import deque
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


class AuditLog:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    @property
    def sources_dir(self) -> Path:
        return self.path.parent / "audit_sources"

    def save_source_text(self, audit_id: str, source_text: str, retention_days: int = 90) -> None:
        if not audit_id or not source_text:
            return
        target_dir = self.sources_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        if retention_days > 0:
            cutoff = datetime.now(timezone.utc).timestamp() - (retention_days * 86400)
            try:
                for f in target_dir.glob("*.txt"):
                    if f.is_file() and f.stat().st_mtime < cutoff:
                        f.unlink(missing_ok=True)
            except OSError:
                pass
        safe_name = "".join(c for c in audit_id if c.isalnum() or c in ("-", "_"))
        if safe_name:
            source_file = target_dir / f"{safe_name}.txt"
            with self._lock:
                source_file.write_text(source_text, encoding="utf-8")

    def get_source_text(self, audit_id: str) -> str | None:
        if not audit_id:
            return None
        safe_name = "".join(c for c in audit_id if c.isalnum() or c in ("-", "_"))
        if not safe_name:
            return None
        source_file = self.sources_dir / f"{safe_name}.txt"
        if not source_file.is_file():
            return None
        try:
            return source_file.read_text(encoding="utf-8")
        except OSError:
            return None

    def has_source_text(self, audit_id: str) -> bool:
        if not audit_id:
            return False
        safe_name = "".join(c for c in audit_id if c.isalnum() or c in ("-", "_"))
        if not safe_name:
            return False
        source_file = self.sources_dir / f"{safe_name}.txt"
        return source_file.is_file() and source_file.stat().st_size > 0

    def append(self, event: dict[str, Any]) -> None:
        # Document text is deliberately excluded from audit_log.jsonl for privacy compliance
        cleaned_event = {k: v for k, v in event.items() if k != "source_text"}
        record = {"schema_version": "1.0", "created_at": datetime.now(timezone.utc).isoformat(), **cleaned_event}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        with self._lock, self.path.open("a", encoding="utf-8") as stream:
            stream.write(line)

    def _iter_events(self):
        if not self.path.is_file():
            return
        try:
            with self.path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    try:
                        item = json.loads(line)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    if isinstance(item, dict) and item.get("schema_version") == "1.0":
                        yield item
        except OSError:
            return

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        if limit <= 0 or not self.path.is_file():
            return []
        records: deque[dict[str, Any]] = deque(maxlen=limit)
        try:
            with self.path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    try:
                        item = json.loads(line)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    if isinstance(item, dict) and item.get("schema_version") == "1.0" and item.get("event_type") == "audit.completed":
                        records.append(item)
        except OSError:
            return []
        return list(reversed(records))

    def get_audit(self, audit_id: str) -> dict[str, Any] | None:
        if not self.path.is_file() or not audit_id:
            return None
        target = str(audit_id).strip()
        for event in reversed(list(self._iter_events())):
            if event.get("event_type") == "audit.completed" and str(event.get("audit_id", "")).strip() == target:
                if isinstance(event.get("evaluation"), dict):
                    return event["evaluation"]
                risk = event.get("risk") if isinstance(event.get("risk"), dict) else {}
                source_text = self.get_source_text(target) or event.get("source_text", "")
                has_source = bool(source_text) or bool(event.get("has_source_text"))
                return {
                    "audit_id": event.get("audit_id"),
                    "created_at": event.get("created_at"),
                    "package_name": event.get("package_name"),
                    "tender_id": event.get("tender_id"),
                    "notice_number": event.get("notice_number"),
                    "pokja_name": event.get("pokja_name"),
                    "company_name": event.get("company_name"),
                    "contract_value_idr": event.get("contract_value_idr"),
                    "review_role": event.get("review_role", "procurement"),
                    "verdict": event.get("verdict"),
                    "risk_score": risk.get("score", 0),
                    "risk_level": risk.get("level", "LOW"),
                    "risk": risk,
                    "summary": event.get("summary", {}),
                    "executive_summary": event.get("executive_summary", {}),
                    "findings": event.get("findings", []),
                    "adendum_reconciliation": event.get("adendum_reconciliation", {}),
                    "penalty_simulation": event.get("penalty_simulation", {}),
                    "contextual_extraction": event.get("contextual_extraction", {}),
                    "source_text": source_text,
                    "has_source_text": has_source,
                }
        return None

    def _write_atomic(self, lines: list[str]) -> None:
        content = "\n".join(lines) + ("\n" if lines else "")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_name(f"{self.path.name}.tmp.{uuid.uuid4().hex}")
        try:
            with temp_path.open("w", encoding="utf-8") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_path, self.path)
        except Exception:
            if temp_path.is_file():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise

    def delete_audit(self, audit_id: str) -> bool:
        if not self.path.is_file() or not audit_id:
            return False
        with self._lock:
            try:
                lines = self.path.read_text(encoding="utf-8").splitlines()
            except OSError:
                return False
            kept_lines = []
            found = False
            for line in lines:
                try:
                    item = json.loads(line)
                    if isinstance(item, dict) and item.get("audit_id") == audit_id:
                        found = True
                        continue
                except (json.JSONDecodeError, TypeError):
                    pass
                kept_lines.append(line)
            if found:
                self._write_atomic(kept_lines)
            return found

    def purge_older_than(self, days: int) -> int:
        if days <= 0 or not self.path.is_file():
            return 0
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        with self._lock:
            try:
                lines = self.path.read_text(encoding="utf-8").splitlines()
            except OSError:
                return 0
            kept_lines = []
            purged = 0
            for line in lines:
                try:
                    item = json.loads(line)
                    if isinstance(item, dict) and "created_at" in item:
                        created = datetime.fromisoformat(str(item["created_at"]))
                        if created.tzinfo is None:
                            created = created.replace(tzinfo=timezone.utc)
                        if created < cutoff:
                            purged += 1
                            continue
                except Exception:
                    pass
                kept_lines.append(line)
            if purged > 0:
                self._write_atomic(kept_lines)
            return purged

    def finding_exists(self, audit_id: str, finding_id: str) -> bool:
        return any(
            event.get("event_type") == "audit.completed"
            and event.get("audit_id") == audit_id
            and isinstance(event.get("findings"), list)
            and any(isinstance(item, dict) and item.get("id") == finding_id for item in event["findings"])
            for event in self._iter_events()
        )

    def feedback_snapshot(self, audit_id: str = "") -> dict[str, Any]:
        eligible: set[tuple[str, str]] = set()
        latest: dict[tuple[str, str], dict[str, Any]] = {}
        for event in self._iter_events():
            event_type = event.get("event_type")
            current_id = str(event.get("audit_id", ""))
            if event_type == "audit.completed" and current_id:
                findings = event.get("findings") if isinstance(event.get("findings"), list) else []
                eligible.update(
                    (current_id, str(finding["id"]))
                    for finding in findings
                    if isinstance(finding, dict) and finding.get("id")
                )
            elif event_type == "finding.reviewed" and current_id and event.get("finding_id"):
                if event.get("outcome") not in {"SUPPORTED", "NEEDS_MORE_INFO", "NOT_SUPPORTED"}:
                    continue
                latest[(current_id, str(event["finding_id"]))] = {
                    "outcome": event.get("outcome"),
                    "recorded_at": event.get("created_at", ""),
                }

        valid_latest = {key: value for key, value in latest.items() if key in eligible}
        counts = {outcome: 0 for outcome in ("SUPPORTED", "NEEDS_MORE_INFO", "NOT_SUPPORTED")}
        for value in valid_latest.values():
            if value.get("outcome") in counts:
                counts[value["outcome"]] += 1

        audit_outcomes = {
            finding_id: value
            for (item_id, finding_id), value in valid_latest.items()
            if audit_id and item_id == audit_id
        }
        total = len(eligible)
        reviewed = len(valid_latest)
        return {
            "audit_id": audit_id or None,
            "outcomes": audit_outcomes,
            "pilot": {
                "audits_with_findings": len({item_id for item_id, _ in eligible}),
                "eligible_findings": total,
                "reviewed_findings": reviewed,
                "coverage_percent": round(reviewed * 100 / total) if total else None,
                "outcome_counts": counts,
            },
            "note": "Catatan reviewer yang dimasukkan pengguna; bukan akurasi, adjudikasi independen, atau metrik dampak.",
        }
