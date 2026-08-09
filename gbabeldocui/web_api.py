"""
FastAPI web server for PDFMathTranslate with multi-user authentication.

This module provides REST API endpoints for:
- User authentication (login, logout, registration)
- File upload and translation
- Settings management
- Translation history
"""

import asyncio
import functools
import ipaddress
import json
import logging
import math
import os
import re
import secrets
import shutil
import socket
import tempfile
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path
from urllib.parse import urlparse

from fastapi import Depends
from fastapi import FastAPI
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import Response
from fastapi import UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from filelock import FileLock
from filelock import Timeout as FileLockTimeout
from pydantic import BaseModel
from pydantic import StrictBool
from starlette.background import BackgroundTask
from starlette.datastructures import Headers

from gbabeldocui import __version__ as gbabeldocui_version
from gbabeldocui._vendor.pdf2zh_next.config.model import SettingsModel
from gbabeldocui._vendor.pdf2zh_next.high_level import do_translate_async_stream
from gbabeldocui.auth import AuthenticationError
from gbabeldocui.auth import UserDataCleanupError
from gbabeldocui.auth import UserManager
from gbabeldocui.translation_task_store import ActiveTaskLimitError
from gbabeldocui.translation_task_store import GlobalActiveTaskLimitError
from gbabeldocui.translation_task_store import TranslationTaskStore

logger = logging.getLogger(__name__)

DEFAULT_MAX_UPLOAD_BYTES = 50 * 1024 * 1024
DEFAULT_MAX_USER_STORAGE_BYTES = 2 * 1024 * 1024 * 1024
DEFAULT_MAX_ACTIVE_TASKS_PER_USER = 2
DEFAULT_MAX_ACTIVE_TASKS_GLOBAL = 8
DEFAULT_TRANSLATION_TIMEOUT_SECONDS = 2 * 60 * 60
DEFAULT_MAX_USERS = 1000
DEFAULT_AUTH_ATTEMPT_LIMIT = 5
DEFAULT_AUTH_ATTEMPT_WINDOW_SECONDS = 300
DEFAULT_ORPHAN_UPLOAD_TTL_SECONDS = 7 * 24 * 60 * 60
DEFAULT_TASK_RETENTION_DAYS = 90
DEFAULT_RETENTION_GRACE_DAYS = 7
ORPHAN_UPLOAD_CLEANUP_INTERVAL_SECONDS = 6 * 60 * 60
UPLOAD_CHUNK_BYTES = 1024 * 1024
MAX_HISTORY_PAGE_SIZE = 200
MAX_HISTORY_OFFSET = 1_000_000
MAX_FILENAME_UTF8_BYTES = 240
MAX_SETTINGS_JSON_BYTES = 256 * 1024
MAX_SETTINGS_FILE_BYTES = MAX_SETTINGS_JSON_BYTES * 2
MAX_SETTINGS_IMPORT_BYTES = MAX_SETTINGS_FILE_BYTES
MAX_JSON_BODY_BYTES = 64 * 1024
PDF_HEADER_SCAN_BYTES = 1024
MAX_CONFIGURED_POOL_WORKERS = 64
MAX_CONFIGURED_QPS = 20
MAX_CONFIGURED_RPM = 1200
MAX_PDF_PAGES = 5000
MAX_FORMULA_PATTERN_LENGTH = 256
SESSION_COOKIE_NAME = "gbabeldocui_session"
CSRF_COOKIE_NAME = "gbabeldocui_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"
COOKIE_MAX_AGE_SECONDS = 24 * 60 * 60
SETUP_TOKEN = os.getenv("GBABELDOCUI_SETUP_TOKEN", "").strip()
SUPPORTED_SERVICES = frozenset(
    {
        "SiliconFlowFree",
        "OpenAI",
        "AzureOpenAI",
        "Gemini",
        "GoogleGemini",
        "DeepL",
        "Ollama",
        "SiliconFlow",
        "DeepSeek",
        "Zhipu",
        "Claude",
        "ClaudeCode",
        "Bing",
        "Google",
        "Tencent",
        "TencentMechineTranslation",
    }
)
# These engines use server-owned local executables or local network services.
# They must not be selectable by ordinary users, even when the frontend is
# bypassed through a direct API request.
PRIVILEGED_SERVICE_NAMES = frozenset({"Ollama", "Claude", "ClaudeCode"})
ENDPOINT_SETTING_NAMES = frozenset(
    {
        "openai_base_url",
        "azure_openai_base_url",
        "ollama_host",
        "siliconflow_base_url",
        "rpc_doclayout",
    }
)
PRIVILEGED_SETTING_NAMES = frozenset(
    {"ollama_host", "rpc_doclayout", "claude_code_path"}
)
SENSITIVE_SETTING_SUFFIXES = (
    "_api_key",
    "_auth_key",
    "_secret_id",
    "_secret_key",
)
TRUSTED_PROVIDER_HOSTS = frozenset({"api.openai.com", "api.siliconflow.cn"})
TRUSTED_PROVIDER_HOST_SUFFIXES = (".openai.azure.com",)
PUBLIC_MUTATING_API_PATHS = frozenset(
    {
        "/api/auth/setup",
        "/api/auth/login",
        "/api/auth/register/public",
    }
)


def _utc_now() -> datetime:
    """Return a naive UTC timestamp for the existing JSON format."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _reject_non_finite_json_number(value: str):
    raise ValueError(f"Non-finite JSON number is not allowed: {value}")


def _load_json_value(serialized_value: str | bytes) -> object:
    """Parse standards-compliant JSON and reject NaN or infinity values."""
    return json.loads(
        serialized_value,
        parse_constant=_reject_non_finite_json_number,
    )


def _configure_babeldoc_formula_cache() -> None:
    """Replace BabelDOC's unbounded formula-font cache with a bounded cache."""
    from babeldoc.format.pdf.document_il.utils import formular_helper

    current_matcher = formular_helper.is_formulas_font
    cache_parameters = getattr(current_matcher, "cache_parameters", None)
    if cache_parameters and cache_parameters().get("maxsize") == 4096:
        return
    uncached_matcher = getattr(current_matcher, "__wrapped__", current_matcher)
    formular_helper.is_formulas_font = functools.lru_cache(maxsize=4096)(
        uncached_matcher
    )


try:
    MAX_UPLOAD_BYTES = int(
        os.getenv("GBABELDOCUI_MAX_UPLOAD_BYTES", str(DEFAULT_MAX_UPLOAD_BYTES))
    )
except ValueError as exc:
    raise RuntimeError("GBABELDOCUI_MAX_UPLOAD_BYTES must be an integer") from exc

if MAX_UPLOAD_BYTES <= 0:
    raise RuntimeError("GBABELDOCUI_MAX_UPLOAD_BYTES must be greater than zero")


def _positive_environment_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    return value


