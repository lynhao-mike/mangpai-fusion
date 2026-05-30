"""Production MVP HTTP API for mangpai-fusion.

Run locally:

    python -m tools.production_api --host 127.0.0.1 --port 8765 --db runtime/analysis.sqlite3

The API intentionally uses Python stdlib only.  It is suitable for local or
internal MVP deployments and can later be replaced by FastAPI/ASGI without
changing the production service boundary.
"""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from engine.application.production_service import (
    ProductionAnalysisService,
    request_from_dict,
)
from engine.infrastructure.analysis_store import SQLiteAnalysisStore


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_DB_PATH = "runtime/analysis.sqlite3"


class ProductionAPIHandler(BaseHTTPRequestHandler):
    """Small JSON HTTP handler for production analysis requests."""

    server_version = "MangpaiFusionProductionAPI/0.1"

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler naming
        parsed = urlparse(self.path)
        if parsed.path == "/v1/health":
            self._send_json(HTTPStatus.OK, self.service.health())
            return

        prefix = "/v1/analyses/"
        if parsed.path.startswith(prefix):
            analysis_id = parsed.path[len(prefix):].strip("/")
            if not analysis_id:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "analysis_id is required"})
                return
            result = self.service.get(analysis_id)
            if result is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "analysis not found"})
                return
            self._send_json(HTTPStatus.OK, result)
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler naming
        parsed = urlparse(self.path)
        if parsed.path != "/v1/analyses":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        try:
            payload = self._read_json_body()
            request = request_from_dict(payload)
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        try:
            result = self.service.submit(request)
        except (FileNotFoundError, ValueError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except Exception as exc:  # noqa: BLE001 - API safety net
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": f"{type(exc).__name__}: {exc}"},
            )
            return

        status = HTTPStatus.OK if result.get("status") == "completed" else HTTPStatus.INTERNAL_SERVER_ERROR
        self._send_json(status, result)

    @property
    def service(self) -> ProductionAnalysisService:
        return self.server.service  # type: ignore[attr-defined]

    def _read_json_body(self) -> dict[str, Any]:
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        if length <= 0:
            raise ValueError("JSON request body is required")
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(int(status))
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep default access logs compact and UTF-8 safe on Windows terminals.
        message = fmt % args
        print(f"[{self.log_date_time_string()}] {self.address_string()} {message}")


class ProductionHTTPServer(ThreadingHTTPServer):
    """Threading HTTP server carrying a production service instance."""

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
        service: ProductionAnalysisService,
    ) -> None:
        super().__init__(server_address, handler_class)
        self.service = service


def build_server(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    db_path: str = DEFAULT_DB_PATH,
    workspace_root: Optional[str] = None,
) -> ProductionHTTPServer:
    store = SQLiteAnalysisStore(Path(db_path))
    service = ProductionAnalysisService(
        store=store,
        workspace_root=Path(workspace_root).resolve() if workspace_root else Path.cwd().resolve(),
    )
    return ProductionHTTPServer((host, int(port)), ProductionAPIHandler, service)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="mangpai-fusion production MVP HTTP API")
    parser.add_argument("--host", default=DEFAULT_HOST, help="bind host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="bind port")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite database path")
    parser.add_argument("--workspace-root", default=None, help="workspace root; defaults to current directory")
    args = parser.parse_args(argv)

    server = build_server(
        host=args.host,
        port=args.port,
        db_path=args.db,
        workspace_root=args.workspace_root,
    )
    print(
        "mangpai-fusion production API listening on "
        f"http://{args.host}:{args.port} with db={args.db}"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down production API")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
