"""应用上下文（单例）：持有全局共享的服务实例"""

from framework.config_manager import ConfigManager
from framework.log_manager import LogManager
from framework.signal_bus import SignalBus


class AppContext:
    """应用上下文单例，持有所有核心 Manager 实例

    在应用启动时调用 initialize() 初始化，
    之后全局通过 AppContext() 访问各 Manager。

    用法:
        context = AppContext()
        context.initialize(app_dir)
        config = context.config
        logger = context.logger.get_logger("module_name")
        signals = context.signals
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = False
            self._app_dir = ""
            self._config_manager = None
            self._log_manager = None
            self._signal_bus = None

    def initialize(self, app_dir: str):
        """在应用启动时调用，初始化所有 Manager

        Args:
            app_dir: 应用根目录路径
        """
        if self._initialized:
            return

        self._app_dir = app_dir
        self._config_manager = ConfigManager(app_dir)
        self._log_manager = LogManager(self._config_manager)
        self._signal_bus = SignalBus()
        self._initialized = True

    @property
    def config(self) -> ConfigManager:
        """获取配置管理器"""
        if self._config_manager is None:
            raise RuntimeError("AppContext 尚未初始化，请先调用 initialize()")
        return self._config_manager

    @property
    def logger(self) -> LogManager:
        """获取日志管理器"""
        if self._log_manager is None:
            raise RuntimeError("AppContext 尚未初始化，请先调用 initialize()")
        return self._log_manager

    @property
    def signals(self) -> SignalBus:
        """获取信号总线"""
        if self._signal_bus is None:
            raise RuntimeError("AppContext 尚未初始化，请先调用 initialize()")
        return self._signal_bus

    @property
    def app_dir(self) -> str:
        """获取应用根目录"""
        return self._app_dir