def _environment_bool(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    normalized_value = raw_value.strip().lower()
    if normalized_value in {"1", "true", "yes", "on"}:
        return True
    if normalized_value in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be a boolean")


MAX_USER_STORAGE_BYTES = _positive_environment_int(
    "GBABELDOCUI_MAX_USER_STORAGE_BYTES", DEFAULT_MAX_USER_STORAGE_BYTES
)
MAX_ACTIVE_TASKS_PER_USER = _positive_environment_int(
    "GBABELDOCUI_MAX_ACTIVE_TASKS_PER_USER", DEFAULT_MAX_ACTIVE_TASKS_PER_USER
)
MAX_ACTIVE_TASKS_GLOBAL = _positive_environment_int(
    "GBABELDOCUI_MAX_ACTIVE_TASKS_GLOBAL", DEFAULT_MAX_ACTIVE_TASKS_GLOBAL
)
MAX_TRANSLATION_TIMEOUT_SECONDS = _positive_environment_int(
    "GBABELDOCUI_TRANSLATION_TIMEOUT_SECONDS", DEFAULT_TRANSLATION_TIMEOUT_SECONDS
)
MAX_USERS = _positive_environment_int("GBABELDOCUI_MAX_USERS", DEFAULT_MAX_USERS)
ALLOW_PRIVATE_ENDPOINTS = _environment_bool("GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS")
ORPHAN_UPLOAD_TTL_SECONDS = _positive_environment_int(
    "GBABELDOCUI_ORPHAN_UPLOAD_TTL_SECONDS",
    DEFAULT_ORPHAN_UPLOAD_TTL_SECONDS,
)
TASK_RETENTION_DAYS = _positive_environment_int(
    "GBABELDOCUI_TASK_RETENTION_DAYS", DEFAULT_TASK_RETENTION_DAYS
)
RETENTION_GRACE_DAYS = _positive_environment_int(
    "GBABELDOCUI_RETENTION_GRACE_DAYS", DEFAULT_RETENTION_GRACE_DAYS
)
COOKIE_SECURE = _environment_bool("GBABELDOCUI_COOKIE_SECURE", default=True)
RETENTION_MARKER_NAME = ".gbabeldocui-retention-v1"
TERMINAL_RETENTION_BATCH_SIZE = 100
MUTATING_HTTP_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
MUTATING_REQUEST_BODY_LIMITS = {
    "/api/upload": MAX_UPLOAD_BYTES + 1024 * 1024,
    "/api/settings/import": MAX_SETTINGS_IMPORT_BYTES + 1024 * 1024,
    "/api/translate": MAX_SETTINGS_JSON_BYTES + 1024 * 1024,
    "/api/settings": MAX_SETTINGS_JSON_BYTES,
}


class AuthenticationAttemptLimiter:
    """Limit repeated login and public-registration failures per client address."""

    def __init__(self, maximum_attempts: int, window_seconds: int):
        self.maximum_attempts = maximum_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = {}
        self._lock = threading.Lock()
        self._last_global_cleanup = 0.0

    def retry_after(self, key: str) -> int | None:
        now = time.monotonic()
        with self._lock:
            self._cleanup_all_expired(now)
            attempts = self._active_attempts(key, now)
            if len(attempts) < self.maximum_attempts:
                return None
            return max(1, int(self.window_seconds - (now - attempts[0]) + 0.999))

    def record_failure(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            self._cleanup_all_expired(now)
            attempts = self._active_attempts(key, now)
            attempts.append(now)
            self._attempts[key] = attempts

    def record_success(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)

    def _active_attempts(self, key: str, now: float) -> list[float]:
        cutoff = now - self.window_seconds
        attempts = [
            attempt for attempt in self._attempts.get(key, []) if attempt > cutoff
        ]
        if attempts:
            self._attempts[key] = attempts
        else:
            self._attempts.pop(key, None)
        return attempts

    def _cleanup_all_expired(self, now: float) -> None:
        if now - self._last_global_cleanup < 60:
            return
        cutoff = now - self.window_seconds
        expired_keys = [
            key
            for key, attempts in self._attempts.items()
            if not attempts or attempts[-1] <= cutoff
        ]
        for key in expired_keys:
            self._attempts.pop(key, None)
        self._last_global_cleanup = now


def _retention_marker_path() -> Path:
    return user_manager.data_dir / RETENTION_MARKER_NAME


def _retention_cleanup_is_ready() -> bool:
    """Create the upgrade marker and wait through the configured grace period."""
    marker_path = _retention_marker_path()
    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            marker_path.touch(exist_ok=False)
        except FileExistsError:
            pass
        marker_time = datetime.fromtimestamp(
            marker_path.stat().st_mtime, tz=timezone.utc
        ).replace(tzinfo=None)
    except OSError:
        logger.exception("Cannot inspect the task-retention upgrade marker")
        return False
    return _utc_now() - marker_time >= timedelta(days=RETENTION_GRACE_DAYS)


async def _cleanup_expired_terminal_tasks_once() -> int:
    """Delete one bounded batch of expired terminal tasks and owned files."""
    retention_cutoff = _utc_now() - timedelta(days=TASK_RETENTION_DAYS)
    removed_count = 0
    expired_tasks = await asyncio.to_thread(
        task_store.list_expired_terminal_tasks,
        completed_before=retention_cutoff,
        limit=TERMINAL_RETENTION_BATCH_SIZE,
    )
    for expired_task in expired_tasks:
        artifacts_removed = await asyncio.to_thread(
            _cleanup_translation_artifacts,
            expired_task,
            user_manager.get_user_dir(expired_task["username"]),
        )
        if not artifacts_removed:
            continue
        record_removed = await asyncio.to_thread(
            task_store.delete_expired_terminal_task,
            expired_task["task_id"],
            completed_before=retention_cutoff,
        )
        if record_removed:
            removed_count += 1
    if removed_count:
        logger.info("Removed %s expired terminal translation task(s)", removed_count)
    return removed_count


# Persistent application state. Runtime task handles are only used for cancellation;
# status, progress, ownership and output paths are stored in SQLite.
user_manager = UserManager()
task_store = TranslationTaskStore(user_manager.db_path)
active_tasks: dict[str, asyncio.Task[None]] = {}
active_task_settings: dict[str, dict] = {}
timed_out_tasks: set[str] = set()
deleting_usernames: set[str] = set()
deleting_usernames_lock = threading.Lock()
authentication_limiter = AuthenticationAttemptLimiter(
    _positive_environment_int(
        "GBABELDOCUI_AUTH_ATTEMPT_LIMIT", DEFAULT_AUTH_ATTEMPT_LIMIT
    ),
    _positive_environment_int(
        "GBABELDOCUI_AUTH_ATTEMPT_WINDOW_SECONDS",
        DEFAULT_AUTH_ATTEMPT_WINDOW_SECONDS,
    ),
)


@asynccontextmanager
async def application_lifespan(_app: FastAPI):
    """Initialize persistent state and stop in-flight work on shutdown."""
    logger.info("PDFMathTranslate Web API starting...")
    instance_lock = FileLock(
        str(user_manager.data_dir / ".gbabeldocui-instance.lock"),
        timeout=0,
        thread_local=False,
    )
    lock_acquired = False
    orphan_cleanup_handle: asyncio.Task[None] | None = None
    try:
        try:
            await asyncio.to_thread(instance_lock.acquire)
        except FileLockTimeout as exc:
            raise RuntimeError(
                "Another GBabelDocUI instance already owns this data directory"
            ) from exc
        lock_acquired = True
        await asyncio.to_thread(user_manager.validate_user_directory_integrity)
        await asyncio.to_thread(user_manager.cleanup_expired_sessions)
        _configure_babeldoc_formula_cache()
        for recovered_task in await asyncio.to_thread(
            task_store.recover_interrupted_tasks
        ):
            await asyncio.to_thread(
                _cleanup_translation_artifacts,
                recovered_task,
                user_manager.get_user_dir(recovered_task["username"]),
            )
        if await asyncio.to_thread(_retention_cleanup_is_ready):
            await _cleanup_expired_terminal_tasks_once()
        orphan_cleanup_handle = asyncio.create_task(
            _periodic_orphan_upload_cleanup(),
            name="orphan-upload-cleanup",
        )
        logger.info("Web API ready")
        yield
    finally:
        if orphan_cleanup_handle is not None:
            orphan_cleanup_handle.cancel()
        running_handles = list(active_tasks.values())
        for task_handle in running_handles:
            task_handle.cancel()
        handles_to_wait = [*running_handles]
        if orphan_cleanup_handle is not None:
            handles_to_wait.insert(0, orphan_cleanup_handle)
        if handles_to_wait:
            await asyncio.gather(*handles_to_wait, return_exceptions=True)
        if lock_acquired:
            await asyncio.to_thread(instance_lock.release)
        logger.info("PDFMathTranslate Web API shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="GBabelDocUI API",
    version=gbabeldocui_version,
    lifespan=application_lifespan,
)

# Add CORS middleware only when a separate trusted frontend is configured.
allowed_origins = tuple(
    origin.strip()
    for origin in os.getenv("GBABELDOCUI_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
)
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(allowed_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", CSRF_HEADER_NAME],
    )


def _prepare_http_response(request: Request, response: Response) -> Response:
    """Apply browser response headers and issue the double-submit CSRF cookie."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
        "font-src 'self'; connect-src 'self'; object-src 'none'; "
        "base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
    )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    if COOKIE_SECURE:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    if not request.cookies.get(CSRF_COOKIE_NAME):
        response.set_cookie(
            CSRF_COOKIE_NAME,
            secrets.token_urlsafe(32),
            max_age=COOKIE_MAX_AGE_SECONDS,
            secure=COOKIE_SECURE,
            httponly=False,
            samesite="strict",
            path="/",
        )
    return response


class RequestBodyLimitMiddleware:
    """Enforce request limits without relying on framework parser exceptions."""

    def __init__(self, application):
        self.application = application

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] != "http"
            or scope.get("method") not in MUTATING_HTTP_METHODS
            or not scope.get("path", "").startswith("/api/")
        ):
            await self.application(scope, receive, send)
            return

        body_limit = MUTATING_REQUEST_BODY_LIMITS.get(
            scope.get("path", ""), MAX_JSON_BODY_BYTES
        )
        headers = Headers(scope=scope)
        content_length = headers.get("content-length")
        if content_length:
            try:
                declared_bytes = int(content_length)
            except ValueError:
                await self._send_error(
                    scope, receive, send, 400, "Invalid Content-Length"
                )
                return
            if declared_bytes < 0:
                await self._send_error(
                    scope, receive, send, 400, "Invalid Content-Length"
                )
                return
            if declared_bytes > body_limit:
                await self._send_error(
                    scope, receive, send, 413, "Request body is too large"
                )
                return

        received_bytes = 0
        body_limit_exceeded = False

        async def limited_receive():
            nonlocal body_limit_exceeded, received_bytes
            if body_limit_exceeded:
                return {"type": "http.request", "body": b"", "more_body": False}
            message = await receive()
            if message.get("type") != "http.request":
                return message
            received_bytes += len(message.get("body", b""))
            if received_bytes > body_limit:
                body_limit_exceeded = True
                return {"type": "http.request", "body": b"", "more_body": False}
            return message

        buffered_messages = []

        async def buffered_send(message):
            buffered_messages.append(message)

        try:
            await self.application(scope, limited_receive, buffered_send)
        except Exception:
            if not body_limit_exceeded:
                raise

        if body_limit_exceeded:
            await self._send_error(
                scope, receive, send, 413, "Request body is too large"
            )
            return
        for message in buffered_messages:
            await send(message)

    @staticmethod
    async def _send_error(scope, receive, send, status_code: int, detail: str):
        request = Request(scope)
        response = _prepare_http_response(
            request,
            JSONResponse(status_code=status_code, content={"detail": detail}),
        )
        await response(scope, receive, send)


app.add_middleware(RequestBodyLimitMiddleware)


@app.middleware("http")
async def add_security_headers_and_csrf_cookie(request: Request, call_next):
    response = await call_next(request)
    return _prepare_http_response(request, response)


@app.middleware("http")
async def authenticate_and_limit_mutating_requests(request: Request, call_next):
    """Validate mutating requests before their body is parsed."""
    is_mutating_api_request = (
        request.url.path.startswith("/api/") and request.method in MUTATING_HTTP_METHODS
    )
    if is_mutating_api_request:
        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME, "")
        csrf_header = request.headers.get(CSRF_HEADER_NAME, "")
        if (
            not csrf_cookie
            or not csrf_header
            or not secrets.compare_digest(csrf_cookie, csrf_header)
        ):
            return _prepare_http_response(
                request,
                JSONResponse(
                    status_code=403, content={"detail": "CSRF validation failed"}
                ),
            )
        if request.url.path not in PUBLIC_MUTATING_API_PATHS:
            token = request.cookies.get(SESSION_COOKIE_NAME, "").strip()
            if not token or not await asyncio.to_thread(
                user_manager.validate_token, token
            ):
                response = JSONResponse(
                    status_code=401, content={"detail": "Invalid or expired session"}
                )
                _clear_session_cookie(response)
                return _prepare_http_response(request, response)

    return await call_next(request)


# Pydantic models for request/response
class SetupRequest(BaseModel):
    username: str
    password: str
    setup_token: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class RegistrationToggleRequest(BaseModel):
    enabled: StrictBool


class TranslationSettings(BaseModel):
    service: str
    lang_from: str = "English"
    lang_to: str = "Simplified Chinese"
    # Add other settings as needed


def _normalize_uploaded_filename(filename: str | None) -> str:
    """Return a safe single-name PDF filename for local storage."""
    candidate = (filename or "").replace("\\", "/")
    if "\x00" in candidate:
        raise HTTPException(status_code=400, detail="Invalid file name")

    safe_filename = Path(candidate).name
    safe_filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", safe_filename)
    safe_filename = safe_filename.strip().rstrip(".")
    if not safe_filename or safe_filename in {".", ".."}:
        raise HTTPException(status_code=400, detail="A PDF file name is required")
    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    if len(safe_filename.encode("utf-8")) > MAX_FILENAME_UTF8_BYTES:
        extension = ".pdf"
        stem = safe_filename[: -len(extension)]
        while stem and len(f"{stem}{extension}".encode()) > MAX_FILENAME_UTF8_BYTES:
            stem = stem[:-1]
        safe_filename = f"{stem or 'translated'}{extension}"
    return safe_filename


def _optional_setting_text(user_settings: dict, setting_name: str) -> str | None:
    raw_setting = user_settings.get(setting_name)
    if raw_setting is None:
        return None
    if isinstance(raw_setting, str):
        normalized_setting = raw_setting.strip()
        return normalized_setting or None
    return str(raw_setting)


def _optional_setting_bool(user_settings: dict, setting_name: str) -> bool | None:
    raw_setting = user_settings.get(setting_name)
    if raw_setting is None:
        return None
    if isinstance(raw_setting, bool):
        return raw_setting
    if isinstance(raw_setting, str):
        normalized_setting = raw_setting.strip().lower()
        if normalized_setting in {"true", "1", "yes", "on"}:
            return True
        if normalized_setting in {"false", "0", "no", "off"}:
            return False
        raise ValueError(f"{setting_name} must be a boolean")
    raise ValueError(f"{setting_name} must be a boolean")


def _setting_bool(
    user_settings: dict, setting_name: str, default: bool = False
) -> bool:
    """Read a saved boolean without treating the string ``"false"`` as true."""
    value = _optional_setting_bool(user_settings, setting_name)
    return default if value is None else value


def _read_float_setting(
    user_settings: dict,
    setting_name: str,
    default: float,
    *,
    minimum: float,
    maximum: float | None = None,
) -> float:
    raw_setting = user_settings.get(setting_name, default)
    if raw_setting is None or raw_setting == "":
        raw_setting = default
    if isinstance(raw_setting, bool):
        raise ValueError(f"{setting_name} must be a number")
    try:
        normalized_setting = float(raw_setting)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{setting_name} must be a number") from exc
    if not math.isfinite(normalized_setting):
        raise ValueError(f"{setting_name} must be a finite number")
    if normalized_setting < minimum:
        raise ValueError(f"{setting_name} must be at least {minimum}")
    if maximum is not None and normalized_setting > maximum:
        raise ValueError(f"{setting_name} must be at most {maximum}")
    return normalized_setting


def _validate_endpoint_url(
    endpoint_value: str | None,
    setting_name: str,
    *,
    allow_private: bool = False,
) -> str | None:
    """Validate provider URLs before the official client can make a request."""
    if endpoint_value is None or not str(endpoint_value).strip():
        return None
    normalized_endpoint = str(endpoint_value).strip()
    parsed_endpoint = urlparse(normalized_endpoint)
    if parsed_endpoint.scheme not in {"http", "https"} or not parsed_endpoint.hostname:
        raise ValueError(f"{setting_name} must be an absolute HTTP or HTTPS URL")
    if parsed_endpoint.username or parsed_endpoint.password:
        raise ValueError(f"{setting_name} must not contain embedded credentials")
    if parsed_endpoint.query or parsed_endpoint.fragment:
        raise ValueError(f"{setting_name} must not contain a query or fragment")
    try:
        endpoint_port = parsed_endpoint.port
    except ValueError as exc:
        raise ValueError(f"{setting_name} contains an invalid port") from exc
    if endpoint_port is not None and not 1 <= endpoint_port <= 65535:
        raise ValueError(f"{setting_name} contains an invalid port")

    hostname = parsed_endpoint.hostname.rstrip(".").lower()
    trusted_provider_host = hostname in TRUSTED_PROVIDER_HOSTS or hostname.endswith(
        TRUSTED_PROVIDER_HOST_SUFFIXES
    )
    private_host = hostname == "localhost" or hostname.endswith(".localhost")
    try:
        host_address = ipaddress.ip_address(hostname)
    except ValueError:
        host_address = None
    if host_address is not None:
        private_host = (
            host_address.is_private
            or host_address.is_loopback
            or host_address.is_link_local
            or host_address.is_reserved
            or host_address.is_multicast
            or host_address.is_unspecified
        )
    else:
        private_host = private_host or hostname.endswith(".local")
    if host_address is None and not trusted_provider_host:
        try:
            resolved_addresses = {
                ipaddress.ip_address(address[4][0])
                for address in socket.getaddrinfo(
                    hostname,
                    endpoint_port or (443 if parsed_endpoint.scheme == "https" else 80),
                    type=socket.SOCK_STREAM,
                )
            }
        except (OSError, ValueError) as exc:
            raise ValueError(f"{setting_name} hostname cannot be resolved") from exc
        if not resolved_addresses:
            raise ValueError(f"{setting_name} hostname cannot be resolved")
        private_host = private_host or any(
            not resolved_address.is_global for resolved_address in resolved_addresses
        )

    private_allowed = allow_private or ALLOW_PRIVATE_ENDPOINTS
    if private_host and not private_allowed:
        raise ValueError(
            f"{setting_name} cannot target localhost, private, loopback, or link-local addresses"
        )
    if parsed_endpoint.scheme != "https" and not private_host:
        raise ValueError(f"{setting_name} must use HTTPS for remote endpoints")
    return normalized_endpoint


def _validate_safe_formula_pattern(pattern: object, setting_name: str) -> str:
    """Accept the small regex subset needed for font and character matching."""
    if not isinstance(pattern, str):
        raise ValueError(f"{setting_name} must be a string")
    normalized_pattern = pattern.strip()
    if not normalized_pattern:
        return ""
    if len(normalized_pattern) > MAX_FORMULA_PATTERN_LENGTH:
        raise ValueError(
            f"{setting_name} must not exceed {MAX_FORMULA_PATTERN_LENGTH} characters"
        )
    if re.search(r"\(\?|\\[1-9]|[+*{}]", normalized_pattern):
        raise ValueError(
            f"{setting_name} contains unsupported high-cost regular expression syntax"
        )
    try:
        re.compile(normalized_pattern)
    except re.error as exc:
        raise ValueError(f"{setting_name} is not a valid regular expression") from exc
    return normalized_pattern


def _parse_page_range(page_range: str, page_count: int) -> str:
    """Validate and normalize a one-based page range against a PDF."""
    if page_count <= 0:
        raise ValueError("The PDF contains no pages")
    if len(page_range) > 200:
        raise ValueError("pages contains an invalid page range")

    normalized_segments: list[str] = []
    selected_pages: set[int] = set()
    for raw_segment in page_range.split(","):
        segment = raw_segment.strip()
        match = re.fullmatch(r"([1-9][0-9]*)(?:\s*-\s*([1-9][0-9]*))?", segment)
        if match is None:
            raise ValueError("pages contains an invalid page range")
        first_page = int(match.group(1))
        last_page = int(match.group(2) or first_page)
        if first_page > last_page:
            raise ValueError("pages range start must not exceed its end")
        if last_page > page_count:
            raise ValueError(f"pages must not exceed the PDF page count ({page_count})")
        segment_pages = set(range(first_page, last_page + 1))
        if selected_pages.intersection(segment_pages):
            raise ValueError("pages contains overlapping or duplicate ranges")
        selected_pages.update(segment_pages)
        normalized_segments.append(
            str(first_page) if first_page == last_page else f"{first_page}-{last_page}"
        )
    if not normalized_segments:
        raise ValueError("pages contains an invalid page range")
    return ",".join(normalized_segments)


def _read_integer_setting(
    user_settings: dict,
    setting_name: str,
    default: int,
    *,
    minimum: int,
    maximum: int | None = None,
) -> int:
    raw_setting = user_settings.get(setting_name, default)
    if raw_setting is None or raw_setting == "":
        raw_setting = default
    if isinstance(raw_setting, bool):
        raise ValueError(f"{setting_name} must be an integer")
    if isinstance(raw_setting, float) and not raw_setting.is_integer():
        raise ValueError(f"{setting_name} must be an integer")
    try:
        normalized_setting = int(raw_setting)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{setting_name} must be an integer") from exc
    if normalized_setting < minimum:
        raise ValueError(f"{setting_name} must be at least {minimum}")
    if maximum is not None and normalized_setting > maximum:
        raise ValueError(f"{setting_name} must be at most {maximum}")
    return normalized_setting


def _build_rate_limit_parameters(
    user_settings: dict,
    *,
    field_prefix: str,
    default_qps: int,
) -> tuple[int, int | None]:
    """Convert WebUI rate-limit controls to official qps and worker settings."""
    if field_prefix:
        mode_name = f"{field_prefix}rate_mode"
        rpm_name = f"{field_prefix}rpm"
        concurrent_name = f"{field_prefix}concurrent"
        qps_name = f"{field_prefix}qps"
        workers_name = f"{field_prefix}workers"
    else:
        mode_name = "rate_limit_mode"
        rpm_name = "rpm"
        concurrent_name = "concurrent_threads"
        qps_name = "custom_qps"
        workers_name = "custom_workers"

    raw_mode = user_settings.get(mode_name, "custom")
    normalized_mode = str(raw_mode or "custom").strip().lower()
    if normalized_mode == "rpm":
        requests_per_minute = _read_integer_setting(
            user_settings,
            rpm_name,
            240,
            minimum=60,
            maximum=MAX_CONFIGURED_RPM,
        )
        qps = max(1, requests_per_minute // 60)
        pool_workers = min(MAX_CONFIGURED_POOL_WORKERS, qps * 10)
    elif normalized_mode == "concurrent":
        concurrent_threads = _read_integer_setting(
            user_settings,
            concurrent_name,
            40,
            minimum=1,
            maximum=MAX_CONFIGURED_POOL_WORKERS,
        )
        pool_workers = min(
            MAX_CONFIGURED_POOL_WORKERS,
            max(1, min(int(concurrent_threads * 0.9), concurrent_threads - 20)),
        )
        qps = max(1, pool_workers)
    elif normalized_mode == "custom":
        qps = _read_integer_setting(
            user_settings,
            qps_name,
            default_qps,
            minimum=1,
            maximum=MAX_CONFIGURED_QPS,
        )
        pool_worker_count = _read_integer_setting(
            user_settings,
            workers_name,
            0,
            minimum=0,
            maximum=MAX_CONFIGURED_POOL_WORKERS,
        )
        pool_workers = pool_worker_count or None
    else:
        raise ValueError(f"{mode_name} must be one of: rpm, concurrent, custom")
    return qps, pool_workers


KNOWN_SETTING_NAMES = frozenset(
    {
        "service",
        "term_service",
        "lang_from",
        "lang_to",
        "page_range",
        "custom_pages",
        "ignore_cache",
        "openai_model",
        "openai_api_key",
        "openai_base_url",
        "openai_timeout",
        "openai_temperature",
        "openai_send_temprature",
        "openai_reasoning_effort",
        "openai_send_reasoning_effort",
        "openai_enable_json_mode",
        "azure_openai_model",
        "azure_openai_api_key",
        "azure_openai_base_url",
        "azure_openai_api_version",
        "gemini_model",
        "gemini_api_key",
        "gemini_enable_json_mode",
        "deepl_api_key",
        "ollama_model",
        "ollama_host",
        "siliconflow_model",
        "siliconflow_api_key",
        "siliconflow_base_url",
        "deepseek_model",
        "deepseek_api_key",
        "zhipu_model",
        "zhipu_api_key",
        "claude_code_model",
        "claude_model",
        "tencent_secret_id",
        "tencent_secret_key",
        "no_mono",
        "no_dual",
        "dual_translate_first",
        "use_alternating_pages",
        "watermark_mode",
        "only_translated_pages",
        "custom_system_prompt",
        "min_text_length",
        "primary_font",
        "enable_term_extraction",
        "save_glossary",
        "rpc_doclayout",
        "skip_clean",
        "disable_rich_text",
        "enhance_compatibility",
        "split_short_lines",
        "split_factor",
        "translate_tables",
        "translate_table_text",
        "skip_scanned_detection",
        "ocr_workaround",
        "auto_ocr",
        "max_pages_per_part",
        "formula_font_pattern",
        "formula_char_pattern",
        "rate_limit_mode",
        "rpm",
        "concurrent_threads",
        "custom_qps",
        "custom_workers",
        "term_rate_mode",
        "term_rpm",
        "term_concurrent",
        "term_qps",
        "term_workers",
        "merge_line_numbers",
        "remove_formula_lines",
        "iou_threshold",
        "protection_threshold",
        "skip_formula_offset",
        "qps",
    }
)
BOOLEAN_SETTING_NAMES = frozenset(
    {
        "ignore_cache",
        "openai_send_temprature",
        "openai_send_reasoning_effort",
        "openai_enable_json_mode",
        "gemini_enable_json_mode",
        "no_mono",
        "no_dual",
        "dual_translate_first",
        "use_alternating_pages",
        "only_translated_pages",
        "enable_term_extraction",
        "save_glossary",
        "skip_clean",
        "disable_rich_text",
        "enhance_compatibility",
        "split_short_lines",
        "translate_tables",
        "translate_table_text",
        "skip_scanned_detection",
        "ocr_workaround",
        "auto_ocr",
        "merge_line_numbers",
        "remove_formula_lines",
        "skip_formula_offset",
    }
)


def _read_settings_file(settings_file: Path) -> dict:
    """Read one user's JSON settings object under the cross-process lock."""
    lock_file = settings_file.with_name(f".{settings_file.name}.lock")
    with FileLock(str(lock_file), timeout=30):
        return _read_settings_file_unlocked(settings_file)


def _read_settings_file_unlocked(settings_file: Path) -> dict:
    if not settings_file.exists():
        return {}
    try:
        if settings_file.stat().st_size > MAX_SETTINGS_FILE_BYTES:
            raise ValueError(
                f"Settings exceed the {MAX_SETTINGS_FILE_BYTES} byte limit"
            )
    except OSError as exc:
        raise ValueError("User settings file is invalid or unreadable") from exc
    try:
        settings = _load_json_value(settings_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("User settings file is invalid or unreadable") from exc
    if not isinstance(settings, dict):
        raise ValueError("User settings must be a JSON object")
    return settings


def _validate_saved_setting_values(settings: dict) -> None:
    """Validate scalar values at the settings boundary before they reach the engine."""
    service = settings.get("service", "SiliconFlowFree")
    if not isinstance(service, str) or service not in SUPPORTED_SERVICES:
        raise ValueError("service is not supported")
    term_service = settings.get("term_service", "same")
    if not isinstance(term_service, str) or (
        term_service != "same" and term_service not in SUPPORTED_SERVICES
    ):
        raise ValueError("term_service is not supported")
    page_range = settings.get("page_range", "all")
    if not isinstance(page_range, str) or page_range not in {
        "all",
        "first",
        "first5",
        "custom",
    }:
        raise ValueError("page_range is invalid")
    custom_pages = settings.get("custom_pages")
    if custom_pages not in (None, ""):
        if not isinstance(custom_pages, str):
            raise ValueError("custom_pages must be a short page range string")
        settings["custom_pages"] = _parse_page_range(custom_pages, MAX_PDF_PAGES)
    watermark_mode = settings.get("watermark_mode", "watermarked")
    if not isinstance(watermark_mode, str) or watermark_mode not in {
        "watermarked",
        "no_watermark",
        "both",
    }:
        raise ValueError("watermark_mode is invalid")

    for setting_name in BOOLEAN_SETTING_NAMES:
        if setting_name in settings:
            settings[setting_name] = _optional_setting_bool(settings, setting_name)

    integer_limits = {
        "min_text_length": (0, 10000),
        "max_pages_per_part": (0, MAX_PDF_PAGES),
        "rpm": (60, MAX_CONFIGURED_RPM),
        "concurrent_threads": (1, MAX_CONFIGURED_POOL_WORKERS),
        "custom_qps": (1, MAX_CONFIGURED_QPS),
        "custom_workers": (0, MAX_CONFIGURED_POOL_WORKERS),
        "term_rpm": (60, MAX_CONFIGURED_RPM),
        "term_concurrent": (1, MAX_CONFIGURED_POOL_WORKERS),
        "term_qps": (1, MAX_CONFIGURED_QPS),
        "term_workers": (0, MAX_CONFIGURED_POOL_WORKERS),
        "qps": (1, MAX_CONFIGURED_QPS),
    }
    for setting_name, (minimum, maximum) in integer_limits.items():
        if setting_name in settings:
            settings[setting_name] = _read_integer_setting(
                settings,
                setting_name,
                minimum,
                minimum=minimum,
                maximum=maximum,
            )

    max_pages_per_part = settings.get("max_pages_per_part", 0)
    if 0 < max_pages_per_part < 50:
        raise ValueError("max_pages_per_part must be 0 or at least 50")

    float_limits = {
        "split_factor": (0.1, 1.0),
        "iou_threshold": (0.0, 1.0),
        "protection_threshold": (0.0, 1.0),
    }
    for setting_name, (minimum, maximum) in float_limits.items():
        if setting_name in settings:
            settings[setting_name] = _read_float_setting(
                settings,
                setting_name,
                minimum,
                minimum=minimum,
                maximum=maximum,
            )

    text_limits = {
        "lang_from": 64,
        "lang_to": 64,
        "primary_font": 256,
        "custom_system_prompt": 32000,
        "openai_model": 256,
        "azure_openai_model": 256,
        "azure_openai_api_version": 64,
        "gemini_model": 256,
        "deepl_model": 256,
        "ollama_model": 256,
        "siliconflow_model": 256,
        "deepseek_model": 256,
        "zhipu_model": 256,
        "claude_model": 256,
        "tencent_secret_id": 512,
        "tencent_secret_key": 4096,
    }
    for setting_name, maximum_length in text_limits.items():
        if setting_name not in settings or settings[setting_name] is None:
            continue
        setting_value = settings[setting_name]
        if not isinstance(setting_value, str):
            raise ValueError(f"{setting_name} must be a string")
        if len(setting_value) > maximum_length:
            raise ValueError(
                f"{setting_name} must not exceed {maximum_length} characters"
            )

    for setting_name in (
        "openai_api_key",
        "azure_openai_api_key",
        "gemini_api_key",
        "deepl_auth_key",
        "siliconflow_api_key",
        "deepseek_api_key",
        "zhipu_api_key",
        "claude_api_key",
    ):
        if setting_name not in settings or settings[setting_name] is None:
            continue
        setting_value = settings[setting_name]
        if not isinstance(setting_value, str):
            raise ValueError(f"{setting_name} must be a string")
        if len(setting_value) > 4096:
            raise ValueError(f"{setting_name} must not exceed 4096 characters")

    for setting_name in ("formula_font_pattern", "formula_char_pattern"):
        if setting_name in settings:
            settings[setting_name] = _validate_safe_formula_pattern(
                settings[setting_name], setting_name
            )


def _validate_service_access(settings: dict, *, is_admin: bool) -> None:
    """Prevent ordinary users from selecting server-owned translation engines."""
    if is_admin:
        return
    for setting_name in ("service", "term_service"):
        service_name = settings.get(setting_name)
        if service_name in PRIVILEGED_SERVICE_NAMES:
            raise PermissionError(
                f"Only administrators can use the {service_name} translation service"
            )


def _merge_user_settings(
    existing_settings: dict,
    incoming_settings: dict,
    *,
    is_admin: bool,
) -> dict:
    """Merge one settings page without dropping unrelated saved values."""
    if not isinstance(incoming_settings, dict):
        raise ValueError("Settings must be a JSON object")
    unsupported_settings = set(incoming_settings) - KNOWN_SETTING_NAMES
    if unsupported_settings:
        names = ", ".join(sorted(str(name) for name in unsupported_settings)[:5])
        raise ValueError(f"Unsupported settings: {names}")
    if "claude_code_path" in incoming_settings:
        raise PermissionError("Claude executable path is controlled by the server")

    merged_settings = dict(existing_settings)
    for setting_name, setting_value in incoming_settings.items():
        if (
            setting_name.casefold().endswith(SENSITIVE_SETTING_SUFFIXES)
            and isinstance(setting_value, str)
            and not setting_value.strip()
            and existing_settings.get(setting_name)
        ):
            continue
        if setting_name in PRIVILEGED_SETTING_NAMES and not is_admin:
            existing_value = existing_settings.get(setting_name)
            existing_is_empty = existing_value is None or (
                isinstance(existing_value, str) and not existing_value.strip()
            )
            incoming_is_empty = setting_value is None or (
                isinstance(setting_value, str) and not setting_value.strip()
            )
            if existing_settings.get(setting_name) != setting_value and not (
                existing_is_empty and incoming_is_empty
            ):
                raise PermissionError(f"Only administrators can change {setting_name}")
        merged_settings[setting_name] = setting_value

    _validate_saved_setting_values(merged_settings)
    _validate_service_access(merged_settings, is_admin=is_admin)
    for setting_name in ENDPOINT_SETTING_NAMES:
        if setting_name in merged_settings:
            _validate_endpoint_url(merged_settings[setting_name], setting_name)

    try:
        serialized_settings = json.dumps(
            merged_settings,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("Settings must contain JSON-compatible values") from exc
    if len(serialized_settings.encode("utf-8")) > MAX_SETTINGS_JSON_BYTES:
        raise ValueError(f"Settings exceed the {MAX_SETTINGS_JSON_BYTES} byte limit")

    if merged_settings.get("service") in {"Claude", "ClaudeCode"} and not is_admin:
        raise PermissionError("Claude Code translation is restricted to administrators")
    if merged_settings.get("term_service") in {"Claude", "ClaudeCode"} and not is_admin:
        raise PermissionError(
            "Claude Code term extraction is restricted to administrators"
        )
    return merged_settings


def _write_json_file(file_path: Path, payload: object) -> None:
    """Atomically replace a JSON file so concurrent saves cannot truncate it."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=file_path.parent,
            prefix=f".{file_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(
                payload,
                temporary_file,
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            )
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        temporary_path.replace(file_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _merge_and_write_settings_file(
    settings_file: Path, incoming_settings: dict, *, is_admin: bool
) -> dict:
    lock_file = settings_file.with_name(f".{settings_file.name}.lock")
    with FileLock(str(lock_file), timeout=30):
        existing_settings = _read_settings_file_unlocked(settings_file)
        merged_settings = _merge_user_settings(
            existing_settings, incoming_settings, is_admin=is_admin
        )
        _write_json_file(settings_file, merged_settings)
    return merged_settings


def _replace_settings_file(settings_file: Path, settings: dict) -> None:
    lock_file = settings_file.with_name(f".{settings_file.name}.lock")
    with FileLock(str(lock_file), timeout=30):
        _write_json_file(settings_file, settings)


def _pdf_page_count(file_path: Path) -> int:
    """Validate a PDF with PyMuPDF and return its positive page count."""
    with file_path.open("rb") as source_file:
        if b"%PDF-" not in source_file.read(PDF_HEADER_SCAN_BYTES):
            raise ValueError("The uploaded file is not a PDF")
    try:
        import fitz

        with fitz.open(filename=str(file_path)) as document:
            page_count = int(document.page_count)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ValueError("The uploaded file is not a readable PDF") from exc
    if page_count <= 0:
        raise ValueError("The PDF contains no pages")
    if page_count > MAX_PDF_PAGES:
        raise ValueError(f"The PDF exceeds the {MAX_PDF_PAGES} page limit")
    return page_count


def _session_token(request: Request) -> str:
    token = request.cookies.get(SESSION_COOKIE_NAME, "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=COOKIE_MAX_AGE_SECONDS,
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="strict",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="strict",
        path="/",
    )


async def require_csrf(request: Request) -> None:
    """Validate the double-submit token before a state-changing request body is used."""
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME, "")
    header_token = request.headers.get(CSRF_HEADER_NAME, "")
    if (
        not cookie_token
        or not header_token
        or not secrets.compare_digest(cookie_token, header_token)
    ):
        raise HTTPException(status_code=403, detail="CSRF validation failed")


def _request_is_loopback(request: Request) -> bool:
    if request.client is None:
        return False
    try:
        return ipaddress.ip_address(request.client.host).is_loopback
    except ValueError:
        return request.client.host.casefold() == "localhost"


def _validate_setup_authorization(request: Request, provided_token: str | None) -> None:
    if _request_is_loopback(request):
        return
    if (
        SETUP_TOKEN
        and provided_token
        and secrets.compare_digest(SETUP_TOKEN, provided_token)
    ):
        return
    raise HTTPException(
        status_code=403,
        detail="Initial setup requires a local request or GBABELDOCUI_SETUP_TOKEN",
    )


async def _save_uploaded_file(file: UploadFile, file_path: Path) -> int:
    """Stream an upload to disk and remove partial files when the limit is exceeded."""
    total_bytes = 0
    try:
        with file_path.open("wb") as destination:
            while chunk := await file.read(UPLOAD_CHUNK_BYTES):
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            f"Uploaded file exceeds the {MAX_UPLOAD_BYTES} byte limit"
                        ),
                    )
                destination.write(chunk)
    except asyncio.CancelledError:
        file_path.unlink(missing_ok=True)
        raise
    except Exception:
        file_path.unlink(missing_ok=True)
        raise
    return total_bytes


def _client_address(request: Request) -> str:
    """Return the transport peer used for public authentication throttling."""
    return request.client.host if request.client else "unknown"


def _enforce_auth_attempt_limit(request: Request, operation: str, username: str) -> str:
    del username
    key = f"{operation}:{_client_address(request)}"
    retry_after = authentication_limiter.retry_after(key)
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    return key


def _user_storage_bytes(user_dir: Path) -> int:
    total_bytes = 0
    if not user_dir.exists():
        return total_bytes
    for candidate in user_dir.rglob("*"):
        if candidate.is_file() and not candidate.is_symlink():
            try:
                total_bytes += candidate.stat().st_size
            except OSError:
                logger.warning("Unable to read file size for %s", candidate)
    return total_bytes


def _ensure_user_storage_quota(user_dir: Path) -> None:
    """Stop retaining translation output when a user exceeds its quota."""
    current_storage_bytes = _user_storage_bytes(user_dir)
    if current_storage_bytes > MAX_USER_STORAGE_BYTES:
        raise RuntimeError(
            "User storage quota exceeded while creating translation output"
        )


def _uploaded_file_lock(user_dir: Path, file_id: str) -> FileLock:
    """Serialize task attachment and cleanup operations across workers."""
    lock_directory = user_dir.parent.parent / ".locks"
    lock_directory.mkdir(parents=True, exist_ok=True)
    lock_component = re.sub(r"[^a-zA-Z0-9_.-]", "_", user_dir.name)
    return FileLock(
        str(lock_directory / f"{lock_component}-{file_id}.lock"),
        timeout=30,
        thread_local=False,
    )


def _user_lifecycle_lock(username: str) -> FileLock:
    """Return a cross-process lock for account deletion and user data writes."""
    lock_directory = user_manager.data_dir / "users" / ".locks"
    lock_directory.mkdir(parents=True, exist_ok=True)
    lock_component = re.sub(r"[^a-zA-Z0-9_.-]", "_", str(username).casefold())
    lock_component = lock_component[:64] or "invalid-user"
    return FileLock(
        str(lock_directory / f"user-{lock_component}.lock"),
        timeout=30,
        thread_local=False,
    )


def _ensure_user_is_active(username: str, *, allow_deleting: bool = False) -> None:
    """Reject requests that raced with account deletion."""
    if not allow_deleting:
        with deleting_usernames_lock:
            if username.casefold() in deleting_usernames:
                raise HTTPException(
                    status_code=409, detail="User deletion is in progress"
                )
    if not user_manager.user_exists(username):
        raise HTTPException(status_code=401, detail="User account no longer exists")


def _ensure_user_deletion_not_in_progress(username: str) -> None:
    with deleting_usernames_lock:
        if username.casefold() in deleting_usernames:
            raise HTTPException(status_code=409, detail="User deletion is in progress")


async def _acquire_file_lock(file_lock: FileLock) -> None:
    """Acquire a file lock without leaking it when the caller is cancelled."""
    acquire_task = asyncio.create_task(asyncio.to_thread(file_lock.acquire))
    try:
        await asyncio.shield(acquire_task)
    except asyncio.CancelledError:
        try:
            acquired_lock = await acquire_task
        except Exception:
            raise
        if acquired_lock:
            await asyncio.to_thread(file_lock.release)
        raise


@asynccontextmanager
async def _user_lifecycle_guard(username: str, *, allow_deleting: bool = False):
    """Serialize account deletion with requests that touch user-owned files."""
    if not allow_deleting:
        _ensure_user_deletion_not_in_progress(username)
    lifecycle_lock = _user_lifecycle_lock(username)
    await _acquire_file_lock(lifecycle_lock)
    try:
        _ensure_user_is_active(username, allow_deleting=allow_deleting)
        yield
    finally:
        await asyncio.to_thread(lifecycle_lock.release)


@asynccontextmanager
async def _uploaded_file_guard(user_dir: Path, file_id: str):
    """Acquire the uploaded-file lock without blocking the event loop."""
    uploaded_file_lock = _uploaded_file_lock(user_dir, file_id)
    await _acquire_file_lock(uploaded_file_lock)
    try:
        yield
    finally:
        await asyncio.to_thread(uploaded_file_lock.release)


@asynccontextmanager
async def _user_uploaded_file_guard(username: str, user_dir: Path, file_id: str):
    """Serialize account deletion with operations on one uploaded file."""
    async with _user_lifecycle_guard(username):
        async with _uploaded_file_guard(user_dir, file_id):
            yield


def _uploaded_files_for_id(user_dir: Path, file_id: str) -> list[Path]:
    """Return regular files belonging to one uploaded file identifier."""
    upload_dir = user_dir / "uploads"
    if not upload_dir.exists():
        return []
    return [
        candidate
        for candidate in upload_dir.glob(f"{file_id}_*")
        if candidate.is_file() and not candidate.is_symlink()
    ]


def _remove_unattached_uploaded_file_locked(
    user_dir: Path, username: str, file_id: str
) -> bool:
    """Remove an upload when the caller already owns its file lock."""
    if task_store.count_tasks_for_file(username, file_id):
        return False
    matching_files = _uploaded_files_for_id(user_dir, file_id)
    for candidate in matching_files:
        try:
            candidate.unlink()
        except OSError as exc:
            logger.error("Failed to remove uploaded file %s: %s", candidate, exc)
            return False
    return bool(matching_files)


def _remove_unattached_uploaded_file(
    user_dir: Path, username: str, file_id: str
) -> bool:
    """Remove an upload only when no persisted task references it."""
    with _uploaded_file_lock(user_dir, file_id):
        return _remove_unattached_uploaded_file_locked(user_dir, username, file_id)


def _cleanup_orphaned_uploaded_files() -> int:
    """Remove old uploads that have never been attached to a translation task."""
    cutoff_timestamp = time.time() - ORPHAN_UPLOAD_TTL_SECONDS
    removed_count = 0
    for username in user_manager.list_registered_usernames():
        user_dir = user_manager.get_user_dir(username)
        upload_dir = user_dir / "uploads"
        if not upload_dir.exists():
            continue
        try:
            candidates = list(upload_dir.iterdir())
        except OSError as exc:
            logger.warning("Unable to scan upload directory %s: %s", upload_dir, exc)
            continue

        for candidate in candidates:
            if not candidate.is_file() or candidate.is_symlink():
                continue
            try:
                if candidate.stat().st_mtime >= cutoff_timestamp:
                    continue
            except OSError as exc:
                logger.warning("Unable to inspect uploaded file %s: %s", candidate, exc)
                continue

            file_id_prefix, separator, _ = candidate.name.partition("_")
            if not separator:
                continue
            try:
                file_id = str(uuid.UUID(file_id_prefix))
            except ValueError:
                continue
            if _remove_unattached_uploaded_file(user_dir, username, file_id):
                removed_count += 1

    if removed_count:
        logger.info("Removed %s orphaned uploaded file(s)", removed_count)
    return removed_count


async def _periodic_orphan_upload_cleanup() -> None:
    """Run bounded maintenance without delaying application startup."""
    while True:
        await asyncio.sleep(ORPHAN_UPLOAD_CLEANUP_INTERVAL_SECONDS)
        try:
            await asyncio.to_thread(_cleanup_orphaned_uploaded_files)
            if await asyncio.to_thread(_retention_cleanup_is_ready):
                await _cleanup_expired_terminal_tasks_once()
        except Exception:
            logger.exception("Periodic data cleanup failed")


def _serialize_task(task: dict) -> dict:
    """Return task metadata without exposing server filesystem paths."""
    mono_path = task.get("mono_path")
    dual_path = task.get("dual_path")
    return {
        "task_id": task["task_id"],
        "file_id": task.get("file_id", ""),
        "filename": task.get("filename", ""),
        "original_filename": task.get("original_filename", ""),
        "status": task.get("status", "failed"),
        "progress": task.get("progress", 0),
        "message": task.get("message", ""),
        "username": task.get("username"),
        "created_at": task.get("created_at"),
        "updated_at": task.get("updated_at"),
        "completed_at": task.get("completed_at"),
        "error": task.get("error"),
        "output_files": {
            "mono": bool(mono_path and Path(mono_path).is_file()),
            "dual": bool(dual_path and Path(dual_path).is_file()),
        },
    }


def _serialize_history_item(task: dict) -> dict:
    serialized_task = _serialize_task(task)
    return {
        "task_id": serialized_task["task_id"],
        "file_id": serialized_task["file_id"],
        "filename": serialized_task["filename"],
        "original_filename": serialized_task["original_filename"],
        "created_at": serialized_task["created_at"],
        "completed_at": serialized_task["completed_at"],
        "status": serialized_task["status"],
        "error": serialized_task["error"],
        "mono_path": serialized_task["output_files"]["mono"],
        "dual_path": serialized_task["output_files"]["dual"],
    }


def _get_owned_task(task_id: str, username: str) -> dict:
    try:
        uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task id") from None

    task = task_store.get_task(task_id, username=username)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _resolve_download_path(task: dict, user_dir: Path, file_type: str) -> Path:
    if file_type not in {"mono", "dual"}:
        raise HTTPException(status_code=400, detail="Invalid file type")

    path_value = task.get(f"{file_type}_path")
    if not path_value:
        raise HTTPException(status_code=404, detail="File not found")

    task_output_dir = (user_dir / "outputs" / task["task_id"]).resolve()
    candidate = Path(path_value).resolve()
    try:
        candidate.relative_to(task_output_dir)
    except ValueError:
        raise HTTPException(status_code=404, detail="File not found") from None
    if candidate.suffix.lower() != ".pdf" or not candidate.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return candidate


def _cleanup_translation_artifacts(task: dict, user_dir: Path) -> bool:
    """Remove task-owned artifacts and report whether cleanup fully succeeded."""
    cleanup_succeeded = True
    task_output_dir = (user_dir / "outputs" / task["task_id"]).resolve()
    outputs_root = (user_dir / "outputs").resolve()
    try:
        task_output_dir.relative_to(outputs_root)
    except ValueError:
        cleanup_succeeded = False
        logger.error(
            "Refusing to remove output path outside user directory: %s", task_output_dir
        )
    else:
        if task_output_dir.is_symlink():
            cleanup_succeeded = False
            logger.error(
                "Refusing to remove symlinked task output: %s", task_output_dir
            )
        elif task_output_dir.exists():
            try:
                shutil.rmtree(task_output_dir)
            except OSError as exc:
                cleanup_succeeded = False
                logger.error(
                    "Failed to remove task output %s: %s", task_output_dir, exc
                )

    input_path_value = task.get("input_path")
    if not input_path_value:
        return cleanup_succeeded
    try:
        with _uploaded_file_lock(user_dir, task["file_id"]):
            active_file_references = task_store.count_active_tasks_for_file(
                task["username"], task["file_id"], exclude_task_id=task["task_id"]
            )
            if active_file_references:
                logger.info(
                    "Keeping uploaded file for task %s because %s active task(s) still use it",
                    task["task_id"],
                    active_file_references,
                )
                return cleanup_succeeded

            uploads_root = (user_dir / "uploads").resolve()
            input_path = Path(input_path_value)
            if input_path.is_symlink():
                cleanup_succeeded = False
                logger.error(
                    "Refusing to remove symlinked uploaded file: %s", input_path
                )
                return cleanup_succeeded
            input_path = input_path.resolve()
            try:
                input_path.relative_to(uploads_root)
            except ValueError:
                cleanup_succeeded = False
                logger.error(
                    "Refusing to remove input path outside user directory: %s",
                    input_path,
                )
            else:
                try:
                    input_path.unlink(missing_ok=True)
                except OSError as exc:
                    cleanup_succeeded = False
                    logger.error(
                        "Failed to remove uploaded file %s: %s", input_path, exc
                    )
    except Exception as exc:
        cleanup_succeeded = False
        logger.error("Failed to clean uploaded file %s: %s", input_path_value, exc)
    return cleanup_succeeded


# Dependency to get current user from the HttpOnly session cookie.
async def get_current_user(request: Request) -> dict:
    """Validate the session cookie and return the current user."""
    token = _session_token(request)
    user_data = await asyncio.to_thread(user_manager.validate_token, token)

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user_data


async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Ensure current user is an admin"""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user


def _build_engine_settings(
    service: str, user_settings: dict, *, allow_privileged_services: bool = False
):
    """Build bundled pdf2zh-next-compatible engine settings from WebUI settings."""
    from gbabeldocui._vendor.pdf2zh_next.config.translate_engine_model import (
        AzureOpenAISettings,
    )
    from gbabeldocui._vendor.pdf2zh_next.config.translate_engine_model import (
        BingSettings,
    )
    from gbabeldocui._vendor.pdf2zh_next.config.translate_engine_model import (
        ClaudeCodeSettings,
    )
    from gbabeldocui._vendor.pdf2zh_next.config.translate_engine_model import (
        DeepLSettings,
    )
    from gbabeldocui._vendor.pdf2zh_next.config.translate_engine_model import (
        DeepSeekSettings,
    )
    from gbabeldocui._vendor.pdf2zh_next.config.translate_engine_model import (
        GeminiSettings,
    )
    from gbabeldocui._vendor.pdf2zh_next.config.translate_engine_model import (
        GoogleSettings,
    )
    from gbabeldocui._vendor.pdf2zh_next.config.translate_engine_model import (
        OllamaSettings,
    )
    from gbabeldocui._vendor.pdf2zh_next.config.translate_engine_model import (
        OpenAISettings,
    )
    from gbabeldocui._vendor.pdf2zh_next.config.translate_engine_model import (
        SiliconFlowFreeSettings,
    )
    from gbabeldocui._vendor.pdf2zh_next.config.translate_engine_model import (
        SiliconFlowSettings,
    )
    from gbabeldocui._vendor.pdf2zh_next.config.translate_engine_model import (
        TencentSettings,
    )
    from gbabeldocui._vendor.pdf2zh_next.config.translate_engine_model import (
        ZhipuSettings,
    )

    normalized_service = service or "SiliconFlowFree"
    if normalized_service not in SUPPORTED_SERVICES:
        raise ValueError(f"Unsupported translation service: {normalized_service}")
    if normalized_service in PRIVILEGED_SERVICE_NAMES and not allow_privileged_services:
        raise ValueError(
            f"The {normalized_service} translation service is restricted to administrators"
        )

    if normalized_service == "OpenAI":
        return OpenAISettings(
            openai_model=user_settings.get("openai_model", "gpt-4o-mini"),
            openai_api_key=user_settings.get("openai_api_key", ""),
            openai_base_url=_validate_endpoint_url(
                user_settings.get("openai_base_url") or "https://api.openai.com/v1",
                "openai_base_url",
            ),
            openai_timeout=_optional_setting_text(user_settings, "openai_timeout"),
            openai_temperature=_optional_setting_text(
                user_settings, "openai_temperature"
            ),
            openai_reasoning_effort=_optional_setting_text(
                user_settings, "openai_reasoning_effort"
            ),
            openai_enable_json_mode=_optional_setting_bool(
                user_settings, "openai_enable_json_mode"
            ),
            openai_send_temprature=_optional_setting_bool(
                user_settings, "openai_send_temprature"
            ),
            openai_send_reasoning_effort=_optional_setting_bool(
                user_settings, "openai_send_reasoning_effort"
            ),
        )
    if normalized_service == "AzureOpenAI":
        return AzureOpenAISettings(
            azure_openai_api_key=user_settings.get("azure_openai_api_key", ""),
            azure_openai_base_url=_validate_endpoint_url(
                user_settings.get("azure_openai_base_url"),
                "azure_openai_base_url",
            ),
            azure_openai_model=user_settings.get("azure_openai_model", ""),
            azure_openai_api_version=user_settings.get(
                "azure_openai_api_version", "2024-06-01"
            ),
        )
    if normalized_service in ("Gemini", "GoogleGemini"):
        return GeminiSettings(
            gemini_model=user_settings.get("gemini_model", "gemini-1.5-flash"),
            gemini_api_key=user_settings.get("gemini_api_key", ""),
            gemini_enable_json_mode=_optional_setting_bool(
                user_settings, "gemini_enable_json_mode"
            ),
        )
    if normalized_service == "DeepL":
        return DeepLSettings(
            deepl_auth_key=user_settings.get("deepl_api_key", ""),
        )
    if normalized_service == "Ollama":
        configured_ollama_host = user_settings.get("ollama_host")
        if isinstance(configured_ollama_host, str):
            configured_ollama_host = configured_ollama_host.strip() or None
        ollama_host = configured_ollama_host or "http://127.0.0.1:11434"
        return OllamaSettings(
            ollama_model=user_settings.get("ollama_model", "gemma2"),
            ollama_host=_validate_endpoint_url(
                ollama_host,
                "ollama_host",
                allow_private=not configured_ollama_host,
            ),
        )
    if normalized_service == "SiliconFlow":
        return SiliconFlowSettings(
            siliconflow_model=user_settings.get(
                "siliconflow_model", "Qwen/Qwen2.5-7B-Instruct"
            ),
            siliconflow_api_key=user_settings.get("siliconflow_api_key", ""),
            siliconflow_base_url=_validate_endpoint_url(
                user_settings.get("siliconflow_base_url")
                or "https://api.siliconflow.cn/v1",
                "siliconflow_base_url",
            ),
        )
    if normalized_service == "DeepSeek":
        return DeepSeekSettings(
            deepseek_model=user_settings.get("deepseek_model", "deepseek-chat"),
            deepseek_api_key=user_settings.get("deepseek_api_key", ""),
        )
    if normalized_service == "Zhipu":
        return ZhipuSettings(
            zhipu_model=user_settings.get("zhipu_model", "glm-4-flash"),
            zhipu_api_key=user_settings.get("zhipu_api_key", ""),
        )
    if normalized_service in ("Claude", "ClaudeCode"):
        return ClaudeCodeSettings(
            claude_code_model=user_settings.get(
                "claude_code_model", user_settings.get("claude_model", "sonnet")
            ),
            claude_code_path=os.getenv("GBABELDOCUI_CLAUDE_CODE_PATH", "claude"),
        )
    if normalized_service == "Bing":
        return BingSettings()
    if normalized_service == "Google":
        return GoogleSettings()
    if normalized_service in ("Tencent", "TencentMechineTranslation"):
        return TencentSettings(
            tencentcloud_secret_id=user_settings.get("tencent_secret_id", ""),
            tencentcloud_secret_key=user_settings.get("tencent_secret_key", ""),
        )
    return SiliconFlowFreeSettings()


def build_settings_model_from_user_config(
    user_settings: dict,
    output_dir: Path,
    pages: str | None = None,
    *,
    allow_privileged_services: bool = False,
) -> SettingsModel:
    """Build official SettingsModel from saved WebUI settings."""
    service = user_settings.get("service", "SiliconFlowFree")
    engine_settings = _build_engine_settings(
        service,
        user_settings,
        allow_privileged_services=allow_privileged_services,
    )

    # Build SettingsModel
    settings = SettingsModel(
        translate_engine_settings=engine_settings,
        report_interval=0.5,
    )

    term_service = user_settings.get("term_service", "same")
    if term_service == "same":
        settings.term_extraction_engine_settings = engine_settings.model_copy(deep=True)
    else:
        settings.term_extraction_engine_settings = _build_engine_settings(
            term_service,
            user_settings,
            allow_privileged_services=allow_privileged_services,
        )

    # Configure translation settings
    settings.translation.lang_in = user_settings.get("lang_from", "en")
    settings.translation.lang_out = user_settings.get("lang_to", "zh")
    settings.translation.output = str(output_dir)
    settings.translation.ignore_cache = _setting_bool(user_settings, "ignore_cache")
    legacy_qps = user_settings.get("qps")
    if legacy_qps is None or legacy_qps == "":
        legacy_qps = 4
    translation_qps, translation_workers = _build_rate_limit_parameters(
        user_settings,
        field_prefix="",
        default_qps=legacy_qps,
    )
    settings.translation.qps = translation_qps
    settings.translation.pool_max_workers = translation_workers

    # Additional translation settings
    min_text_length = _read_integer_setting(
        user_settings,
        "min_text_length",
        5,
        minimum=0,
        maximum=10000,
    )
    settings.translation.min_text_length = min_text_length

    rpc_doclayout = user_settings.get("rpc_doclayout", "")
    if rpc_doclayout:
        settings.translation.rpc_doclayout = _validate_endpoint_url(
            rpc_doclayout, "rpc_doclayout"
        )

    custom_prompt = user_settings.get("custom_system_prompt", "")
    if custom_prompt:
        settings.translation.custom_system_prompt = custom_prompt

    primary_font = user_settings.get("primary_font", "")
    if primary_font and primary_font != "auto":
        settings.translation.primary_font_family = primary_font

    # Term extraction settings
    settings.translation.no_auto_extract_glossary = not _setting_bool(
        user_settings, "enable_term_extraction"
    )
    settings.translation.save_auto_extracted_glossary = _setting_bool(
        user_settings, "save_glossary"
    )

    if any(
        setting_name in user_settings
        for setting_name in (
            "term_rate_mode",
            "term_rpm",
            "term_concurrent",
            "term_qps",
            "term_workers",
        )
    ):
        term_qps, term_workers = _build_rate_limit_parameters(
            user_settings,
            field_prefix="term_",
            default_qps=translation_qps,
        )
        settings.translation.term_qps = term_qps
        settings.translation.term_pool_max_workers = term_workers

    # Configure PDF settings
    if pages:
        settings.pdf.pages = pages
    settings.pdf.no_dual = _setting_bool(user_settings, "no_dual")
    settings.pdf.no_mono = _setting_bool(user_settings, "no_mono")
    settings.pdf.dual_translate_first = _setting_bool(
        user_settings, "dual_translate_first"
    )
    settings.pdf.skip_clean = _setting_bool(user_settings, "skip_clean")
    settings.pdf.enhance_compatibility = _setting_bool(
        user_settings, "enhance_compatibility"
    )
    settings.pdf.ocr_workaround = _setting_bool(user_settings, "ocr_workaround")
    if "translate_tables" in user_settings:
        settings.pdf.translate_table_text = _setting_bool(
            user_settings, "translate_tables", True
        )
    else:
        settings.pdf.translate_table_text = _setting_bool(
            user_settings, "translate_table_text", True
        )

    # Additional PDF settings
    settings.pdf.split_short_lines = _setting_bool(user_settings, "split_short_lines")
    settings.pdf.short_line_split_factor = _read_float_setting(
        user_settings, "split_factor", 0.8, minimum=0.1, maximum=1.0
    )
    settings.pdf.disable_rich_text_translate = _setting_bool(
        user_settings, "disable_rich_text"
    )
    settings.pdf.use_alternating_pages_dual = _setting_bool(
        user_settings, "use_alternating_pages"
    )
    settings.pdf.skip_scanned_detection = _setting_bool(
        user_settings, "skip_scanned_detection"
    )
    settings.pdf.only_include_translated_page = _setting_bool(
        user_settings, "only_translated_pages"
    )
    settings.pdf.auto_enable_ocr_workaround = _setting_bool(user_settings, "auto_ocr")

    # Max pages per part (0 means None/no limit)
    max_pages = _read_integer_setting(
        user_settings,
        "max_pages_per_part",
        0,
        minimum=0,
        maximum=MAX_PDF_PAGES,
    )
    if 0 < max_pages < 50:
        raise ValueError("max_pages_per_part must be 0 or at least 50")
    if max_pages > 0:
        settings.pdf.max_pages_per_part = max_pages

    formula_font = _validate_safe_formula_pattern(
        user_settings.get("formula_font_pattern", ""), "formula_font_pattern"
    )
    if formula_font:
        settings.pdf.formular_font_pattern = formula_font
    formula_char = _validate_safe_formula_pattern(
        user_settings.get("formula_char_pattern", ""), "formula_char_pattern"
    )
    if formula_char:
        settings.pdf.formular_char_pattern = formula_char

    # BabelDOC settings (note: frontend uses positive, backend uses negative/no_ prefix)
    # merge_line_numbers=True means we WANT to merge, so no_merge should be False
    settings.pdf.no_merge_alternating_line_numbers = not _setting_bool(
        user_settings, "merge_line_numbers", True
    )
    # remove_formula_lines=True means we WANT to remove, so no_remove should be False
    settings.pdf.no_remove_non_formula_lines = not _setting_bool(
        user_settings, "remove_formula_lines", True
    )
    settings.pdf.non_formula_line_iou_threshold = _read_float_setting(
        user_settings,
        "iou_threshold",
        0.9,
        minimum=0.0,
        maximum=1.0,
    )
    settings.pdf.figure_table_protection_threshold = _read_float_setting(
        user_settings,
        "protection_threshold",
        0.9,
        minimum=0.0,
        maximum=1.0,
    )
    settings.pdf.skip_formula_offset_calculation = _setting_bool(
        user_settings, "skip_formula_offset"
    )

    # Map watermark mode - frontend uses 'watermarked', 'no_watermark', 'both' which matches backend
    watermark_mode = user_settings.get("watermark_mode", "watermarked")
    # Pass through directly as values match backend expected values
    settings.pdf.watermark_output_mode = watermark_mode

    return settings


# Authentication endpoints
@app.get("/api/auth/status")
async def check_auth_status():
    """Check if initial setup is required"""
    return {
        "setup_required": not await asyncio.to_thread(user_manager.has_users),
        "setup_token_required": bool(SETUP_TOKEN),
        "version": gbabeldocui_version,
    }


@app.get("/api/auth/me")
async def get_authenticated_user(current_user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "username": current_user["username"],
        "is_admin": current_user["is_admin"],
    }


@app.post("/api/auth/setup")
async def initial_setup(
    http_request: Request,
    response: Response,
    request: SetupRequest,
    _csrf: None = Depends(require_csrf),
):
    """Create the first admin user"""
    _validate_setup_authorization(http_request, request.setup_token)
    try:
        await asyncio.to_thread(
            user_manager.create_initial_admin, request.username, request.password
        )
        token = await asyncio.to_thread(
            user_manager.authenticate, request.username, request.password
        )
        if token is None:
            raise HTTPException(status_code=500, detail="Failed to create session")
        _set_session_cookie(response, token)

        return {
            "success": True,
            "username": request.username,
            "is_admin": True,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/auth/login")
async def login(
    http_request: Request,
    response: Response,
    request: LoginRequest,
    _csrf: None = Depends(require_csrf),
):
    """Authenticate a user and set an HttpOnly session cookie."""
    attempt_key = _enforce_auth_attempt_limit(http_request, "login", request.username)
    token = await asyncio.to_thread(
        user_manager.authenticate, request.username, request.password
    )

    if not token:
        authentication_limiter.record_failure(attempt_key)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user_data = await asyncio.to_thread(user_manager.validate_token, token)
    if user_data is None:
        authentication_limiter.record_failure(attempt_key)
        raise HTTPException(status_code=401, detail="Authentication state changed")
    authentication_limiter.record_success(attempt_key)
    _set_session_cookie(response, token)

    return {
        "success": True,
        "username": user_data["username"],
        "is_admin": user_data["is_admin"],
    }


@app.post("/api/auth/logout")
async def logout(
    http_request: Request,
    response: Response,
    _current_user: dict = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Logout current user"""
    token = _session_token(http_request)
    await asyncio.to_thread(user_manager.logout, token)
    _clear_session_cookie(response)

    return {"success": True, "message": "Logged out successfully"}


@app.post("/api/auth/register")
async def register_user(
    request: RegisterRequest,
    _admin_user: dict = Depends(get_admin_user),
    _csrf: None = Depends(require_csrf),
):
    """Register a new user (admin only)"""
    try:
        await asyncio.to_thread(
            user_manager.create_user,
            request.username,
            request.password,
            False,
            max_users=MAX_USERS,
        )
        return {
            "success": True,
            "message": f"User '{request.username}' created successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/api/auth/users")
async def list_users(admin_user: dict = Depends(get_admin_user)):
    """List all users (admin only)"""
    try:
        users = await asyncio.to_thread(user_manager.list_users, admin_user["username"])
        return {"success": True, "users": users}
    except AuthenticationError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@app.delete("/api/auth/users/{username}")
async def delete_user(
    username: str,
    admin_user: dict = Depends(get_admin_user),
    _csrf: None = Depends(require_csrf),
):
    """Delete a user (admin only)"""
    deletion_key = username.casefold()
    with deleting_usernames_lock:
        if deletion_key in deleting_usernames:
            raise HTTPException(
                status_code=409, detail="User deletion is already in progress"
            )
        deleting_usernames.add(deletion_key)
    try:
        # Mark the account before cancellation so newly arriving requests and
        # background critical sections cannot enter while local tasks are settling.
        active_user_tasks = task_store.list_active_tasks(deletion_key)
        task_handles = []
        for active_user_task in active_user_tasks:
            task_handle = active_tasks.get(active_user_task["task_id"])
            if task_handle and not task_handle.done():
                task_handle.cancel()
                task_handles.append(task_handle)
        if task_handles:
            await asyncio.gather(*task_handles, return_exceptions=True)

        async with _user_lifecycle_guard(deletion_key, allow_deleting=True):
            user_dir = user_manager.get_user_dir(deletion_key)

            # A task can exist in SQLite without an in-memory handle after a worker
            # handoff; settle those records before the user row is cascaded.
            for active_user_task in task_store.list_active_tasks(deletion_key):
                task_store.mark_cancelled(active_user_task["task_id"])
                _cleanup_translation_artifacts(active_user_task, user_dir)
            await asyncio.to_thread(
                user_manager.delete_user, username, admin_user["username"]
            )
        return {"success": True, "message": f"User '{username}' deleted successfully"}
    except AuthenticationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except UserDataCleanupError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        with deleting_usernames_lock:
            deleting_usernames.discard(deletion_key)


@app.get("/api/auth/registration-status")
async def get_registration_status():
    """Check if user registration is enabled (public endpoint)"""
    enabled = await asyncio.to_thread(user_manager.get_registration_enabled)
    return {"success": True, "enabled": enabled}


@app.post("/api/auth/registration-toggle")
async def toggle_registration(
    request: RegistrationToggleRequest,
    admin_user: dict = Depends(get_admin_user),
    _csrf: None = Depends(require_csrf),
):
    """Enable or disable user registration (admin only)"""
    try:
        enabled = request.enabled
        await asyncio.to_thread(
            user_manager.set_registration_enabled, enabled, admin_user["username"]
        )
        return {
            "success": True,
            "enabled": enabled,
            "message": f"Registration {'enabled' if enabled else 'disabled'}",
        }
    except AuthenticationError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@app.post("/api/auth/register/public")
async def register_public(
    http_request: Request,
    response: Response,
    request: RegisterRequest,
    _csrf: None = Depends(require_csrf),
):
    """Public user registration endpoint (only works if registration is enabled)"""
    attempt_key = _enforce_auth_attempt_limit(
        http_request, "register", request.username
    )
    # Check if registration is enabled
    if not await asyncio.to_thread(user_manager.get_registration_enabled):
        raise HTTPException(
            status_code=403,
            detail="User registration is currently disabled. Please contact an administrator.",
        )

    try:
        await asyncio.to_thread(
            user_manager.create_user,
            request.username,
            request.password,
            False,
            max_users=MAX_USERS,
        )

        # Automatically log in the new user
        token = await asyncio.to_thread(
            user_manager.authenticate, request.username, request.password
        )
        if token is None:
            raise HTTPException(status_code=500, detail="Failed to create session")
        user_data = await asyncio.to_thread(user_manager.validate_token, token)
        if user_data is None:
            raise HTTPException(status_code=500, detail="Failed to validate session")
        authentication_limiter.record_success(attempt_key)
        _set_session_cookie(response, token)

        return {
            "success": True,
            "message": f"Account created successfully! Welcome, {request.username}!",
            "username": user_data["username"],
            "is_admin": user_data["is_admin"],
        }
    except ValueError as e:
        authentication_limiter.record_failure(attempt_key)
        raise HTTPException(status_code=400, detail=str(e)) from e


# Settings endpoints
@app.get("/api/settings")
async def get_settings(current_user: dict = Depends(get_current_user)):
    """Get current user's settings"""
    async with _user_lifecycle_guard(current_user["username"]):
        user_dir = user_manager.get_user_dir(current_user["username"])
        settings_file = user_dir / "settings.json"

        try:
            settings = await asyncio.to_thread(_read_settings_file, settings_file)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    browser_settings, configured_credentials = _settings_for_browser(settings)
    return {
        "success": True,
        "settings": browser_settings,
        "configured_credentials": configured_credentials,
    }


@app.post("/api/settings")
async def update_settings(
    settings: dict,
    current_user: dict = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Update current user's settings"""
    async with _user_lifecycle_guard(current_user["username"]):
        user_dir = user_manager.get_user_dir(current_user["username"])
        user_dir.mkdir(parents=True, exist_ok=True)
        settings_file = user_dir / "settings.json"

        try:
            await asyncio.to_thread(
                _merge_and_write_settings_file,
                settings_file,
                settings,
                is_admin=bool(current_user.get("is_admin")),
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"success": True, "message": "Settings updated successfully"}


@app.post("/api/settings/password")
async def change_password(
    response: Response,
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Change current user's password"""
    async with _user_lifecycle_guard(current_user["username"]):
        try:
            await asyncio.to_thread(
                user_manager.change_password,
                current_user["username"],
                request.old_password,
                request.new_password,
            )
            _clear_session_cookie(response)
            return {"success": True, "message": "Password changed successfully"}
        except (AuthenticationError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/settings/reset")
async def reset_settings(
    current_user: dict = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Reset current user's settings to default"""
    async with _user_lifecycle_guard(current_user["username"]):
        user_dir = user_manager.get_user_dir(current_user["username"])
        settings_file = user_dir / "settings.json"

        await asyncio.to_thread(_replace_settings_file, settings_file, {})

    return {"success": True, "message": "Settings reset to default"}


@app.get("/api/settings/export")
async def export_settings(current_user: dict = Depends(get_current_user)):
    """Export current user's settings as JSON file"""
    async with _user_lifecycle_guard(current_user["username"]):
        user_dir = user_manager.get_user_dir(current_user["username"])
        settings_file = user_dir / "settings.json"

        try:
            settings = await asyncio.to_thread(_read_settings_file, settings_file)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        # Create export data with metadata
        export_data = {
            "version": "1.0",
            "exported_at": _utc_now().isoformat(),
            "exported_by": current_user["username"],
            "settings": settings,
        }

        # Create temporary file for export
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
            temp_path = f.name

    # Generate filename with timestamp
    timestamp = _utc_now().strftime("%Y%m%d_%H%M%S")
    filename = f"translation_config_{timestamp}.json"

    return FileResponse(
        temp_path,
        media_type="application/json",
        filename=filename,
        background=BackgroundTask(Path(temp_path).unlink),
    )


@app.post("/api/settings/import")
async def import_settings(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Import settings from JSON file"""
    import_filename = file.filename or ""
    if not import_filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files are allowed")

    try:
        # Read and parse JSON
        content = await file.read(MAX_SETTINGS_IMPORT_BYTES + 1)
        if len(content) > MAX_SETTINGS_IMPORT_BYTES:
            raise HTTPException(
                status_code=413,
                detail=(
                    "Configuration file exceeds the "
                    f"{MAX_SETTINGS_IMPORT_BYTES} byte limit"
                ),
            )
        import_data = _load_json_value(content.decode("utf-8"))

        # Validate structure
        if not isinstance(import_data, dict) or "settings" not in import_data:
            raise HTTPException(
                status_code=400,
                detail="Invalid configuration file: missing 'settings' field",
            )

        # Optional: Check version compatibility
        if "version" in import_data:
            version = import_data["version"]
            if version != "1.0":
                logger.warning(f"Importing config with different version: {version}")

        # Get imported settings
        imported_settings = import_data["settings"]
        if not isinstance(imported_settings, dict):
            raise HTTPException(
                status_code=400,
                detail="Invalid configuration file: 'settings' must be an object",
            )

        async with _user_lifecycle_guard(current_user["username"]):
            user_dir = user_manager.get_user_dir(current_user["username"])
            user_dir.mkdir(parents=True, exist_ok=True)
            settings_file = user_dir / "settings.json"

            await asyncio.to_thread(
                _merge_and_write_settings_file,
                settings_file,
                imported_settings,
                is_admin=bool(current_user.get("is_admin")),
            )

        setting_count = len(imported_settings)

        return {
            "success": True,
            "message": f"Successfully imported {setting_count} settings",
            "imported_count": setting_count,
            "imported_from": import_data.get("exported_by", "unknown"),
            "exported_at": import_data.get("exported_at", "unknown"),
        }

    except HTTPException:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Invalid JSON file") from None
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to import settings")
        raise HTTPException(
            status_code=500, detail="Failed to import settings"
        ) from exc


def _resolve_translation_pages(
    requested_settings: dict, saved_settings: dict, page_count: int
) -> str | None:
    """Resolve explicit per-task pages before falling back to saved preferences."""
    if "pages" in requested_settings:
        requested_pages = requested_settings["pages"]
        if requested_pages in (None, "", "all"):
            return None
        if not isinstance(requested_pages, str):
            raise ValueError("pages must be a page range string")
        page_range = requested_pages.strip()
    else:
        saved_page_range = saved_settings.get("page_range", "all")
        if saved_page_range == "first":
            return "1"
        if saved_page_range == "first5":
            last_page = min(5, page_count)
            return "1" if last_page == 1 else f"1-{last_page}"
        if saved_page_range == "custom":
            page_range = str(saved_settings.get("custom_pages") or "").strip()
            return _parse_page_range(page_range, page_count) if page_range else None
        return None

    return _parse_page_range(page_range, page_count)


def _settings_without_credentials(user_settings: dict) -> dict:
    """Create a persistent task snapshot without provider credentials."""
    return {
        setting_name: setting_value
        for setting_name, setting_value in user_settings.items()
        if not setting_name.casefold().endswith(SENSITIVE_SETTING_SUFFIXES)
    }


def _settings_for_browser(user_settings: dict) -> tuple[dict, list[str]]:
    """Return editable settings without sending saved provider credentials."""
    browser_settings = _settings_without_credentials(user_settings)
    configured_credentials = sorted(
        setting_name
        for setting_name, setting_value in user_settings.items()
        if setting_name.casefold().endswith(SENSITIVE_SETTING_SUFFIXES)
        and isinstance(setting_value, str)
        and bool(setting_value)
    )
    return browser_settings, configured_credentials


def _load_task_settings_snapshot(
    user_dir: Path,
    requested_settings: dict,
    input_path: Path,
    output_dir: Path,
    *,
    is_admin: bool,
) -> dict:
    settings_file = user_dir / "settings.json"
    saved_settings = _read_settings_file(settings_file)
    page_count = _pdf_page_count(input_path)
    page_range = _resolve_translation_pages(
        requested_settings, saved_settings, page_count
    )
    settings_snapshot = {
        "user_settings": saved_settings,
        "pages": page_range,
        "allow_privileged_services": is_admin,
    }
    translation_model = build_settings_model_from_user_config(
        saved_settings,
        output_dir,
        page_range,
        allow_privileged_services=is_admin,
    )
    try:
        translation_model.validate_settings()
    except ValueError as exc:
        raise ValueError(f"Invalid translation settings: {exc}") from exc
    return settings_snapshot


# File upload and translation endpoints
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Upload a PDF file for translation"""
    safe_filename = _normalize_uploaded_filename(file.filename)

    username = current_user["username"]
    async with _user_lifecycle_guard(username):
        user_dir = user_manager.get_user_dir(username)
        current_storage_bytes = await asyncio.to_thread(_user_storage_bytes, user_dir)
        if current_storage_bytes >= MAX_USER_STORAGE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="User storage quota exceeded",
            )

        upload_dir = user_dir / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_id = str(uuid.uuid4())
        file_path = upload_dir / f"{file_id}_{safe_filename}"

        uploaded_bytes = await _save_uploaded_file(file, file_path)
        try:
            page_count = await asyncio.to_thread(_pdf_page_count, file_path)
        except ValueError as exc:
            file_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        current_storage_bytes = await asyncio.to_thread(_user_storage_bytes, user_dir)
        if current_storage_bytes > MAX_USER_STORAGE_BYTES:
            file_path.unlink(missing_ok=True)
            raise HTTPException(status_code=413, detail="User storage quota exceeded")

    return {
        "success": True,
        "file_id": file_id,
        "filename": safe_filename,
        "size": uploaded_bytes,
        "page_count": page_count,
    }


@app.delete("/api/upload/{file_id}")
async def delete_uploaded_file(
    file_id: str,
    current_user: dict = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Delete an uploaded file that has not been attached to a translation task."""
    try:
        normalized_file_id = str(uuid.UUID(file_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file id") from None

    username = current_user["username"]
    async with _user_lifecycle_guard(username):
        user_dir = user_manager.get_user_dir(username)
        async with _uploaded_file_guard(user_dir, normalized_file_id):
            if task_store.count_tasks_for_file(username, normalized_file_id):
                raise HTTPException(
                    status_code=409, detail="The file is already used by a task"
                )
            matching_files = _uploaded_files_for_id(user_dir, normalized_file_id)
            if not matching_files:
                raise HTTPException(status_code=404, detail="File not found")
            for candidate in matching_files:
                try:
                    candidate.unlink()
                except OSError as exc:
                    logger.error(
                        "Failed to delete uploaded file %s: %s", candidate, exc
                    )
                    raise HTTPException(
                        status_code=500, detail="Failed to delete uploaded file"
                    ) from exc
    return {"success": True}


@app.post("/api/translate")
async def start_translation(
    file_id: str = Form(...),
    settings: str = Form(...),
    current_user: dict = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Start a translation task"""
    if len(settings.encode("utf-8")) > MAX_SETTINGS_JSON_BYTES:
        raise HTTPException(
            status_code=413, detail="Translation settings are too large"
        )
    try:
        translation_settings = _load_json_value(settings)
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid settings JSON") from None
    if not isinstance(translation_settings, dict):
        raise HTTPException(
            status_code=400, detail="Translation settings must be an object"
        )
    if set(translation_settings) - {"pages"}:
        raise HTTPException(status_code=400, detail="Unsupported translation settings")

    try:
        normalized_file_id = str(uuid.UUID(file_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file id") from None

    username = current_user["username"]
    user_dir = user_manager.get_user_dir(username)
    async with _user_uploaded_file_guard(username, user_dir, normalized_file_id):
        upload_dir = user_dir / "uploads"
        matching_file = next(
            (
                candidate
                for candidate in upload_dir.glob(f"{normalized_file_id}_*")
                if candidate.is_file() and not candidate.is_symlink()
            ),
            None,
        )
        if matching_file is None:
            raise HTTPException(status_code=404, detail="File not found")

        file_path = matching_file
        task_id = str(uuid.uuid4())
        output_dir = user_dir / "outputs" / task_id
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            settings_snapshot = _load_task_settings_snapshot(
                user_dir,
                translation_settings,
                file_path,
                output_dir,
                is_admin=bool(current_user.get("is_admin")),
            )
            persistent_settings_snapshot = {
                **settings_snapshot,
                "user_settings": _settings_without_credentials(
                    settings_snapshot["user_settings"]
                ),
            }
            task_store.create_task(
                task_id=task_id,
                username=username,
                file_id=normalized_file_id,
                filename=file_path.name.removeprefix(f"{normalized_file_id}_"),
                input_path=file_path,
                output_dir=output_dir,
                settings_snapshot=persistent_settings_snapshot,
                max_active_tasks=MAX_ACTIVE_TASKS_PER_USER,
                max_active_tasks_global=MAX_ACTIVE_TASKS_GLOBAL,
            )
            active_task_settings[task_id] = settings_snapshot
        except ActiveTaskLimitError as exc:
            shutil.rmtree(output_dir, ignore_errors=True)
            _remove_unattached_uploaded_file_locked(
                user_dir, username, normalized_file_id
            )
            raise HTTPException(
                status_code=429,
                detail=(
                    "Too many active translation tasks. "
                    "Please wait for an existing task to finish."
                ),
            ) from exc
        except GlobalActiveTaskLimitError as exc:
            shutil.rmtree(output_dir, ignore_errors=True)
            _remove_unattached_uploaded_file_locked(
                user_dir, username, normalized_file_id
            )
            raise HTTPException(
                status_code=429,
                detail="The service is currently processing its maximum number of tasks",
            ) from exc
        except ValueError as exc:
            shutil.rmtree(output_dir, ignore_errors=True)
            _remove_unattached_uploaded_file_locked(
                user_dir, username, normalized_file_id
            )
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception:
            shutil.rmtree(output_dir, ignore_errors=True)
            _remove_unattached_uploaded_file_locked(
                user_dir, username, normalized_file_id
            )
            raise

        task_handle = asyncio.create_task(
            run_translation_with_timeout(task_id, username),
            name=f"translation-{task_id}",
        )
        active_tasks[task_id] = task_handle

    return {"success": True, "task_id": task_id, "message": "Translation started"}


async def run_translation(task_id: str, username: str) -> None:
    """Run one persisted translation task using the official translation engine."""
    mono_path: Path | None = None
    dual_path: Path | None = None
    task: dict | None = None
    user_dir = user_manager.get_user_dir(username)

    try:
        async with _user_lifecycle_guard(username):
            task = task_store.get_task(task_id, username=username)
            if task is None:
                return

            if not task.get("input_path") or not task.get("output_dir"):
                raise ValueError("Saved translation paths are invalid")
            file_path = Path(task["input_path"])
            output_dir = Path(task["output_dir"])
            original_filename = task["original_filename"]
            if not task_store.mark_processing(task_id, "Loading user settings..."):
                _cleanup_translation_artifacts(task, user_dir)
                return

        task_snapshot = active_task_settings.get(task_id)
        if task_snapshot is None:
            try:
                task_snapshot = _load_json_value(task.get("settings_json") or "{}")
            except (TypeError, json.JSONDecodeError, ValueError) as exc:
                raise ValueError("Saved translation settings are invalid") from exc
        if not task_snapshot or "user_settings" not in task_snapshot:
            raise ValueError("Saved translation settings are incomplete")
        user_settings = task_snapshot["user_settings"]
        pages = task_snapshot.get("pages")
        allow_privileged_services = bool(task_snapshot.get("allow_privileged_services"))
        if not isinstance(user_settings, dict):
            raise ValueError("Saved translation settings are invalid")

        logger.info(
            "Starting translation task %s for user %s with service %s",
            task_id,
            username,
            user_settings.get("service", "SiliconFlowFree"),
        )

        settings = build_settings_model_from_user_config(
            user_settings,
            output_dir,
            pages,
            allow_privileged_services=allow_privileged_services,
        )
        try:
            settings.validate_settings()
        except ValueError as e:
            raise ValueError(f"Invalid translation settings: {e}") from e

        if not task_store.mark_processing(task_id, "Starting translation..."):
            _cleanup_translation_artifacts(task, user_dir)
            return
        finished = False
        async for event in do_translate_async_stream(settings, file_path):
            if event["type"] in ("progress_start", "progress_update", "progress_end"):
                stage = event.get("stage", "Processing")
                progress = event.get("overall_progress", 0)
                part_index = event.get("part_index", 1)
                total_parts = event.get("total_parts", 1)
                stage_current = event.get("stage_current", 0)
                stage_total = event.get("stage_total", 1)

                message = f"{stage} ({part_index}/{total_parts}, {stage_current}/{stage_total})"
                if not task_store.update_progress(task_id, int(progress), message):
                    _cleanup_translation_artifacts(task, user_dir)
                    return
                logger.debug("Task %s: %s%% - %s", task_id, progress, message)

            elif event["type"] == "finish":
                result = event["translate_result"]
                result_mono_path = result.mono_pdf_path
                result_dual_path = result.dual_pdf_path

                async with _user_lifecycle_guard(username):
                    if not task_store.is_processing(task_id):
                        _cleanup_translation_artifacts(task, user_dir)
                        return

                    if result_mono_path and result_mono_path.exists():
                        mono_path = output_dir / f"{original_filename}_mono.pdf"
                        result_mono_path.replace(mono_path)
                        logger.info("Mono PDF saved: %s", mono_path)

                    if result_dual_path and result_dual_path.exists():
                        dual_path = output_dir / f"{original_filename}_dual.pdf"
                        result_dual_path.replace(dual_path)
                        logger.info("Dual PDF saved: %s", dual_path)

                finished = True
                break

            elif event["type"] == "error":
                error_msg = event.get("error", "Unknown error")
                raise RuntimeError(f"Translation error: {error_msg}")

        if not finished:
            raise RuntimeError("Translation engine ended without a result")
        if not mono_path and not dual_path:
            raise RuntimeError("Translation completed without producing a PDF")
        async with _user_lifecycle_guard(username):
            await asyncio.to_thread(_ensure_user_storage_quota, user_dir)

            if not task_store.mark_completed(task_id, mono_path, dual_path):
                _cleanup_translation_artifacts(task, user_dir)
                return
        logger.info("Translation task %s completed successfully", task_id)

    except asyncio.CancelledError:
        try:
            async with _user_lifecycle_guard(username):
                timed_out = task_id in timed_out_tasks
                if timed_out:
                    task_store.mark_failed(
                        task_id,
                        "Translation exceeded the configured execution time limit",
                    )
                else:
                    task_store.mark_cancelled(task_id)
                if task is not None:
                    _cleanup_translation_artifacts(task, user_dir)
        except HTTPException:
            # Account deletion owns cleanup after it marks the account as deleting.
            pass
        raise
    except HTTPException:
        # The account disappeared or entered deletion while this task was running.
        logger.info(
            "Stopping translation task %s because its account is inactive", task_id
        )
    except Exception as e:
        error_message = str(e)[:1000]
        logger.error(
            "Translation task %s failed: %s", task_id, error_message, exc_info=True
        )
        try:
            async with _user_lifecycle_guard(username):
                task_store.mark_failed(task_id, error_message)
                if task is not None:
                    _cleanup_translation_artifacts(task, user_dir)
        except HTTPException:
            # Account deletion owns cleanup after it marks the account as deleting.
            pass
    finally:
        active_tasks.pop(task_id, None)
        active_task_settings.pop(task_id, None)


async def run_translation_with_timeout(task_id: str, username: str) -> None:
    """Run one task with a total wall-clock limit on Python 3.10+ runtimes."""
    translation_task = asyncio.create_task(run_translation(task_id, username))
    try:
        await asyncio.wait_for(
            asyncio.shield(translation_task), MAX_TRANSLATION_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        timed_out_tasks.add(task_id)
        translation_task.cancel()
        await asyncio.gather(translation_task, return_exceptions=True)
    except asyncio.CancelledError:
        translation_task.cancel()
        await asyncio.gather(translation_task, return_exceptions=True)
        raise
    finally:
        timed_out_tasks.discard(task_id)


@app.get("/api/translate/status/{task_id}")
async def get_translation_status(
    task_id: str, current_user: dict = Depends(get_current_user)
):
    """Get status of a translation task"""
    async with _user_lifecycle_guard(current_user["username"]):
        task = _get_owned_task(task_id, current_user["username"])
        return {"success": True, "task": _serialize_task(task)}


@app.get("/api/translate/history")
async def get_translation_history(
    limit: int = Query(100, ge=1, le=MAX_HISTORY_PAGE_SIZE),
    offset: int = Query(0, ge=0, le=MAX_HISTORY_OFFSET),
    current_user: dict = Depends(get_current_user),
):
    """Get current user's translation history"""
    username = current_user["username"]
    async with _user_lifecycle_guard(username):
        tasks = task_store.list_tasks(username, limit=limit, offset=offset)
        return {
            "success": True,
            "history": [_serialize_history_item(task) for task in tasks],
            "total": task_store.count_tasks(username),
            "limit": limit,
            "offset": offset,
        }


@app.delete("/api/translate/history/{task_id}")
async def delete_history_item(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
):
    """Delete a history item and its associated files"""
    username = current_user["username"]
    task = _get_owned_task(task_id, username)
    task_handle = active_tasks.get(task_id)
    if task_handle and not task_handle.done():
        task_handle.cancel()
        await asyncio.gather(task_handle, return_exceptions=True)

    async with _user_lifecycle_guard(username):
        task = _get_owned_task(task_id, username)
        user_dir = user_manager.get_user_dir(username)
        if not _cleanup_translation_artifacts(task, user_dir):
            raise HTTPException(
                status_code=500,
                detail="Task files could not be removed; the history record was kept",
            )
        deleted_task = task_store.delete_task(task_id, username)
        if deleted_task is None:
            raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "message": "History item deleted"}


@app.get("/api/translate/download/{task_id}")
async def download_translation(
    task_id: str,
    file_type: str = "mono",
    current_user: dict = Depends(get_current_user),
):
    """Download a translated file"""
    username = current_user["username"]
    async with _user_lifecycle_guard(username):
        task = _get_owned_task(task_id, username)
        if task["status"] != "completed":
            raise HTTPException(status_code=400, detail="Translation not completed")

        user_dir = user_manager.get_user_dir(username)
        file_path = _resolve_download_path(task, user_dir, file_type)
        temporary_download = tempfile.NamedTemporaryFile(
            mode="wb", suffix=".pdf", delete=False
        )
        temporary_download.close()
        temporary_download_path = Path(temporary_download.name)
        try:
            await asyncio.to_thread(shutil.copyfile, file_path, temporary_download_path)
        except Exception:
            temporary_download_path.unlink(missing_ok=True)
            raise

    original_filename = str(task.get("original_filename") or "translated")
    clean_name = re.sub(r"[^\w\-\u4e00-\u9fff.]", "_", original_filename)
    download_filename = f"{clean_name}_{file_type}.pdf"

    return FileResponse(
        temporary_download_path,
        media_type="application/pdf",
        filename=download_filename,
        background=BackgroundTask(temporary_download_path.unlink, missing_ok=True),
    )


# Serve static files (frontend)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    # Mount CSS and JS directories
    css_dir = static_dir / "css"
    js_dir = static_dir / "js"

    if css_dir.exists():
        app.mount("/static/css", StaticFiles(directory=str(css_dir)), name="css")
    if js_dir.exists():
        app.mount("/static/js", StaticFiles(directory=str(js_dir)), name="js")

    # Serve HTML files from static root
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static_html")

    # Serve root HTML files
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="root")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
