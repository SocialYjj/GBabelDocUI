import asyncio
import importlib
import ipaddress
import json
import os
import socket
import sqlite3
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import fitz
import pytest
from fastapi.testclient import TestClient
from filelock import FileLock


def create_sample_pdf_bytes(page_count=1):
    document = fitz.open()
    try:
        for _ in range(page_count):
            document.new_page()
        return document.tobytes()
    finally:
        document.close()


SAMPLE_PDF_BYTES = create_sample_pdf_bytes()
BOOTSTRAP_VALUE = "test-setup-token"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_web_api_module(tmp_path, monkeypatch):
    monkeypatch.setenv("GBABELDOCUI_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("GBABELDOCUI_COOKIE_SECURE", "false")
    monkeypatch.setenv("GBABELDOCUI_SETUP_TOKEN", BOOTSTRAP_VALUE)

    import gbabeldocui.auth as auth_module
    import gbabeldocui.web_api as web_api_module

    auth_module = importlib.reload(auth_module)
    web_api_module = importlib.reload(web_api_module)
    web_api_module.active_tasks.clear()
    return web_api_module


def setup_admin_headers(client):
    status_response = client.get("/api/auth/status")
    assert status_response.status_code == 200
    csrf_token = client.cookies.get("gbabeldocui_csrf")
    assert csrf_token
    response = client.post(
        "/api/auth/setup",
        json={
            "username": "admin",
            "password": "secret123",
            "setup_token": BOOTSTRAP_VALUE,
        },
        headers={"X-CSRF-Token": csrf_token},
    )
    assert response.status_code == 200
    assert "token" not in response.json()
    return {"X-CSRF-Token": csrf_token}


def login_headers(client, username, password):
    csrf_token = client.cookies.get("gbabeldocui_csrf")
    assert csrf_token
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert response.status_code == 200
    assert "token" not in response.json()
    return {"X-CSRF-Token": csrf_token}


def test_build_settings_model_uses_bundled_verified_runtime(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)

    settings = web_api_module.build_settings_model_from_user_config(
        {
            "service": "OpenAI",
            "openai_model": "gpt-4o-mini",
            "openai_api_key": "test-key",
            "openai_base_url": "https://api.openai.com/v1",
            "term_service": "same",
            "enable_term_extraction": True,
            "lang_from": "en",
            "lang_to": "zh",
        },
        tmp_path / "output",
        pages="1-2",
    )

    assert settings.translate_engine_settings.translate_engine_type == "OpenAI"
    assert settings.term_extraction_engine_settings.translate_engine_type == "OpenAI"
    assert settings.translation.output == str(tmp_path / "output")
    assert settings.pdf.pages == "1-2"
    settings.validate_settings()


def test_ollama_empty_host_uses_server_default(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)

    settings = web_api_module.build_settings_model_from_user_config(
        {
            "service": "Ollama",
            "ollama_host": "",
            "ollama_model": "gemma2",
            "lang_from": "en",
            "lang_to": "zh",
        },
        tmp_path / "output",
        allow_privileged_services=True,
    )

    assert settings.translate_engine_settings.ollama_host == "http://127.0.0.1:11434"


def test_translation_pages_use_saved_preference_when_request_is_not_explicit(
    tmp_path, monkeypatch
):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)

    assert (
        web_api_module._resolve_translation_pages(
            {}, {"page_range": "first5"}, page_count=4
        )
        == "1-4"
    )
    assert (
        web_api_module._resolve_translation_pages(
            {}, {"page_range": "custom", "custom_pages": "2,4-5"}, page_count=5
        )
        == "2,4-5"
    )
    assert (
        web_api_module._resolve_translation_pages(
            {"pages": "all"}, {"page_range": "first"}, page_count=1
        )
        is None
    )


