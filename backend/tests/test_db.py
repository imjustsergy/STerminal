from app.db import init_db

EXPECTED_COLUMNS = {
    "positions": {
        "id",
        "symbol",
        "asset_class",
        "quantity",
        "cost_price",
        "opened_at",
        "account",
    },
    "watchlist": {"id", "symbol", "sort_order"},
    "settings": {"key", "value"},
}


def _table_columns(conn, table: str) -> set[str]:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def test_init_db_creates_expected_tables() -> None:
    conn = init_db(":memory:")
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert {"positions", "watchlist", "settings"} <= tables


def test_init_db_creates_expected_columns() -> None:
    conn = init_db(":memory:")
    for table, expected_columns in EXPECTED_COLUMNS.items():
        assert _table_columns(conn, table) == expected_columns


def test_init_db_is_idempotent() -> None:
    conn = init_db(":memory:")
    # Running the schema twice on the same connection must not raise.
    from app.db import _SCHEMA

    conn.executescript(_SCHEMA)
    conn.commit()
