"""商品链接分析页面：输入商品链接，解析并抓取商品信息

支持的操作:
    1. 粘贴/输入商品链接（支持多行批量输入）
    2. 点击分析按钮，后台异步解析 + 抓取
    3. 展示商品信息卡片（标题、价格、店铺、图片）
    4. 历史记录表格，可重新查看以往分析结果
"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QWidget, QScrollArea,
    QTextEdit, QPushButton, QSplitter, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QGridLayout, QSizePolicy, QAbstractItemView,
    QMessageBox, QProgressBar,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor

from framework.base_page import BasePage
from framework.app_context import AppContext
from apps.product_analyzer.link_parser import ParsedLink, Platform
from apps.product_analyzer.product_scraper import ProductInfo
from apps.product_analyzer.scrape_worker import ScrapeWorker


class ProductAnalyzerPage(BasePage):
    """商品链接分析页面

    布局:
        QSplitter (水平)
        ├── 左侧面板 (输入区 + 控制区)
        │   ├── 链接输入框 (QTextEdit)
        │   ├── 分析按钮 + 进度条
        │   └── 历史记录表格
        └── 右侧面板 (结果展示)
            ├── 链接解析结果
            └── 商品信息卡片
    """

    def __init__(self, page_key: str, title: str, icon: str = ""):
        super().__init__(page_key, title, icon)
        self._context = AppContext()
        self._logger = self._context.logger.get_logger("product_analyzer")

        # 履历
        self._history: list[dict] = []         # 分析历史 [{time, url, parsed, product}]
        self._current_result: dict | None = None  # 当前分析结果
        self._worker: ScrapeWorker | None = None

        # UI 控件引用
        self._url_input: QTextEdit | None = None
        self._analyze_btn: QPushButton | None = None
        self._clear_btn: QPushButton | None = None
        self._progress: QProgressBar | None = None
        self._status_label: QLabel | None = None
        self._history_table: QTableWidget | None = None

        # 右侧结果控件
        self._platform_label: QLabel | None = None
        self._product_id_label: QLabel | None = None
        self._normalized_url_label: QLabel | None = None
        self._title_label: QLabel | None = None
        self._price_label: QLabel | None = None
        self._shop_label: QLabel | None = None
        self._desc_label: QLabel | None = None
        self._fetch_time_label: QLabel | None = None
        self._optimize_title_btn: QPushButton | None = None
        self._error_label: QLabel | None = None
        self._result_stack: QWidget | None = None
        self._empty_result: QWidget | None = None

    def _setup_ui(self):
        """构建页面 UI"""
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # === 左侧面板 ===
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # === 右侧面板 ===
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        # 默认比例: 左侧 40%、右侧 60%
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([400, 600])

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.addWidget(splitter)

    # ===================== 左侧面板 =====================

    def _create_left_panel(self) -> QWidget:
        """创建左侧输入和控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(12)

        # 输入区域
        input_group = QGroupBox("商品链接")
        input_layout = QVBoxLayout(input_group)

        self._url_input = QTextEdit()
        self._url_input.setPlaceholderText(
            "请粘贴商品链接（每行一个）:\n\n"
            "支持平台:\n"
            "  - 淘宝: item.taobao.com/item.htm?id=xxx\n"
            "  - 天猫: detail.tmall.com/item.htm?id=xxx\n"
            "  - 京东: item.jd.com/xxx.html\n"
            "  - 拼多多: mobile.yangkeduo.com/goods.html?goods_id=xxx\n"
            "  - 抖音: haohuo.jinritemai.com/product/xxx\n\n"
            "示例:\n"
            "https://item.taobao.com/item.htm?id=12345678901\n"
            "https://item.jd.com/100012345678.html"
        )
        self._url_input.setMaximumHeight(200)
        self._url_input.setAcceptRichText(False)
        font = QFont()
        font.setPointSize(10)
        self._url_input.setFont(font)
        input_layout.addWidget(self._url_input)

        layout.addWidget(input_group)

        # 按钮栏
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._analyze_btn = QPushButton("开始分析")
        self._analyze_btn.setObjectName("PrimaryButton")
        self._analyze_btn.setMinimumHeight(36)
        self._analyze_btn.clicked.connect(self._on_analyze_clicked)

        self._clear_btn = QPushButton("清空")
        self._clear_btn.setMinimumHeight(36)
        self._clear_btn.clicked.connect(self._on_clear_clicked)

        btn_layout.addWidget(self._analyze_btn)
        btn_layout.addWidget(self._clear_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # 进度条
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setMinimum(0)
        self._progress.setMaximum(0)  # 不确定模式
        self._progress.setMaximumHeight(6)
        self._progress.setTextVisible(False)
        layout.addWidget(self._progress)

        # 状态标签
        self._status_label = QLabel("就绪")
        self._status_label.setObjectName("PageSubtitle")
        self._status_label.setStyleSheet("color: #888; font-size: 9pt;")
        layout.addWidget(self._status_label)

        # 历史记录
        history_group = QGroupBox("分析历史")
        history_layout = QVBoxLayout(history_group)

        self._history_table = QTableWidget(0, 4)
        self._history_table.setHorizontalHeaderLabels([
            "时间", "平台", "商品ID", "标题"
        ])
        self._history_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._history_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._history_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._history_table.clicked.connect(self._on_history_clicked)

        header = self._history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self._history_table.verticalHeader().setVisible(False)
        self._history_table.setAlternatingRowColors(True)

        history_layout.addWidget(self._history_table)
        layout.addWidget(history_group, stretch=1)

        return panel

    # ===================== 右侧面板 =====================

    def _create_right_panel(self) -> QWidget:
        """创建右侧结果展示面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(12)

        # 结果标题
        title_label = QLabel("分析结果")
        title_label.setObjectName("PageTitle")
        layout.addWidget(title_label)

        # 空结果提示
        self._empty_result = QWidget()
        empty_layout = QVBoxLayout(self._empty_result)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hint_label = QLabel("在左侧输入商品链接，点击「开始分析」")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setStyleSheet("color: #aaa; font-size: 11pt;")
        empty_layout.addWidget(hint_label)

        layout.addWidget(self._empty_result)

        # 结果展示区域（默认隐藏）
        self._result_stack = QWidget()
        self._result_stack.setVisible(False)
        result_layout = QVBoxLayout(self._result_stack)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(12)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        result_content = QWidget()
        result_content_layout = QVBoxLayout(result_content)
        result_content_layout.setContentsMargins(0, 0, 0, 0)
        result_content_layout.setSpacing(12)

        # 1) 链接解析信息
        link_group = QGroupBox("链接信息")
        link_layout = QGridLayout(link_group)
        link_layout.setSpacing(8)

        link_layout.addWidget(QLabel("平台:"), 0, 0)
        self._platform_label = QLabel("-")
        self._platform_label.setStyleSheet("font-weight: bold;")
        link_layout.addWidget(self._platform_label, 0, 1)

        link_layout.addWidget(QLabel("商品ID:"), 1, 0)
        self._product_id_label = QLabel("-")
        link_layout.addWidget(self._product_id_label, 1, 1)

        link_layout.addWidget(QLabel("规范化链接:"), 2, 0)
        self._normalized_url_label = QLabel("-")
        self._normalized_url_label.setWordWrap(True)
        self._normalized_url_label.setStyleSheet("color: #4a47a3;")
        self._normalized_url_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        link_layout.addWidget(self._normalized_url_label, 2, 1)

        result_content_layout.addWidget(link_group)

        # 2) 商品信息
        product_group = QGroupBox("商品信息")
        product_layout = QGridLayout(product_group)
        product_layout.setSpacing(8)

        product_layout.addWidget(QLabel("标题:"), 0, 0)
        self._title_label = QLabel("-")
        self._title_label.setWordWrap(True)
        self._title_label.setStyleSheet("font-size: 11pt; font-weight: bold;")
        product_layout.addWidget(self._title_label, 0, 1)

        product_layout.addWidget(QLabel("价格:"), 1, 0)
        self._price_label = QLabel("-")
        self._price_label.setStyleSheet("color: #e74c3c; font-size: 14pt; font-weight: bold;")
        product_layout.addWidget(self._price_label, 1, 1)

        product_layout.addWidget(QLabel("店铺:"), 2, 0)
        self._shop_label = QLabel("-")
        product_layout.addWidget(self._shop_label, 2, 1)

        product_layout.addWidget(QLabel("描述:"), 3, 0)
        self._desc_label = QLabel("-")
        self._desc_label.setWordWrap(True)
        self._desc_label.setStyleSheet("color: #555;")
        product_layout.addWidget(self._desc_label, 3, 1)

        product_layout.addWidget(QLabel("耗时:"), 4, 0)
        self._fetch_time_label = QLabel("-")
        product_layout.addWidget(self._fetch_time_label, 4, 1)

        result_content_layout.addWidget(product_group)

        # 3) AI优化标题按钮
        optimize_layout = QHBoxLayout()
        optimize_layout.addStretch()
        self._optimize_title_btn = QPushButton("✨ AI 优化标题")
        self._optimize_title_btn.setObjectName("PrimaryButton")
        self._optimize_title_btn.setMinimumHeight(36)
        self._optimize_title_btn.setToolTip("将当前商品标题发送到 AI 标题优化页面")
        self._optimize_title_btn.clicked.connect(self._on_optimize_title)
        self._optimize_title_btn.setVisible(False)
        optimize_layout.addWidget(self._optimize_title_btn)
        optimize_layout.addStretch()
        result_content_layout.addLayout(optimize_layout)

        # 4) 错误信息
        self._error_label = QLabel()
        self._error_label.setVisible(False)
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet(
            "color: #e74c3c; background-color: #fde8e8; "
            "border: 1px solid #f5c6cb; border-radius: 4px; padding: 8px;"
        )
        result_content_layout.addWidget(self._error_label)

        result_content_layout.addStretch()
        scroll.setWidget(result_content)
        result_layout.addWidget(scroll)

        layout.addWidget(self._result_stack, stretch=1)

        return panel

    # ===================== 信号处理 =====================

    def _on_analyze_clicked(self):
        """点击分析按钮"""
        url_text = self._url_input.toPlainText().strip() if self._url_input else ""
        if not url_text:
            QMessageBox.warning(self, "提示", "请输入商品链接")
            return

        # 取第一行作为分析链接
        url = url_text.split("\n")[0].strip()
        if not url:
            QMessageBox.warning(self, "提示", "链接不能为空")
            return

        self._start_analysis(url)

    def _on_clear_clicked(self):
        """清空输入和结果"""
        if self._url_input:
            self._url_input.clear()
        self._show_empty_result()

    def _on_history_clicked(self, index):
        """点击历史记录行，显示对应结果"""
        row = index.row()
        if 0 <= row < len(self._history):
            self._display_result(self._history[row])

    # ===================== 分析流程 =====================

    def _start_analysis(self, url: str):
        """启动异步分析"""
        # 禁用输入控件
        self._set_ui_enabled(False)
        self._progress.setVisible(True)
        self._status_label.setText(f"正在解析链接...")
        self._error_label.setVisible(False)

        # 清理旧 worker
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(2000)
            self._worker = None

        # 启动 worker
        self._worker = ScrapeWorker(url)
        self._worker.parse_started.connect(self._on_parse_started)
        self._worker.parse_finished.connect(self._on_parse_finished)
        self._worker.scrape_started.connect(self._on_scrape_started)
        self._worker.scrape_finished.connect(self._on_scrape_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.finished.connect(self._on_worker_done)
        self._worker.start()

        self._logger.info(f"开始分析链接: {url}")

    def _on_parse_started(self, url: str):
        """解析开始"""
        self._status_label.setText(f"正在解析链接: {url[:60]}...")

    def _on_parse_finished(self, parsed: ParsedLink):
        """解析完成"""
        if parsed.is_valid:
            self._status_label.setText(
                f"链接解析成功 - 平台: {parsed.platform.value} | "
                f"商品ID: {parsed.product_id}"
            )
        else:
            self._status_label.setText(f"链接解析失败: {parsed.error_message}")
        self._logger.info(f"链接解析完成: valid={parsed.is_valid}")

    def _on_scrape_started(self, url: str):
        """抓取开始"""
        self._status_label.setText(f"正在抓取商品信息...")

    def _on_scrape_finished(self, info: ProductInfo):
        """抓取完成"""
        if info.success:
            self._status_label.setText("分析完成!")
        elif info.error_message:
            self._status_label.setText(f"抓取失败: {info.error_message}")
        else:
            self._status_label.setText("分析完成，部分信息未能提取")

        self._current_result = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "url": info.url or (self._worker._url if self._worker else ""),
            "platform": info.platform,
            "product_id": info.product_id,
            "title": info.title,
            "price": info.price,
            "shop_name": info.shop_name,
            "description": info.description,
            "fetch_time": info.fetch_time,
            "success": info.success,
            "error_message": info.error_message,
            "parsed": None,  # ParsedLink 不可序列化，仅展示用
        }

        self._display_result(self._current_result)

        # 添加到历史记录
        if info.title or info.shop_name:
            self._add_to_history(self._current_result)

        self._logger.info(
            f"抓取完成: platform={info.platform}, success={info.success}, "
            f"time={info.fetch_time}s"
        )

    def _on_worker_error(self, error_msg: str):
        """Worker 异常"""
        self._status_label.setText(f"错误: {error_msg}")
        self._error_label.setText(f"分析过程出错: {error_msg}")
        self._error_label.setVisible(True)
        self._logger.error(f"分析出错: {error_msg}")

    def _on_worker_done(self):
        """Worker 执行完毕"""
        self._progress.setVisible(False)
        self._set_ui_enabled(True)

    def _on_optimize_title(self):
        """将当前商品标题发送到 AI 标题优化页面"""
        if self._current_result and self._current_result.get("title"):
            self._context.signals.title_optimize_request.emit(
                self._current_result["title"]
            )

    def _set_ui_enabled(self, enabled: bool):
        """设置 UI 控件的启用状态"""
        if self._analyze_btn:
            self._analyze_btn.setEnabled(enabled)
        if self._clear_btn:
            self._clear_btn.setEnabled(enabled)
        if self._url_input:
            self._url_input.setEnabled(enabled)

    # ===================== 结果展示 =====================

    def _display_result(self, result: dict | None):
        """在右侧面板显示分析结果"""
        if result is None:
            self._show_empty_result()
            return

        self._empty_result.setVisible(False)
        self._result_stack.setVisible(True)
        self._error_label.setVisible(False)

        # 链接信息
        self._set_label(self._platform_label, result.get("platform", "-"))
        self._set_label(self._product_id_label, result.get("product_id", "-"))
        self._set_label(self._normalized_url_label, result.get("url", "-"))

        # 商品信息
        if result.get("success"):
            title = result.get("title", "-")
            self._set_label(self._title_label, title)
            self._set_label(self._price_label, result.get("price", "-"))
            self._set_label(self._shop_label, result.get("shop_name", "-"))
            self._set_label(self._desc_label, result.get("description", "-"))
            fetch_time = result.get("fetch_time", 0)
            self._set_label(self._fetch_time_label, f"{fetch_time:.2f} 秒")
            # 有标题时显示 AI 优化按钮
            if self._optimize_title_btn:
                has_title = title and title != "-" and title.strip()
                self._optimize_title_btn.setVisible(has_title)
        elif result.get("error_message"):
            # 解析失败但有平台信息
            self._set_label(self._title_label, "-")
            self._set_label(self._price_label, "-")
            self._set_label(self._shop_label, "-")
            self._set_label(self._desc_label, "-")
            self._set_label(self._fetch_time_label, "-")

            self._error_label.setText(f"解析失败: {result['error_message']}")
            self._error_label.setVisible(True)

    def _show_empty_result(self):
        """显示空结果提示"""
        self._empty_result.setVisible(True)
        self._result_stack.setVisible(False)
        if self._optimize_title_btn:
            self._optimize_title_btn.setVisible(False)
        self._current_result = None

    @staticmethod
    def _set_label(label: QLabel | None, text: str):
        """安全设置标签文本"""
        if label:
            label.setText(str(text))

    # ===================== 历史记录 =====================

    def _add_to_history(self, result: dict):
        """将分析结果添加到历史表格"""
        self._history.insert(0, result)

        table = self._history_table
        table.insertRow(0)

        table.setItem(0, 0, QTableWidgetItem(result.get("time", "")))
        table.setItem(0, 1, QTableWidgetItem(result.get("platform", "")))
        table.setItem(0, 2, QTableWidgetItem(result.get("product_id", "")))
        table.setItem(0, 3, QTableWidgetItem(result.get("title", "")))

        # 限制历史记录数量
        max_history = 50
        while table.rowCount() > max_history:
            table.removeRow(table.rowCount() - 1)
        while len(self._history) > max_history:
            self._history.pop()
