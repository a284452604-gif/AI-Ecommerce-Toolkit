"""首页/仪表盘：展示应用概览、快捷入口、版本信息"""

from pathlib import Path

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QScrollArea,
    QGridLayout,
)
from PySide6.QtCore import Qt

from framework.base_page import BasePage
from framework.app_context import AppContext
from components.card_widget import CardWidget


class HomePage(BasePage):
    """首页/仪表盘

    展示应用概览信息，包括：
    - 顶部欢迎横幅（应用名称 + 版本）
    - 功能卡片区域（展示即将上线的功能入口）
    - 底部技术信息
    """

    def __init__(self, page_key: str, title: str, icon: str = ""):
        super().__init__(page_key, title, icon)

    def _setup_ui(self):
        """构建首页 UI"""
        # 主滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 读取应用信息
        context = AppContext()
        config = context.config
        app_name = config.get("app.name", "AI电商工具箱")
        version = config.get("app.version", "0.1.0")

        # === 顶部欢迎横幅 ===
        banner = QWidget()
        banner.setObjectName("WelcomeBanner")
        banner.setStyleSheet("""
            #WelcomeBanner {
                background-color: #4a47a3;
                border-radius: 10px;
            }
        """)
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(24, 20, 24, 20)
        banner_layout.setSpacing(6)

        welcome_label = QLabel(f"欢迎使用 {app_name}")
        welcome_label.setStyleSheet("color: white; font-size: 18pt; font-weight: bold;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        banner_layout.addWidget(welcome_label)

        version_label = QLabel(f"版本 V{version}  |  AI 驱动的电商运营工具")
        version_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 10pt;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        banner_layout.addWidget(version_label)

        layout.addWidget(banner)

        # === 功能卡片区域 ===
        section_label = QLabel("功能模块")
        section_label.setObjectName("PageTitle")
        layout.addWidget(section_label)

        # 卡片网格布局
        cards_widget = QWidget()
        cards_layout = QGridLayout(cards_widget)
        cards_layout.setSpacing(16)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        # 功能卡片（即将上线）
        cards_data = [
            ("AI商品分析", "智能分析商品链接，提取关键信息，生成优化建议", "即将上线"),
            ("AI标题优化", "基于 AI 的商品标题自动优化，提升搜索排名和点击率", "即将上线"),
            ("竞品监控", "实时监控竞品价格、销量、评价变化", "即将上线"),
            ("数据导出", "将分析结果导出为 Excel、CSV 等格式", "即将上线"),
            ("批量管理", "批量管理商品信息，一键优化多个商品", "即将上线"),
            ("店铺概览", "多店铺数据汇总，全盘掌握运营状况", "即将上线"),
        ]

        for i, (title, desc, status) in enumerate(cards_data):
            card = CardWidget(title, desc, status)
            card.setFixedHeight(140)
            row = i // 3
            col = i % 3
            cards_layout.addWidget(card, row, col)

        layout.addWidget(cards_widget)

        # === 底部信息 ===
        layout.addStretch()

        info_label = QLabel("提示: 在左侧导航栏选择功能模块开始使用")
        info_label.setObjectName("PageSubtitle")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        scroll.setWidget(content)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
