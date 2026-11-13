import sqlite3
import json
import time
from typing import Optional, List, Dict, Any
from .config import settings


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS deals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,
        external_id TEXT NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        model_name TEXT,
        price INTEGER NOT NULL,
        market_avg_price INTEGER NOT NULL,
        condition TEXT NOT NULL,
        region TEXT,
        posted_at TEXT,
        url TEXT NOT NULL,
        data_source_type TEXT NOT NULL,
        is_notified INTEGER DEFAULT 0,
        is_saved INTEGER DEFAULT 0,
        created_at INTEGER NOT NULL,
        UNIQUE(platform, external_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS api_cache (
        cache_key TEXT PRIMARY KEY,
        payload_json TEXT NOT NULL,
        expires_at INTEGER NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS notification_logs (
        deal_uid TEXT PRIMARY KEY,
        notified_at INTEGER NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def get_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    now = int(time.time())
    cur.execute("SELECT payload_json, expires_at FROM api_cache WHERE cache_key = ?", (cache_key,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    if row["expires_at"] < now:
        return None
    return json.loads(row["payload_json"])


def set_cache(cache_key: str, payload: Any, ttl: Optional[int] = None) -> None:
    conn = get_connection()
    cur = conn.cursor()
    expires_at = int(time.time()) + (ttl or settings.cache_ttl_seconds)
    cur.execute(
        "INSERT OR REPLACE INTO api_cache (cache_key, payload_json, expires_at) VALUES (?, ?, ?)",
        (cache_key, json.dumps(payload, ensure_ascii=False), expires_at),
    )
    conn.commit()
    conn.close()


def upsert_deal(deal: Dict[str, Any]) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    now = int(time.time())
    try:
        cur.execute(
            """
            INSERT INTO deals (
                platform, external_id, category, title, model_name,
                price, market_avg_price, condition, region, posted_at,
                url, data_source_type, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                deal["platform"],
                deal["external_id"],
                deal.get("category", "기타 중고 전자제품"),
                deal["title"],
                deal.get("model_name", deal["title"]),
                int(deal["price"]),
                int(deal["market_avg_price"]),
                deal.get("condition", "상"),
                deal.get("region", "전국"),
                deal.get("posted_at", "방금 전"),
                deal["url"],
                deal.get("data_source_type", "SAMPLE_DEMO"),
                now,
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        cur.execute(
            "UPDATE deals SET price = ?, market_avg_price = ? WHERE platform = ? AND external_id = ?",
            (int(deal["price"]), int(deal["market_avg_price"]), deal["platform"], deal["external_id"]),
        )
        conn.commit()
        return False
    finally:
        conn.close()


def get_all_deals(category: Optional[str] = None, saved_only: bool = False) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM deals WHERE 1=1"
    params: List[Any] = []
    if category and category != "전체":
        query += " AND category = ?"
        params.append(category)
    if saved_only:
        query += " AND is_saved = 1"
    query += " ORDER BY created_at DESC, id DESC"
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def toggle_save_deal(platform: str, external_id: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT is_saved FROM deals WHERE platform = ? AND external_id = ?", (platform, external_id))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    new_val = 0 if row["is_saved"] == 1 else 1
    cur.execute(
        "UPDATE deals SET is_saved = ? WHERE platform = ? AND external_id = ?",
        (new_val, platform, external_id),
    )
    conn.commit()
    conn.close()
    return bool(new_val)
