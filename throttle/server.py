import asyncio
import json
import logging
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

log = logging.getLogger(__name__)
WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
COMMAND_TIMEOUT = 5.0


def make_server(train, loop: asyncio.AbstractEventLoop, host: str, port: int) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/api/state":
                self._json(HTTPStatus.OK, train.snapshot())
                return
            self._static()

        def do_POST(self):
            if not self.path.startswith("/api/"):
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            action = self.path.removeprefix("/api/")
            try:
                value = self._read_value()
                future = asyncio.run_coroutine_threadsafe(train.apply(action, value), loop)
                self._json(HTTPStatus.OK, future.result(timeout=COMMAND_TIMEOUT))
            except ValueError as error:
                log.warning("rejected %s: %s", action, error)
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            except TimeoutError:
                log.warning("%s timed out waiting for the engine", action)
                self._json(HTTPStatus.GATEWAY_TIMEOUT, {"error": "engine did not respond"})

        def _read_value(self):
            length = int(self.headers.get("Content-Length") or 0)
            if not length:
                return None
            try:
                body = json.loads(self.rfile.read(length))
            except json.JSONDecodeError as error:
                raise ValueError("body must be JSON") from error
            if not isinstance(body, dict):
                raise ValueError("body must be a JSON object")
            return body.get("value")

        def _static(self):
            relative = "index.html" if self.path in ("", "/") else self.path.split("?")[0].lstrip("/")
            target = (WEB_ROOT / relative).resolve()
            if not target.is_relative_to(WEB_ROOT) or not target.is_file():
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            body = target.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status, payload):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            pass

    return ThreadingHTTPServer((host, port), Handler)
