"""数据库管理器测试"""

import pytest
import tempfile
import os

from database.db_manager import DatabaseManager


class TestDatabaseManager:
    """测试 DatabaseManager"""

    @pytest.fixture(autouse=True)
    def setup_db(self, tmp_path):
        """在每个测试前初始化临时数据库"""
        # 重置单例
        DatabaseManager._instance = None
        db = DatabaseManager.get_instance()
        db.initialize(str(tmp_path))
        yield db
        db.shutdown()
        DatabaseManager._instance = None

    def test_initialization(self, setup_db):
        """测试数据库初始化"""
        db = setup_db
        assert db.initialized

    def test_save_and_get_analysis(self, setup_db):
        """测试保存和查询分析记录"""
        db = setup_db
        record = {
            "url": "https://item.jd.com/12345.html",
            "platform": "京东",
            "product_id": "12345",
            "title": "测试商品",
            "price": "¥99.00",
            "shop_name": "测试店铺",
            "description": "测试描述",
            "fetch_time": 1.23,
            "success": True,
            "error_message": "",
        }
        rid = db.save_analysis_record(record)
        assert rid > 0

        records = db.get_analysis_history(limit=10)
        assert len(records) == 1
        assert records[0]["platform"] == "京东"
        assert records[0]["title"] == "测试商品"
        assert records[0]["success"] is True

    def test_save_and_get_optimization(self, setup_db):
        """测试保存和查询优化记录"""
        db = setup_db
        record = {
            "original_title": "手机壳",
            "optimized_title": "iPhone 15 Pro Max 防摔硅胶手机壳",
            "style_key": "seo",
            "style_name": "搜索优化",
            "seo_keywords": ["手机壳", "防摔", "硅胶"],
            "improvement_reason": "增加了品牌型号和材质关键词",
            "tokens_used": 150,
            "success": True,
            "error_message": "",
            "product_info": {"category": "手机配件"},
        }
        rid = db.save_optimization_record(record)
        assert rid > 0

        records = db.get_optimization_history(limit=10)
        assert len(records) == 1
        assert records[0]["style_name"] == "搜索优化"
        assert records[0]["success"] is True
        assert len(records[0]["seo_keywords"]) == 3

    def test_filter_by_platform(self, setup_db):
        """测试按平台筛选"""
        db = setup_db
        db.save_analysis_record({"url": "url1", "platform": "京东", "title": "jd", "success": True})
        db.save_analysis_record({"url": "url2", "platform": "淘宝", "title": "tb", "success": True})
        db.save_analysis_record({"url": "url3", "platform": "京东", "title": "jd2", "success": True})

        records = db.get_analysis_history(platform="京东")
        assert len(records) == 2

        records = db.get_analysis_history(platform="淘宝")
        assert len(records) == 1

    def test_filter_by_style(self, setup_db):
        """测试按风格筛选优化记录"""
        db = setup_db
        db.save_optimization_record({"original_title": "a", "style_key": "seo", "style_name": "搜索优化", "success": True})
        db.save_optimization_record({"original_title": "b", "style_key": "brand", "style_name": "品牌调性", "success": True})

        records = db.get_optimization_history(style="seo")
        assert len(records) == 1
        records = db.get_optimization_history(style="brand")
        assert len(records) == 1

    def test_search_analysis(self, setup_db):
        """测试搜索分析记录"""
        db = setup_db
        db.save_analysis_record({"url": "u1", "platform": "京东", "title": "iPhone手机壳", "success": True})
        db.save_analysis_record({"url": "u2", "platform": "淘宝", "title": "数据线", "success": True})

        records = db.get_analysis_history(search="iPhone")
        assert len(records) == 1
        records = db.get_analysis_history(search="线")
        assert len(records) == 1
        records = db.get_analysis_history(search="不存在")
        assert len(records) == 0

    def test_delete_record(self, setup_db):
        """测试删除记录"""
        db = setup_db
        rid = db.save_analysis_record({"url": "u", "platform": "京东", "title": "test", "success": True})
        assert db.get_analysis_count() == 1

        db.delete_analysis_record(rid)
        assert db.get_analysis_count() == 0

    def test_clear_all(self, setup_db):
        """测试清空全部记录"""
        db = setup_db
        db.save_analysis_record({"url": "u1", "platform": "京东", "title": "a", "success": True})
        db.save_analysis_record({"url": "u2", "platform": "淘宝", "title": "b", "success": True})
        assert db.get_analysis_count() == 2

        db.clear_analysis_history()
        assert db.get_analysis_count() == 0

    def test_get_stats(self, setup_db):
        """测试统计数据"""
        db = setup_db
        db.save_analysis_record({"url": "u1", "platform": "京东", "title": "a", "success": True})
        db.save_analysis_record({"url": "u2", "platform": "淘宝", "title": "b", "success": True})
        db.save_optimization_record({"original_title": "x", "style_key": "seo", "style_name": "搜索优化", "success": True})

        stats = db.get_stats()
        assert stats["total_analysis"] == 2
        assert stats["total_optimization"] == 1
        assert "today_analysis" in stats
        assert "recent_analysis" in stats
        assert len(stats["recent_analysis"]) <= 5

    def test_export_analysis_to_list(self, setup_db):
        """测试导出分析记录为列表"""
        db = setup_db
        db.save_analysis_record({"url": "u1", "platform": "京东", "title": "a", "success": True, "price": "¥10"})
        db.save_analysis_record({"url": "u2", "platform": "淘宝", "title": "b", "success": True, "price": "¥20"})

        data = db.export_analysis_to_list()
        assert len(data) == 2
        assert data[0]["platform"] in ("京东", "淘宝")

        # 按平台筛选导出
        data = db.export_analysis_to_list(platform="京东")
        assert len(data) == 1

    def test_migrated_db_column_order(self, tmp_path):
        """回归测试：旧库经 ALTER 追加 keyword_layout 后列顺序变化，解析不应错位。

        复现 V1.2.1 线上 bug：旧版 optimization_history 表没有 keyword_layout，
        迁移时 ALTER TABLE 将其追加到末尾（index 12），而 _row_to_dict 按位置
        读取会错位，导致 product_info 指向 created_at 日期串并 json.loads 失败。
        """
        import sqlite3

        # 用独立路径，避免与 autouse fixture 的临时库冲突
        # 注意：DatabaseManager 把库放在 app_dir/data/toolkit.db
        custom_dir = tmp_path / "migrated"
        (custom_dir / "data").mkdir(parents=True)
        cx = sqlite3.connect(str(custom_dir / "data" / "toolkit.db"))
        # 旧版表结构（无 keyword_layout），共 12 列
        cx.execute("""CREATE TABLE optimization_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_title TEXT NOT NULL,
            optimized_title TEXT DEFAULT '',
            style_key TEXT DEFAULT '',
            style_name TEXT DEFAULT '',
            seo_keywords TEXT DEFAULT '[]',
            improve_reason TEXT DEFAULT '',
            tokens_used INTEGER DEFAULT 0,
            success INTEGER DEFAULT 0,
            error_msg TEXT DEFAULT '',
            product_info TEXT DEFAULT '{}',
            created_at TEXT NOT NULL
        )""")
        cx.execute(
            """INSERT INTO optimization_history
               (original_title, optimized_title, style_key, style_name,
                seo_keywords, improve_reason, tokens_used, success,
                error_msg, product_info, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            ("原标题X", "优化标题X", "seo", "搜索优化",
             '["关键词A","关键词B"]', "优化理由说明", 120, 1, "",
             '{"cat":"手机"}', "2026-07-30 20:26:37"),
        )
        cx.commit()
        cx.close()

        # 重置单例并用同一文件初始化（触发 ALTER 追加 keyword_layout 到末尾）
        DatabaseManager._instance = None
        db = DatabaseManager.get_instance()
        db.initialize(str(custom_dir))

        records = db.get_optimization_history(limit=10)
        assert len(records) == 1
        r = records[0]
        assert isinstance(r["seo_keywords"], list)
        assert r["seo_keywords"] == ["关键词A", "关键词B"]
        assert isinstance(r["product_info"], dict)
        assert r["product_info"] == {"cat": "手机"}
        assert r["created_at"] == "2026-07-30 20:26:37"
        assert r["keyword_layout"] == ""  # 迁移新增列的默认值
        assert r["improvement_reason"] == "优化理由说明"
        assert r["tokens_used"] == 120
        assert r["success"] is True
        db.shutdown()
        DatabaseManager._instance = None

    def test_corrupt_json_does_not_break_load(self, setup_db):
        """回归测试：单条记录的 JSON 字段损坏不应拖垮整个历史加载"""
        db = setup_db
        # 直接写入一条 seo_keywords / product_info 为非 JSON 文本的脏数据
        db._cx.execute(
            "INSERT INTO optimization_history "
            "(original_title, seo_keywords, product_info, created_at) "
            "VALUES (?,?,?,?)",
            ("脏数据标题", "这不是合法JSON", "也不是", "2026-07-30 20:26:37"),
        )
        db._cx.commit()
        # 同时写入一条正常数据
        db.save_optimization_record({
            "original_title": "正常标题",
            "style_key": "seo",
            "style_name": "搜索优化",
            "seo_keywords": ["a"],
            "product_info": {"k": "v"},
            "success": True,
        })
        records = db.get_optimization_history(limit=10)
        assert len(records) == 2
        titles = {r["original_title"] for r in records}
        assert "脏数据标题" in titles
        assert "正常标题" in titles
        # 脏数据降级为默认值，不抛异常
        for r in records:
            assert isinstance(r["seo_keywords"], list)
            assert isinstance(r["product_info"], dict)
