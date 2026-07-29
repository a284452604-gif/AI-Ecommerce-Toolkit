"""侧边栏单个导航项组件"""

from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Signal, Qt


class NavItem(QPushButton):
    """侧边栏单个导航项

    支持选中状态（checkable），点击时发出带有 page_key 的信号。
    通过 QSS 的 :checked 伪状态实现高亮效果。
    """

    clicked_with_key = Signal(str)  # 参数: page_key

    def __init__(self, key: str, title: str, icon: str = ""):
        """初始化导航项

        Args:
            key: 页面唯一标识符
            title: 显示文本
            icon: 图标名称（预留）
        """
        super().__init__()
        self._key = key
        self._title = title
        self._icon = icon

        self.setText(title)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("NavItem")

        # 点击时发出信号
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self):
        """点击时发出带有 key 的信号"""
        self.clicked_with_key.emit(self._key)

    @property
    def key(self) -> str:
        """页面标识符"""
        return self._key

    def set_active(self, active: bool):
        """设置激活状态

        Args:
            active: 是否激活（高亮）
        """
        self.setChecked(active)
