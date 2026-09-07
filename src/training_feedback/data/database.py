"""SQLite 连接配置（外键、忙等待、行工厂）与统一的事务边界。"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .migrations import apply_migrations


class Database:
    """SQLite 连接包装：打开时执行迁移，并验证外键约束已启用。"""
    def __init__(self, path: Path):
        self.path = Path(path)
        self.connection: sqlite3.Connection | None = None

    def __enter__(self) -> sqlite3.Connection:
        try:
            self.connection = sqlite3.connect(self.path)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.execute("PRAGMA busy_timeout = 5000")
            if self.connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
                raise sqlite3.DatabaseError("SQLite foreign keys could not be enabled.")
            apply_migrations(self.connection)
            return self.connection
        except Exception:
            self.close()
            raise

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.connection is not None:
            if exc_type is not None:
                self.connection.rollback()
            self.close()

    @contextmanager
    def transaction(self, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        """在已打开的连接上开启一个写事务；等同于模块级 transaction()。"""
        if self.connection is None:
            raise RuntimeError("Database is not open.")
        with transaction(self.connection, immediate):
            yield self.connection

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None


@contextmanager
def transaction(
    connection: sqlite3.Connection, immediate: bool = False
) -> Iterator[sqlite3.Connection]:
    """Run one runtime write transaction with a consistent rollback boundary."""
    connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()
