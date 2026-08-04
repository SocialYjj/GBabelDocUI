"""
FastAPI web server for PDFMathTranslate with multi-user authentication.

This module provides REST API endpoints for:
- User authentication (login, logout, registration)
- File upload and translation
- Settings management
- Translation history
"""

import asyncio
import ipaddress
import json
import logging
import os
import re
import shutil
import tempfile
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from datetime import timezone
from pathlib import Path
from urllib.parse import urlparse

from fastapi import Depends
from fastapi import FastAPI
from fastapi import File
from fastapi import Form
from fastapi import Header
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from filelock import FileLock
from pdf2zh_next import __version__
from pdf2zh_next.config.model import SettingsModel
from pdf2zh_next.high_level import do_translate_async_stream
from pydantic import BaseModel
from pydantic import StrictBool
from starlette.background import BackgroundTask

from gbabeldocui.auth import AuthenticationError
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
ORPHAN_UPLOAD_CLEANUP_INTERVAL_SECONDS = 6 * 60 * 60
UPLOAD_CHUNK_BYTES = 1024 * 1024
MAX_HISTORY_PAGE_SIZE = 200
MAX_HISTORY_OFFSET = 1_000_000
MAX_FILENAME_UTF8_BYTES = 240
MAX_SETTINGS_JSON_BYTES = 256 * 1024
MAX_SETTINGS_FILE_BYTES = MAX_SETTINGS_JSON_BYTES * 2
MAX_SETTINGS_IMPORT_BYTES = MAX_SETTINGS_FILE_BYTES
PDF_HEADER_SCAN_BYTES = 1024
MAX_CONFIGURED_POOL_WORKERS = 1000
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
PRIVILEGED_SETTING_NAMES = ENDPOINT_SETTING_NAMES | {"claude_code_path"}


def _utc_now() -> datetime:
    """Return a naive UTC timestamp for the existing JSON format."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


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


class AuthenticationAttemptLimiter:
    """Limit repeated login and public-registration failures per client address."""

    def __init__(self, maximum_attempts: int, window_seconds: int):
        self.maximum_attempts = maximum_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def retry_after(self, key: str) -> int | None:
        now = time.monotonic()
        with self._lock:
            attempts = self._active_attempts(key, now)
            if len(attempts) < self.maximum_attempts:
                return None
            return max(1, int(self.window_seconds - (now - attempts[0]) + 0.999))

    def record_failure(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
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


# Persistent application state. Runtime task handles are only used for cancellation;
# status, progress, ownership and output paths are stored in SQLite.
user_manager = UserManager()
task_store = TranslationTaskStore(user_manager.db_path)
active_tasks: dict[str, asyncio.Task[None]] = {}
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
    user_manager.validate_user_directory_integrity()
    user_manager.cleanup_expired_sessions()
    for recovered_task in task_store.recover_interrupted_tasks():
        _cleanup_translation_artifacts(
            recovered_task,
            user_manager.get_user_dir(recovered_task["username"]),
        )
        task_store.synchronize_history(recovered_task)
    orphan_cleanup_handle = asyncio.create_task(
        _periodic_orphan_upload_cleanup(),
        name="orphan-upload-cleanup",
    )
    logger.info("Web API ready")
    try:
        yield
    finally:
        orphan_cleanup_handle.cancel()
        running_handles = list(active_tasks.values())
        for task_handle in running_handles:
            task_handle.cancel()
        await asyncio.gather(
            orphan_cleanup_handle,
            *running_handles,
            return_exceptions=True,
        )
        logger.info("PDFMathTranslate Web API shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="PDFMathTranslate API",
    version="2.0.0",
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
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )


# Pydantic models for request/response
class SetupRequest(BaseModel):
    username: str
    password: str


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
    if private_host and not (allow_private or ALLOW_PRIVATE_ENDPOINTS):
        raise ValueError(
            f"{setting_name} cannot target localhost, private, loopback, or link-local addresses"
        )
    return normalized_endpoint


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
            user_settings, rpm_name, 240, minimum=60
        )
        qps = max(1, requests_per_minute // 60)
        pool_workers = min(MAX_CONFIGURED_POOL_WORKERS, qps * 10)
    elif normalized_mode == "concurrent":
        concurrent_threads = _read_integer_setting(
            user_settings, concurrent_name, 40, minimum=1
        )
        pool_workers = min(
            MAX_CONFIGURED_POOL_WORKERS,
            max(1, min(int(concurrent_threads * 0.9), concurrent_threads - 20)),
        )
        qps = max(1, pool_workers)
    elif normalized_mode == "custom":
        qps = _read_integer_setting(user_settings, qps_name, default_qps, minimum=1)
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
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
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
        if not isinstance(custom_pages, str) or len(custom_pages) > 200:
            raise ValueError("custom_pages must be a short page range string")
        if not re.fullmatch(r"[0-9,\-\s]+", custom_pages):
            raise ValueError("custom_pages contains invalid characters")
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
        "max_pages_per_part": (0, 100000),
        "rpm": (60, 100000),
        "concurrent_threads": (1, MAX_CONFIGURED_POOL_WORKERS),
        "custom_qps": (1, MAX_CONFIGURED_POOL_WORKERS),
        "custom_workers": (0, MAX_CONFIGURED_POOL_WORKERS),
        "term_rpm": (60, 100000),
        "term_concurrent": (1, MAX_CONFIGURED_POOL_WORKERS),
        "term_qps": (1, MAX_CONFIGURED_POOL_WORKERS),
        "term_workers": (0, MAX_CONFIGURED_POOL_WORKERS),
        "qps": (1, MAX_CONFIGURED_POOL_WORKERS),
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
            merged_settings, ensure_ascii=False, separators=(",", ":")
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
            json.dump(payload, temporary_file, indent=2, ensure_ascii=False)
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        temporary_path.replace(file_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _is_readable_pdf(file_path: Path) -> bool:
    """Perform a lightweight parser check before queuing the translation."""
    with file_path.open("rb") as source_file:
        if b"%PDF-" not in source_file.read(PDF_HEADER_SCAN_BYTES):
            return False
    try:
        import fitz

        with fitz.open(filename=str(file_path)) as document:
            _ = document.page_count
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def _extract_bearer_token(authorization: str | None) -> str:
    """Extract a non-empty bearer token from an Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    scheme, separator, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not separator or not token.strip():
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token.strip()


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
    except Exception:
        file_path.unlink(missing_ok=True)
        raise
    return total_bytes


