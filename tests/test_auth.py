import sqlite3

from gbabeldocui.auth import UserManager


def test_deleted_user_token_is_invalidated(tmp_path):
    manager = UserManager(tmp_path / "data" / "users.db")
    manager.create_user("admin", "secret123", is_admin=True)
    manager.create_user("worker", "secret123")

    token = manager.authenticate("worker", "secret123")
    assert token

    manager.delete_user("worker", "admin")

    assert manager.validate_token(token) is None
    with sqlite3.connect(manager.db_path) as connection:
        session_count = connection.execute(
            "SELECT COUNT(*) FROM sessions WHERE username = ?",
            ("worker",),
        ).fetchone()[0]
    assert session_count == 0


def test_custom_database_path_owns_user_files(tmp_path):
    database_path = tmp_path / "custom" / "users.db"
    manager = UserManager(database_path)
    manager.create_user("admin", "secret123", is_admin=True)

    assert (database_path.parent / "users" / "admin").is_dir()
    assert not (tmp_path / "data" / "users" / "admin").exists()


def test_new_user_does_not_reuse_case_insensitive_orphan_directory(tmp_path):
    database_path = tmp_path / "data" / "users.db"
    orphan_directory = database_path.parent / "users" / "Alice"
    orphan_directory.mkdir(parents=True)
    (orphan_directory / "private.txt").write_text("keep", encoding="utf-8")

    manager = UserManager(database_path)

    try:
        manager.create_user("alice", "secret123")
    except ValueError as exc:
        assert "data directory already exists" in str(exc)
    else:
        raise AssertionError("an orphan user directory must not be reused")

    assert (orphan_directory / "private.txt").read_text(encoding="utf-8") == "keep"


def test_initial_admin_does_not_reuse_case_insensitive_orphan_directory(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("GBABELDOCUI_DATA_DIR", str(tmp_path / "data"))

    import importlib

    import gbabeldocui.auth as auth_module
    import gbabeldocui.web_api as web_api_module

    auth_module = importlib.reload(auth_module)
    web_api_module = importlib.reload(web_api_module)
    orphan_directory = tmp_path / "data" / "users" / "Alice"
    orphan_directory.mkdir(parents=True)
    (orphan_directory / "private.txt").write_text("keep", encoding="utf-8")

    from fastapi.testclient import TestClient

    response = TestClient(web_api_module.app).post(
        "/api/auth/setup",
        json={"username": "alice", "password": "secret123"},
    )

    assert response.status_code == 400
    assert (orphan_directory / "private.txt").read_text(encoding="utf-8") == "keep"
