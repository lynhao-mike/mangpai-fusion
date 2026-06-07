"""V2 Evidence 适配器基础工具。"""

from __future__ import annotations

import hashlib
from typing import Any

DOMAIN_ALIASES: dict[str, str] = {
    "事业": "career",
    "职业": "career",
    "官名": "career",
    "学业": "education",
    "学历": "education",
    "考试": "education",
    "财运": "wealth",
    "财富": "wealth",
    "婚姻": "marriage",
    "感情": "marriage",
    "健康": "health",
    "疾病": "health",
    "灾厄": "health",
    "家庭": "family",
    "父母": "family",
    "子女": "family",
    "性格": "personality",
    "general": "general",
}

SCHOOL_ALIASES: dict[str, str] = {
    "子平": "ziping",
    "滴天髓": "tiaohou_ditiansui",
    "调候": "tiaohou_ditiansui",
    "段": "duan",
    "杨": "yang",
    "任": "ren",
    "高": "gao",
}


def normalize_domain(domain: str) -> str:
    value = str(domain or "general").strip()
    return DOMAIN_ALIASES.get(value, value or "general")


def clamp_confidence(value: Any, default: float = 0.5) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = default
    return max(0.0, min(1.0, score))


def confidence_from_obj(obj: Any, default: float = 0.5) -> float:
    if obj is None:
        return default
    if isinstance(obj, (int, float)):
        return clamp_confidence(obj, default)
    posterior = getattr(obj, "posterior", None)
    if posterior is not None:
        return clamp_confidence(posterior, default)
    percent = getattr(obj, "percent", None)
    if percent is not None:
        value = float(percent)
        return clamp_confidence(value / 100 if value > 1 else value, default)
    if isinstance(obj, dict):
        if "posterior" in obj:
            return clamp_confidence(obj["posterior"], default)
        if "percent" in obj:
            value = float(obj["percent"])
            return clamp_confidence(value / 100 if value > 1 else value, default)
    return default


def stable_evidence_id(*parts: object) -> str:
    raw = "|".join(str(part) for part in parts if part is not None)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"v2ev-{digest}"


def text_from_evidence_item(item: Any) -> str:
    if item is None:
        return ""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return str(item.get("description") or item.get("summary") or item.get("ref") or item)
    return str(getattr(item, "description", None) or getattr(item, "summary", None) or item)
