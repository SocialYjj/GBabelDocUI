import sqlite3
from concurrent.futures import ThreadPoolExecutor

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
    monkeypatch.setenv("GBABELDOCUI_COOKIE_SECURE", "false")
    monkeypatch.setenv("GBABELDOCUI_SETUP_TOKEN", "test-setup-token")

    import importlib

    import gbabeldocui.auth as auth_module
    import gbabeldocui.web_api as web_api_module

    auth_module = importlib.reload(auth_module)
    web_api_module = importlib.reload(web_api_module)
    orphan_directory = tmp_path / "data" / "users" / "Alice"
    orphan_directory.mkdir(parents=True)
    (orphan_directory / "private.txt").write_text("keep", encoding="utf-8")

    from fastapi.testclient import TestClient

    client = TestClient(web_api_module.app)
    assert client.get("/api/auth/status").status_code == 200
    csrf_token = client.cookies.get("gbabeldocui_csrf")
    assert csrf_token
    response = client.post(
        "/api/auth/setup",
        json={
            "username": "alice",
            "password": "secret123",
            "setup_token": "test-setup-token",
        },
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 400
    assert (orphan_directory / "private.txt").read_text(encoding="utf-8") == "keep"


def test_password_change_invalidates_all_existing_sessions(tmp_path):
    manager = UserManager(tmp_path / "data" / "users.db")
    manager.create_user("alice", "secret123")
    first_token = manager.authenticate("alice", "secret123")
    second_token = manager.authenticate("alice", "secret123")
    assert first_token and second_token

    manager.change_password("alice", "secret123", "updated123")

    assert manager.validate_token(first_token) is None
    assert manager.validate_token(second_token) is None
    assert manager.authenticate("alice", "secret123") is None
    assert manager.authenticate("alice", "updated123")


def test_concurrent_old_password_logins_cannot_survive_password_change(tmp_path):
    manager = UserManager(tmp_path / "data" / "users.db")
    manager.create_user("alice", "secret123")

    with ThreadPoolExecutor(max_workers=8) as executor:
        login_futures = [
            executor.submit(manager.authenticate, "alice", "secret123")
            for _ in range(12)
        ]
        password_change = executor.submit(
            manager.change_password,
            "alice",
            "secret123",
            "updated123",
        )
        password_change.result()
        issued_tokens = [future.result() for future in login_futures]

    assert all(
        token is None or manager.validate_token(token) is None
        for token in issued_tokens
    )


def test_user_managers_keep_database_secrets_isolated(tmp_path):
    first_manager = UserManager(tmp_path / "first" / "users.db")
    first_manager.create_user("alice", "secret123")
    first_token = first_manager.authenticate("alice", "secret123")
    assert first_token

    second_manager = UserManager(tmp_path / "second" / "users.db")
    second_manager.create_user("bob", "secret123")

    assert first_manager.validate_token(first_token)
    assert second_manager.validate_token(first_token) is None


def test_session_count_is_bounded_per_user(tmp_path, monkeypatch):
    monkeypatch.setenv("GBABELDOCUI_MAX_SESSIONS_PER_USER", "3")
    manager = UserManager(tmp_path / "data" / "users.db")
    manager.create_user("alice", "secret123")

    tokens = [manager.authenticate("alice", "secret123") for _ in range(5)]

    assert all(tokens)
    with sqlite3.connect(manager.db_path) as connection:
        session_count = connection.execute(
            "SELECT COUNT(*) FROM sessions WHERE username = 'alice'"
        ).fetchone()[0]
    assert session_count == 3
    assert manager.validate_token(tokens[0]) is None
    assert manager.validate_token(tokens[-1])
