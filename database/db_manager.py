"""SQLite 数据库管理器

统一管理所有业务数据的持久化存储，包括:
- 商品链接分析历史
- AI 标题优化历史

数据库文件: data/toolkit.db
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Optional


# ── 表结构定义 ──────────────────────────────────────────────

CREATE_ANALYSIS_TABLE = """
CREATE TABLE IF NOT EXISTS analysis_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    url         TEXT    NOT NULL,
    platform    TEXT    DEFAULT '',
    product_id  TEXT    DEFAULT '',
    title       TEXT    DEFAULT '',
    price       TEXT    DEFAULT '',
    shop_name   TEXT    DEFAULT '',
    description TEXT    DEFAULT '',
    fetch_time  REAL    DEFAULT 0,
    success     INTEGER DEFAULT 0,
    error_msg   TEXT    DEFAULT '',
    created_at  TEXT    NOT NULL
)
"""

CREATE_OPTIMIZATION_TABLE = """
CREATE TABLE IF NOT EXISTS optimization_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    original_title  TEXT    NOT NULL,
    optimized_title TEXT    DEFAULT '',
    style_key       TEXT    DEFAULT '',
    style_name      TEXT    DEFAULT '',
    seo_keywords    TEXT    DEFAULT '[]',
    improve_reason  TEXT    DEFAULT '',
    keyword_layout  TEXT    DEFAULT '',
    tokens_used     INTEGER DEFAULT 0,
    success         INTEGER DEFAULT 0,
    error_msg       TEXT    DEFAULT '',
    product_info    TEXT    DEFAULT '{}',
    created_at      TEXT    NOT NULL
)
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_analysis_created ON analysis_history(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_analysis_platform ON analysis_history(platform)",
    "CREATE INDEX IF NOT EXISTS idx_optimization_created ON optimization_history(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_optimization_style ON optimization_history(style_key)",
]


def _safe_json_loads(value, default):
    """安全解析 JSON 字段，解析失败时返回默认值。

    避免单条历史记录中的脏数据（如列顺序错位写入的文本）导致
    整个历史列表加载抛异常。
    """
    if value is None or value == "":
        return default
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return default