def _client_address(request: Request) -> str:
    """Return the transport peer used for public authentication throttling."""
    return request.client.host if request.client else "unknown"


def _enforce_auth_attempt_limit(request: Request, operation: str, username: str) -> str:
    # Include the account name so a reverse proxy does not make all users share
    # one bucket. The account name is bounded because it is untrusted input.
    identity = str(username).strip().casefold()[:128]
    key = f"{operation}:{_client_address(request)}:{identity}"
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
    """Run conservative orphan cleanup without delaying application startup."""
    while True:
        await asyncio.sleep(ORPHAN_UPLOAD_CLEANUP_INTERVAL_SECONDS)
        try:
            await asyncio.to_thread(_cleanup_orphaned_uploaded_files)
        except Exception:
            logger.exception("Orphan upload cleanup failed")


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


def _cleanup_translation_artifacts(task: dict, user_dir: Path) -> None:
    """Remove only artifacts owned by the task being failed or cancelled."""
    task_output_dir = (user_dir / "outputs" / task["task_id"]).resolve()
    outputs_root = (user_dir / "outputs").resolve()
    try:
        task_output_dir.relative_to(outputs_root)
    except ValueError:
        logger.error(
            "Refusing to remove output path outside user directory: %s", task_output_dir
        )
    else:
        if task_output_dir.is_symlink():
            logger.error(
                "Refusing to remove symlinked task output: %s", task_output_dir
            )
        elif task_output_dir.exists():
            try:
                shutil.rmtree(task_output_dir)
            except OSError as exc:
                logger.error(
                    "Failed to remove task output %s: %s", task_output_dir, exc
                )

    input_path_value = task.get("input_path")
    if not input_path_value:
        return
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
                return

            uploads_root = (user_dir / "uploads").resolve()
            input_path = Path(input_path_value)
            if input_path.is_symlink():
                logger.error(
                    "Refusing to remove symlinked uploaded file: %s", input_path
                )
                return
            input_path = input_path.resolve()
            try:
                input_path.relative_to(uploads_root)
            except ValueError:
                logger.error(
                    "Refusing to remove input path outside user directory: %s",
                    input_path,
                )
            else:
                try:
                    input_path.unlink(missing_ok=True)
                except OSError as exc:
                    logger.error(
                        "Failed to remove uploaded file %s: %s", input_path, exc
                    )
    except Exception as exc:
        logger.error("Failed to clean uploaded file %s: %s", input_path_value, exc)


