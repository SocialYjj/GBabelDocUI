"""持久化翻译任务及其兼容的历史文件。"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

from filelock import FileLock

logger = logging.getLogger(__name__)

TASK_STATUSES = frozenset({"queued", "processing", "completed", "failed", "cancelled"})
ACTIVE_TASK_STATUSES = ("queued", "processing")
ACTIVE_TASK_STATUS_SQL = "('queued', 'processing')"


class ActiveTaskLimitError(Exception):
    """Raised when a user reaches the configured active-task limit."""


class GlobalActiveTaskLimitError(Exception):
    """Raised when the service reaches its global active-task limit."""


def _utc_now() -> datetime:
    """Return a naive UTC timestamp used by the existing data format."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _history_record_from_task(task: dict[str, Any]) -> dict[str, Any]:
    """Build the on-disk history representation from a task record."""
    return {
        "task_id": task["task_id"],
        "file_id": task.get("file_id", ""),
        "filename": task.get("filename", ""),
        "original_filename": task.get("original_filename", ""),
        "created_at": task.get("created_at"),
        "completed_at": task.get("completed_at"),
        "status": task.get("status", "failed"),
        "mono_path": task.get("mono_path"),
        "dual_path": task.get("dual_path"),
        "error": task.get("error"),
    }


class TranslationHistoryFile:
    """Atomically update one user's legacy-compatible ``history.json`` file."""

    def __init__(self, history_file: Path):
        self.history_file = history_file
        self.lock_file = history_file.with_name(f".{history_file.name}.lock")

    def read(self) -> list[dict[str, Any]]:
        """Read history without changing the user's existing file."""
        if not self.history_file.exists():
            return []

        with FileLock(str(self.lock_file), timeout=30):
            history = json.loads(self.history_file.read_text(encoding="utf-8"))

        if not isinstance(history, list):
            raise ValueError("Translation history must be a JSON array")
        return [item for item in history if isinstance(item, dict)]

    def upsert(self, task: dict[str, Any]) -> None:
        """Insert or replace one task while serializing concurrent writers."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        history_record = _history_record_from_task(task)

        with FileLock(str(self.lock_file), timeout=30):
            history = self._read_locked()
            replaced = False
            for index, item in enumerate(history):
                if item.get("task_id") == history_record["task_id"]:
                    history[index] = history_record
                    replaced = True
                    break
            if not replaced:
                history.append(history_record)
            self._write_locked(history)

    def remove(self, task_id: str) -> None:
        """Remove one history item without touching unrelated records."""
        if not self.history_file.exists():
            return

        with FileLock(str(self.lock_file), timeout=30):
            history = self._read_locked()
            remaining = [item for item in history if item.get("task_id") != task_id]
            if len(remaining) != len(history):
                self._write_locked(remaining)

    def _read_locked(self) -> list[dict[str, Any]]:
        if not self.history_file.exists():
            return []
        history = json.loads(self.history_file.read_text(encoding="utf-8"))
        if not isinstance(history, list):
            raise ValueError("Translation history must be a JSON array")
        return [item for item in history if isinstance(item, dict)]

    def _write_locked(self, history: list[dict[str, Any]]) -> None:
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.history_file.parent,
                prefix=f".{self.history_file.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                json.dump(history, temporary_file, indent=2, ensure_ascii=False)
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            temporary_path.replace(self.history_file)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)


class TranslationTaskStore:
    """Persist task state in SQLite and retain the existing JSON history export."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.data_dir = self.db_path.parent
        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    @contextmanager
    def _managed_connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize_database(self) -> None:
        with self._managed_connection() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS translation_tasks (
                    task_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    file_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    input_path TEXT NOT NULL,
                    output_dir TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    error TEXT,
                    mono_path TEXT,
                    dual_path TEXT,
                    settings_json TEXT NOT NULL DEFAULT '{}',
                    CHECK (status IN ('queued', 'processing', 'completed', 'failed', 'cancelled')),
                    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
                )
                """
            )
            existing_columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(translation_tasks)"
                ).fetchall()
            }
            if "settings_json" not in existing_columns:
                try:
                    connection.execute(
                        "ALTER TABLE translation_tasks ADD COLUMN settings_json TEXT NOT NULL DEFAULT '{}'"
                    )
                except sqlite3.OperationalError as exc:
                    if "duplicate column name" not in str(exc).lower():
                        raise
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_translation_tasks_user_created
                ON translation_tasks (username, created_at DESC)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_translation_tasks_active_file
                ON translation_tasks (username, file_id, status)
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS translation_history_imports (
                    username TEXT PRIMARY KEY,
                    imported_at TEXT NOT NULL,
                    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
                )
                """
            )

    def create_task(
        self,
        *,
        task_id: str,
        username: str,
        file_id: str,
        filename: str,
        input_path: Path,
        output_dir: Path,
        settings_snapshot: dict[str, Any] | None = None,
        max_active_tasks: int | None = None,
        max_active_tasks_global: int | None = None,
    ) -> dict[str, Any]:
        """Create a queued task before the background coroutine starts."""
        if max_active_tasks is not None and max_active_tasks <= 0:
            raise ValueError("max_active_tasks must be greater than zero")
        if max_active_tasks_global is not None and max_active_tasks_global <= 0:
            raise ValueError("max_active_tasks_global must be greater than zero")
        if settings_snapshot is None:
            settings_snapshot = {}
        if not isinstance(settings_snapshot, dict):
            raise ValueError("settings_snapshot must be a JSON object")
        try:
            serialized_settings_snapshot = json.dumps(
                settings_snapshot, ensure_ascii=False, separators=(",", ":")
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("settings_snapshot must contain JSON values") from exc
        if max_active_tasks is not None or max_active_tasks_global is not None:
            self._ensure_legacy_history_imported(username)

        now = _utc_now().isoformat()
        with self._managed_connection() as connection:
            if max_active_tasks is not None or max_active_tasks_global is not None:
                # Serialize the count-and-insert pair so concurrent requests cannot
                # both pass the limit check before either task is committed.
                connection.execute("BEGIN IMMEDIATE")
            if max_active_tasks_global is not None:
                global_active_task_count = connection.execute(
                    """
                    SELECT COUNT(*) FROM translation_tasks
                    WHERE status IN ('queued', 'processing')
                    """
                ).fetchone()[0]
                if global_active_task_count >= max_active_tasks_global:
                    raise GlobalActiveTaskLimitError
            if max_active_tasks is not None:
                active_task_count = connection.execute(
                    """
                    SELECT COUNT(*) FROM translation_tasks
                    WHERE username = ? COLLATE NOCASE
                      AND status IN ('queued', 'processing')
                    """,
                    (username,),
                ).fetchone()[0]
                if active_task_count >= max_active_tasks:
                    raise ActiveTaskLimitError

            connection.execute(
                """
                INSERT INTO translation_tasks (
                    task_id, username, file_id, filename, original_filename,
                    input_path, output_dir, status, progress, message,
                    created_at, updated_at, settings_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', 0, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    username,
                    file_id,
                    filename,
                    Path(filename).stem,
                    str(input_path),
                    str(output_dir),
                    "Translation queued",
                    now,
                    now,
                    serialized_settings_snapshot,
                ),
            )
        return self.get_task(task_id, username=username)  # type: ignore[return-value]

    def mark_processing(self, task_id: str, message: str) -> bool:
        return self._update_task_status(
            task_id,
            "processing",
            message=message,
            allowed_current_statuses=("queued", "processing"),
        )

    def update_progress(self, task_id: str, progress: int, message: str) -> bool:
        now = _utc_now().isoformat()
        bounded_progress = max(0, min(100, int(progress)))
        with self._managed_connection() as connection:
            update_result = connection.execute(
                """
                UPDATE translation_tasks
                SET progress = ?, message = ?, updated_at = ?
                WHERE task_id = ? AND status IN ('queued', 'processing')
                """,
                (bounded_progress, message, now, task_id),
            )
            if update_result.rowcount == 0:
                logger.debug("Ignoring progress update for inactive task %s", task_id)
            return update_result.rowcount > 0

    def is_processing(self, task_id: str) -> bool:
        """Return whether a task can still publish translation output."""
        with self._managed_connection() as connection:
            return (
                connection.execute(
                    """
                    SELECT 1 FROM translation_tasks
                    WHERE task_id = ? AND status = 'processing'
                    """,
                    (task_id,),
                ).fetchone()
                is not None
            )

    def mark_completed(
        self, task_id: str, mono_path: Path | None, dual_path: Path | None
    ) -> bool:
        now = _utc_now().isoformat()
        with self._managed_connection() as connection:
            update_result = connection.execute(
                """
                UPDATE translation_tasks
                SET status = 'completed', progress = 100,
                    message = 'Translation completed', updated_at = ?,
                    completed_at = ?, error = NULL, mono_path = ?, dual_path = ?
                WHERE task_id = ? AND status = 'processing'
                """,
                (
                    now,
                    now,
                    str(mono_path) if mono_path else None,
                    str(dual_path) if dual_path else None,
                    task_id,
                ),
            )
            if update_result.rowcount == 0:
                logger.warning("Ignoring completion update for task %s", task_id)
            return update_result.rowcount > 0

    def mark_failed(self, task_id: str, error_message: str) -> bool:
        return self._update_terminal_task(
            task_id, "failed", f"Translation failed: {error_message}", error_message
        )

    def mark_cancelled(self, task_id: str) -> bool:
        return self._update_terminal_task(
            task_id,
            "cancelled",
            "Translation cancelled",
            "Translation cancelled by user or server shutdown",
        )

    def _update_task_status(
        self,
        task_id: str,
        status: str,
        *,
        message: str,
        allowed_current_statuses: tuple[str, ...],
    ) -> bool:
        if status not in TASK_STATUSES:
            raise ValueError(f"Unsupported task status: {status}")
        if not allowed_current_statuses:
            raise ValueError("allowed_current_statuses must not be empty")
        now = _utc_now().isoformat()
        with self._managed_connection() as connection:
            status_update_sql = {
                ("queued",): """
                    UPDATE translation_tasks
                    SET status = ?, message = ?, updated_at = ?
                    WHERE task_id = ? AND status = ?
                """,
                ("queued", "processing"): """
                    UPDATE translation_tasks
                    SET status = ?, message = ?, updated_at = ?
                    WHERE task_id = ? AND status IN (?, ?)
                """,
            }.get(allowed_current_statuses)
            if status_update_sql is None:
                raise ValueError("Unsupported allowed task status transition")
            update_result = connection.execute(
                status_update_sql,
                (status, message, now, task_id, *allowed_current_statuses),
            )
            if update_result.rowcount == 0:
                logger.debug("Ignoring invalid status transition for task %s", task_id)
            return update_result.rowcount > 0

    def _update_terminal_task(
        self, task_id: str, status: str, message: str, error_message: str
    ) -> bool:
        now = _utc_now().isoformat()
        with self._managed_connection() as connection:
            update_result = connection.execute(
                """
                UPDATE translation_tasks
                SET status = ?, message = ?, updated_at = ?, completed_at = ?,
                    error = ?, mono_path = NULL, dual_path = NULL
                WHERE task_id = ? AND status IN ('queued', 'processing')
                """,
                (status, message, now, now, error_message, task_id),
            )
            if update_result.rowcount == 0:
                logger.debug("Ignoring terminal update for task %s", task_id)
            return update_result.rowcount > 0

    def get_task(
        self, task_id: str, *, username: str | None = None
    ) -> dict[str, Any] | None:
        if username is not None:
            self._ensure_legacy_history_imported(username)

        query = "SELECT * FROM translation_tasks WHERE task_id = ?"
        parameters: list[str] = [task_id]
        if username is not None:
            query += " AND username = ? COLLATE NOCASE"
            parameters.append(username)

        with self._managed_connection() as connection:
            row = connection.execute(query, parameters).fetchone()
        return dict(row) if row else None

    def list_tasks(
        self, username: str, *, limit: int, offset: int
    ) -> list[dict[str, Any]]:
        self._ensure_legacy_history_imported(username)
        with self._managed_connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM translation_tasks
                WHERE username = ? COLLATE NOCASE
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (username, limit, offset),
            ).fetchall()
        return [dict(row) for row in rows]

    def count_tasks(self, username: str) -> int:
        self._ensure_legacy_history_imported(username)
        with self._managed_connection() as connection:
            return int(
                connection.execute(
                    "SELECT COUNT(*) FROM translation_tasks "
                    "WHERE username = ? COLLATE NOCASE",
                    (username,),
                ).fetchone()[0]
            )

    def count_active_tasks(self, username: str) -> int:
        with self._managed_connection() as connection:
            return int(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM translation_tasks
                    WHERE username = ? COLLATE NOCASE
                      AND (status = ? OR status = ?)
                    """,
                    (username, *ACTIVE_TASK_STATUSES),
                ).fetchone()[0]
            )

    def count_all_active_tasks(self) -> int:
        """Return the number of queued or processing tasks for the service."""
        with self._managed_connection() as connection:
            return int(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM translation_tasks
                    WHERE status IN ('queued', 'processing')
                    """
                ).fetchone()[0]
            )

    def count_active_tasks_for_file(
        self, username: str, file_id: str, *, exclude_task_id: str | None = None
    ) -> int:
        """Count active tasks that still need one uploaded input file."""
        self._ensure_legacy_history_imported(username)
        query = """
            SELECT COUNT(*) FROM translation_tasks
            WHERE username = ? COLLATE NOCASE AND file_id = ?
              AND status IN ('queued', 'processing')
        """
        parameters: list[str] = [username, file_id]
        if exclude_task_id is not None:
            query += " AND task_id != ?"
            parameters.append(exclude_task_id)
        with self._managed_connection() as connection:
            return int(connection.execute(query, parameters).fetchone()[0])

    def count_tasks_for_file(self, username: str, file_id: str) -> int:
        """Count all task records that refer to one uploaded file."""
        self._ensure_legacy_history_imported(username)
        with self._managed_connection() as connection:
            return int(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM translation_tasks
                    WHERE username = ? COLLATE NOCASE AND file_id = ?
                    """,
                    (username, file_id),
                ).fetchone()[0]
            )

    def list_active_tasks(self, username: str) -> list[dict[str, Any]]:
        """List a user's active tasks for cancellation or administration."""
        with self._managed_connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM translation_tasks
                WHERE username = ? COLLATE NOCASE
                  AND status IN ('queued', 'processing')
                ORDER BY created_at
                """,
                (username,),
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_task(self, task_id: str, username: str) -> dict[str, Any] | None:
        task = self.get_task(task_id, username=username)
        if task is None:
            return None
        with self._managed_connection() as connection:
            connection.execute(
                "DELETE FROM translation_tasks "
                "WHERE task_id = ? AND username = ? COLLATE NOCASE",
                (task_id, username),
            )
        return task

    def recover_interrupted_tasks(self) -> list[dict[str, Any]]:
        """Mark tasks that cannot resume after a process restart as failed."""
        now = _utc_now().isoformat()
        error_message = "Translation interrupted because the service restarted"
        with self._managed_connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM translation_tasks
                WHERE status IN ('queued', 'processing')
                """
            ).fetchall()
            connection.execute(
                """
                UPDATE translation_tasks
                SET status = 'failed',
                    message = ?, updated_at = ?, completed_at = ?,
                    error = ?, mono_path = NULL, dual_path = NULL
                WHERE status IN ('queued', 'processing')
                """,
                (
                    error_message,
                    now,
                    now,
                    error_message,
                ),
            )

        recovered_tasks: list[dict[str, Any]] = []
        for row in rows:
            task = dict(row)
            task.update(
                {
                    "status": "failed",
                    "message": error_message,
                    "updated_at": now,
                    "completed_at": now,
                    "error": error_message,
                    "mono_path": None,
                    "dual_path": None,
                }
            )
            recovered_tasks.append(task)
        return recovered_tasks

    def synchronize_history(self, task: dict[str, Any]) -> None:
        """Write the current task into the user's legacy JSON history."""
        history_file = self._history_file(task["username"])
        try:
            TranslationHistoryFile(history_file).upsert(task)
        except Exception as exc:
            logger.error(
                "Failed to synchronize history for task %s: %s", task["task_id"], exc
            )

    def remove_from_history(self, username: str, task_id: str) -> None:
        history_file = self._history_file(username)
        try:
            TranslationHistoryFile(history_file).remove(task_id)
        except Exception as exc:
            logger.error("Failed to remove history item %s: %s", task_id, exc)

    def _history_file(self, username: str) -> Path:
        return self._user_dir(username) / "history.json"

    def _user_dir(self, username: str) -> Path:
        """Resolve legacy username casing when data moves to a case-sensitive OS."""
        users_root = self.data_dir / "users"
        direct_path = users_root / username
        if direct_path.exists():
            return direct_path
        normalized_username = username.casefold()
        if users_root.exists():
            for candidate in users_root.iterdir():
                if (
                    candidate.is_dir()
                    and candidate.name.casefold() == normalized_username
                ):
                    return candidate
        return direct_path

    def _ensure_legacy_history_imported(self, username: str) -> None:
        with self._managed_connection() as connection:
            user_exists = connection.execute(
                "SELECT 1 FROM users WHERE username = ? COLLATE NOCASE",
                (username,),
            ).fetchone()
            if user_exists is None:
                return
            imported = connection.execute(
                "SELECT 1 FROM translation_history_imports WHERE username = ?",
                (username,),
            ).fetchone()
        if imported:
            return

        history_file = TranslationHistoryFile(self._history_file(username))
        try:
            history = history_file.read()
        except Exception as exc:
            logger.error("Failed to import legacy history for %s: %s", username, exc)
            return

        user_dir = self._user_dir(username)
        now = _utc_now().isoformat()
        with self._managed_connection() as connection:
            user_exists = connection.execute(
                "SELECT 1 FROM users WHERE username = ? COLLATE NOCASE",
                (username,),
            ).fetchone()
            if user_exists is None:
                return
            for item in history:
                task_id = str(item.get("task_id", "")).strip()
                if not task_id:
                    continue

                file_id = str(item.get("file_id", "") or "")
                input_path = self._find_uploaded_file(user_dir, file_id)
                filename = str(item.get("filename", "") or "")
                original_filename = str(
                    item.get("original_filename") or Path(filename).stem or "translated"
                )
                status = str(item.get("status", "failed"))
                if status not in TASK_STATUSES:
                    status = "failed"
                legacy_task_was_active = status in ACTIVE_TASK_STATUSES
                if legacy_task_was_active:
                    status = "failed"
                error_message = item.get("error")
                if status == "failed" and not error_message:
                    error_message = (
                        "Legacy translation task could not be resumed after migration"
                    )
                connection.execute(
                    """
                    INSERT OR IGNORE INTO translation_tasks (
                        task_id, username, file_id, filename, original_filename,
                        input_path, output_dir, status, progress, message,
                        created_at, updated_at, completed_at, error,
                        mono_path, dual_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task_id,
                        username,
                        file_id,
                        filename,
                        original_filename,
                        str(input_path) if input_path else "",
                        str(user_dir / "outputs" / task_id),
                        status,
                        100 if status == "completed" else 0,
                        "Translation completed"
                        if status == "completed"
                        else str(error_message or "Translation failed"),
                        str(item.get("created_at") or now),
                        str(item.get("completed_at") or item.get("created_at") or now),
                        item.get("completed_at")
                        or (now if legacy_task_was_active else None),
                        str(error_message) if error_message else None,
                        item.get("mono_path"),
                        item.get("dual_path"),
                    ),
                )
            connection.execute(
                """
                INSERT OR IGNORE INTO translation_history_imports (username, imported_at)
                VALUES (?, ?)
                """,
                (username, now),
            )

    @staticmethod
    def _find_uploaded_file(user_dir: Path, file_id: str) -> Path | None:
        if not file_id:
            return None
        upload_dir = user_dir / "uploads"
        for candidate in upload_dir.glob(f"{file_id}_*"):
            if candidate.is_file():
                return candidate
        return None
