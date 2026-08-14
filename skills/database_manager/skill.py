"""
EvolvixOS — Database Manager Skill
Manage local databases: SQLite, DuckDB. Query, create, backup, migrate.
100% local. Zero tokens. Zero cloud.

No pip install needed for SQLite (stdlib).
Pip: pip install duckdb (optional, for DuckDB)
License: PSF (sqlite3), MIT (DuckDB)
"""

import os
import json
import time
import sqlite3
from pathlib import Path
from typing import Optional, List
from rich.console import Console

console = Console()


class Skill:
    """Database manager — SQLite + DuckDB. Free, local."""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get("output_dir", "./output/databases"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._connections = {}

    def run(self, args: dict) -> str:
        action = args.get("action", "query")

        if action == "query":
            return self.query(args.get("db", ""), args.get("sql", ""),
                              args.get("params", []))
        elif action == "execute":
            return self.execute(args.get("db", ""), args.get("sql", ""),
                                args.get("params", []))
        elif action == "create_table":
            return self.create_table(args.get("db", ""), args.get("table", ""),
                                     args.get("columns", {}))
        elif action == "insert":
            return self.insert(args.get("db", ""), args.get("table", ""),
                               args.get("data", {}))
        elif action == "select":
            return self.select(args.get("db", ""), args.get("table", ""),
                               args.get("columns", "*"), args.get("where", ""),
                               args.get("limit", 100))
        elif action == "update":
            return self.update(args.get("db", ""), args.get("table", ""),
                               args.get("data", {}), args.get("where", ""))
        elif action == "delete":
            return self.delete(args.get("db", ""), args.get("table", ""),
                               args.get("where", ""))
        elif action == "tables":
            return self.list_tables(args.get("db", ""))
        elif action == "schema":
            return self.table_schema(args.get("db", ""), args.get("table", ""))
        elif action == "backup":
            return self.backup(args.get("db", ""))
        elif action == "export":
            return self.export(args.get("db", ""), args.get("table", ""),
                               args.get("format", "json"))
        elif action == "import":
            return self.import_data(args.get("db", ""), args.get("table", ""),
                                    args.get("file", ""), args.get("format", "json"))
        else:
            return (f"Unknown action: {action}. Use: query, execute, create_table, "
                    "insert, select, update, delete, tables, schema, backup, export, import")

    def query(self, db_path: str, sql: str, params: list = None) -> str:
        if not db_path or not sql:
            return "Error: db and sql are required."
        if not os.path.exists(db_path) and db_path != ":memory:":
            return f"Error: Database {db_path} not found."

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params or [])
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return json.dumps(rows, indent=2, default=str)[:10000]
        except Exception as e:
            return f"Error: {e}"

    def execute(self, db_path: str, sql: str, params: list = None) -> str:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.execute(sql, params or [])
            conn.commit()
            result = f"Executed. Rows affected: {cursor.rowcount}"
            conn.close()
            return result
        except Exception as e:
            return f"Error: {e}"

    def create_table(self, db_path: str, table: str, columns: dict) -> str:
        cols_sql = ", ".join([f'"{name}" {dtype}' for name, dtype in columns.items()])
        sql = f'CREATE TABLE IF NOT EXISTS "{table}" ({cols_sql})'
        return self.execute(db_path, sql)

    def insert(self, db_path: str, table: str, data: dict) -> str:
        cols = ", ".join([f'"{k}"' for k in data.keys()])
        placeholders = ", ".join(["?" for _ in data])
        sql = f'INSERT INTO "{table}" ({cols}) VALUES ({placeholders})'
        return self.execute(db_path, sql, list(data.values()))

    def select(self, db_path: str, table: str, columns: str = "*",
               where: str = "", limit: int = 100) -> str:
        sql = f'SELECT {columns} FROM "{table}"'
        if where:
            sql += f" WHERE {where}"
        sql += f" LIMIT {limit}"
        return self.query(db_path, sql)

    def update(self, db_path: str, table: str, data: dict, where: str = "") -> str:
        sets = ", ".join([f'"{k}" = ?' for k in data.keys()])
        sql = f'UPDATE "{table}" SET {sets}'
        if where:
            sql += f" WHERE {where}"
        return self.execute(db_path, sql, list(data.values()))

    def delete(self, db_path: str, table: str, where: str = "") -> str:
        sql = f'DELETE FROM "{table}"'
        if where:
            sql += f" WHERE {where}"
        return self.execute(db_path, sql)

    def list_tables(self, db_path: str) -> str:
        return self.query(db_path,
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")

    def table_schema(self, db_path: str, table: str) -> str:
        return self.query(db_path, f'PRAGMA table_info("{table}")')

    def backup(self, db_path: str) -> str:
        if not os.path.exists(db_path):
            return "Error: Database not found."

        backup_path = self.output_dir / f"backup_{Path(db_path).stem}_{int(time.time())}.db"

        try:
            source = sqlite3.connect(db_path)
            target = sqlite3.connect(str(backup_path))
            source.backup(target)
            target.close()
            source.close()
            return f"Backup created: {backup_path}"
        except Exception as e:
            return f"Error: {e}"

    def export(self, db_path: str, table: str, fmt: str = "json") -> str:
        data = self.select(db_path, table, limit=10000)
        rows = json.loads(data) if not data.startswith("Error") else []

        out = self.output_dir / f"export_{table}_{int(time.time())}.{fmt}"

        if fmt == "json":
            out.write_text(json.dumps(rows, indent=2))
        elif fmt == "csv":
            import csv
            if rows:
                with open(out, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
            else:
                out.write_text("")
        else:
            out.write_text(json.dumps(rows, indent=2))

        return f"Exported {len(rows)} rows to {out}"

    def import_data(self, db_path: str, table: str, file_path: str,
                    fmt: str = "json") -> str:
        if not os.path.exists(file_path):
            return "Error: File not found."

        try:
            if fmt == "json":
                data = json.loads(Path(file_path).read_text())
            elif fmt == "csv":
                import csv
                with open(file_path) as f:
                    data = list(csv.DictReader(f))
            else:
                data = json.loads(Path(file_path).read_text())

            count = 0
            for row in data:
                self.insert(db_path, table, row)
                count += 1

            return f"Imported {count} rows into {table}"
        except Exception as e:
            return f"Error: {e}"