# Dependency to get current user from token
async def get_current_user(authorization: str | None = Header(None)) -> dict:
    """Validate authentication token and return current user"""
    token = _extract_bearer_token(authorization)
    user_data = user_manager.validate_token(token)

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
    """Build official pdf2zh-next engine settings from WebUI settings."""
    from pdf2zh_next.config.translate_engine_model import AzureOpenAISettings
    from pdf2zh_next.config.translate_engine_model import BingSettings
    from pdf2zh_next.config.translate_engine_model import ClaudeCodeSettings
    from pdf2zh_next.config.translate_engine_model import DeepLSettings
    from pdf2zh_next.config.translate_engine_model import DeepSeekSettings
    from pdf2zh_next.config.translate_engine_model import GeminiSettings
    from pdf2zh_next.config.translate_engine_model import GoogleSettings
    from pdf2zh_next.config.translate_engine_model import OllamaSettings
    from pdf2zh_next.config.translate_engine_model import OpenAISettings
    from pdf2zh_next.config.translate_engine_model import SiliconFlowFreeSettings
    from pdf2zh_next.config.translate_engine_model import SiliconFlowSettings
    from pdf2zh_next.config.translate_engine_model import TencentSettings
    from pdf2zh_next.config.translate_engine_model import ZhipuSettings

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
        maximum=100000,
    )
    if max_pages > 0:
        settings.pdf.max_pages_per_part = max_pages

    # Formula patterns (note: frontend uses 'formula', backend uses 'formular')
    formula_font = user_settings.get("formula_font_pattern", "")
    if formula_font:
        settings.pdf.formular_font_pattern = formula_font
    formula_char = user_settings.get("formula_char_pattern", "")
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
    return {"setup_required": not user_manager.has_users(), "version": __version__}


