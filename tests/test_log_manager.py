"""LogManager 单元测试"""

import logging
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from framework.config_manager import ConfigManager
from framework.log_manager import LogManager


class TestLogManager:
    """LogManager 测试套件"""

    def test_logger_creation(self, temp_app_dir):
        """测试 logger 创建"""
        config = ConfigManager(temp_app_dir)
        log_manager = LogManager(config)

        logger = log_manager.get_logger("test_module")
        assert logger is not None
        assert logger.name == "test_module"

    def test_log_file_creation(self, temp_app_dir):
        """测试日志文件创建"""
        config = ConfigManager(temp_app_dir)
        log_manager = LogManager(config)

        logger = log_manager.get_logger("test_file")
        logger.info("测试日志消息")

        log_file = Path(temp_app_dir) / "logs" / "app.log"
        assert log_file.exists()

        # 验证日志内容
        content = log_file.read_text(encoding="utf-8")
        assert "测试日志消息" in content
        assert "INFO" in content

    def test_log_level_from_config(self, temp_app_dir):
        """测试从配置读取日志级别"""
        config = ConfigManager(temp_app_dir)
        config.set("logging.level", "DEBUG")

        log_manager = LogManager(config)
        root_logger = logging.getLogger()

        assert root_logger.level == logging.DEBUG

    def test_different_log_levels(self, temp_app_dir):
        """测试不同日志级别"""
        config = ConfigManager(temp_app_dir)
        config.set("logging.level", "DEBUG")
        log_manager = LogManager(config)

        logger = log_manager.get_logger("test_levels")
        logger.debug("调试消息")
        logger.info("信息消息")
        logger.warning("警告消息")
        logger.error("错误消息")

        log_file = Path(temp_app_dir) / "logs" / "app.log"
        content = log_file.read_text(encoding="utf-8")

        assert "调试消息" in content
        assert "信息消息" in content
        assert "警告消息" in content
        assert "错误消息" in content

    def test_log_format(self, temp_app_dir):
        """测试日志格式"""
        config = ConfigManager(temp_app_dir)
        log_manager = LogManager(config)

        logger = log_manager.get_logger("test_format")
        logger.info("格式测试")

        log_file = Path(temp_app_dir) / "logs" / "app.log"
        content = log_file.read_text(encoding="utf-8")

        # 验证格式包含时间戳、级别、logger名称
        assert "[INFO" in content
        assert "[test_format]" in content
        assert "格式测试" in content

    def test_logs_directory_creation(self, temp_app_dir):
        """测试 logs 目录自动创建"""
        # 删除 logs 目录
        logs_dir = Path(temp_app_dir) / "logs"
        if logs_dir.exists():
            import shutil
            shutil.rmtree(logs_dir)

        config = ConfigManager(temp_app_dir)
        LogManager(config)

        assert logs_dir.exists()
