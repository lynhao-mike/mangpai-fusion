"""SQLite-backed production analysis store.

This module is intentionally stdlib-only so the production MVP can run in the
current repository without adding runtime dependencies.  It stores operational
metadata only; canonical analysis artifacts remain under cases/ and reports/.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional, Union


ISO_TEXT = str


@dataclass(frozen=True)
class AnalysisArtifactRecord:
    """A persisted artifact attached to one production analysis job."""

    kind: str
    path: str
    sha256: str = ""
    created_at: ISO_TEXT = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "path": self.path,
            "sha256": self.sha256,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class AnalysisJobRecord:
    """Operational state for one analysis request."""

    analysis_id: str
    case_id: str
    status: str
    input_path: str
    input_sha256: str
    cache_key: str
    engine_version: str
    render: bool
    template_name: str
    cache_hit: bool = False
    error: str = ""
    summary: dict[str, Any] = field(default_factory=dict)
    created_at: ISO_TEXT = ""
    started_at: ISO_TEXT = ""
    completed_at: ISO_TEXT = ""
    artifacts: list[AnalysisArtifactRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "case_id": self.case_id,
            "status": self.status,
            "input_path": self.input_path,
            "input_sha256": self.input_sha256,
            "cache_key": self.cache_key,
            "engine_version": self.engine_version,
            "render": self.render,
            "template_name": self.template_name,
            "cache_hit": self.cache_hit,
            "error": self.error,
            "summary": self.summary,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "artifacts": [a.to_dict() for a in self.artifacts],
        }


class SQLiteAnalysisStore:
    """Small SQLite repository for production analysis jobs and cache metadata."""

    def __init__(self, db_path: Union[str, Path]) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS analysis_jobs (
                  analysis_id TEXT PRIMARY KEY,
                  case_id TEXT,
                  status TEXT NOT NULL,
                  input_path TEXT NOT NULL,
                  input_sha256 TEXT NOT NULL,
                  cache_key TEXT NOT NULL,
                  engine_version TEXT NOT NULL,
                  render INTEGER NOT NULL,
                  template_name TEXT NOT NULL,
                  cache_hit INTEGER NOT NULL DEFAULT 0,
                  error TEXT,
                  summary_json TEXT NOT NULL DEFAULT '{}',
                  created_at TEXT NOT NULL,
                  started_at TEXT,
                  completed_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_analysis_jobs_cache_key
                  ON analysis_jobs(cache_key);
                CREATE INDEX IF NOT EXISTS idx_analysis_jobs_case_id
                  ON analysis_jobs(case_id);

                CREATE TABLE IF NOT EXISTS analysis_artifacts (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  analysis_id TEXT NOT NULL,
                  kind TEXT NOT NULL,
                  path TEXT NOT NULL,
                  sha256 TEXT,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY (analysis_id) REFERENCES analysis_jobs(analysis_id)
                    ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS analysis_cache (
                  cache_key TEXT PRIMARY KEY,
                  analysis_id TEXT NOT NULL,
                  case_id TEXT NOT NULL,
                  input_sha256 TEXT NOT NULL,
                  engine_version TEXT NOT NULL,
                  summary_json TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY (analysis_id) REFERENCES analysis_jobs(analysis_id)
                    ON DELETE CASCADE
                );
                """
            )

    def create_job(
        self,
        *,
        analysis_id: str,
        input_path: str,
        input_sha256: str,
        cache_key: str,
        engine_version: str,
        render: bool,
        template_name: str,
        created_at: str,
        status: str = "running",
        case_id: str = "",
        cache_hit: bool = False,
        started_at: str = "",
    ) -> AnalysisJobRecord:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO analysis_jobs (
                  analysis_id, case_id, status, input_path, input_sha256,
                  cache_key, engine_version, render, template_name, cache_hit,
                  error, summary_json, created_at, started_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    case_id,
                    status,
                    input_path,
                    input_sha256,
                    cache_key,
                    engine_version,
                    1 if render else 0,
                    template_name,
                    1 if cache_hit else 0,
                    "",
                    "{}",
                    created_at,
                    started_at,
                    "",
                ),
            )
        job = self.get_job(analysis_id)
        if job is None:
            raise RuntimeError(f"analysis job was not created: {analysis_id}")
        return job

    def complete_job(
        self,
        *,
        analysis_id: str,
        case_id: str,
        summary: dict[str, Any],
        completed_at: str,
        artifacts: list[AnalysisArtifactRecord],
        cache_hit: bool = False,
    ) -> AnalysisJobRecord:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE analysis_jobs
                   SET case_id = ?, status = 'completed', cache_hit = ?,
                       summary_json = ?, completed_at = ?, error = ''
                 WHERE analysis_id = ?
                """,
                (
                    case_id,
                    1 if cache_hit else 0,
                    json.dumps(summary, ensure_ascii=False, sort_keys=True),
                    completed_at,
                    analysis_id,
                ),
            )
            conn.execute(
                "DELETE FROM analysis_artifacts WHERE analysis_id = ?",
                (analysis_id,),
            )
            conn.executemany(
                """
                INSERT INTO analysis_artifacts (
                  analysis_id, kind, path, sha256, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        analysis_id,
                        artifact.kind,
                        artifact.path,
                        artifact.sha256,
                        artifact.created_at or completed_at,
                    )
                    for artifact in artifacts
                ],
            )
        job = self.get_job(analysis_id)
        if job is None:
            raise RuntimeError(f"analysis job disappeared: {analysis_id}")
        return job

    def fail_job(self, *, analysis_id: str, error: str, completed_at: str) -> AnalysisJobRecord:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE analysis_jobs
                   SET status = 'failed', error = ?, completed_at = ?
                 WHERE analysis_id = ?
                """,
                (error, completed_at, analysis_id),
            )
        job = self.get_job(analysis_id)
        if job is None:
            raise RuntimeError(f"analysis job disappeared: {analysis_id}")
        return job

    def save_cache(
        self,
        *,
        cache_key: str,
        analysis_id: str,
        case_id: str,
        input_sha256: str,
        engine_version: str,
        summary: dict[str, Any],
        created_at: str,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO analysis_cache (
                  cache_key, analysis_id, case_id, input_sha256,
                  engine_version, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                  analysis_id = excluded.analysis_id,
                  case_id = excluded.case_id,
                  input_sha256 = excluded.input_sha256,
                  engine_version = excluded.engine_version,
                  summary_json = excluded.summary_json,
                  created_at = excluded.created_at
                """,
                (
                    cache_key,
                    analysis_id,
                    case_id,
                    input_sha256,
                    engine_version,
                    json.dumps(summary, ensure_ascii=False, sort_keys=True),
                    created_at,
                ),
            )

    def get_cached_job(self, cache_key: str) -> Optional[AnalysisJobRecord]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT analysis_id FROM analysis_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        if row is None:
            return None
        return self.get_job(str(row["analysis_id"]))

    def get_job(self, analysis_id: str) -> Optional[AnalysisJobRecord]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM analysis_jobs WHERE analysis_id = ?",
                (analysis_id,),
            ).fetchone()
            if row is None:
                return None
            artifact_rows = conn.execute(
                """
                SELECT kind, path, sha256, created_at
                  FROM analysis_artifacts
                 WHERE analysis_id = ?
                 ORDER BY id ASC
                """,
                (analysis_id,),
            ).fetchall()
        return self._job_from_row(row, artifact_rows)

    def _job_from_row(
        self,
        row: sqlite3.Row,
        artifact_rows: list[sqlite3.Row],
    ) -> AnalysisJobRecord:
        try:
            summary = json.loads(row["summary_json"] or "{}")
        except json.JSONDecodeError:
            summary = {"raw": row["summary_json"]}
        artifacts = [
            AnalysisArtifactRecord(
                kind=str(a["kind"]),
                path=str(a["path"]),
                sha256=str(a["sha256"] or ""),
                created_at=str(a["created_at"] or ""),
            )
            for a in artifact_rows
        ]
        return AnalysisJobRecord(
            analysis_id=str(row["analysis_id"]),
            case_id=str(row["case_id"] or ""),
            status=str(row["status"]),
            input_path=str(row["input_path"]),
            input_sha256=str(row["input_sha256"]),
            cache_key=str(row["cache_key"]),
            engine_version=str(row["engine_version"]),
            render=bool(row["render"]),
            template_name=str(row["template_name"]),
            cache_hit=bool(row["cache_hit"]),
            error=str(row["error"] or ""),
            summary=summary if isinstance(summary, dict) else {"value": summary},
            created_at=str(row["created_at"]),
            started_at=str(row["started_at"] or ""),
            completed_at=str(row["completed_at"] or ""),
            artifacts=artifacts,
        )
