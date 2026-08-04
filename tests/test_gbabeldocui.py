import importlib
import sys
import time
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

SAMPLE_PDF_BYTES = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_web_api_module(tmp_path, monkeypatch):
    monkeypatch.setenv("GBABELDOCUI_DATA_DIR", str(tmp_path / "data"))

    import gbabeldocui.auth as auth_module
    import gbabeldocui.web_api as web_api_module

    auth_module = importlib.reload(auth_module)
    web_api_module = importlib.reload(web_api_module)
    web_api_module.active_tasks.clear()
    return web_api_module


def setup_admin_headers(client):
    response = client.post(
        "/api/auth/setup",
        json={"username": "admin", "password": "secret123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_build_settings_model_uses_official_pdf2zh_next(tmp_path, monkeypatch):
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
        web_api_module._resolve_translation_pages({}, {"page_range": "first5"}) == "1-5"
    )
    assert (
        web_api_module._resolve_translation_pages(
            {}, {"page_range": "custom", "custom_pages": "2,4-5"}
        )
        == "2,4-5"
    )
    assert (
        web_api_module._resolve_translation_pages(
            {"pages": "all"}, {"page_range": "first"}
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

        setup_resp = client.post(
            "/api/auth/setup",
            json={"username": "admin", "password": "secret123"},
        )
        assert setup_resp.status_code == 200
        token = setup_resp.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

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


def test_registration_toggle_requires_boolean_and_bearer_is_case_insensitive(
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

    lowercase_scheme_response = client.get(
        "/api/settings",
        headers={"Authorization": headers["Authorization"].replace("Bearer", "bearer")},
    )
    assert lowercase_scheme_response.status_code == 200


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

    worker_token = web_api_module.user_manager.authenticate("worker", "secret123")
    assert worker_token
    worker_headers = {"Authorization": f"Bearer {worker_token}"}

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

    worker_token = web_api_module.user_manager.authenticate("worker", "secret123")
    assert worker_token
    worker_headers = {"Authorization": f"Bearer {worker_token}"}

    worker_response = client.post(
        "/api/settings",
        json={"service": "Ollama"},
        headers=worker_headers,
    )
    assert worker_response.status_code == 403

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

    response = client.post(
        "/api/auth/setup",
        json={"username": "../outside", "password": "secret123"},
    )

    assert response.status_code == 400
    assert not (tmp_path / "outside").exists()