class DatabaseManager:
    """SQLite 数据库管理器（线程安全单例）

    用法:
        db = DatabaseManager.get_instance()
        db.initialize(app_dir)
        db.save_analysis_record(...)
        records = db.get_analysis_history(limit=50)
    """

    _instance: Optional[DatabaseManager] = None
    _lock = threading.Lock()

    def __init__(self):
        self._conn: Optional[sqlite3.Connection] = None
        self._db_path: str = ""
        self._local = threading.local()

    # ── 单例 ────────────────────────────────────────────────

    @classmethod
    def get_instance(cls) -> DatabaseManager:
        """获取单例实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ── 初始化 ──────────────────────────────────────────────

    @property
    def initialized(self) -> bool:
        return self._conn is not None

    def initialize(self, app_dir: str):
        """初始化数据库连接并创建表

        Args:
            app_dir: 应用根目录路径
        """
        if self._conn is not None:
            return

        # 确保 data 目录存在
        data_dir = os.path.join(app_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        self._db_path = os.path.join(data_dir, "toolkit.db")
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        # 使用 Row 工厂，使行可按列名访问，避免因表结构迁移导致列顺序错位
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

        # 建表
        self._conn.execute(CREATE_ANALYSIS_TABLE)
        self._conn.execute(CREATE_OPTIMIZATION_TABLE)
        for idx_sql in CREATE_INDEXES:
            self._conn.execute(idx_sql)
        # 迁移：为旧表增加 keyword_layout 字段
        self._migrate_add_keyword_layout()
        self._conn.commit()

    def shutdown(self):
        """关闭数据库连接"""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _migrate_add_keyword_layout(self):
        """为旧版 optimization_history 表增加 keyword_layout 字段"""
        try:
            self._conn.execute(
                "ALTER TABLE optimization_history ADD COLUMN keyword_layout TEXT DEFAULT ''"
            )
        except sqlite3.OperationalError:
            # 字段已存在
            pass

    # ── 内部辅助 ────────────────────────────────────────────

    @property
    def _cx(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("DatabaseManager 尚未初始化")
        return self._conn

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ══════════════════════════════════════════════════════════
    #  分析记录 CRUD
    # ══════════════════════════════════════════════════════════

    def save_analysis_record(self, record: dict) -> int:
        """保存一条分析记录，返回自增 ID

        Args:
            record: 包含 url, platform, product_id, title, price,
                    shop_name, description, fetch_time, success, error_msg 的字典
        """
        sql = """INSERT INTO analysis_history
            (url, platform, product_id, title, price, shop_name,
             description, fetch_time, success, error_msg, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

        params = (
            record.get("url", ""),
            record.get("platform", ""),
            record.get("product_id", ""),
            record.get("title", ""),
            record.get("price", ""),
            record.get("shop_name", ""),
            record.get("description", ""),
            record.get("fetch_time", 0.0),
            1 if record.get("success") else 0,
            record.get("error_message", ""),
            self._now(),
        )

        cursor = self._cx.execute(sql, params)
        self._cx.commit()
        return cursor.lastrowid

    def get_analysis_history(self, limit: int = 50, offset: int = 0,
                             platform: str = "", search: str = "") -> list[dict]:
        """查询分析历史记录

        Args:
            limit: 返回条数
            offset: 偏移量
            platform: 按平台筛选（空=全部）
            search: 按标题/商品ID/店铺名搜索
        """
        sql = "SELECT * FROM analysis_history WHERE 1=1"
        params: list = []

        if platform:
            sql += " AND platform = ?"
            params.append(platform)

        if search:
            sql += " AND (title LIKE ? OR product_id LIKE ? OR shop_name LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like, like])

        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self._cx.execute(sql, params).fetchall()
        return [self._row_to_dict(row, "analysis") for row in rows]

    def get_analysis_count(self, platform: str = "") -> int:
        """获取分析记录总数"""
        if platform:
            row = self._cx.execute(
                "SELECT COUNT(*) FROM analysis_history WHERE platform = ?",
                (platform,)
            ).fetchone()
        else:
            row = self._cx.execute(
                "SELECT COUNT(*) FROM analysis_history"
            ).fetchone()
        return row[0] if row else 0

    def delete_analysis_record(self, record_id: int):
        """删除单条分析记录"""
        self._cx.execute("DELETE FROM analysis_history WHERE id = ?", (record_id,))
        self._cx.commit()

    def clear_analysis_history(self):
        """清空所有分析记录"""
        self._cx.execute("DELETE FROM analysis_history")
        self._cx.commit()

    # ══════════════════════════════════════════════════════════
    #  优化记录 CRUD
    # ══════════════════════════════════════════════════════════

    def save_optimization_record(self, record: dict) -> int:
        """保存一条优化记录，返回自增 ID

        Args:
            record: 包含 original_title, optimized_title, style_key,
                    style_name, seo_keywords, improvement_reason,
                    tokens_used, success, error_message, product_info 的字典
        """
        sql = """INSERT INTO optimization_history
            (original_title, optimized_title, style_key, style_name,
             seo_keywords, improve_reason, keyword_layout, tokens_used,
             success, error_msg, product_info, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

        params = (
            record.get("original_title", ""),
            record.get("optimized_title", ""),
            record.get("style_key", ""),
            record.get("style_name", ""),
            json.dumps(record.get("seo_keywords", []), ensure_ascii=False),
            record.get("improvement_reason", ""),
            record.get("keyword_layout", ""),
            record.get("tokens_used", 0),
            1 if record.get("success") else 0,
            record.get("error_message", ""),
            json.dumps(record.get("product_info", {}), ensure_ascii=False),
            self._now(),
        )

        cursor = self._cx.execute(sql, params)
        self._cx.commit()
        return cursor.lastrowid

    def get_optimization_history(self, limit: int = 50, offset: int = 0,
                                  style: str = "", search: str = "") -> list[dict]:
        """查询优化历史记录

        Args:
            limit: 返回条数
            offset: 偏移量
            style: 按风格筛选 (seo/promotion/brand)
            search: 按原标题或优化标题搜索
        """
        sql = "SELECT * FROM optimization_history WHERE 1=1"
        params: list = []

        if style:
            sql += " AND style_key = ?"
            params.append(style)

        if search:
            sql += " AND (original_title LIKE ? OR optimized_title LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like])

        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self._cx.execute(sql, params).fetchall()
        return [self._row_to_dict(row, "optimization") for row in rows]

    def get_optimization_count(self, style: str = "") -> int:
        """获取优化记录总数"""
        if style:
            row = self._cx.execute(
                "SELECT COUNT(*) FROM optimization_history WHERE style_key = ?",
                (style,)
            ).fetchone()
        else:
            row = self._cx.execute(
                "SELECT COUNT(*) FROM optimization_history"
            ).fetchone()
        return row[0] if row else 0

    def delete_optimization_record(self, record_id: int):
        """删除单条优化记录"""
        self._cx.execute("DELETE FROM optimization_history WHERE id = ?", (record_id,))
        self._cx.commit()

    def clear_optimization_history(self):
        """清空所有优化记录"""
        self._cx.execute("DELETE FROM optimization_history")
        self._cx.commit()

    # ══════════════════════════════════════════════════════════
    #  统计查询
    # ══════════════════════════════════════════════════════════

    def get_stats(self) -> dict:
        """获取仪表盘统计数据"""
        today = datetime.now().strftime("%Y-%m-%d")

        total_analysis = self._cx.execute(
            "SELECT COUNT(*) FROM analysis_history"
        ).fetchone()[0]

        total_optimization = self._cx.execute(
            "SELECT COUNT(*) FROM optimization_history"
        ).fetchone()[0]

        today_analysis = self._cx.execute(
            "SELECT COUNT(*) FROM analysis_history WHERE created_at >= ?",
            (today,)
        ).fetchone()[0]

        today_optimization = self._cx.execute(
            "SELECT COUNT(*) FROM optimization_history WHERE created_at >= ?",
            (today,)
        ).fetchone()[0]

        # 最近 5 条记录
        recent_analysis = self._cx.execute(
            "SELECT * FROM analysis_history ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
        recent_optimization = self._cx.execute(
            "SELECT * FROM optimization_history ORDER BY created_at DESC LIMIT 5"
        ).fetchall()

        return {
            "total_analysis": total_analysis,
            "total_optimization": total_optimization,
            "today_analysis": today_analysis,
            "today_optimization": today_optimization,
            "recent_analysis": [self._row_to_dict(r, "analysis") for r in recent_analysis],
            "recent_optimization": [self._row_to_dict(r, "optimization") for r in recent_optimization],
        }

    # ══════════════════════════════════════════════════════════
    #  导出
    # ══════════════════════════════════════════════════════════

    def export_analysis_to_list(self, platform: str = "",
                                 date_from: str = "", date_to: str = "") -> list[dict]:
        """导出分析记录为字典列表，供 export 模块使用"""
        sql = "SELECT * FROM analysis_history WHERE 1=1"
        params: list = []

        if platform:
            sql += " AND platform = ?"
            params.append(platform)
        if date_from:
            sql += " AND created_at >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND created_at <= ?"
            params.append(date_to + " 23:59:59")

        sql += " ORDER BY created_at DESC"
        rows = self._cx.execute(sql, params).fetchall()
        return [self._row_to_dict(r, "analysis") for r in rows]

    def export_optimization_to_list(self, style: str = "",
                                     date_from: str = "", date_to: str = "") -> list[dict]:
        """导出优化记录为字典列表"""
        sql = "SELECT * FROM optimization_history WHERE 1=1"
        params: list = []

        if style:
            sql += " AND style_key = ?"
            params.append(style)
        if date_from:
            sql += " AND created_at >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND created_at <= ?"
            params.append(date_to + " 23:59:59")

        sql += " ORDER BY created_at DESC"
        rows = self._cx.execute(sql, params).fetchall()
        return [self._row_to_dict(r, "optimization") for r in rows]

    # ── 工具方法 ────────────────────────────────────────────

    def _row_to_dict(self, row, table: str) -> dict:
        """将数据库行转换为字典（按列名访问，避免迁移后列顺序错位）"""
        if table == "analysis":
            return {
                "id": row["id"],
                "url": row["url"],
                "platform": row["platform"],
                "product_id": row["product_id"],
                "title": row["title"],
                "price": row["price"],
                "shop_name": row["shop_name"],
                "description": row["description"],
                "fetch_time": row["fetch_time"],
                "success": bool(row["success"]),
                "error_message": row["error_msg"],
                "created_at": row["created_at"],
            }
        else:  # optimization
            return {
                "id": row["id"],
                "original_title": row["original_title"],
                "optimized_title": row["optimized_title"],
                "style_key": row["style_key"],
                "style_name": row["style_name"],
                "seo_keywords": _safe_json_loads(row["seo_keywords"], []),
                "improvement_reason": row["improve_reason"],
                "keyword_layout": row["keyword_layout"],
                "tokens_used": row["tokens_used"],
                "success": bool(row["success"]),
                "error_message": row["error_msg"],
                "product_info": _safe_json_loads(row["product_info"], {}),
                "created_at": row["created_at"],
            }
