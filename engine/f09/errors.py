from dataclasses import dataclass

@dataclass(frozen=True)
class F09Error(Exception):
    issue_code: str
    field_path: str
    diagnostic: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.issue_code, str) or not self.issue_code.strip():
            raise ValueError("issue_code must be a nonempty string")
        if not isinstance(self.field_path, str) or not self.field_path.strip():
            raise ValueError("field_path must be a nonempty string")
        if not isinstance(self.diagnostic, str):
            raise TypeError("diagnostic must be a string")

    def __str__(self) -> str:
        return self.diagnostic

@dataclass(frozen=True)
class F09IntegrityError(F09Error):
    pass

@dataclass(frozen=True)
class F09SourceError(F09Error):
    pass

@dataclass(frozen=True)
class F09ContractError(F09Error):
    pass

@dataclass(frozen=True)
class F09WriteError(F09Error):
    pass
