"""导航管理器：管理 QStackedWidget 中的页面注册与切换"""

from PySide6.QtWidgets import QStackedWidget
from PySide6.QtCore import QObject, Signal

from framework.base_page import BasePage


class NavigationManager(QObject):
    """导航管理器：管理 QStackedWidget 中的页面注册与切换

    职责：
    - 注册页面到 QStackedWidget
    - 切换当前显示的页面
    - 跟踪当前页面状态
    - 发出页面切换信号

    通过 NavigationManager，导航逻辑与导航 UI（Sidebar）完全解耦。
    """

    page_changed = Signal(str)  # 参数: page_key — 页面已切换

    def __init__(self, stacked_widget: QStackedWidget):
        """初始化导航管理器

        Args:
            stacked_widget: QStackedWidget 实例，用于管理页面显示
        """
        super().__init__()
        self._stacked = stacked_widget
        self._pages: dict[str, BasePage] = {}
        self._current_key: str = ""

    def register_page(self, page: BasePage) -> int:
        """注册页面到 QStackedWidget

        Args:
            page: 要注册的页面实例

        Returns:
            页面在 QStackedWidget 中的索引
        """
        page.initialize()
        index = self._stacked.addWidget(page)
        self._pages[page.page_key] = page
        return index

    def navigate_to(self, page_key: str):
        """切换到指定页面

        Args:
            page_key: 目标页面标识符
        """
        if page_key not in self._pages:
            return

        # 隐藏当前页面
        if self._current_key and self._current_key in self._pages:
            self._pages[self._current_key].on_hide()

        # 显示目标页面
        page = self._pages[page_key]
        self._stacked.setCurrentWidget(page)
        page.on_show()
        self._current_key = page_key
        self.page_changed.emit(page_key)

    def get_current_page_key(self) -> str:
        """获取当前页面标识符"""
        return self._current_key

    def get_page(self, page_key: str) -> BasePage | None:
        """获取指定页面实例

        Args:
            page_key: 页面标识符

        Returns:
            页面实例，不存在则返回 None
        """
        return self._pages.get(page_key)

    @property
    def page_count(self) -> int:
        """已注册的页面数量"""
        return len(self._pages)
