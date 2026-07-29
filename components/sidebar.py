"""侧边栏导航组件"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Signal, Qt

from components.nav_item import NavItem


class Sidebar(QWidget):
    """侧边栏导航组件

    包含三个区域：
    - 顶部：应用 Logo / 名称
    - 中间：导航项列表
    - 底部：版本号

    点击导航项时发出 navigate_requested 信号。
    """

    navigate_requested = Signal(str)  # 参数: page_key

    SIDEBAR_WIDTH = 200  # 固定侧边栏宽度

    def __init__(self, app_name: str = "AI电商工具箱", version: str = "0.1.0"):
        """初始化侧边栏

        Args:
            app_name: 应用名称（显示在顶部）
            version: 版本号（显示在底部）
        """
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(self.SIDEBAR_WIDTH)

        self._app_name = app_name
        self._version = version
        self._items: dict[str, NavItem] = {}
        self._current_active = ""

        self._setup_ui()

    def _setup_ui(self):
        """构建侧边栏布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部 Logo / 应用名称区域
        logo_label = QLabel(self._app_name)
        logo_label.setObjectName("SidebarLogo")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setFixedHeight(60)
        layout.addWidget(logo_label)

        # 导航项容器
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        self._nav_layout = nav_layout
        layout.addWidget(nav_container)

        # 弹性空间，将版本号推到底部
        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # 底部版本号
        version_label = QLabel(f"V{self._version}")
        version_label.setObjectName("SidebarVersion")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setFixedHeight(36)
        layout.addWidget(version_label)

    def add_item(self, key: str, title: str, icon: str = ""):
        """添加导航项

        Args:
            key: 页面唯一标识符
            title: 显示文本
            icon: 图标名称（预留）
        """
        item = NavItem(key, title, icon)
        item.clicked_with_key.connect(self._on_item_clicked)
        self._items[key] = item
        self._nav_layout.addWidget(item)

    def _on_item_clicked(self, key: str):
        """导航项点击回调"""
        self.navigate_requested.emit(key)

    def set_active(self, key: str):
        """设置高亮的导航项

        Args:
            key: 要高亮的页面标识符
        """
        self._current_active = key
        for item_key, item in self._items.items():
            item.set_active(item_key == key)

    def update_version(self, version: str):
        """更新底部版本号显示"""
        self._version = version
