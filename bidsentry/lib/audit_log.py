"""Append-only metadata audit log. Document text is deliberately excluded."""

from __future__ import annotations

import json
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLog:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def append(self, event: dict[str, Any]) -> None:
        record = {"schema_version": "1.0", "created_at": datetime.now(timezone.utc).isoformat(), **event}
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
