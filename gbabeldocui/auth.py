"""
Multi-user authentication system for PDFMathTranslate web UI.

This module provides:
- User registration and management
- Password hashing with bcrypt
- JWT-based session management
- User-specific configuration isolation
"""

import logging
import os
import re
import secrets
import shutil
import sqlite3
import threading
import time
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path

import bcrypt
import jwt
from filelock import FileLock

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = secrets.token_urlsafe(32)  # Will be generated on first run
TOKEN_EXPIRY_HOURS = 24
DATA_DIR = Path(os.getenv("GBABELDOCUI_DATA_DIR", "data"))
DB_PATH = DATA_DIR / "users.db"
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,63}$")


def _utc_now() -> datetime:
    """Return an aware UTC timestamp for correct JWT expiry calculations."""
    return datetime.now(timezone.utc)


def _database_timestamp(timestamp: datetime | None = None) -> str:
    """Serialize a UTC timestamp in the existing database format."""
    value = timestamp or _utc_now()
    return value.astimezone(timezone.utc).replace(tzinfo=None).isoformat()


def _parse_database_timestamp(value: str) -> datetime:
    """Parse both legacy naive-UTC and newer timezone-aware timestamps."""
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalize_username(username: str) -> str:
    """Validate and canonicalize a username before it reaches SQLite or a path."""
    if not isinstance(username, str):
        raise ValueError("Username must be a string")

    normalized_username = username.casefold()
    if not USERNAME_PATTERN.fullmatch(normalized_username):
        raise ValueError(
            "Username must be 3-64 characters and contain only letters, "
            "digits, '.', '_' or '-'; it must start with a letter or digit"
        )
    if normalized_username.endswith("."):
        raise ValueError("Username must not end with a period")

    reserved_name = normalized_username.split(".", 1)[0].upper()
    if reserved_name in {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{index}" for index in range(1, 10)),
        *(f"LPT{index}" for index in range(1, 10)),
    }:
        raise ValueError("This username is reserved by the operating system")
    return normalized_username


def _validate_password(password: str, field_name: str = "Password") -> None:
    """Validate the bcrypt-supported password boundary once at the API layer."""
    if not isinstance(password, str) or len(password) < 6:
        raise ValueError(f"{field_name} must be at least 6 characters long")
    if len(password.encode("utf-8")) > 72:
        raise ValueError(f"{field_name} must not exceed 72 UTF-8 bytes")


class AuthenticationError(Exception):
    """Raised when authentication fails"""

    pass


