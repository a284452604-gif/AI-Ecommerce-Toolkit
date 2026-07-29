"""日志管理器：配置根 logger，文件轮转 + 控制台输出"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


class LogManager:
    """日志管理器：配置 Python logging，支持文件轮转和控制台输出"""

    LOG_FORMAT = "[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, config):
        """初始化日志管理器

        Args:
            config: ConfigManager 实例，用于读取日志配置
        """
        self._config = config
        self._app_dir = Path(config._app_dir)
        self._setup()

    def _setup(self):
        """配置 logging 系统"""
        # 1. 创建 logs/ 目录
        log_dir = self._app_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # 2. 读取配置
        level_str = self._config.get("logging.level", "INFO")
        max_bytes = self._config.get("logging.max_bytes", 5242880)
        backup_count = self._config.get("logging.backup_count", 10)

        level = getattr(logging, level_str.upper(), logging.INFO)

        # 3. 创建格式化器
        formatter = logging.Formatter(self.LOG_FORMAT, datefmt=self.DATE_FORMAT)

        # 4. 创建文件处理器（轮转）
        log_file = log_dir / "app.log"
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)

        # 5. 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)

        # 6. 配置根 logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # 移除已有处理器，避免重复
        root_logger.handlers.clear()
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """获取命名 logger

        Args:
            name: logger 名称，通常用模块名

        Returns:
            logging.Logger 实例
        """
        return logging.getLogger(name)
