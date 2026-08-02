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

    client = TestClient(web_api_module.app)

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
        raise AssertionError(f"translation task not completed, latest status={task}")

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


def test_username_cannot_escape_data_directory(tmp_path, monkeypatch):
    web_api_module = load_web_api_module(tmp_path, monkeypatch)
    client = TestClient(web_api_module.app)

    response = client.post(
        "/api/auth/setup",
        json={"username": "../outside", "password": "secret123"},
    )

    assert response.status_code == 400
    assert not (tmp_path / "outside").exists()
