"""Export RNMD's Railway SQLite rows into D1-compatible INSERT statements.

The output includes private Business chat archives. Keep it off GitHub and
delete it securely when migration is complete.
"""

import argparse
import os
import sqlite3
import tempfile
from pathlib import Path

TABLES = (
    "chats", "bad_words", "auto_replies", "warnings", "schedules",
    "business_connections", "business_settings", "business_replies",
    "business_seen_chats", "business_muted_chats", "business_message_archive",
    "business_mute_controls",
)
MAX_STATEMENT_BYTES = 100_000  # Cloudflare D1 limit.


def sql_literal(value):
    if value is None:
        return "NULL"
    if isinstance(value, bytes):
        return "X'" + value.hex() + "'"
    if isinstance(value, str):
        if "\x00" in value:
            return "CAST(X'" + value.encode("utf-8").hex() + "' AS TEXT)"
        return "'" + value.replace("'", "''") + "'"
    if isinstance(value, (int, float)):
        return repr(value)
    raise TypeError(f"Unsupported SQLite value: {type(value).__name__}")


def export(source: Path, dest: Path):
    if not source.is_file():
        raise ValueError("SQLite database file not found")
    if dest.exists():
        raise ValueError("Output already exists; choose a new filename")
    dest.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)
    temp_name = None
    counts = {}
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=dest.parent,
            prefix=".rnmd-d1-export-", suffix=".sql", delete=False,
        ) as out:
            temp_name = out.name
            os.chmod(temp_name, 0o600)
            out.write("-- RNMD data only; create cloudflare-bot/schema.sql in D1 first.\n")
            for table in TABLES:
                present = db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
                ).fetchone()
                if not present:
                    counts[table] = 0
                    continue
                columns = [r[1] for r in db.execute(f'PRAGMA table_info("{table}")')]
                fields = ",".join(f'"{name}"' for name in columns)
                counts[table] = 0
                for row in db.execute(f'SELECT {fields} FROM "{table}"'):
                    values = ",".join(map(sql_literal, row))
                    statement = f'INSERT OR REPLACE INTO "{table}"({fields}) VALUES({values});\n'
                    if len(statement.encode("utf-8")) > MAX_STATEMENT_BYTES:
                        raise ValueError(f"Row in {table} exceeds D1's 100 KB SQL limit")
                    out.write(statement)
                    counts[table] += 1
        os.replace(temp_name, dest)
        temp_name = None
    finally:
        db.close()
        if temp_name is not None:
            os.unlink(temp_name)
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Existing Railway bot SQLite database")
    parser.add_argument("output", type=Path, help="Private D1 SQL output; never commit")
    args = parser.parse_args()
    result = export(args.source, args.output)
    print(f"Exported {sum(result.values())} rows to {args.output} (private data; do not share).")
    print(", ".join(f"{table}: {amount}" for table, amount in result.items()))
