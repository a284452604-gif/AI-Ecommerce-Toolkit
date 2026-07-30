"""首页/仪表盘：展示应用概览、快捷入口、版本信息、实时统计"""

from pathlib import Path

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QScrollArea,
    QGridLayout,
    QFrame,
)
from PySide6.QtCore import Qt

from framework.base_page import BasePage
from framework.app_context import AppContext
from components.card_widget import CardWidget


class HomePage(BasePage):
    """首页/仪表盘

    展示:
    - 顶部欢迎横幅 + 实时统计数据
    - 功能卡片区域
    - 底部提示
    """

    def __init__(self, page_key: str, title: str, icon: str = ""):
        super().__init__(page_key, title, icon)
        self._context = AppContext()
        self._stats_labels: dict[str, QLabel] = {}

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        config = self._context.config
        app_name = config.get("app.name", "AI电商工具箱")
        version = config.get("app.version", "0.3.0")

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
        banner_layout.addWidget(welcome_label)

        version_label = QLabel(f"版本 V{version}  |  AI 驱动的电商运营工具")
        version_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 10pt;")
        banner_layout.addWidget(version_label)

        layout.addWidget(banner)

        # === 数据统计条 ===
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background: #fff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(16, 12, 16, 12)
        stats_layout.setSpacing(24)

        for key, label_text in [
            ("total_analysis", "分析次数"),
            ("total_optimization", "优化次数"),
            ("today_analysis", "今日分析"),
            ("today_optimization", "今日优化"),
        ]:
            item = QVBoxLayout()
            item.setSpacing(2)
            value = QLabel("--")
            value.setStyleSheet("font-size: 18pt; font-weight: bold; color: #4a47a3;")
            item.addWidget(value, alignment=Qt.AlignmentFlag.AlignCenter)
            desc = QLabel(label_text)
            desc.setStyleSheet("font-size: 9pt; color: #888;")
            item.addWidget(desc, alignment=Qt.AlignmentFlag.AlignCenter)
            stats_layout.addLayout(item)
            self._stats_labels[key] = value

        stats_layout.addStretch()
        layout.addWidget(stats_frame)

        # === 功能卡片区域 ===
        section_label = QLabel("功能模块")
        section_label.setObjectName("PageTitle")
        layout.addWidget(section_label)

        cards_widget = QWidget()
        cards_layout = QGridLayout(cards_widget)
        cards_layout.setSpacing(16)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        cards_data = [
            ("商品链接分析", "智能分析商品链接，识别平台、提取商品信息\n支持批量链接、历史溯源", "可用"),
            ("AI标题优化", "基于 DeepSeek AI 的商品标题自动优化\n三种风格、多标题批量、SEO关键词", "可用"),
            ("历史记录", "统一管理分析/优化历史记录\n搜索、筛选、删除、追溯", "可用"),
            ("数据导出", "将分析/优化结果导出为 Excel、CSV 格式\n支持日期和平台筛选", "可用"),
            ("竞品监控", "实时监控竞品价格、销量、评价变化", "即将上线"),
            ("店铺概览", "多店铺数据汇总，全盘掌握运营状况", "即将上线"),
        ]

        for i, (title, desc, status) in enumerate(cards_data):
            card = CardWidget(title, desc, status)
            card.setFixedHeight(140)
            row = i // 3
            col = i % 3
            cards_layout.addWidget(card, row, col)

        layout.addWidget(cards_widget)

        layout.addStretch()

        info_label = QLabel("提示: 在左侧导航栏选择功能模块开始使用")
        info_label.setObjectName("PageSubtitle")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def on_show(self):
        """页面显示时刷新统计数据"""
        self._refresh_stats()

    def _refresh_stats(self):
        """从数据库获取统计数据"""
        try:
            stats = self._context.db.get_stats()
            mappings = {
                "total_analysis": str(stats.get("total_analysis", 0)),
                "total_optimization": str(stats.get("total_optimization", 0)),
                "today_analysis": str(stats.get("today_analysis", 0)),
                "today_optimization": str(stats.get("today_optimization", 0)),
            }
            for key, label in self._stats_labels.items():
                label.setText(mappings.get(key, "--"))
        except Exception:
            pass  # 首次启动 DB 可能还没数据
