"""服务基类：为未来的功能服务（如 AI 服务、数据服务等）提供统一接口"""

from abc import ABC, abstractmethod


class BaseService(ABC):
    """服务基类（抽象）

    未来所有功能服务（如 AIService、DataService、ExportService 等）
    都应继承此基类，统一服务生命周期管理。

    V0.1 仅为占位，无具体实现。
    """

    def __init__(self, name: str = ""):
        self._name = name
        self._initialized = False

    @property
    def name(self) -> str:
        """服务名称"""
        return self._name

    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._initialized

    @abstractmethod
    def initialize(self):
        """初始化服务（子类实现）"""
        pass

    @abstractmethod
    def shutdown(self):
        """关闭服务，释放资源（子类实现）"""
        pass
