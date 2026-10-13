"""六源三领域分析的输入、上下文与切片结果契约。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

from engine.v5.domain import V5Claim, V5School

DomainId = Literal["career", "wealth", "marriage"]
SliceStatus = Literal["implemented", "abstain", "unsupported"]
DOMAIN_IDS: tuple[DomainId, ...] = ("career", "wealth", "marriage")


@dataclass(frozen=True, slots=True)
class DomainAnalysisRequest:
    """交互与非交互入口共用的规范化分析请求。"""

    gender: str
    birth_datetime: datetime
    as_of_date: date
    domains: tuple[DomainId, ...] = DOMAIN_IDS
    output_dir: str = "reports/domain-analysis"
    case_id: str = ""

    def __post_init__(self) -> None:
        if self.gender not in {"乾", "坤"}:
            raise ValueError("gender must be 乾 or 坤")
        if not isinstance(self.birth_datetime, datetime):
            raise ValueError("birth_datetime must be a datetime")
        if self.birth_datetime.tzinfo is not None:
            raise ValueError("birth_datetime must be naive and already corrected")
        if not isinstance(self.as_of_date, date):
            raise ValueError("as_of_date must be a date")
        normalized = tuple(dict.fromkeys(self.domains))
        if not normalized or any(domain not in DOMAIN_IDS for domain in normalized):
            raise ValueError("domains must be a non-empty subset of career/wealth/marriage")
        if not str(self.output_dir).strip():
            raise ValueError("output_dir must be non-empty")
        if self.case_id and (Path(self.case_id).name != self.case_id or self.case_id in {".", ".."}):
            raise ValueError("case_id must be a safe filename identity")
        object.__setattr__(self, "domains", normalized)
        object.__setattr__(self, "output_dir", Path(self.output_dir).as_posix())

    def to_dict(self) -> dict[str, Any]:
        result = {
            "gender": self.gender,
            "birth_datetime": self.birth_datetime.isoformat(sep=" ", timespec="seconds"),
            "as_of_date": self.as_of_date.isoformat(),
            "domains": list(self.domains),
            "output_dir": self.output_dir,
        }
        if self.case_id:
            result["case_id"] = self.case_id
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainAnalysisRequest":
        return cls(
            gender=str(data["gender"]),
            birth_datetime=datetime.fromisoformat(str(data["birth_datetime"])),
            as_of_date=date.fromisoformat(str(data["as_of_date"])),
            domains=tuple(data.get("domains", DOMAIN_IDS)),
            output_dir=str(data.get("output_dir", "reports/domain-analysis")),
            case_id=str(data.get("case_id", "")),
        )


@dataclass(frozen=True, slots=True)
class DomainAnalysisContext:
    """排盘结果与原局、当前大运、未来三年的统一只读上下文。"""

    request: DomainAnalysisRequest
    case_id: str
    pillars: tuple[str, str, str, str]
    dayun: tuple[dict[str, int | str], ...]
    current_dayun: dict[str, int | str]
    future_years: tuple[tuple[int, str], ...]
    calculator: str

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id is required")
        if len(self.pillars) != 4 or any(len(item) != 2 for item in self.pillars):
            raise ValueError("pillars must contain four Ganzhi strings")
        if len(self.future_years) != 3:
            raise ValueError("future_years must contain exactly three years")
        if not self.current_dayun.get("ganzhi"):
            raise ValueError("current_dayun is required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": self.request.to_dict(),
            "case_id": self.case_id,
            "pillars": list(self.pillars),
            "dayun": [dict(item) for item in self.dayun],
            "current_dayun": dict(self.current_dayun),
            "future_years": [[year, ganzhi] for year, ganzhi in self.future_years],
            "calculator": self.calculator,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainAnalysisContext":
        return cls(
            request=DomainAnalysisRequest.from_dict(data["request"]),
            case_id=str(data["case_id"]),
            pillars=tuple(data["pillars"]),
            dayun=tuple(dict(item) for item in data["dayun"]),
            current_dayun=dict(data["current_dayun"]),
            future_years=tuple((int(item[0]), str(item[1])) for item in data["future_years"]),
            calculator=str(data["calculator"]),
        )


@dataclass(frozen=True, slots=True)
class SliceAudit:
    reason: str = ""
    error_type: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"reason": self.reason, "error_type": self.error_type}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "SliceAudit":
        data = data or {}
        return cls(reason=str(data.get("reason", "")), error_type=str(data.get("error_type", "")))


@dataclass(frozen=True, slots=True)
class SliceResult:
    school: V5School
    domain: DomainId
    status: SliceStatus
    claims: tuple[V5Claim, ...] = field(default_factory=tuple)
    audit: SliceAudit = field(default_factory=SliceAudit)

    def __post_init__(self) -> None:
        if self.domain not in DOMAIN_IDS:
            raise ValueError(f"invalid domain: {self.domain}")
        if self.status != "implemented" and self.claims:
            raise ValueError("only implemented slices may contain claims")
        if any(claim.school != self.school for claim in self.claims):
            raise ValueError("claim school must match slice school")

    def to_dict(self) -> dict[str, Any]:
        return {
            "school": self.school,
            "domain": self.domain,
            "status": self.status,
            "claims": [claim.to_dict() for claim in self.claims],
            "audit": self.audit.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SliceResult":
        return cls(
            school=data["school"],
            domain=data["domain"],
            status=data["status"],
            claims=tuple(V5Claim.from_dict(item) for item in data.get("claims", [])),
            audit=SliceAudit.from_dict(data.get("audit")),
        )
