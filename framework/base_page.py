"""页面基类：定义所有功能页面的通用接口和生命周期"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal


class BasePage(QWidget):
    """所有功能页面的基类

    子类需要重写以下方法:
        _setup_ui(self)        — 构建 UI 布局
        _setup_connections(self) — 连接信号槽

    可选重写:
        on_show(self)    — 页面显示时回调
        on_hide(self)    — 页面隐藏时回调

    生命周期:
        1. __init__(page_key, title, icon) — 构造
        2. initialize() — 调用 _setup_ui() + _setup_connections()
        3. on_show() / on_hide() — 由 NavigationManager 在切换时调用
    """

    # 信号
    page_shown = Signal()        # 页面已显示
    page_hidden = Signal()       # 页面已隐藏
    status_message = Signal(str)  # 向状态栏发送消息

    def __init__(self, page_key: str, title: str, icon: str = ""):
        """初始化页面基类

        Args:
            page_key: 页面唯一标识符（如 "home", "settings"）
            title: 页面标题（显示在导航栏中）
            icon: 图标名称（预留，暂未使用）
        """
        super().__init__()
        self._page_key = page_key
        self._title = title
        self._icon = icon
        self._initialized = False

    @property
    def page_key(self) -> str:
        """页面唯一标识符"""
        return self._page_key

    @property
    def title(self) -> str:
        """页面标题"""
        return self._title

    @property
    def icon(self) -> str:
        """页面图标"""
        return self._icon

    def initialize(self):
        """初始化页面内容（延迟加载）

        首次调用时执行 _setup_ui() 和 _setup_connections()，
        重复调用不会重复初始化。
        """
        if not self._initialized:
            self._setup_ui()
            self._setup_connections()
            self._initialized = True

    def _setup_ui(self):
        """子类重写：构建 UI 布局"""
        pass

    def _setup_connections(self):
        """子类重写：连接信号槽"""
        pass

    def on_show(self):
        """页面显示时回调（由 NavigationManager 调用）"""
        self.page_shown.emit()

    def on_hide(self):
        """页面隐藏时回调（由 NavigationManager 调用）"""
        self.page_hidden.emit()
