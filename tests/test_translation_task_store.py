import json
import sqlite3
from datetime import datetime
from datetime import timedelta

import pytest
from gbabeldocui.auth import UserManager
from gbabeldocui.translation_task_store import TranslationTaskStore


def create_store(tmp_path):
    database_path = tmp_path / "data" / "users.db"
    manager = UserManager(database_path)
    manager.create_user("alice", "secret123")
    return manager, TranslationTaskStore(database_path)


def create_task_files(manager, task_id="00000000-0000-4000-8000-000000000001"):
    user_dir = manager.get_user_dir("alice")
    input_path = user_dir / "uploads" / "file-id_document.pdf"
    input_path.write_bytes(b"%PDF-1.4\n%%EOF\n")
    output_dir = user_dir / "outputs" / task_id
    output_dir.mkdir(parents=True)
    return input_path, output_dir


def test_task_paths_are_stored_relative_and_materialized_safely(tmp_path):
    manager, store = create_store(tmp_path)
    task_id = "00000000-0000-4000-8000-000000000001"
    input_path, output_dir = create_task_files(manager, task_id)

    created_task = store.create_task(
        task_id=task_id,
        username="alice",
        file_id="file-id",
        filename="document.pdf",
        input_path=input_path,
        output_dir=output_dir,
        settings_snapshot={"pages": "1"},
    )

    assert created_task["input_path"] == str(input_path.resolve())
    assert created_task["output_dir"] == str(output_dir.resolve())
    with sqlite3.connect(store.db_path) as connection:
        stored_input, stored_output = connection.execute(
            "SELECT input_path, output_dir FROM translation_tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
    assert stored_input == "users/alice/uploads/file-id_document.pdf"
    assert stored_output == f"users/alice/outputs/{task_id}"


def test_task_snapshot_rejects_non_finite_numbers(tmp_path):
    manager, store = create_store(tmp_path)
    input_path, output_dir = create_task_files(manager)

    with pytest.raises(ValueError, match="JSON values"):
        store.create_task(
            task_id="00000000-0000-4000-8000-000000000001",
            username="alice",
            file_id="file-id",
            filename="document.pdf",
            input_path=input_path,
            output_dir=output_dir,
            settings_snapshot={"temperature": float("nan")},
        )


def test_legacy_history_is_imported_once_without_rewriting_the_file(tmp_path):
    manager, store = create_store(tmp_path)
    user_dir = manager.get_user_dir("alice")
    task_id = "00000000-0000-4000-8000-000000000002"
    history_file = user_dir / "history.json"
    legacy_history = [
        {
            "task_id": task_id,
            "file_id": "legacy-file",
            "filename": "legacy.pdf",
            "status": "completed",
            "created_at": "2026-01-01T00:00:00",
            "completed_at": "2026-01-01T00:05:00",
        }
    ]
    original_contents = json.dumps(legacy_history, ensure_ascii=False)
    history_file.write_text(original_contents, encoding="utf-8")

    tasks = store.list_tasks("alice", limit=10, offset=0)

    assert [task["task_id"] for task in tasks] == [task_id]
    assert history_file.read_text(encoding="utf-8") == original_contents
    with sqlite3.connect(store.db_path) as connection:
        import_status = connection.execute(
            "SELECT status, error_summary FROM translation_history_imports "
            "WHERE username = 'alice'"
        ).fetchone()
    assert import_status == ("success", None)


def test_invalid_legacy_history_records_failure_and_is_not_retried(tmp_path):
    manager, store = create_store(tmp_path)
    history_file = manager.get_user_dir("alice") / "history.json"
    history_file.write_text("{invalid", encoding="utf-8")

    assert store.list_tasks("alice", limit=10, offset=0) == []
    history_file.write_text(
        '[{"task_id":"00000000-0000-4000-8000-000000000003"}]',
        encoding="utf-8",
    )
    assert store.list_tasks("alice", limit=10, offset=0) == []

    with sqlite3.connect(store.db_path) as connection:
        import_status = connection.execute(
            "SELECT status, error_summary FROM translation_history_imports "
            "WHERE username = 'alice'"
        ).fetchone()
    assert import_status[0] == "failed"
    assert import_status[1]


def test_retention_cleanup_lists_only_expired_terminal_tasks(tmp_path):
    manager, store = create_store(tmp_path)
    terminal_task_id = "00000000-0000-4000-8000-000000000004"
    active_task_id = "00000000-0000-4000-8000-000000000005"
    terminal_input, terminal_output = create_task_files(manager, terminal_task_id)
    active_input = manager.get_user_dir("alice") / "uploads" / "active_document.pdf"
    active_input.write_bytes(b"%PDF-1.4\n%%EOF\n")
    active_output = manager.get_user_dir("alice") / "outputs" / active_task_id
    active_output.mkdir(parents=True)

    store.create_task(
        task_id=terminal_task_id,
        username="alice",
        file_id="terminal-file",
        filename="terminal.pdf",
        input_path=terminal_input,
        output_dir=terminal_output,
    )
    store.mark_processing(terminal_task_id, "processing")
    result_pdf = terminal_output / "terminal_mono.pdf"
    result_pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")
    store.mark_completed(terminal_task_id, result_pdf, None)
    store.create_task(
        task_id=active_task_id,
        username="alice",
        file_id="active-file",
        filename="active.pdf",
        input_path=active_input,
        output_dir=active_output,
    )

    expired_tasks = store.list_expired_terminal_tasks(
        completed_before=datetime.now() + timedelta(days=1)
    )

    assert [task["task_id"] for task in expired_tasks] == [terminal_task_id]
    assert store.get_task(terminal_task_id) is not None
    assert store.get_task(active_task_id) is not None
    assert store.delete_task(active_task_id, "alice") is None

    assert store.delete_expired_terminal_task(
        terminal_task_id, completed_before=datetime.now() + timedelta(days=1)
    )
    assert store.get_task(terminal_task_id) is None


def test_legacy_external_paths_are_not_materialized(tmp_path):
    manager, store = create_store(tmp_path)
    input_path, output_dir = create_task_files(manager)
    task_id = "00000000-0000-4000-8000-000000000001"
    store.create_task(
        task_id=task_id,
        username="alice",
        file_id="file-id",
        filename="document.pdf",
        input_path=input_path,
        output_dir=output_dir,
    )
    external_path = (tmp_path / "outside.pdf").resolve()
    with sqlite3.connect(store.db_path) as connection:
        connection.execute(
            "UPDATE translation_tasks SET mono_path = ? WHERE task_id = ?",
            (str(external_path), task_id),
        )

    assert store.get_task(task_id)["mono_path"] is None
