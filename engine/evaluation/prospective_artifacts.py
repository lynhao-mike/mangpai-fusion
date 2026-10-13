from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


_CASE_ID_PATTERN = re.compile(
    r"P-GO-\d{4}-\d{3}-[乾坤]-[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]{8}"
)
_ARTIFACT_KIND_PATTERN = re.compile(r"[a-z][a-z0-9-]*")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_REVISION_FIELDS = frozenset(
    {"supersedes", "supersedes_sha256", "reason", "approved_by"}
)
_REPOSITORY_STATE = Path("META/project-state.json")
_R3_CONTRACT = Path(
    ".omo/drafts/w2-c4-governance-promotion-remediation-r3-admission-contract-2026-08-08.md"
)
_CONCRETE_PATH_TYPE = type(Path())


@dataclass(frozen=True, slots=True)
class _RepositoryAuthority:
    root: Path
    project_state_sha256: str
    contract_sha256: str
    issuer: object


def _regular_file_digest(root: Path, relative: Path, description: str) -> str:
    path = authenticate_path(root / relative, admitted_root=root)
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise ValueError(f"{description} is unreadable") from error


def _trusted_repository_root() -> Path:
    """Resolve the repository only from this already-loaded production module."""
    return Path(__file__).absolute().parents[2]


def _authority_api():
    issuer = object()
    cached: _RepositoryAuthority | None = None

    def issue() -> _RepositoryAuthority:
        nonlocal cached
        root = _trusted_repository_root()
        if type(root) is not _CONCRETE_PATH_TYPE or not root.is_absolute():
            raise TypeError("repository authority root must be an exact absolute Path")
        project_state_sha256 = _regular_file_digest(
            root, _REPOSITORY_STATE, "canonical project state"
        )
        contract_sha256 = _regular_file_digest(root, _R3_CONTRACT, "frozen R3 contract")
        if cached is not None and cached.root == root:
            if (
                cached.project_state_sha256 != project_state_sha256
                or cached.contract_sha256 != contract_sha256
            ):
                raise ValueError("canonical repository authority anchor drift detected")
            return cached
        cached = _RepositoryAuthority(
            root=root,
            project_state_sha256=project_state_sha256,
            contract_sha256=contract_sha256,
            issuer=issuer,
        )
        return cached

    def admitted_root(authority: _RepositoryAuthority) -> Path:
        if (
            type(authority) is not _RepositoryAuthority
            or authority.issuer is not issuer
        ):
            raise TypeError("repository authority must be the private exact token")
        return authority.root

    return issue, admitted_root


_repository_authority, _authority_root = _authority_api()
del _authority_api


@dataclass(frozen=True)
class ArtifactRef:
    artifact_path: str
    artifact_sha256: str


def canonical_artifact_sha256(payload: Mapping[str, Any]) -> str:
    unsigned = {
        key: value for key, value in payload.items() if key != "artifact_sha256"
    }
    encoded = json.dumps(
        unsigned,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def single_case_artifact_path(
    root: Path,
    case_id: str,
    artifact_kind: str,
    version: int,
) -> Path:
    if _CASE_ID_PATTERN.fullmatch(case_id) is None:
        raise ValueError("invalid prospective case_id")
    if (
        isinstance(version, bool)
        or not isinstance(version, int)
        or version < 1
        or _ARTIFACT_KIND_PATTERN.fullmatch(artifact_kind) is None
    ):
        raise ValueError("invalid artifact identity")
    return Path(root) / case_id / f"{case_id}--{artifact_kind}--v{version:03d}.json"


def _document_bytes(document: Mapping[str, Any]) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _is_reparse_point(path: Path) -> bool:
    """Return whether *path* is a Windows reparse point without following it."""
    try:
        attributes = path.lstat().st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def authenticate_path(
    path: Path,
    *,
    admitted_root: Path,
    destination: bool = False,
) -> Path:
    """Authenticate one lexical path boundary without resolving link-like entries.

    This narrows link and alias races but cannot eliminate filesystem TOCTOU; callers
    must retain create-only publication or descriptor-level controls as appropriate.
    """
    if not isinstance(path, Path) or not isinstance(admitted_root, Path):
        raise TypeError("PATH_TYPE: path and admitted_root must be pathlib.Path")
    if type(destination) is not bool:
        raise TypeError("PATH_TYPE: destination must be exact bool")
    if not path.is_absolute() or not admitted_root.is_absolute():
        raise ValueError("PATH_ABSOLUTE: path and admitted_root must be absolute")
    if any(part in {".", ".."} for part in path.parts):
        category = "PATH_TRAVERSAL" if ".." in path.parts else "PATH_ALIAS"
        raise ValueError(f"{category}: explicit path alias is forbidden")

    canonical_path = _lexical_absolute(path)
    canonical_root = _lexical_absolute(admitted_root)
    if os.path.normcase(os.fspath(path)) != os.path.normcase(os.fspath(canonical_path)):
        raise ValueError("PATH_ALIAS: path must already be lexically normalized")
    try:
        relative = canonical_path.relative_to(canonical_root)
    except ValueError as exc:
        raise ValueError("PATH_OUTSIDE_ROOT: path escapes admitted root") from exc

    candidates = [canonical_root]
    current = canonical_root
    for part in relative.parts:
        current = current / part
        candidates.append(current)
    for candidate in candidates:
        if _is_reparse_point(candidate):
            raise ValueError(f"PATH_LINK_LIKE: link-like path component: {candidate}")
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ValueError(f"PATH_UNREADABLE: cannot inspect {candidate}") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"PATH_LINK_LIKE: link-like path component: {candidate}")

    if destination:
        if canonical_path.exists() or canonical_path.is_symlink():
            raise ValueError(f"output already exists: {canonical_path}")
    else:
        try:
            metadata = canonical_path.lstat()
        except OSError as exc:
            raise ValueError(
                f"PATH_UNREADABLE: path is unreadable: {canonical_path}"
            ) from exc
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError(
                f"PATH_LEAF_TYPE: path is not a regular file: {canonical_path}"
            )
    return canonical_path


