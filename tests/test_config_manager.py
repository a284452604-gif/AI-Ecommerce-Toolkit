"""ConfigManager 单元测试"""

import json
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from framework.config_manager import ConfigManager


class TestConfigManager:
    """ConfigManager 测试套件"""

    def test_load_default_config(self, temp_app_dir):
        """测试加载默认配置"""
        config = ConfigManager(temp_app_dir)

        assert config.get("app.name") == "AI电商工具箱"
        assert config.get("app.version") == "1.2.3"
        assert config.get("window.width") == 1200
        assert config.get("window.height") == 800

    def test_get_with_default(self, temp_app_dir):
        """测试 get 方法返回默认值"""
        config = ConfigManager(temp_app_dir)

        assert config.get("nonexistent.key", "default_value") == "default_value"
        assert config.get("app.nonexistent", 42) == 42

    def test_set_and_get(self, temp_app_dir):
        """测试 set 和 get 方法"""
        config = ConfigManager(temp_app_dir)

        config.set("ai_service.provider", "OpenAI")
        config.set("ai_service.api_key", "sk-test-key")

        assert config.get("ai_service.provider") == "OpenAI"
        assert config.get("ai_service.api_key") == "sk-test-key"

    def test_set_nested_key(self, temp_app_dir):
        """测试设置嵌套键（自动创建中间层级）"""
        config = ConfigManager(temp_app_dir)

        config.set("new_section.new_key", "new_value")
        assert config.get("new_section.new_key") == "new_value"

    def test_save_and_reload(self, temp_app_dir):
        """测试保存和重新加载配置"""
        config = ConfigManager(temp_app_dir)
        config.set("ai_service.provider", "DeepSeek")
        config.set("window.width", 1400)
        config.save()

        # 重新加载
        config2 = ConfigManager(temp_app_dir)
        assert config2.get("ai_service.provider") == "DeepSeek"
        assert config2.get("window.width") == 1400

    def test_reset_to_default(self, temp_app_dir):
        """测试重置为默认配置"""
        config = ConfigManager(temp_app_dir)
        config.set("ai_service.provider", "OpenAI")
        config.set("window.width", 9999)
        config.save()

        config.reset_to_default()

        assert config.get("ai_service.provider") == "deepseek"
        assert config.get("window.width") == 1200

    def test_user_config_merge(self, temp_app_dir):
        """测试用户配置与默认配置的深度合并"""
        # 创建用户配置文件，只覆盖部分值
        user_config = {
            "ai_service": {
                "provider": "OpenAI",
                "api_key": "sk-test"
            },
            "window": {
                "width": 1600
            }
        }
        user_config_path = Path(temp_app_dir) / "config" / "app_config.json"
        with open(user_config_path, "w", encoding="utf-8") as f:
            json.dump(user_config, f)

        config = ConfigManager(temp_app_dir)

        # 用户配置覆盖的值
        assert config.get("ai_service.provider") == "OpenAI"
        assert config.get("ai_service.api_key") == "sk-test"
        assert config.get("window.width") == 1600

        # 默认配置保留的值（深度合并）
        assert config.get("ai_service.model") == "deepseek-chat"
        assert config.get("ai_service.timeout") == 30
        assert config.get("window.height") == 800

    def test_get_all(self, temp_app_dir):
        """测试获取完整配置字典"""
        config = ConfigManager(temp_app_dir)
        all_config = config.get_all()

        assert isinstance(all_config, dict)
        assert "app" in all_config
        assert "window" in all_config
        assert "ai_service" in all_config
        assert "appearance" in all_config
        assert "logging" in all_config

    def test_corrupted_user_config(self, temp_app_dir):
        """测试用户配置损坏时回退到默认配置"""
        user_config_path = Path(temp_app_dir) / "config" / "app_config.json"
        user_config_path.write_text("invalid json content", encoding="utf-8")

        config = ConfigManager(temp_app_dir)

        # 应回退到默认配置
        assert config.get("app.name") == "AI电商工具箱"
