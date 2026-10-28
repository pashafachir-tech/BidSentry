"""Loader for declarative rules from config/rules.yaml."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml


_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "rules.yaml"


@functools.lru_cache(maxsize=1)
def load_rules_config() -> dict[str, Any]:
    """Load and parse rules.yaml. Cached for fast in-process access."""
    if not _CONFIG_PATH.exists():
        return {}
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def get_threshold(name: str, default: Any = None) -> Any:
    cfg = load_rules_config()
    return cfg.get("thresholds", {}).get(name, default)


def get_brand_equivalency_phrases() -> list[str]:
    cfg = load_rules_config()
    return cfg.get("brand_lockin", {}).get("equivalency_phrases", [
        "atau setara", "setara", "atau ekuivalen", "ekuivalen", "equivalent", "or equivalent"
    ])


def get_rules_list() -> list[dict[str, Any]]:
    cfg = load_rules_config()
    return cfg.get("rules", [])


def get_rule_by_id(rule_id: str) -> dict[str, Any] | None:
    for rule in get_rules_list():
        if rule.get("id") == rule_id:
            return rule
    return None


def get_billing_rate_limits(role: str) -> tuple[float, float, str]:
    cfg = load_rules_config()
    rates = cfg.get("thresholds", {}).get("billing_rates", {})
    role_cfg = rates.get(role, {})
    min_val = float(role_cfg.get("min_idr", 40_000_000))
    max_val = float(role_cfg.get("max_idr", 70_000_000))
    guideline = str(role_cfg.get("guideline", "Pedoman INKINDO"))
    return min_val, max_val, guideline