class UserManager:
    """Manages user authentication and database operations"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.data_dir = self.db_path.parent
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._session_cleanup_lock = threading.Lock()
        self._last_session_cleanup = 0.0
        self._init_database()
        self._load_or_create_secret()

    def _connect(self) -> sqlite3.Connection:
        """Open a database connection with the required integrity settings."""
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _account_mutation_lock(self, normalized_username: str) -> FileLock:
        """Serialize account creation and deletion with filesystem cleanup."""
        lock_directory = self.data_dir / "users" / ".locks"
        lock_directory.mkdir(parents=True, exist_ok=True)
        return FileLock(
            str(lock_directory / f"account-{normalized_username}.lock"),
            timeout=30,
            thread_local=False,
        )

    def _init_database(self):
        """Initialize the SQLite database with required tables"""
        conn = self._connect()
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                last_login TEXT
            )
        """)

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
            )
        """)

        # User configs table (for storing user-specific settings)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                config_key TEXT NOT NULL,
                config_value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(username, config_key),
                FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
            )
        """)

        # App config table (for storing app-level settings like secret key)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions (expires_at)"
        )

        conn.commit()
        conn.close()

    def _load_or_create_secret(self):
        """Load existing secret key or create a new one"""
        global SECRET_KEY
        conn = self._connect()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT value FROM app_config WHERE key = 'secret_key'")
            result = cursor.fetchone()

            if not result:
                cursor.execute(
                    "INSERT OR IGNORE INTO app_config (key, value) VALUES ('secret_key', ?)",
                    (secrets.token_urlsafe(32),),
                )
                result = cursor.execute(
                    "SELECT value FROM app_config WHERE key = 'secret_key'"
                ).fetchone()
                if not result:
                    raise RuntimeError("Failed to initialize the application secret")
                conn.commit()

            SECRET_KEY = result[0]
        finally:
            conn.close()

    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except (ValueError, TypeError, UnicodeEncodeError):
            return False

    def has_users(self) -> bool:
        """Check if any users exist in the database"""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def user_exists(self, username: str) -> bool:
        """Return whether an account still exists, using the same username rules."""
        try:
            normalized_username = _normalize_username(username)
        except ValueError:
            return False
        conn = self._connect()
        try:
            return (
                conn.execute(
                    "SELECT 1 FROM users WHERE username = ? COLLATE NOCASE",
                    (normalized_username,),
                ).fetchone()
                is not None
            )
        finally:
            conn.close()

    def count_users(self) -> int:
        """Return the current account count for registration quotas."""
        conn = self._connect()
        try:
            return int(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0])
        finally:
            conn.close()

    def create_initial_admin(self, username: str, password: str) -> bool:
        """Atomically create the only administrator during first-time setup."""
        normalized_username = _normalize_username(username)
        _validate_password(password)
        conn = self._connect()
        cursor = conn.cursor()
        user_dir = self.data_dir / "users" / normalized_username
        user_dir_existed = user_dir.exists()
        account_lock = self._account_mutation_lock(normalized_username)
        try:
            account_lock.acquire()
        except Exception:
            conn.close()
            raise
        try:
            conn.execute("BEGIN IMMEDIATE")
            if cursor.execute("SELECT 1 FROM users LIMIT 1").fetchone():
                raise ValueError("Setup already completed")
            conflicting_directories = self._find_user_directories(normalized_username)
            if conflicting_directories:
                directory_names = ", ".join(
                    sorted(candidate.name for candidate in conflicting_directories)
                )
                raise ValueError(
                    "A data directory already exists for this username: "
                    f"{directory_names}. Resolve it before creating the user."
                )
            self._initialize_user_files(normalized_username)
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, is_admin, created_at)
                VALUES (?, ?, 1, ?)
                """,
                (
                    normalized_username,
                    self._hash_password(password),
                    _database_timestamp(),
                ),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            if not user_dir_existed:
                self._discard_uncommitted_user_files(user_dir)
            raise
        finally:
            conn.close()
            account_lock.release()
        return True

    def _initialize_user_files(self, username: str) -> None:
        user_dir = self.get_user_dir(username)
        user_dir.mkdir(parents=True, exist_ok=True)
        (user_dir / "uploads").mkdir(exist_ok=True)
        (user_dir / "outputs").mkdir(exist_ok=True)
        settings_file = user_dir / "settings.json"
        if not settings_file.exists():
            settings_file.write_text("{}", encoding="utf-8")
        history_file = user_dir / "history.json"
        if not history_file.exists():
            history_file.write_text("[]", encoding="utf-8")

    @staticmethod
    def _discard_uncommitted_user_files(user_dir: Path) -> None:
        """Remove only the structure created by a failed account insert."""
        if not user_dir.is_dir():
            return
        expected_names = {"uploads", "outputs", "settings.json", "history.json"}
        try:
            if all(child.name in expected_names for child in user_dir.iterdir()):
                shutil.rmtree(user_dir)
        except OSError:
            # Preserve any remaining files if cleanup cannot be completed.
            return

    def create_user(
        self,
        username: str,
        password: str,
        is_admin: bool = False,
        *,
        max_users: int | None = None,
    ) -> bool:
        """
        Create a new user

        Args:
            username: Username for the new user
            password: Password for the new user
            is_admin: Whether the user should have admin privileges

        Returns:
            True if user was created successfully

        Raises:
            ValueError: If username already exists or is invalid
        """
        normalized_username = _normalize_username(username)
        _validate_password(password)
        if max_users is not None and max_users <= 0:
            raise ValueError("max_users must be greater than zero")

        conn = self._connect()
        cursor = conn.cursor()
        user_dir = self.data_dir / "users" / normalized_username
        user_dir_existed = user_dir.exists()
        account_lock = self._account_mutation_lock(normalized_username)
        try:
            account_lock.acquire()
        except Exception:
            conn.close()
            raise

        try:
            conn.execute("BEGIN IMMEDIATE")
            if max_users is not None:
                if (
                    cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                    >= max_users
                ):
                    raise ValueError("The maximum number of users has been reached")
            if cursor.execute(
                "SELECT 1 FROM users WHERE username = ? COLLATE NOCASE",
                (normalized_username,),
            ).fetchone():
                raise ValueError(f"Username '{username}' already exists")

            conflicting_directories = self._find_user_directories(normalized_username)
            if conflicting_directories:
                directory_names = ", ".join(
                    sorted(candidate.name for candidate in conflicting_directories)
                )
                raise ValueError(
                    "A data directory already exists for this username: "
                    f"{directory_names}. Resolve it before creating the user."
                )

            self._initialize_user_files(normalized_username)
            password_hash = self._hash_password(password)
            created_at = _database_timestamp()

            cursor.execute(
                "INSERT INTO users (username, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?)",
                (normalized_username, password_hash, 1 if is_admin else 0, created_at),
            )
            conn.commit()

            return True

        except sqlite3.IntegrityError:
            conn.rollback()
            if not user_dir_existed:
                self._discard_uncommitted_user_files(user_dir)
            raise ValueError(f"Username '{username}' already exists") from None
        except Exception:
            conn.rollback()
            if not user_dir_existed:
                self._discard_uncommitted_user_files(user_dir)
            raise
        finally:
            conn.close()
            account_lock.release()

    def authenticate(self, username: str, password: str) -> str | None:
        """
        Authenticate a user and create a session token

        Args:
            username: Username to authenticate
            password: Password to verify

        Returns:
            Session token if authentication successful, None otherwise
        """
        try:
            normalized_username = _normalize_username(username)
        except ValueError:
            return None

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT username, password_hash, is_admin FROM users WHERE username = ? COLLATE NOCASE",
            (normalized_username,),
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            return None

        stored_username, password_hash, is_admin = result

        if not self._verify_password(password, password_hash):
            conn.close()
            return None

        # Update last login
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE username = ?",
            (_database_timestamp(), stored_username),
        )

        # Create session token
        now = _utc_now()
        expires_at = now + timedelta(hours=TOKEN_EXPIRY_HOURS)
        token_data = {
            "username": stored_username,
            "is_admin": bool(is_admin),
            "exp": expires_at.timestamp(),
        }

        session_token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")

        # Store session in database
        cursor.execute(
            "INSERT INTO sessions (session_token, username, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (
                session_token,
                stored_username,
                _database_timestamp(now),
                _database_timestamp(expires_at),
            ),
        )

        conn.commit()
        conn.close()

        return session_token

    def _cleanup_expired_sessions_if_due(self) -> None:
        """Run session cleanup at a low frequency instead of on every request."""
        now_monotonic = time.monotonic()
        if now_monotonic - self._last_session_cleanup < 300:
            return
        with self._session_cleanup_lock:
            if now_monotonic - self._last_session_cleanup < 300:
                return
            self.cleanup_expired_sessions()
            self._last_session_cleanup = now_monotonic

    def validate_token(self, token: str) -> dict | None:
        """
        Validate a session token

        Args:
            token: Session token to validate

        Returns:
            User data dict if valid, None otherwise
        """
        try:
            self._cleanup_expired_sessions_if_due()
            # Decode JWT token
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

            conn = self._connect()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT sessions.username, sessions.expires_at, users.is_admin
                FROM sessions
                INNER JOIN users ON users.username = sessions.username
                WHERE sessions.session_token = ?
                """,
                (token,),
            )
            result = cursor.fetchone()
            conn.close()

            if not result:
                return None

            username, expires_at, is_admin = result

            # Check if session has expired
            try:
                is_expired = _parse_database_timestamp(expires_at) < _utc_now()
            except (TypeError, ValueError):
                is_expired = True
            if is_expired:
                self.logout(token)
                return None

            return {
                "username": username,
                "is_admin": bool(is_admin),
            }

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def logout(self, token: str) -> bool:
        """
        Logout a user by invalidating their session token

        Args:
            token: Session token to invalidate

        Returns:
            True if logout successful
        """
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM sessions WHERE session_token = ?", (token,))
        conn.commit()
        conn.close()

        return True

    def delete_user(self, username: str, admin_username: str) -> bool:
        """
        Delete a user (admin only)

        Args:
            username: Username to delete
            admin_username: Username of the admin performing the deletion

        Returns:
            True if deletion successful

        Raises:
            AuthenticationError: If admin_username is not an admin
            ValueError: If trying to delete the last admin
        """
        normalized_admin_username = _normalize_username(admin_username)
        normalized_target_username = _normalize_username(username)
        account_lock = self._account_mutation_lock(normalized_target_username)

        with account_lock:
            conn = self._connect()
            try:
                cursor = conn.cursor()
                conn.execute("BEGIN IMMEDIATE")

                cursor.execute(
                    "SELECT username, is_admin FROM users "
                    "WHERE username = ? COLLATE NOCASE",
                    (normalized_admin_username,),
                )
                result = cursor.fetchone()
                if not result or not result[1]:
                    raise AuthenticationError("Only admins can delete users")

                cursor.execute(
                    "SELECT username, is_admin FROM users "
                    "WHERE username = ? COLLATE NOCASE",
                    (normalized_target_username,),
                )
                result = cursor.fetchone()
                if not result:
                    raise ValueError(f"User '{username}' does not exist")

                target_username = result[0]
                if result[1]:
                    cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
                    admin_count = cursor.fetchone()[0]
                    if admin_count <= 1:
                        raise ValueError("Cannot delete the last admin user")

                # Commit the account deletion before removing files. A database
                # failure must not destroy the user's data. The account lock is
                # held through cleanup so a new account cannot reuse the path.
                user_dir = self.get_user_dir(target_username)
                users_root = self.data_dir / "users"
                if user_dir.exists():
                    try:
                        user_dir.resolve().relative_to(users_root.resolve())
                    except ValueError as exc:
                        raise ValueError(
                            "User data directory is outside the users root"
                        ) from exc
                cursor.execute(
                    "DELETE FROM users WHERE username = ?", (target_username,)
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

            if user_dir.exists():
                try:
                    shutil.rmtree(user_dir)
                except OSError as exc:
                    logger.warning(
                        "User %s was deleted but data cleanup failed: %s",
                        target_username,
                        exc,
                    )

        return True

    def list_users(self, admin_username: str) -> list[dict]:
        """
        List all users (admin only)

        Args:
            admin_username: Username of the admin requesting the list

        Returns:
            List of user dictionaries

        Raises:
            AuthenticationError: If admin_username is not an admin
        """
        # Check if requester is admin
        normalized_admin_username = _normalize_username(admin_username)
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT is_admin FROM users WHERE username = ? COLLATE NOCASE",
                (normalized_admin_username,),
            )
            result = cursor.fetchone()
            if not result or not result[0]:
                raise AuthenticationError("Only admins can list users")

            cursor.execute(
                "SELECT username, is_admin, created_at, last_login "
                "FROM users ORDER BY created_at"
            )
            return [
                {
                    "username": row[0],
                    "is_admin": bool(row[1]),
                    "created_at": row[2],
                    "last_login": row[3],
                }
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def change_password(
        self, username: str, old_password: str, new_password: str
    ) -> bool:
        """
        Change a user's password

        Args:
            username: Username whose password to change
            old_password: Current password for verification
            new_password: New password to set

        Returns:
            True if password changed successfully

        Raises:
            AuthenticationError: If old password is incorrect
            ValueError: If new password is invalid
        """
        normalized_username = _normalize_username(username)
        _validate_password(new_password, "New password")

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT username, password_hash FROM users WHERE username = ? COLLATE NOCASE",
            (normalized_username,),
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            raise ValueError(f"User '{username}' does not exist")

        stored_username, password_hash = result
        if not self._verify_password(old_password, password_hash):
            conn.close()
            raise AuthenticationError("Incorrect current password")

        new_hash = self._hash_password(new_password)
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (new_hash, stored_username),
        )

        # Invalidate all existing sessions for this user
        cursor.execute("DELETE FROM sessions WHERE username = ?", (stored_username,))

        conn.commit()
        conn.close()

        return True

    def get_user_dir(self, username: str) -> Path:
        """Get the data directory for a specific user"""
        normalized_username = _normalize_username(username)
        users_root = self.data_dir / "users"
        normalized_path = users_root / normalized_username
        if normalized_path.exists():
            return normalized_path

        original_path = users_root / username
        if original_path.exists():
            return original_path

        # Preserve access to databases created before usernames were
        # canonicalized, including when the data directory is moved to Linux.
        conflicting_directories = self._find_user_directories(normalized_username)
        if conflicting_directories:
            return conflicting_directories[0]
        return normalized_path

    def _find_user_directories(self, normalized_username: str) -> list[Path]:
        """Find legacy user directories that collide after username normalization."""
        users_root = self.data_dir / "users"
        if not users_root.exists():
            return []
        return sorted(
            (
                candidate
                for candidate in users_root.iterdir()
                if candidate.is_dir()
                and candidate.name.casefold() == normalized_username
            ),
            key=lambda candidate: candidate.name.casefold(),
        )

    def list_registered_usernames(self) -> list[str]:
        """Return usernames stored in the database for maintenance tasks."""
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT username FROM users ORDER BY username COLLATE NOCASE"
            ).fetchall()
        finally:
            connection.close()
        return [row[0] for row in rows]

    def validate_user_directory_integrity(self) -> None:
        """Reject ambiguous legacy directories before serving user data."""
        for username in self.list_registered_usernames():
            conflicting_directories = self._find_user_directories(username.casefold())
            if len(conflicting_directories) > 1:
                directory_names = ", ".join(
                    sorted(candidate.name for candidate in conflicting_directories)
                )
                raise RuntimeError(
                    "Ambiguous user data directories for "
                    f"'{username}': {directory_names}. Resolve the conflict before startup."
                )

    def get_registration_enabled(self) -> bool:
        """
        Check if user registration is enabled

        Returns:
            True if registration is enabled, False otherwise (default: False)
        """
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM app_config WHERE key = 'allow_registration'")
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0].lower() == "true"
        return False  # Default to disabled for security

    def set_registration_enabled(self, enabled: bool, admin_username: str) -> bool:
        """
        Enable or disable user registration (admin only)

        Args:
            enabled: Whether to enable registration
            admin_username: Username of the admin making the change

        Returns:
            True if setting was updated successfully

        Raises:
            AuthenticationError: If admin_username is not an admin
        """
        # Check if requester is admin
        normalized_admin_username = _normalize_username(admin_username)
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT is_admin FROM users WHERE username = ? COLLATE NOCASE",
                (normalized_admin_username,),
            )
            result = cursor.fetchone()
            if not result or not result[0]:
                raise AuthenticationError(
                    "Only admins can change registration settings"
                )

            # Update or insert the setting
            value = "true" if enabled else "false"
            cursor.execute(
                "INSERT OR REPLACE INTO app_config (key, value) "
                "VALUES ('allow_registration', ?)",
                (value,),
            )

            conn.commit()
            return True
        finally:
            conn.close()

    def cleanup_expired_sessions(self):
        """Remove expired sessions from the database"""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM sessions WHERE expires_at < ?", (_database_timestamp(),)
        )

        conn.commit()
        conn.close()
