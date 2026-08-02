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
