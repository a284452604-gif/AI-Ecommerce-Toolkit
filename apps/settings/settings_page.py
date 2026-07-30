"""系统设置页：AI服务配置、外观设置、日志设置"""

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
    QScrollArea,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QPushButton,
    QMessageBox,
    QPlainTextEdit,
    QCheckBox,
)
from PySide6.QtCore import Qt

from framework.base_page import BasePage
from framework.app_context import AppContext


class SettingsPage(BasePage):
    """系统设置页面

    包含三个设置分组：
    - AI 服务设置（服务商、API Key、模型、Base URL、超时）
    - 外观设置（主题、字体、字号）
    - 日志设置（日志级别、最大文件大小、备份数量）

    修改后点击保存按钮持久化到 app_config.json。
    """

    def __init__(self, page_key: str, title: str, icon: str = ""):
        super().__init__(page_key, title, icon)
        self._context = AppContext()

    def _setup_ui(self):
        """构建设置页 UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 页面标题
        title_label = QLabel("系统设置")
        title_label.setObjectName("PageTitle")
        layout.addWidget(title_label)

        subtitle = QLabel("配置 AI 服务、外观和日志选项")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(subtitle)

        # === AI 服务设置 ===
        ai_group = QGroupBox("AI 服务设置")
        ai_layout = QFormLayout(ai_group)
        ai_layout.setSpacing(12)
        ai_layout.setContentsMargins(16, 20, 16, 16)

        self._provider_combo = QComboBox()
        self._provider_combo.setEditable(True)
        self._provider_combo.addItems([
            "",
            "OpenAI",
            "DeepSeek",
            "智谱 GLM",
            "通义千问",
            "自定义",
        ])
        ai_layout.addRow("服务商:", self._provider_combo)

        self._api_key_edit = QLineEdit()
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_edit.setPlaceholderText("输入 API Key")
        ai_layout.addRow("API Key:", self._api_key_edit)

        self._model_edit = QLineEdit()
        self._model_edit.setPlaceholderText("如 gpt-4o, deepseek-chat 等")
        ai_layout.addRow("模型名称:", self._model_edit)

        self._base_url_edit = QLineEdit()
        self._base_url_edit.setPlaceholderText("如 https://api.openai.com/v1")
        ai_layout.addRow("API Base URL:", self._base_url_edit)

        self._timeout_spin = QSpinBox()
        self._timeout_spin.setRange(5, 300)
        self._timeout_spin.setSuffix(" 秒")
        ai_layout.addRow("超时时间:", self._timeout_spin)

        layout.addWidget(ai_group)

        # === 外观设置 ===
        appearance_group = QGroupBox("外观设置")
        appearance_layout = QFormLayout(appearance_group)
        appearance_layout.setSpacing(12)
        appearance_layout.setContentsMargins(16, 20, 16, 16)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["浅色", "深色"])
        appearance_layout.addRow("主题:", self._theme_combo)

        self._font_combo = QComboBox()
        self._font_combo.setEditable(True)
        self._font_combo.addItems([
            "Microsoft YaHei UI",
            "Microsoft YaHei",
            "SimSun",
            "KaiTi",
            "Segoe UI",
        ])
        appearance_layout.addRow("字体:", self._font_combo)

        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(8, 20)
        self._font_size_spin.setSuffix(" pt")
        appearance_layout.addRow("字号:", self._font_size_spin)

        layout.addWidget(appearance_group)

        # === 日志设置 ===
        log_group = QGroupBox("日志设置")
        log_layout = QFormLayout(log_group)
        log_layout.setSpacing(12)
        log_layout.setContentsMargins(16, 20, 16, 16)

        self._log_level_combo = QComboBox()
        self._log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_layout.addRow("日志级别:", self._log_level_combo)

        self._max_bytes_spin = QSpinBox()
        self._max_bytes_spin.setRange(1048576, 104857600)  # 1MB - 100MB
        self._max_bytes_spin.setSuffix(" 字节")
        log_layout.addRow("最大文件大小:", self._max_bytes_spin)

        self._backup_count_spin = QSpinBox()
        self._backup_count_spin.setRange(1, 100)
        self._backup_count_spin.setSuffix(" 个")
        log_layout.addRow("保留备份数:", self._backup_count_spin)

        layout.addWidget(log_group)

        # === 商品抓取设置 ===
        scraper_group = QGroupBox("商品抓取设置")
        scraper_layout = QFormLayout(scraper_group)
        scraper_layout.setSpacing(12)
        scraper_layout.setContentsMargins(16, 20, 16, 16)

        self._browser_check = QCheckBox("启用浏览器抓取（推荐：可渲染 JS、绕过反爬获取真实标题/价格/店铺）")
        self._browser_check.setChecked(True)
        scraper_layout.addRow(self._browser_check)

        cookie_help = QLabel(
            "填入已登录对应平台的浏览器 Cookie（F12 → Application → Cookies 复制），"
            "可抓取价格、店铺等登录后才显示的信息。不填则仅能获取未登录可见内容。"
        )
        cookie_help.setWordWrap(True)
        cookie_help.setObjectName("PageSubtitle")
        scraper_layout.addRow(cookie_help)

        self._cookie_taobao = QPlainTextEdit()
        self._cookie_taobao.setPlaceholderText("淘宝 Cookie: key1=val1; key2=val2")
        self._cookie_taobao.setMaximumHeight(54)
        scraper_layout.addRow("淘宝:", self._cookie_taobao)

        self._cookie_tmall = QPlainTextEdit()
        self._cookie_tmall.setPlaceholderText("天猫 Cookie: key1=val1; key2=val2")
        self._cookie_tmall.setMaximumHeight(54)
        scraper_layout.addRow("天猫:", self._cookie_tmall)

        self._cookie_jd = QPlainTextEdit()
        self._cookie_jd.setPlaceholderText("京东 Cookie: key1=val1; key2=val2")
        self._cookie_jd.setMaximumHeight(54)
        scraper_layout.addRow("京东:", self._cookie_jd)

        self._cookie_pdd = QPlainTextEdit()
        self._cookie_pdd.setPlaceholderText("拼多多 Cookie: key1=val1; key2=val2")
        self._cookie_pdd.setMaximumHeight(54)
        scraper_layout.addRow("拼多多:", self._cookie_pdd)

        self._cookie_douyin = QPlainTextEdit()
        self._cookie_douyin.setPlaceholderText("抖音 Cookie: key1=val1; key2=val2")
        self._cookie_douyin.setMaximumHeight(54)
        scraper_layout.addRow("抖音:", self._cookie_douyin)

        layout.addWidget(scraper_group)

        # === 按钮区域 ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._reset_btn = QPushButton("重置为默认")
        self._reset_btn.setObjectName("SecondaryButton")
        self._reset_btn.clicked.connect(self._on_reset)
        btn_layout.addWidget(self._reset_btn)

        self._save_btn = QPushButton("保存设置")
        self._save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self._save_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 加载当前配置到 UI
        self._load_config_to_ui()

    def _setup_connections(self):
        """连接信号槽"""
        pass

    def _load_config_to_ui(self):
        """从配置加载当前值到 UI 控件"""
        config = self._context.config

        # AI 服务
        self._provider_combo.setCurrentText(config.get("ai_service.provider", ""))
        self._api_key_edit.setText(config.get("ai_service.api_key", ""))
        self._model_edit.setText(config.get("ai_service.model", ""))
        self._base_url_edit.setText(config.get("ai_service.base_url", ""))
        self._timeout_spin.setValue(config.get("ai_service.timeout", 30))

        # 外观
        theme = config.get("appearance.theme", "light")
        self._theme_combo.setCurrentIndex(0 if theme == "light" else 1)
        self._font_combo.setCurrentText(config.get("appearance.font_family", "Microsoft YaHei UI"))
        self._font_size_spin.setValue(config.get("appearance.font_size", 10))

        # 日志
        self._log_level_combo.setCurrentText(config.get("logging.level", "INFO"))
        self._max_bytes_spin.setValue(config.get("logging.max_bytes", 5242880))
        self._backup_count_spin.setValue(config.get("logging.backup_count", 10))

        # 商品抓取
        self._browser_check.setChecked(config.get("scraper.browser_enabled", True))
        cookies = config.get("scraper.cookies", {}) or {}
        self._cookie_taobao.setPlainText(cookies.get("taobao", ""))
        self._cookie_tmall.setPlainText(cookies.get("tmall", ""))
        self._cookie_jd.setPlainText(cookies.get("jd", ""))
        self._cookie_pdd.setPlainText(cookies.get("pdd", ""))
        self._cookie_douyin.setPlainText(cookies.get("douyin", ""))

    def _save_ui_to_config(self):
        """将 UI 控件的值保存到配置"""
        config = self._context.config

        # AI 服务
        config.set("ai_service.provider", self._provider_combo.currentText())
        config.set("ai_service.api_key", self._api_key_edit.text())
        config.set("ai_service.model", self._model_edit.text())
        config.set("ai_service.base_url", self._base_url_edit.text())
        config.set("ai_service.timeout", self._timeout_spin.value())

        # 外观
        theme = "light" if self._theme_combo.currentIndex() == 0 else "dark"
        config.set("appearance.theme", theme)
        config.set("appearance.font_family", self._font_combo.currentText())
        config.set("appearance.font_size", self._font_size_spin.value())

        # 日志
        config.set("logging.level", self._log_level_combo.currentText())
        config.set("logging.max_bytes", self._max_bytes_spin.value())
        config.set("logging.backup_count", self._backup_count_spin.value())

        # 商品抓取
        config.set("scraper.browser_enabled", self._browser_check.isChecked())
        cookies = {
            "taobao": self._cookie_taobao.toPlainText().strip(),
            "tmall": self._cookie_tmall.toPlainText().strip(),
            "jd": self._cookie_jd.toPlainText().strip(),
            "pdd": self._cookie_pdd.toPlainText().strip(),
            "douyin": self._cookie_douyin.toPlainText().strip(),
        }
        config.set("scraper.cookies", cookies)

    def _on_save(self):
        """保存设置"""
        self._save_ui_to_config()
        self._context.config.save()

        logger = self._context.logger.get_logger("settings")
        logger.info("设置已保存")

        # 发出配置变更信号
        self._context.signals.config_saved.emit()
        self._context.signals.status_message.emit("设置已保存")

        QMessageBox.information(self, "保存成功", "设置已保存，部分设置可能需要重启应用后生效。")

    def _on_reset(self):
        """重置为默认配置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要重置所有设置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._context.config.reset_to_default()
            self._load_config_to_ui()

            logger = self._context.logger.get_logger("settings")
            logger.info("设置已重置为默认")

            self._context.signals.status_message.emit("设置已重置为默认")
