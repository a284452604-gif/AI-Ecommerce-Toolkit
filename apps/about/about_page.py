"""关于页面：应用信息、版本、技术栈、开源许可"""

from pathlib import Path

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QScrollArea,
    QPushButton,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

from framework.base_page import BasePage
from framework.app_context import AppContext


class AboutPage(BasePage):
    """关于页面

    展示应用信息：
    - 应用图标 + 名称
    - 版本号（从 VERSION 文件读取）
    - 技术栈信息
    - GitHub 仓库链接
    - 开源许可信息
    - 第三方库致谢
    """

    GITHUB_URL = "https://github.com/a284452604-gif/AI-Ecommerce-Toolkit"

    def __init__(self, page_key: str, title: str, icon: str = ""):
        super().__init__(page_key, title, icon)
        self._context = AppContext()

    def _setup_ui(self):
        """构建关于页 UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 读取版本号
        version = self._read_version()

        # === 应用图标 + 名称 ===
        app_name = self._context.config.get("app.name", "AI电商工具箱")

        name_label = QLabel(app_name)
        name_label.setObjectName("AboutAppName")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        version_label = QLabel(f"版本 V{version}")
        version_label.setObjectName("AboutVersion")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        layout.addSpacing(10)

        # === 简介 ===
        desc_label = QLabel(
            "一款基于 AI 的电商运营桌面工具，\n"
            "为淘宝、京东、拼多多、抖音店铺运营提供智能化解决方案。"
        )
        desc_label.setObjectName("AboutInfo")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addSpacing(20)

        # === 技术栈 ===
        tech_title = QLabel("技术栈")
        tech_title.setObjectName("PageTitle")
        tech_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(tech_title)

        tech_info = QLabel(
            "• Python 3.13\n"
            "• PySide6 (Qt for Python)\n"
            "• 标准库 logging (RotatingFileHandler)\n"
            "• JSON 配置管理"
        )
        tech_info.setObjectName("AboutInfo")
        layout.addWidget(tech_info)

        layout.addSpacing(16)

        # === GitHub 仓库 ===
        repo_title = QLabel("开源仓库")
        repo_title.setObjectName("PageTitle")
        repo_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(repo_title)

        repo_link = QLabel(self.GITHUB_URL)
        repo_link.setObjectName("LinkLabel")
        repo_link.setCursor(Qt.CursorShape.PointingHandCursor)
        repo_link.mousePressEvent = lambda e: self._open_url(self.GITHUB_URL)
        layout.addWidget(repo_link)

        layout.addSpacing(16)

        # === 开源许可 ===
        license_title = QLabel("开源许可")
        license_title.setObjectName("PageTitle")
        license_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(license_title)

        license_info = QLabel("MIT License")
        license_info.setObjectName("AboutInfo")
        layout.addWidget(license_info)

        layout.addSpacing(16)

        # === 第三方库 ===
        libs_title = QLabel("第三方库")
        libs_title.setObjectName("PageTitle")
        libs_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(libs_title)

        libs_info = QLabel(
            "• PySide6 — Qt for Python (LGPLv3)\n"
            "• pytest — 测试框架 (MIT)\n"
            "• pytest-qt — Qt 测试插件 (MIT)\n"
            "• PyInstaller — 打包工具 (GPL)"
        )
        libs_info.setObjectName("AboutInfo")
        layout.addWidget(libs_info)

        layout.addStretch()

        # === 版权信息 ===
        copyright_label = QLabel(f"© 2026 {app_name}. All rights reserved.")
        copyright_label.setObjectName("PageSubtitle")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _read_version(self) -> str:
        """从 VERSION 文件读取版本号"""
        version_path = Path(self._context.app_dir) / "VERSION"
        if version_path.exists():
            return version_path.read_text(encoding="utf-8").strip()
        return self._context.config.get("app.version", "0.0.0")

    def _open_url(self, url: str):
        """在浏览器中打开 URL"""
        QDesktopServices.openUrl(QUrl(url))
