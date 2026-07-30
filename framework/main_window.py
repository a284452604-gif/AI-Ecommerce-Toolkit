"""主窗口：组装所有 UI 组件，管理窗口生命周期"""

from pathlib import Path

from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from framework.app_context import AppContext
from framework.navigation_manager import NavigationManager
from framework.base_page import BasePage
from components.sidebar import Sidebar


class MainWindow(QMainWindow):
    """应用主窗口

    组装侧边栏（Sidebar）和页面栈（QStackedWidget），
    管理窗口生命周期（恢复/保存窗口状态）。

    布局结构:
        QMainWindow
        └── Central Widget (QHBoxLayout)
            ├── Sidebar (固定宽度 200px)
            └── QStackedWidget (stretch=1)
                ├── HomePage
                ├── SettingsPage
                └── AboutPage
    """

    def __init__(self):
        super().__init__()

        self._context = AppContext()
        self._nav_manager: NavigationManager | None = None
        self._sidebar: Sidebar | None = None
        self._stacked: QStackedWidget | None = None

        self._setup_window()
        self._setup_ui()
        self._setup_connections()
        self._register_pages()
        self._apply_stylesheet()
        self._restore_window_state()

    def _setup_window(self):
        """设置窗口基础属性"""
        config = self._context.config
        app_name = config.get("app.name", "AI电商工具箱")
        self.setWindowTitle(app_name)
        self.setMinimumSize(900, 600)

        # 设置窗口图标
        icon_path = Path(self._context.app_dir) / "resources" / "icons" / "app_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _setup_ui(self):
        """构建主布局：Sidebar + QStackedWidget"""
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 侧边栏
        config = self._context.config
        app_name = config.get("app.name", "AI电商工具箱")
        version = config.get("app.version", "0.1.0")
        self._sidebar = Sidebar(app_name, version)

        # 页面栈
        self._stacked = QStackedWidget()

        layout.addWidget(self._sidebar)
        layout.addWidget(self._stacked, stretch=1)

        self.setCentralWidget(central)

        # 导航管理器
        self._nav_manager = NavigationManager(self._stacked)

        # 状态栏
        self.statusBar().showMessage("就绪")

    def _setup_connections(self):
        """连接信号槽"""
        signals = self._context.signals

        # 侧边栏 → 信号总线 → 导航管理器
        self._sidebar.navigate_requested.connect(signals.navigate_to.emit)
        signals.navigate_to.connect(self._nav_manager.navigate_to)

        # 导航管理器 → 信号总线 + 侧边栏高亮 + 状态栏
        self._nav_manager.page_changed.connect(signals.page_changed.emit)
        self._nav_manager.page_changed.connect(self._sidebar.set_active)
        self._nav_manager.page_changed.connect(self._on_page_changed)

        # 状态栏消息
        signals.status_message.connect(self.statusBar().showMessage)

    def _on_page_changed(self, page_key: str):
        """页面切换回调：更新状态栏"""
        page = self._nav_manager.get_page(page_key)
        if page:
            self.statusBar().showMessage(f"已切换到: {page.title}")

    def _register_pages(self):
        """注册所有页面

        未来新增页面在此添加：
        1. import 新页面类
        2. 创建实例并注册
        3. 在侧边栏添加导航项
        """
        from apps.home.home_page import HomePage
        from apps.settings.settings_page import SettingsPage
        from apps.about.about_page import AboutPage
        from apps.product_analyzer.product_analyzer_page import ProductAnalyzerPage
        from apps.title_optimizer.title_optimizer_page import TitleOptimizerPage
        from apps.data_export.data_export_page import DataExportPage
        from apps.history.history_page import HistoryPage

        pages: list[BasePage] = [
            HomePage("home", "首页", "home"),
            ProductAnalyzerPage("product_analyzer", "商品链接分析", "analyze"),
            TitleOptimizerPage("title_optimizer", "AI标题优化", "sparkle"),
            HistoryPage("history", "历史记录", "history"),
            DataExportPage("data_export", "数据导出", "export"),
            SettingsPage("settings", "系统设置", "settings"),
            AboutPage("about", "关于", "about"),
        ]

        for page in pages:
            self._nav_manager.register_page(page)
            self._sidebar.add_item(page.page_key, page.title, page.icon)

        # 默认显示首页
        self._nav_manager.navigate_to("home")

    def _apply_stylesheet(self):
        """加载 QSS 样式表"""
        qss_path = Path(self._context.app_dir) / "resources" / "styles" / "main.qss"
        if qss_path.exists():
            qss_text = qss_path.read_text(encoding="utf-8")
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.setStyleSheet(qss_text)

    def _restore_window_state(self):
        """从配置恢复窗口大小和位置"""
        config = self._context.config
        width = config.get("window.width", 1200)
        height = config.get("window.height", 800)
        x = config.get("window.x", -1)
        y = config.get("window.y", -1)
        maximized = config.get("window.maximized", False)

        self.resize(width, height)

        if x >= 0 and y >= 0:
            self.move(x, y)

        if maximized:
            self.showMaximized()

    def _save_window_state(self):
        """保存窗口大小和位置到配置"""
        config = self._context.config

        if self.isMaximized():
            config.set("window.maximized", True)
        else:
            config.set("window.maximized", False)
            config.set("window.width", self.width())
            config.set("window.height", self.height())
            pos = self.pos()
            config.set("window.x", pos.x())
            config.set("window.y", pos.y())

        config.save()

    def closeEvent(self, event):
        """窗口关闭时保存状态"""
        self._save_window_state()
        self._context.signals.app_closing.emit()

        logger = self._context.logger.get_logger("main_window")
        logger.info("窗口关闭，状态已保存")

        super().closeEvent(event)
