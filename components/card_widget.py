"""卡片容器组件：用于首页等功能卡片展示"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class CardWidget(QWidget):
    """可复用卡片容器组件

    用于首页展示功能入口卡片，包含标题、描述和状态标签。
    通过 QSS #CardWidget 选择器统一样式。
    """

    def __init__(
        self,
        title: str = "",
        description: str = "",
        status: str = "",
        parent: QWidget = None,
    ):
        """初始化卡片

        Args:
            title: 卡片标题
            description: 卡片描述文字
            status: 状态标签（如 "即将上线"）
            parent: 父组件
        """
        super().__init__(parent)
        self.setObjectName("CardWidget")

        self._title = title
        self._description = description
        self._status = status

        self._setup_ui()

    def _setup_ui(self):
        """构建卡片布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        # 标题
        self._title_label = QLabel(self._title)
        self._title_label.setObjectName("CardTitle")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._title_label)

        # 描述
        self._desc_label = QLabel(self._description)
        self._desc_label.setObjectName("CardDescription")
        self._desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._desc_label.setWordWrap(True)
        layout.addWidget(self._desc_label)

        # 状态标签
        if self._status:
            self._status_label = QLabel(self._status)
            self._status_label.setObjectName("CardStatus")
            self._status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
            layout.addWidget(self._status_label)

        layout.addStretch()

    def set_title(self, title: str):
        """设置卡片标题"""
        self._title = title
        self._title_label.setText(title)

    def set_description(self, description: str):
        """设置卡片描述"""
        self._description = description
        self._desc_label.setText(description)

    def set_status(self, status: str):
        """设置状态标签"""
        self._status = status
        if hasattr(self, "_status_label") and self._status_label:
            self._status_label.setText(status)