def test_web_flow_with_mocked_translation(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)

    async def fake_translate(settings, file_path):
        output_dir = Path(settings.translation.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        mono_path = output_dir / "fake_mono.pdf"
        mono_path.write_bytes(SAMPLE_PDF_BYTES)
        yield {
            "type": "progress_update",
            "stage": "Mock",
            "overall_progress": 55,
            "part_index": 1,
            "total_parts": 1,
            "stage_current": 1,
            "stage_total": 1,
        }
        yield {
            "type": "finish",
            "translate_result": SimpleNamespace(
                mono_pdf_path=mono_path,
                dual_pdf_path=None,
                total_seconds=0.1,
                original_pdf_path=Path(file_path),
            ),
            "token_usage": {},
        }

    monkeypatch.setattr(web_api_module, "do_translate_async_stream", fake_translate)

    with TestClient(web_api_module.app) as client:
        status_resp = client.get("/api/auth/status")
        assert status_resp.status_code == 200
        assert status_resp.json()["setup_required"] is True

        headers = setup_admin_headers(client)

        settings_payload = {
            "service": "OpenAI",
            "openai_model": "gpt-4o-mini",
            "openai_api_key": "test-key",
            "openai_base_url": "https://api.openai.com/v1",
            "lang_from": "en",
            "lang_to": "zh",
            "term_service": "same",
        }
        save_resp = client.post("/api/settings", json=settings_payload, headers=headers)
        assert save_resp.status_code == 200

        upload_resp = client.post(
            "/api/upload",
            files={"file": ("sample.pdf", SAMPLE_PDF_BYTES, "application/pdf")},
            headers=headers,
        )
        assert upload_resp.status_code == 200
        file_id = upload_resp.json()["file_id"]

        translate_resp = client.post(
            "/api/translate",
            data={"file_id": file_id, "settings": '{"pages":"1"}'},
            headers=headers,
        )
        assert translate_resp.status_code == 200
        task_id = translate_resp.json()["task_id"]

        with sqlite3.connect(web_api_module.task_store.db_path) as connection:
            settings_json = connection.execute(
                "SELECT settings_json FROM translation_tasks WHERE task_id = ?",
                (task_id,),
            ).fetchone()[0]
        persistent_settings = json.loads(settings_json)
        assert "openai_api_key" not in persistent_settings["user_settings"]
        assert "test-key" not in settings_json

        for _ in range(20):
            task_resp = client.get(f"/api/translate/status/{task_id}", headers=headers)
            assert task_resp.status_code == 200
            task = task_resp.json()["task"]
            if task["status"] == "completed":
                break
            time.sleep(0.1)
        else:
            raise AssertionError(
                f"translation task not completed, latest status={task}"
            )

        history_resp = client.get("/api/translate/history", headers=headers)
        assert history_resp.status_code == 200
        history = history_resp.json()["history"]
        assert len(history) == 1
        assert history[0]["status"] == "completed"

        download_resp = client.get(
            f"/api/translate/download/{task_id}?file_type=mono",
            headers=headers,
        )
        assert download_resp.status_code == 200
        assert download_resp.content.startswith(b"%PDF")


def test_upload_filename_is_confined_to_user_upload_directory(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    client = TestClient(web_api_module.app)
    headers = setup_admin_headers(client)

    response = client.post(
        "/api/upload",
        files={"file": ("../../outside.pdf", SAMPLE_PDF_BYTES, "application/pdf")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "outside.pdf"
    assert "file_path" not in response.json()
    upload_dir = tmp_path / "data" / "users" / "admin" / "uploads"
    uploaded_files = list(upload_dir.iterdir())
    assert len(uploaded_files) == 1
    assert uploaded_files[0].parent == upload_dir
    assert not (tmp_path / "data" / "users" / "outside.pdf").exists()


def test_upload_size_limit_removes_partial_file(tmp_path, monkeypatch):
    monkeypatch.setenv("GBABELDOCUI_MAX_UPLOAD_BYTES", "8")
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    client = TestClient(web_api_module.app)
    headers = setup_admin_headers(client)

    response = client.post(
        "/api/upload",
        files={"file": ("sample.pdf", SAMPLE_PDF_BYTES, "application/pdf")},
        headers=headers,
    )

    assert response.status_code == 413
    upload_dir = tmp_path / "data" / "users" / "admin" / "uploads"
    assert list(upload_dir.iterdir()) == []


def test_cancelled_upload_removes_partial_file(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    file_path = tmp_path / "partial.pdf"

    class CancelledUpload:
        def __init__(self):
            self.read_count = 0

        async def read(self, _chunk_size):
            self.read_count += 1
            if self.read_count == 1:
                return b"partial"
            raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(web_api_module._save_uploaded_file(CancelledUpload(), file_path))

    assert not file_path.exists()


def test_failed_translation_start_removes_unattached_upload(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    client = TestClient(web_api_module.app)
    headers = setup_admin_headers(client)

    upload_response = client.post(
        "/api/upload",
        files={"file": ("sample.pdf", SAMPLE_PDF_BYTES, "application/pdf")},
        headers=headers,
    )
    assert upload_response.status_code == 200
    file_id = upload_response.json()["file_id"]

    failed_response = client.post(
        "/api/translate",
        data={"file_id": file_id, "settings": '{"pages":"invalid"}'},
        headers=headers,
    )

    assert failed_response.status_code == 400
    upload_dir = tmp_path / "data" / "users" / "admin" / "uploads"
    assert list(upload_dir.iterdir()) == []


def test_orphan_upload_cleanup_preserves_referenced_files(tmp_path, monkeypatch):
    monkeypatch.setenv("GBABELDOCUI_ORPHAN_UPLOAD_TTL_SECONDS", "1")
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    client = TestClient(web_api_module.app)
    headers = setup_admin_headers(client)

    upload_response = client.post(
        "/api/upload",
        files={"file": ("sample.pdf", SAMPLE_PDF_BYTES, "application/pdf")},
        headers=headers,
    )
    assert upload_response.status_code == 200
    upload_dir = tmp_path / "data" / "users" / "admin" / "uploads"
    uploaded_path = next(upload_dir.iterdir())
    old_timestamp = time.time() - 10
    import os

    os.utime(uploaded_path, (old_timestamp, old_timestamp))

    assert web_api_module._cleanup_orphaned_uploaded_files() == 1
    assert not uploaded_path.exists()

    referenced_upload_response = client.post(
        "/api/upload",
        files={"file": ("referenced.pdf", SAMPLE_PDF_BYTES, "application/pdf")},
        headers=headers,
    )
    referenced_file_id = referenced_upload_response.json()["file_id"]
    referenced_path = next(
        path for path in upload_dir.iterdir() if referenced_file_id in path.name
    )
    os.utime(referenced_path, (old_timestamp, old_timestamp))
    web_api_module.task_store.create_task(
        task_id="00000000-0000-4000-8000-000000000001",
        username="admin",
        file_id=referenced_file_id,
        filename="referenced.pdf",
        input_path=referenced_path,
        output_dir=tmp_path / "data" / "users" / "admin" / "outputs" / "referenced",
        settings_snapshot={},
    )

    assert web_api_module._cleanup_orphaned_uploaded_files() == 0
    assert referenced_path.exists()


def test_registration_toggle_requires_boolean_and_authorization_header_is_ignored(
    tmp_path, monkeypatch
):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    client = TestClient(web_api_module.app)
    headers = setup_admin_headers(client)

    invalid_response = client.post(
        "/api/auth/registration-toggle",
        json={"enabled": "false"},
        headers=headers,
    )
    assert invalid_response.status_code == 422

    enabled_response = client.post(
        "/api/auth/registration-toggle",
        json={"enabled": True},
        headers=headers,
    )
    assert enabled_response.status_code == 200

    bearer_token = web_api_module.user_manager.authenticate("admin", "secret123")
    assert bearer_token
    client.cookies.delete(web_api_module.SESSION_COOKIE_NAME)
    authorization_header_response = client.get(
        "/api/settings",
        headers={"Authorization": f"Bearer {bearer_token}"},
    )
    assert authorization_header_response.status_code == 401


def test_regular_user_can_save_settings_with_empty_privileged_endpoints(
    tmp_path, monkeypatch
):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    client = TestClient(web_api_module.app)
    admin_headers = setup_admin_headers(client)

    create_user_response = client.post(
        "/api/auth/register",
        json={"username": "worker", "password": "secret123"},
        headers=admin_headers,
    )
    assert create_user_response.status_code == 200

    worker_headers = login_headers(client, "worker", "secret123")

    response = client.post(
        "/api/settings",
        json={
            "service": "SiliconFlowFree",
            "lang_from": "en",
            "lang_to": "zh",
            "rpc_doclayout": "",
        },
        headers=worker_headers,
    )

    assert response.status_code == 200


def test_regular_user_cannot_select_server_owned_translation_service(
    tmp_path, monkeypatch
):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    client = TestClient(web_api_module.app)
    admin_headers = setup_admin_headers(client)

    create_user_response = client.post(
        "/api/auth/register",
        json={"username": "worker", "password": "secret123"},
        headers=admin_headers,
    )
    assert create_user_response.status_code == 200

    worker_headers = login_headers(client, "worker", "secret123")

    worker_response = client.post(
        "/api/settings",
        json={"service": "Ollama"},
        headers=worker_headers,
    )
    assert worker_response.status_code == 403

    admin_headers = login_headers(client, "admin", "secret123")
    admin_response = client.post(
        "/api/settings",
        json={"service": "Ollama"},
        headers=admin_headers,
    )
    assert admin_response.status_code == 200


def test_translation_output_quota_removes_oversized_result(tmp_path, monkeypatch):
    monkeypatch.setenv("GBABELDOCUI_MAX_USER_STORAGE_BYTES", "1024")
    web_api_module = load_web_api_module(tmp_path, monkeypatch)

    async def fake_translate(settings, file_path):
        output_dir = Path(settings.translation.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        mono_path = output_dir / "fake_mono.pdf"
        mono_path.write_bytes(SAMPLE_PDF_BYTES * 100)
        yield {
            "type": "finish",
            "translate_result": SimpleNamespace(
                mono_pdf_path=mono_path,
                dual_pdf_path=None,
                total_seconds=0.1,
                original_pdf_path=Path(file_path),
            ),
            "token_usage": {},
        }

    monkeypatch.setattr(web_api_module, "do_translate_async_stream", fake_translate)
    with TestClient(web_api_module.app) as client:
        headers = setup_admin_headers(client)

        upload_response = client.post(
            "/api/upload",
            files={"file": ("sample.pdf", SAMPLE_PDF_BYTES, "application/pdf")},
            headers=headers,
        )
        assert upload_response.status_code == 200

        translate_response = client.post(
            "/api/translate",
            data={"file_id": upload_response.json()["file_id"], "settings": "{}"},
            headers=headers,
        )
        assert translate_response.status_code == 200
        task_id = translate_response.json()["task_id"]

        for _ in range(20):
            status_response = client.get(
                f"/api/translate/status/{task_id}", headers=headers
            )
            assert status_response.status_code == 200
            task = status_response.json()["task"]
            if task["status"] == "failed":
                break
            time.sleep(0.1)
        else:
            raise AssertionError(f"translation task did not fail, latest status={task}")

        assert "quota" in task["error"].lower()
        output_dir = tmp_path / "data" / "users" / "admin" / "outputs" / task_id
        assert not output_dir.exists()
        assert list((tmp_path / "data" / "users" / "admin" / "uploads").iterdir()) == []


def test_invalid_setting_types_return_client_errors(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    client = TestClient(web_api_module.app)
    headers = setup_admin_headers(client)

    invalid_page_range = client.post(
        "/api/settings", json={"page_range": []}, headers=headers
    )
    invalid_watermark_mode = client.post(
        "/api/settings", json={"watermark_mode": {}}, headers=headers
    )

    assert invalid_page_range.status_code == 400
    assert invalid_watermark_mode.status_code == 400


def test_username_cannot_escape_data_directory(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    client = TestClient(web_api_module.app)
    assert client.get("/api/auth/status").status_code == 200
    csrf_token = client.cookies.get("gbabeldocui_csrf")
    assert csrf_token

    response = client.post(
        "/api/auth/setup",
        json={
            "username": "../outside",
            "password": "secret123",
            "setup_token": BOOTSTRAP_VALUE,
        },
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 400
    assert not (tmp_path / "outside").exists()


def test_session_cookie_is_http_only_secure_and_same_site_strict(tmp_path, monkeypatch):
    monkeypatch.setenv("GBABELDOCUI_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("GBABELDOCUI_COOKIE_SECURE", "true")
    monkeypatch.setenv("GBABELDOCUI_SETUP_TOKEN", BOOTSTRAP_VALUE)

    import gbabeldocui.auth as auth_module
    import gbabeldocui.web_api as web_api_module

    importlib.reload(auth_module)
    web_api_module = importlib.reload(web_api_module)
    with TestClient(web_api_module.app, base_url="https://testserver") as client:
        status_response = client.get("/api/auth/status")
        csrf_cookie = client.cookies.get(web_api_module.CSRF_COOKIE_NAME)
        assert csrf_cookie
        csrf_set_cookie = status_response.headers.get("set-cookie", "").lower()
        assert "secure" in csrf_set_cookie
        assert "samesite=strict" in csrf_set_cookie
        assert "httponly" not in csrf_set_cookie

        setup_response = client.post(
            "/api/auth/setup",
            json={
                "username": "admin",
                "password": "secret123",
                "setup_token": BOOTSTRAP_VALUE,
            },
            headers={"X-CSRF-Token": csrf_cookie},
        )

    assert setup_response.status_code == 200
    session_cookie = setup_response.headers.get("set-cookie", "").lower()
    assert "gbabeldocui_session=" in session_cookie
    assert "httponly" in session_cookie
    assert "secure" in session_cookie
    assert "samesite=strict" in session_cookie
    assert "token" not in setup_response.json()


def test_mutating_request_without_csrf_is_rejected_before_body_use(
    tmp_path, monkeypatch
):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    client = TestClient(web_api_module.app)

    response = client.post(
        "/api/auth/login",
        content="{" + ("x" * 1000),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 403


def test_streaming_request_without_content_length_is_limited(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    with TestClient(web_api_module.app) as client:
        assert client.get("/api/auth/status").status_code == 200
        csrf_token = client.cookies.get(web_api_module.CSRF_COOKIE_NAME)
        assert csrf_token

        def oversized_body():
            yield b'{"username":"admin","password":"'
            yield b"x" * (web_api_module.MAX_JSON_BODY_BYTES + 1)
            yield b'"}'

        response = client.post(
            "/api/auth/login",
            content=oversized_body(),
            headers={
                web_api_module.CSRF_HEADER_NAME: csrf_token,
                "Content-Type": "application/json",
            },
        )

    assert response.status_code == 413
    assert response.json()["detail"] == "Request body is too large"


def test_settings_reject_non_finite_json_numbers(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    client = TestClient(web_api_module.app)
    headers = setup_admin_headers(client)

    response = client.post(
        "/api/settings",
        content='{"split_factor":NaN}',
        headers={**headers, "Content-Type": "application/json"},
    )

    assert response.status_code == 400


def test_settings_response_omits_saved_credentials_and_blank_keeps_them(
    tmp_path, monkeypatch
):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    client = TestClient(web_api_module.app)
    headers = setup_admin_headers(client)
    save_response = client.post(
        "/api/settings",
        json={
            "service": "OpenAI",
            "openai_api_key": "configured-key",
            "openai_model": "gpt-4o-mini",
        },
        headers=headers,
    )
    assert save_response.status_code == 200

    settings_response = client.get("/api/settings")
    assert settings_response.status_code == 200
    payload = settings_response.json()
    assert "openai_api_key" not in payload["settings"]
    assert "openai_api_key" in payload["configured_credentials"]

    blank_save = client.post(
        "/api/settings",
        json={"openai_api_key": ""},
        headers=headers,
    )
    assert blank_save.status_code == 200
    settings_file = tmp_path / "data" / "users" / "admin" / "settings.json"
    assert "configured-key" in settings_file.read_text(encoding="utf-8")


def test_page_range_and_max_part_boundaries(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)

    assert web_api_module._parse_page_range("1,3-4", 4) == "1,3-4"
    for invalid_range in ("0", "4-3", "1-2,2", "5"):
        try:
            web_api_module._parse_page_range(invalid_range, 4)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid range accepted: {invalid_range}")

    for invalid_maximum in range(1, 50):
        try:
            web_api_module._validate_saved_setting_values(
                {"max_pages_per_part": invalid_maximum}
            )
        except ValueError:
            continue
        raise AssertionError(f"invalid maximum accepted: {invalid_maximum}")


def test_endpoint_validation_uses_resolved_address_classification(
    tmp_path, monkeypatch
):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)

    monkeypatch.setattr(
        web_api_module.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )
    assert (
        web_api_module._validate_endpoint_url(
            "https://translator.example/v1", "openai_base_url"
        )
        == "https://translator.example/v1"
    )

    monkeypatch.setattr(
        web_api_module.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
        ],
    )
    try:
        web_api_module._validate_endpoint_url(
            "https://translator.example/v1", "openai_base_url"
        )
    except ValueError:
        pass
    else:
        raise AssertionError("non-public resolved endpoint was accepted")

    assert ipaddress.ip_address("93.184.216.34").is_global


def test_formula_patterns_reject_unsupported_or_unbounded_syntax(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)

    assert (
        web_api_module._validate_safe_formula_pattern(
            "CMMI|CMR", "formula_font_pattern"
        )
        == "CMMI|CMR"
    )
    for invalid_pattern in ("a+", "(a+)+", "(.)\\1", "x" * 257):
        try:
            web_api_module._validate_safe_formula_pattern(
                invalid_pattern, "formula_font_pattern"
            )
        except ValueError:
            continue
        raise AssertionError(f"unsupported pattern accepted: {invalid_pattern[:20]}")


def test_formula_font_cache_is_bounded(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    from babeldoc.format.pdf.document_il.utils import formular_helper

    original_matcher = formular_helper.is_formulas_font
    try:
        formular_helper.is_formulas_font = lambda font_name, pattern: bool(
            font_name and pattern
        )
        web_api_module._configure_babeldoc_formula_cache()
        for index in range(5000):
            formular_helper.is_formulas_font(f"font-{index}", "formula")
        cache_info = formular_helper.is_formulas_font.cache_info()
        assert cache_info.maxsize == 4096
        assert cache_info.currsize == 4096
    finally:
        formular_helper.is_formulas_font = original_matcher


def test_retention_marker_preserves_initial_creation_time(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    assert web_api_module._retention_cleanup_is_ready() is False

    marker_path = web_api_module._retention_marker_path()
    expired_timestamp = (
        time.time() - (web_api_module.RETENTION_GRACE_DAYS + 1) * 24 * 60 * 60
    )
    os.utime(marker_path, (expired_timestamp, expired_timestamp))
    marker_mtime = marker_path.stat().st_mtime_ns

    assert web_api_module._retention_cleanup_is_ready() is True
    assert marker_path.stat().st_mtime_ns == marker_mtime


def test_retention_cleanup_keeps_record_when_file_cleanup_fails(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    with TestClient(web_api_module.app) as client:
        setup_admin_headers(client)

    user_dir = web_api_module.user_manager.get_user_dir("admin")
    input_path = user_dir / "uploads" / "retention.pdf"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(SAMPLE_PDF_BYTES)
    task_id = "00000000-0000-4000-8000-000000000099"
    output_dir = user_dir / "outputs" / task_id
    output_dir.mkdir(parents=True)
    output_path = output_dir / "retention_mono.pdf"
    output_path.write_bytes(SAMPLE_PDF_BYTES)
    web_api_module.task_store.create_task(
        task_id=task_id,
        username="admin",
        file_id="retention-file",
        filename="retention.pdf",
        input_path=input_path,
        output_dir=output_dir,
    )
    web_api_module.task_store.mark_processing(task_id, "processing")
    web_api_module.task_store.mark_completed(task_id, output_path, None)
    with sqlite3.connect(web_api_module.task_store.db_path) as connection:
        connection.execute(
            "UPDATE translation_tasks SET completed_at = ? WHERE task_id = ?",
            ("2020-01-01T00:00:00", task_id),
        )

    monkeypatch.setattr(
        web_api_module, "_cleanup_translation_artifacts", lambda *_args: False
    )
    assert asyncio.run(web_api_module._cleanup_expired_terminal_tasks_once()) == 0
    assert web_api_module.task_store.get_task(task_id) is not None

    monkeypatch.setattr(
        web_api_module, "_cleanup_translation_artifacts", lambda *_args: True
    )
    assert asyncio.run(web_api_module._cleanup_expired_terminal_tasks_once()) == 1
    assert web_api_module.task_store.get_task(task_id) is None


def test_second_instance_for_same_data_directory_fails_fast(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    lock = FileLock(
        str(web_api_module.user_manager.data_dir / ".gbabeldocui-instance.lock"),
        timeout=0,
        thread_local=False,
    )
    lock.acquire()
    try:

        async def start_second_instance():
            async with web_api_module.application_lifespan(web_api_module.app):
                raise AssertionError("second instance unexpectedly started")

        with pytest.raises(RuntimeError, match="already owns this data directory"):
            asyncio.run(start_second_instance())
    finally:
        lock.release()