def publish_new_json(
    path: Path,
    payload: Mapping[str, Any],
    *,
    dry_run: bool,
    admitted_root: Path | None = None,
) -> ArtifactRef:
    digest = canonical_artifact_sha256(payload)
    reference = ArtifactRef(path.as_posix(), digest)
    if dry_run:
        return reference
    if path.exists() or path.is_symlink():
        raise ValueError(f"output already exists: {path}")
    root = Path(admitted_root) if admitted_root is not None else path.parent
    path = authenticate_path(path, admitted_root=root, destination=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    authenticate_path(path, admitted_root=root, destination=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        document = {**payload, "artifact_sha256": digest}
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_document_bytes(document))
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError as exc:
            raise ValueError(f"output already exists: {path}") from exc
    finally:
        temporary_path.unlink(missing_ok=True)
    return reference


def validate_parent_ref(
    ref: ArtifactRef,
    *,
    admitted_root: Path | None = None,
) -> dict[str, Any]:
    if type(ref) is not ArtifactRef:
        raise TypeError("PARENT_SCHEMA: ref must be exact ArtifactRef")
    if (
        type(ref.artifact_path) is not str
        or not ref.artifact_path
        or type(ref.artifact_sha256) is not str
        or _SHA256_PATTERN.fullmatch(ref.artifact_sha256) is None
    ):
        raise ValueError("PARENT_SCHEMA: invalid artifact reference")
    path = Path(ref.artifact_path)
    recurse = admitted_root is not None
    root = Path(admitted_root) if recurse else path.parent
    return _validate_parent_tree(ref, admitted_root=root, active=set(), recurse=recurse)


def _validate_parent_tree(
    ref: ArtifactRef,
    *,
    admitted_root: Path,
    active: set[str],
    recurse: bool,
) -> dict[str, Any]:
    path = authenticate_path(
        Path(ref.artifact_path), admitted_root=admitted_root, destination=False
    )
    identity = os.path.normcase(os.fspath(path))
    if identity in active:
        raise ValueError("PARENT_CYCLE: recursive parent cycle detected")
    active.add(identity)
    try:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise ValueError(
                f"PATH_UNREADABLE: parent artifact is unreadable: {path}"
            ) from exc
        try:
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"parent artifact is not valid UTF-8 JSON: {path}"
            ) from exc
        if not isinstance(document, dict):
            raise ValueError("parent artifact must be a JSON object")
        if "artifact_sha256" not in document:
            if hashlib.sha256(raw).hexdigest() != ref.artifact_sha256:
                raise ValueError("raw parent byte digest mismatch")
            return document
        if raw != _document_bytes(document):
            raise ValueError("parent artifact byte drift detected")

        stored_digest = document.get("artifact_sha256")
        if stored_digest != ref.artifact_sha256:
            raise ValueError("parent stored digest does not match reference")
        recomputed_digest = canonical_artifact_sha256(document)
        if recomputed_digest != stored_digest:
            raise ValueError("parent canonical digest mismatch")

        if not recurse:
            return document
        parents = document.get("parents", [])
        if type(parents) is not list:
            raise ValueError("PARENT_SCHEMA: parents must be an exact list")
        seen: set[str] = set()
        for value in parents:
            if type(value) is not dict or set(value) != {
                "artifact_path",
                "artifact_sha256",
            }:
                raise ValueError("PARENT_SCHEMA: recursive parent ref is invalid")
            parent_path = value.get("artifact_path")
            parent_digest = value.get("artifact_sha256")
            if (
                type(parent_path) is not str
                or not parent_path
                or type(parent_digest) is not str
                or _SHA256_PATTERN.fullmatch(parent_digest) is None
            ):
                raise ValueError("PARENT_SCHEMA: recursive parent ref is invalid")
            logical = os.path.normcase(os.fspath(_lexical_absolute(Path(parent_path))))
            if logical in seen:
                raise ValueError("PARENT_DUPLICATE: duplicate logical parent")
            seen.add(logical)
            _validate_parent_tree(
                ArtifactRef(parent_path, parent_digest),
                admitted_root=admitted_root,
                active=active,
                recurse=True,
            )
        return document
    finally:
        active.remove(identity)


def validate_revision_metadata(payload: Mapping[str, Any], version: int) -> None:
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise ValueError("invalid artifact version")

    present = _REVISION_FIELDS.intersection(payload)
    if version == 1:
        if present:
            raise ValueError("v001 must not contain revision metadata")
        return

    missing = _REVISION_FIELDS.difference(payload)
    if missing:
        raise ValueError(
            "revision metadata missing required field(s): " + ", ".join(sorted(missing))
        )
    for field in ("supersedes", "reason", "approved_by"):
        value = payload[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"revision metadata {field} must be a non-empty string")
    digest = payload["supersedes_sha256"]
    if not isinstance(digest, str) or _SHA256_PATTERN.fullmatch(digest) is None:
        raise ValueError(
            "revision metadata supersedes_sha256 must be a lowercase SHA-256"
        )