@app.post("/api/auth/setup")
async def initial_setup(request: SetupRequest):
    """Create the first admin user"""
    try:
        user_manager.create_initial_admin(request.username, request.password)
        token = user_manager.authenticate(request.username, request.password)

        return {
            "success": True,
            "token": token,
            "username": request.username,
            "is_admin": True,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/auth/login")
async def login(http_request: Request, request: LoginRequest):
    """Authenticate user and return session token"""
    attempt_key = _enforce_auth_attempt_limit(http_request, "login", request.username)
    token = user_manager.authenticate(request.username, request.password)

    if not token:
        authentication_limiter.record_failure(attempt_key)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Get user info
    user_data = user_manager.validate_token(token)
    authentication_limiter.record_success(attempt_key)

    return {
        "success": True,
        "token": token,
        "username": user_data["username"],
        "is_admin": user_data["is_admin"],
    }


@app.post("/api/auth/logout")
async def logout(
    _current_user: dict = Depends(get_current_user),
    authorization: str | None = Header(None),
):
    """Logout current user"""
    token = _extract_bearer_token(authorization)
    user_manager.logout(token)

    return {"success": True, "message": "Logged out successfully"}


@app.post("/api/auth/register")
async def register_user(
    request: RegisterRequest, _admin_user: dict = Depends(get_admin_user)
):
    """Register a new user (admin only)"""
    try:
        user_manager.create_user(
            request.username,
            request.password,
            is_admin=False,
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
        users = user_manager.list_users(admin_user["username"])
        return {"success": True, "users": users}
    except AuthenticationError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@app.delete("/api/auth/users/{username}")
async def delete_user(username: str, admin_user: dict = Depends(get_admin_user)):
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
                cancelled_task = task_store.get_task(
                    active_user_task["task_id"], username=deletion_key
                )
                if cancelled_task:
                    task_store.synchronize_history(cancelled_task)
            await asyncio.to_thread(
                user_manager.delete_user, username, admin_user["username"]
            )
        return {"success": True, "message": f"User '{username}' deleted successfully"}
    except AuthenticationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        with deleting_usernames_lock:
            deleting_usernames.discard(deletion_key)


@app.get("/api/auth/registration-status")
async def get_registration_status():
    """Check if user registration is enabled (public endpoint)"""
    enabled = user_manager.get_registration_enabled()
    return {"success": True, "enabled": enabled}


@app.post("/api/auth/registration-toggle")
async def toggle_registration(
    request: RegistrationToggleRequest,
    admin_user: dict = Depends(get_admin_user),
):
    """Enable or disable user registration (admin only)"""
    try:
        enabled = request.enabled
        user_manager.set_registration_enabled(enabled, admin_user["username"])
        return {
            "success": True,
            "enabled": enabled,
            "message": f"Registration {'enabled' if enabled else 'disabled'}",
        }
    except AuthenticationError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@app.post("/api/auth/register/public")
async def register_public(http_request: Request, request: RegisterRequest):
    """Public user registration endpoint (only works if registration is enabled)"""
    attempt_key = _enforce_auth_attempt_limit(
        http_request, "register", request.username
    )
    # Check if registration is enabled
    if not user_manager.get_registration_enabled():
        raise HTTPException(
            status_code=403,
            detail="User registration is currently disabled. Please contact an administrator.",
        )

    try:
        user_manager.create_user(
            request.username,
            request.password,
            is_admin=False,
            max_users=MAX_USERS,
        )

        # Automatically log in the new user
        token = user_manager.authenticate(request.username, request.password)
        user_data = user_manager.validate_token(token)
        authentication_limiter.record_success(attempt_key)

        return {
            "success": True,
            "message": f"Account created successfully! Welcome, {request.username}!",
            "token": token,
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
            settings = _read_settings_file(settings_file)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"success": True, "settings": settings}


@app.post("/api/settings")
async def update_settings(
    settings: dict, current_user: dict = Depends(get_current_user)
):
    """Update current user's settings"""
    async with _user_lifecycle_guard(current_user["username"]):
        user_dir = user_manager.get_user_dir(current_user["username"])
        user_dir.mkdir(parents=True, exist_ok=True)
        settings_file = user_dir / "settings.json"

        try:
            lock_file = settings_file.with_name(f".{settings_file.name}.lock")
            with FileLock(str(lock_file), timeout=30):
                existing_settings = _read_settings_file_unlocked(settings_file)
                merged_settings = _merge_user_settings(
                    existing_settings,
                    settings,
                    is_admin=bool(current_user.get("is_admin")),
                )
                _write_json_file(settings_file, merged_settings)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"success": True, "message": "Settings updated successfully"}


@app.post("/api/settings/password")
async def change_password(
    request: ChangePasswordRequest, current_user: dict = Depends(get_current_user)
):
    """Change current user's password"""
    async with _user_lifecycle_guard(current_user["username"]):
        try:
            user_manager.change_password(
                current_user["username"], request.old_password, request.new_password
            )
            return {"success": True, "message": "Password changed successfully"}
        except (AuthenticationError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/settings/reset")
async def reset_settings(current_user: dict = Depends(get_current_user)):
    """Reset current user's settings to default"""
    async with _user_lifecycle_guard(current_user["username"]):
        user_dir = user_manager.get_user_dir(current_user["username"])
        settings_file = user_dir / "settings.json"

        lock_file = settings_file.with_name(f".{settings_file.name}.lock")
        with FileLock(str(lock_file), timeout=30):
            _write_json_file(settings_file, {})

    return {"success": True, "message": "Settings reset to default"}


@app.get("/api/settings/export")
async def export_settings(current_user: dict = Depends(get_current_user)):
    """Export current user's settings as JSON file"""
    async with _user_lifecycle_guard(current_user["username"]):
        user_dir = user_manager.get_user_dir(current_user["username"])
        settings_file = user_dir / "settings.json"

        try:
            settings = _read_settings_file(settings_file)
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
    file: UploadFile = File(...), current_user: dict = Depends(get_current_user)
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
        import_data = json.loads(content.decode("utf-8"))

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

            lock_file = settings_file.with_name(f".{settings_file.name}.lock")
            with FileLock(str(lock_file), timeout=30):
                existing_settings = _read_settings_file_unlocked(settings_file)
                merged_settings = _merge_user_settings(
                    existing_settings,
                    imported_settings,
                    is_admin=bool(current_user.get("is_admin")),
                )
                _write_json_file(settings_file, merged_settings)

        setting_count = len(merged_settings)

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
    requested_settings: dict, saved_settings: dict
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
            return "1-5"
        if saved_page_range == "custom":
            page_range = str(saved_settings.get("custom_pages") or "").strip()
            return page_range or None
        return None

    if len(page_range) > 200 or not re.fullmatch(r"[0-9,\-\s]+", page_range):
        raise ValueError("pages contains an invalid page range")
    return page_range


def _load_task_settings_snapshot(
    user_dir: Path,
    requested_settings: dict,
    output_dir: Path,
    *,
    is_admin: bool,
) -> dict:
    settings_file = user_dir / "settings.json"
    saved_settings = _read_settings_file(settings_file)
    page_range = _resolve_translation_pages(requested_settings, saved_settings)
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
    file: UploadFile = File(...), current_user: dict = Depends(get_current_user)
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
        if not await asyncio.to_thread(_is_readable_pdf, file_path):
            file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400, detail="The uploaded file is not a PDF"
            )
        current_storage_bytes = await asyncio.to_thread(_user_storage_bytes, user_dir)
        if current_storage_bytes > MAX_USER_STORAGE_BYTES:
            file_path.unlink(missing_ok=True)
            raise HTTPException(status_code=413, detail="User storage quota exceeded")

    return {
        "success": True,
        "file_id": file_id,
        "filename": safe_filename,
        "size": uploaded_bytes,
    }


@app.delete("/api/upload/{file_id}")
async def delete_uploaded_file(
    file_id: str, current_user: dict = Depends(get_current_user)
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
):
    """Start a translation task"""
    if len(settings.encode("utf-8")) > MAX_SETTINGS_JSON_BYTES:
        raise HTTPException(
            status_code=413, detail="Translation settings are too large"
        )
    try:
        translation_settings = json.loads(settings)
    except json.JSONDecodeError:
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
                output_dir,
                is_admin=bool(current_user.get("is_admin")),
            )
            queued_task = task_store.create_task(
                task_id=task_id,
                username=username,
                file_id=normalized_file_id,
                filename=file_path.name.removeprefix(f"{normalized_file_id}_"),
                input_path=file_path,
                output_dir=output_dir,
                settings_snapshot=settings_snapshot,
                max_active_tasks=MAX_ACTIVE_TASKS_PER_USER,
                max_active_tasks_global=MAX_ACTIVE_TASKS_GLOBAL,
            )
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

        task_store.synchronize_history(queued_task)
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

            file_path = Path(task["input_path"])
            output_dir = Path(task["output_dir"])
            original_filename = task["original_filename"]
            if not task_store.mark_processing(task_id, "Loading user settings..."):
                _cleanup_translation_artifacts(task, user_dir)
                return

        try:
            task_snapshot = json.loads(task.get("settings_json") or "{}")
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Saved translation settings are invalid") from exc
        if task_snapshot and "user_settings" in task_snapshot:
            user_settings = task_snapshot["user_settings"]
            pages = task_snapshot.get("pages")
            allow_privileged_services = bool(
                task_snapshot.get("allow_privileged_services")
            )
        else:
            # Tasks created by an older database schema can still be inspected;
            # they are not expected to resume after a restart.
            async with _user_lifecycle_guard(username):
                user_settings = _read_settings_file(user_dir / "settings.json")
            pages = None
            allow_privileged_services = False
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
            completed_task = task_store.get_task(task_id, username=username)
            if completed_task:
                task_store.synchronize_history(completed_task)
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
                cancelled_task = task_store.get_task(task_id, username=username)
                if cancelled_task:
                    task_store.synchronize_history(cancelled_task)
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
                failed_task = task_store.get_task(task_id, username=username)
                if failed_task:
                    task_store.synchronize_history(failed_task)
        except HTTPException:
            # Account deletion owns cleanup after it marks the account as deleting.
            pass
    finally:
        active_tasks.pop(task_id, None)


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
    task_id: str, current_user: dict = Depends(get_current_user)
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
        _cleanup_translation_artifacts(task, user_dir)
        deleted_task = task_store.delete_task(task_id, username)
        if deleted_task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        task_store.remove_from_history(username, task_id)
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
