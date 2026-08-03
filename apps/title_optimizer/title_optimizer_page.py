"""AI 标题优化页面：输入商品标题，由 AI 生成优化建议

设计原则（V1.2.3 起）：
    所有优化风格都必须基于用户提供的「平台搜索词榜单数据 / 平台数据截图」，
    AI 只能使用其中的真实关键词，严禁凭经验编造通用词。

支持:
    1. 手动输入标题 + 商品信息（类目、价格）
    2. 从 V0.2 商品分析页面跳转（通过 SignalBus 接收原标题）
    3. 上传平台数据截图 -> 一键 OCR 识别并整理为 8 列搜索词榜单
    4. 四种优化风格：搜索优化、促销转化、品牌调性、数据驱动优化
    5. 单风格优化 + 批量全风格优化 + 多标题批量优化
    6. 结果对比展示 + 优化历史
"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QWidget, QScrollArea,
    QTextEdit, QPushButton, QSplitter, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QGridLayout, QSizePolicy, QAbstractItemView,
    QMessageBox, QProgressBar, QComboBox, QCheckBox,
    QLineEdit, QRadioButton, QButtonGroup, QTextBrowser,
    QFileDialog, QListWidget, QListWidgetItem,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor

from framework.base_page import BasePage
from framework.app_context import AppContext
from framework.ai_service_manager import create_ai_service
from database.db_manager import DatabaseManager
from apps.title_optimizer.title_optimizer import (
    TitleOptimizer, OptimizeResult, OPTIMIZE_STYLES,
)
from apps.title_optimizer.optimize_worker import (
    OptimizeWorker, BatchOptimizeWorker, MarketExtractWorker,
)
from apps.title_optimizer.multi_title_worker import MultiTitleOptimizeWorker
from apps.title_optimizer.market_data_extractor import MARKET_KEYS


class TitleOptimizerPage(BasePage):
    """AI 标题优化页面

    布局:
        QSplitter (水平)
        ├── 左侧面板: 输入 + 控制
        │   ├── 标题输入框
        │   ├── 商品信息补充区
        │   ├── 优化风格选择
        │   ├── 优化按钮 + 进度条
        │   └── 优化历史表格
        └── 右侧面板: 结果展示
            ├── 优化前后对比卡片
            ├── SEO 关键词标签
            └── 优化理由说明
    """

    def __init__(self, page_key: str, title: str, icon: str = ""):
        super().__init__(page_key, title, icon)
        self._context = AppContext()
        self._logger = self._context.logger.get_logger("title_optimizer")

        # AI 服务
        self._optimizer: TitleOptimizer | None = None
        self._ai_available = False
        self._init_ai_service()

        # 状态
        self._history: list[OptimizeResult] = []
        self._worker: OptimizeWorker | BatchOptimizeWorker | MultiTitleOptimizeWorker | None = None
        self._extract_worker: MarketExtractWorker | None = None
        self._multi_results: list[OptimizeResult] = []

        # UI 引用
        self._title_input: QTextEdit | None = None
        self._category_input: QLineEdit | None = None
        self._price_input: QLineEdit | None = None
        self._style_buttons: dict[str, QRadioButton] = {}
        self._batch_check: QCheckBox | None = None
        self._multi_title_check: QCheckBox | None = None
        self._optimize_btn: QPushButton | None = None
        self._progress: QProgressBar | None = None
        self._status_label: QLabel | None = None
        self._history_table: QTableWidget | None = None

        # 平台市场数据
        self._image_paths: list[str] = []
        self._image_list: QListWidget | None = None
        self._market_table: QTableWidget | None = None

        # 右侧结果
        self._original_title_label: QLabel | None = None
        self._optimized_title_label: QLabel | None = None
        self._keywords_label: QLabel | None = None
        self._keyword_layout_label: QLabel | None = None
        self._reason_browser: QTextBrowser | None = None
        self._tokens_label: QLabel | None = None
        self._error_label: QLabel | None = None
        self._result_stack: QWidget | None = None
        self._empty_result: QWidget | None = None
        self._multi_table: QTableWidget | None = None
        self._multi_summary_label: QLabel | None = None

        # 监听来自其他页面的请求
        self._context.signals.title_optimize_request.connect(self._on_external_request)

    def _init_ai_service(self):
        """初始化 AI 服务"""
        config = self._context.config
        ai_service = create_ai_service(config.get("ai_service", {}))
        if ai_service is not None:
            try:
                ai_service.initialize()
                self._optimizer = TitleOptimizer(ai_service)
                self._ai_available = True
                self._logger.info("AI 服务已就绪")
            except Exception as e:
                self._logger.error(f"AI 服务初始化失败: {e}")
                self._ai_available = False
        else:
            self._logger.warning("AI 服务未配置（缺少 API Key）")
            self._ai_available = False

    def _setup_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([350, 700])

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.addWidget(splitter)

    # ===================== 左侧面板 =====================

    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(12)

        # -- 输入区 --
        input_group = QGroupBox("商品标题")
        input_layout = QVBoxLayout(input_group)

        self._title_input = QTextEdit()
        self._title_input.setPlaceholderText(
            "请输入需要优化的商品标题\n\n"
            "示例:\n"
            "  iPhone 15 Pro Max 手机壳 硅胶防摔 全包保护套 男女通用"
        )
        self._title_input.setMaximumHeight(120)
        self._title_input.setAcceptRichText(False)
        input_layout.addWidget(self._title_input)
        layout.addWidget(input_group)

        # -- 商品信息补充 --
        info_group = QGroupBox("商品信息（可选，用于更精准的优化）")
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(8)

        info_layout.addWidget(QLabel("类目:"), 0, 0)
        self._category_input = QLineEdit()
        self._category_input.setPlaceholderText("如: 手机配件、女装、家居")
        info_layout.addWidget(self._category_input, 0, 1)

        info_layout.addWidget(QLabel("价格:"), 1, 0)
        self._price_input = QLineEdit()
        self._price_input.setPlaceholderText("如: 29.9")
        info_layout.addWidget(self._price_input, 1, 1)

        layout.addWidget(info_group)

        # -- 平台市场数据（截图 + 搜索词榜单） --
        market_group = self._create_market_data_group()
        layout.addWidget(market_group)

        # -- 优化风格 --
        style_group = QGroupBox("优化风格")
        style_layout = QVBoxLayout(style_group)

        self._style_group = QButtonGroup(self)
        for i, style in enumerate(OPTIMIZE_STYLES):
            radio = QRadioButton(f"{style.name} - {style.description}")
            radio.setToolTip(style.description)
            self._style_buttons[style.key] = radio
            style_layout.addWidget(radio)
            if i == 0:
                radio.setChecked(True)

        # 批量优化复选框
        self._batch_check = QCheckBox("对全部三种风格进行优化（对比效果）")
        self._batch_check.toggled.connect(self._on_batch_toggled)
        style_layout.addWidget(self._batch_check)

        # 多标题批量
        self._multi_title_check = QCheckBox("多标题批量优化（每行一个标题）")
        style_layout.addWidget(self._multi_title_check)

        layout.addWidget(style_group)

        # -- 按钮 --
        btn_layout = QHBoxLayout()
        self._optimize_btn = QPushButton("开始优化")
        self._optimize_btn.setObjectName("PrimaryButton")
        self._optimize_btn.setMinimumHeight(36)
        self._optimize_btn.clicked.connect(self._on_optimize_clicked)

        clear_btn = QPushButton("清空")
        clear_btn.setMinimumHeight(36)
        clear_btn.clicked.connect(self._on_clear_clicked)

        btn_layout.addWidget(self._optimize_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # -- 进度条 --
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(True)
        self._progress.setMaximumHeight(20)
        layout.addWidget(self._progress)

        # -- 状态 --
        if not self._ai_available:
            warning = QLabel("⚠️ AI 服务未就绪，请在系统设置中配置 DeepSeek API Key")
            warning.setStyleSheet("color: #e67e22; font-size: 9pt; padding: 8px; "
                                  "background: #fef3e2; border-radius: 4px;")
            warning.setWordWrap(True)
            layout.addWidget(warning)

        self._status_label = QLabel("就绪")
        self._status_label.setObjectName("PageSubtitle")
        self._status_label.setStyleSheet("color: #888; font-size: 9pt;")
        layout.addWidget(self._status_label)

        # -- 历史记录 --
        history_group = QGroupBox("优化历史")
        history_layout = QVBoxLayout(history_group)

        self._history_table = QTableWidget(0, 4)
        self._history_table.setHorizontalHeaderLabels(["时间", "风格", "原标题", "优化标题"])
        self._history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._history_table.clicked.connect(self._on_history_clicked)

        header = self._history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._history_table.verticalHeader().setVisible(False)
        self._history_table.setAlternatingRowColors(True)

        history_layout.addWidget(self._history_table)
        layout.addWidget(history_group, stretch=1)

        return panel

    def _create_market_data_group(self) -> QGroupBox:
        """创建平台市场数据输入区：截图上传 + 搜索词榜单表格"""
        group = QGroupBox("平台市场数据（必填，所有优化均基于此）")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        hint = QLabel("所有优化都必须基于平台真实数据：上传截图并点击「识别截图并填充表格」"
                      "自动提取，或直接在下方表格手动填写。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #b8860b; font-size: 9pt;")
        layout.addWidget(hint)

        # 图片上传区
        img_label = QLabel("平台数据截图：")
        layout.addWidget(img_label)

        self._image_list = QListWidget()
        self._image_list.setMaximumHeight(80)
        self._image_list.setToolTip("已上传的数据截图，可用于 OCR 提取或供 vision 模型直接看图")
        layout.addWidget(self._image_list)

        img_btn_layout = QHBoxLayout()
        upload_btn = QPushButton("上传截图")
        upload_btn.setToolTip("支持 JPG / PNG 格式的平台数据截图")
        upload_btn.clicked.connect(self._on_upload_image)
        clear_img_btn = QPushButton("清除图片")
        clear_img_btn.clicked.connect(self._on_clear_images)
        extract_btn = QPushButton("识别截图并填充表格")
        extract_btn.setObjectName("PrimaryButton")
        extract_btn.setToolTip("OCR 识别截图文字，并由 AI 整理为下方 8 列搜索词榜单")
        extract_btn.clicked.connect(self._on_extract_market_data)
        img_btn_layout.addWidget(upload_btn)
        img_btn_layout.addWidget(clear_img_btn)
        img_btn_layout.addWidget(extract_btn)
        img_btn_layout.addStretch()
        layout.addLayout(img_btn_layout)

        # 搜索词榜单表格
        table_label = QLabel("搜索词榜单数据：")
        layout.addWidget(table_label)

        self._market_table = QTableWidget(0, 8)
        self._market_table.setHorizontalHeaderLabels([
            "榜单类型", "搜索词", "搜索人气", "趋势词",
            "搜索增速", "核心词", "搜索增量", "修饰词",
        ])
        self._market_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._market_table.setAlternatingRowColors(True)
        self._market_table.verticalHeader().setVisible(False)
        header = self._market_table.horizontalHeader()
        for i in range(8):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._market_table)

        table_btn_layout = QHBoxLayout()
        add_row_btn = QPushButton("添加行")
        add_row_btn.clicked.connect(self._on_add_market_row)
        del_row_btn = QPushButton("删除选中行")
        del_row_btn.clicked.connect(self._on_delete_market_row)
        clear_table_btn = QPushButton("清空数据")
        clear_table_btn.clicked.connect(self._on_clear_market_data)
        table_btn_layout.addWidget(add_row_btn)
        table_btn_layout.addWidget(del_row_btn)
        table_btn_layout.addWidget(clear_table_btn)
        table_btn_layout.addStretch()
        layout.addLayout(table_btn_layout)

        return group

    # ===================== 右侧面板 =====================

    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(12)

        title_label = QLabel("优化结果")
        title_label.setObjectName("PageTitle")
        layout.addWidget(title_label)

        # 空结果
        self._empty_result = QWidget()
        empty_layout = QVBoxLayout(self._empty_result)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = QLabel("在左侧输入商品标题，选择优化风格后点击「开始优化」")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #aaa; font-size: 11pt;")
        empty_layout.addWidget(hint)
        layout.addWidget(self._empty_result)

        # 结果区（默认隐藏）
        self._result_stack = QWidget()
        self._result_stack.setVisible(False)
        result_layout = QVBoxLayout(self._result_stack)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        result_content = QWidget()
        rc_layout = QVBoxLayout(result_content)
        rc_layout.setContentsMargins(0, 0, 0, 0)
        rc_layout.setSpacing(12)

        # 原标题
        orig_group = QGroupBox("原标题")
        orig_layout = QVBoxLayout(orig_group)
        self._original_title_label = QLabel("-")
        self._original_title_label.setWordWrap(True)
        self._original_title_label.setStyleSheet("font-size: 11pt; color: #555;")
        orig_layout.addWidget(self._original_title_label)
        rc_layout.addWidget(orig_group)

        # 优化标题
        opt_group = QGroupBox("优化后标题")
        opt_group.setStyleSheet("QGroupBox { border: 2px solid #2ecc71; border-radius: 6px; }")
        opt_layout = QVBoxLayout(opt_group)
        self._optimized_title_label = QLabel("-")
        self._optimized_title_label.setWordWrap(True)
        self._optimized_title_label.setStyleSheet(
            "font-size: 13pt; font-weight: bold; color: #2c3e50; padding: 4px;"
        )
        self._optimized_title_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        opt_layout.addWidget(self._optimized_title_label)
        rc_layout.addWidget(opt_group)

        # SEO 关键词
        kw_group = QGroupBox("SEO 关键词")
        kw_layout = QVBoxLayout(kw_group)
        self._keywords_label = QLabel("-")
        self._keywords_label.setWordWrap(True)
        self._keywords_label.setStyleSheet("font-size: 10pt; color: #4a47a3;")
        kw_layout.addWidget(self._keywords_label)
        rc_layout.addWidget(kw_group)

        # 关键词布局
        layout_group = QGroupBox("关键词布局")
        layout_layout = QVBoxLayout(layout_group)
        self._keyword_layout_label = QLabel("-")
        self._keyword_layout_label.setWordWrap(True)
        self._keyword_layout_label.setStyleSheet("font-size: 10pt; color: #2c3e50;")
        layout_layout.addWidget(self._keyword_layout_label)
        rc_layout.addWidget(layout_group)

        # 优化理由
        reason_group = QGroupBox("优化理由")
        reason_layout = QVBoxLayout(reason_group)
        self._reason_browser = QTextBrowser()
        self._reason_browser.setMaximumHeight(80)
        self._reason_browser.setStyleSheet("font-size: 10pt; color: #555;")
        reason_layout.addWidget(self._reason_browser)
        rc_layout.addWidget(reason_group)

        # Token 用量
        self._tokens_label = QLabel()
        self._tokens_label.setStyleSheet("color: #aaa; font-size: 9pt;")
        rc_layout.addWidget(self._tokens_label)

        # 错误
        self._error_label = QLabel()
        self._error_label.setVisible(False)
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet(
            "color: #e74c3c; background: #fde8e8; border: 1px solid #f5c6cb; "
            "border-radius: 4px; padding: 8px;"
        )
        rc_layout.addWidget(self._error_label)

        # 多标题批量结果
        self._multi_summary_label = QLabel()
        self._multi_summary_label.setVisible(False)
        self._multi_summary_label.setStyleSheet(
            "font-weight: bold; font-size: 11pt; padding: 4px 0;"
        )
        rc_layout.addWidget(self._multi_summary_label)

        self._multi_table = QTableWidget(0, 4)
        self._multi_table.setVisible(False)
        self._multi_table.setHorizontalHeaderLabels(["原标题", "优化标题", "风格", "状态"])
        self._multi_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._multi_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._multi_table.setAlternatingRowColors(True)
        self._multi_table.verticalHeader().setVisible(False)
        self._multi_table.setMaximumHeight(300)
        mheader = self._multi_table.horizontalHeader()
        mheader.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        mheader.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        mheader.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        mheader.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        rc_layout.addWidget(self._multi_table)

        rc_layout.addStretch()
        scroll.setWidget(result_content)
        result_layout.addWidget(scroll)

        layout.addWidget(self._result_stack, stretch=1)
        return panel

    # ===================== 信号处理 =====================

    def _on_batch_toggled(self, checked: bool):
        """批量优化复选框切换"""
        for radio in self._style_buttons.values():
            radio.setEnabled(not checked)

    def _on_optimize_clicked(self):
        if not self._ai_available:
            QMessageBox.warning(self, "提示",
                "AI 服务未就绪。\n请在「系统设置」中配置 DeepSeek API Key。")
            return

        title = self._title_input.toPlainText().strip() if self._title_input else ""
        if not title:
            QMessageBox.warning(self, "提示", "请输入商品标题")
            return

        # 多标题批量模式
        if self._multi_title_check and self._multi_title_check.isChecked():
            titles = [t.strip() for t in title.split("\n") if t.strip()]
            if len(titles) <= 1:
                # 只有单行标题则退化为普通模式
                self._start_optimization(titles[0])
                return
            self._start_multi_title_optimization(titles)
        else:
            # 取第一行
            single_title = title.split("\n")[0].strip()
            self._start_optimization(single_title)

    def _on_clear_clicked(self):
        if self._title_input:
            self._title_input.clear()
        if self._category_input:
            self._category_input.clear()
        if self._price_input:
            self._price_input.clear()
        self._show_empty_result()

    def _on_history_clicked(self, index):
        row = index.row()
        if 0 <= row < len(self._history):
            self._display_result(self._history[row])

    def _on_external_request(self, title: str):
        """处理来自其他页面（如商品分析）的标题优化请求"""
        if self._title_input:
            self._title_input.setPlainText(title)
        # 切换到本页面
        self._context.signals.navigate_to.emit(self.page_key)

    # -------------------- 平台市场数据操作 --------------------

    def _on_upload_image(self):
        """上传平台数据截图"""
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择平台数据截图",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if paths:
            for path in paths:
                if path not in self._image_paths:
                    self._image_paths.append(path)
                    item = QListWidgetItem(path)
                    item.setToolTip(path)
                    self._image_list.addItem(item)

    def _on_clear_images(self):
        """清除所有上传的截图"""
        self._image_paths.clear()
        self._image_list.clear()

    def _on_extract_market_data(self):
        """OCR 识别截图并整理为搜索词榜单表格（异步）"""
        if not self._ai_available:
            QMessageBox.warning(self, "提示",
                "AI 服务未就绪，无法整理数据。\n请在「系统设置」中配置 DeepSeek API Key。")
            return
        if not self._image_paths:
            QMessageBox.warning(self, "提示",
                "请先上传平台数据截图，再点击「识别截图并填充表格」。")
            return
        if self._extract_worker and self._extract_worker.isRunning():
            return

        self._set_ui_enabled(False)
        self._status_label.setText("正在识别截图并整理数据...")
        if self._progress:
            self._progress.setVisible(True)
            self._progress.setRange(0, 0)

        self._extract_worker = MarketExtractWorker(
            self._optimizer._ai, image_paths=list(self._image_paths)
        )
        self._extract_worker.extracted_signal.connect(self._on_market_extracted)
        self._extract_worker.error_signal.connect(self._on_extract_error)
        self._extract_worker.start()

    def _on_market_extracted(self, rows: list[dict], error_message: str):
        self._set_ui_enabled(True)
        if self._progress:
            self._progress.setVisible(False)
        if error_message:
            QMessageBox.warning(self, "识别失败", error_message)
            self._status_label.setText("就绪")
            return
        self._fill_market_table(rows)
        self._status_label.setText(
            f"已从截图提取 {len(rows)} 条搜索词数据，请核对后点击「开始优化」"
        )

    def _on_extract_error(self, error_msg: str):
        self._set_ui_enabled(True)
        if self._progress:
            self._progress.setVisible(False)
        self._status_label.setText("识别出错")
        QMessageBox.warning(self, "识别出错", error_msg)

    def _fill_market_table(self, rows: list[dict]):
        """用提取结果覆盖填写搜索词榜单表格"""
        self._market_table.setRowCount(0)
        for row_data in rows:
            row = self._market_table.rowCount()
            self._market_table.insertRow(row)
            for col, key in enumerate(MARKET_KEYS):
                value = row_data.get(key, "")
                self._market_table.setItem(row, col, QTableWidgetItem(str(value)))

    def _on_add_market_row(self):
        """在搜索词榜单表格末尾添加空行"""
        row = self._market_table.rowCount()
        self._market_table.insertRow(row)
        for col in range(8):
            self._market_table.setItem(row, col, QTableWidgetItem(""))

    def _on_delete_market_row(self):
        """删除搜索词榜单表格中选中的行"""
        rows = sorted({idx.row() for idx in self._market_table.selectedIndexes()}, reverse=True)
        for row in rows:
            self._market_table.removeRow(row)

    def _on_clear_market_data(self):
        """清空搜索词榜单表格"""
        self._market_table.setRowCount(0)

    def _get_market_data(self) -> list[dict]:
        """从表格读取搜索词榜单数据"""
        data = []
        keys = [
            "rank_type", "search_term", "search_popularity", "trend_word",
            "search_growth", "core_word", "search_increment", "modifier_word",
        ]
        for row in range(self._market_table.rowCount()):
            row_data = {}
            has_value = False
            for col, key in enumerate(keys):
                item = self._market_table.item(row, col)
                value = item.text().strip() if item else ""
                row_data[key] = value
                if value:
                    has_value = True
            if has_value:
                data.append(row_data)
        return data

    def _get_image_paths(self) -> list[str]:
        """获取已上传的截图路径"""
        return list(self._image_paths)

    # ===================== 优化流程 =====================

    def _get_product_info(self) -> dict | None:
        """获取补充的商品信息"""
        info = {}
        if self._category_input and self._category_input.text().strip():
            info["category"] = self._category_input.text().strip()
        if self._price_input and self._price_input.text().strip():
            info["price"] = self._price_input.text().strip()
        return info if info else None

    def _get_selected_style(self) -> str | None:
        """获取选中的单个风格 key"""
        for key, radio in self._style_buttons.items():
            if radio.isChecked():
                return key
        return None

    def _start_optimization(self, title: str):
        """启动异步优化"""
        self._set_ui_enabled(False)
        self._progress.setVisible(True)
        self._progress.setMinimum(0)
        self._progress.setMaximum(0)
        self._status_label.setText("正在调用 AI 优化...")
        self._error_label.setVisible(False)

        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(2000)
            self._worker = None

        product_info = self._get_product_info()
        market_data = self._get_market_data()
        image_paths = self._get_image_paths()

        # 强制要求平台数据：所有优化风格都必须基于平台真实数据
        if not market_data and not image_paths:
            QMessageBox.warning(
                self, "缺少平台数据",
                "所有优化都必须基于平台真实数据，不能仅凭原标题凭空生成。\n\n"
                "请先：\n"
                "  1) 上传平台数据截图，点击「识别截图并填充表格」；或\n"
                "  2) 在下方表格手动填写搜索词榜单数据。\n\n"
                "然后再点击「开始优化」。",
            )
            self._set_ui_enabled(True)
            if self._progress:
                self._progress.setVisible(False)
            self._status_label.setText("就绪")
            return

        if self._batch_check and self._batch_check.isChecked():
            # 批量全风格优化
            style_keys = [s.key for s in OPTIMIZE_STYLES]
            self._worker = BatchOptimizeWorker(
                self._optimizer, title, style_keys, product_info,
                market_data=market_data, image_paths=image_paths,
            )
            self._worker.progress_signal.connect(self._on_batch_progress)
            self._worker.result_signal.connect(self._on_single_result)
            self._worker.finished_signal.connect(self._on_batch_finished)
            self._worker.error_signal.connect(self._on_worker_error)

            self._progress.setMaximum(len(style_keys))
            self._progress.setMinimum(0)
            self._progress.setValue(0)
        else:
            # 单风格优化
            style_key = self._get_selected_style() or "seo"
            self._worker = OptimizeWorker(
                self._optimizer, title, style_key, product_info,
                market_data=market_data, image_paths=image_paths,
            )
            self._worker.finished_signal.connect(self._on_single_finished)
            self._worker.error_signal.connect(self._on_worker_error)

            self._progress.setMinimum(0)
            self._progress.setMaximum(0)

        self._worker.start()
        self._logger.info(f"开始标题优化: {title[:30]}...")

    def _on_batch_progress(self, current: int, total: int):
        self._progress.setValue(current)
        self._status_label.setText(f"正在优化 ({current}/{total})...")

    def _on_single_result(self, result: OptimizeResult):
        """批量模式下每个结果到达"""
        self._status_label.setText(
            f"「{result.style_name}」优化完成"
        )

    def _on_batch_finished(self, results: list[OptimizeResult]):
        """批量优化全部完成"""
        self._on_worker_done()

        # 显示第一个成功的结果，历史记录添加全部
        success_results = [r for r in results if r.success]
        if success_results:
            self._display_result(success_results[0])
            for r in success_results:
                self._add_to_history(r)
        else:
            QMessageBox.warning(self, "提示", "所有风格的优化均失败，请检查 AI 配置")
        self._logger.info(f"批量优化完成: {len(success_results)}/{len(results)} 成功")

    def _on_single_finished(self, result: OptimizeResult):
        """单风格优化完成"""
        self._on_worker_done()

        if result.success:
            self._display_result(result)
            self._add_to_history(result)
            self._logger.info(f"标题优化完成: tokens={result.tokens_used}")
        else:
            self._error_label.setText(f"优化失败: {result.error_message}")
            self._error_label.setVisible(True)
            self._logger.error(f"标题优化失败: {result.error_message}")

    def _on_worker_error(self, error_msg: str):
        self._status_label.setText(f"错误: {error_msg}")
        self._error_label.setText(f"优化过程出错: {error_msg}")
        self._error_label.setVisible(True)
        self._logger.error(f"优化出错: {error_msg}")

    def _on_worker_done(self):
        self._progress.setVisible(False)
        self._set_ui_enabled(True)
        self._status_label.setText("就绪")

    # ===================== 多标题批量优化 =====================

    def _start_multi_title_optimization(self, titles: list[str]):
        """启动多标题批量优化"""
        self._multi_results = []
        self._multi_table.setVisible(True)
        self._multi_table.setRowCount(0)
        self._multi_summary_label.setVisible(True)
        self._multi_summary_label.setText(f"批量优化中 (0/{len(titles)})...")
        self._set_ui_enabled(False)
        self._progress.setVisible(True)
        self._progress.setMinimum(0)
        self._progress.setMaximum(len(titles))
        self._progress.setValue(0)
        self._status_label.setText(f"多标题批量优化: 共 {len(titles)} 个标题")
        self._error_label.setVisible(False)

        # 清理旧 worker
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(2000)
            self._worker = None

        style_key = self._get_selected_style() or "seo"
        product_info = self._get_product_info()
        market_data = self._get_market_data()
        image_paths = self._get_image_paths()

        # 强制要求平台数据：多标题批量优化同样必须基于平台真实数据
        if not market_data and not image_paths:
            QMessageBox.warning(
                self, "缺少平台数据",
                "所有优化都必须基于平台真实数据，不能仅凭原标题凭空生成。\n\n"
                "请先：\n"
                "  1) 上传平台数据截图，点击「识别截图并填充表格」；或\n"
                "  2) 在下方表格手动填写搜索词榜单数据。\n\n"
                "然后再点击「开始优化」。",
            )
            self._set_ui_enabled(True)
            if self._progress:
                self._progress.setVisible(False)
            self._status_label.setText("就绪")
            return

        self._worker = MultiTitleOptimizeWorker(
            self._optimizer, titles, style_key, product_info,
            market_data=market_data, image_paths=image_paths,
        )
        self._worker.progress.connect(self._on_multi_progress)
        self._worker.item_finished.connect(self._on_multi_item)
        self._worker.all_finished.connect(self._on_multi_all_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

        self._logger.info(f"开始多标题批量优化: {len(titles)} 个标题, 风格={style_key}")

    def _on_multi_progress(self, current: int, total: int):
        self._progress.setValue(current)
        self._multi_summary_label.setText(f"批量优化中 ({current}/{total})...")

    def _on_multi_item(self, result: OptimizeResult):
        """单个标题优化完成"""
        self._multi_results.append(result)
        # 保存到数据库
        try:
            db_record = {
                "original_title": result.original_title,
                "optimized_title": result.optimized_title,
                "style_key": result.style,
                "style_name": result.style_name,
                "seo_keywords": result.seo_keywords,
                "improvement_reason": result.improvement_reason,
                "keyword_layout": result.keyword_layout,
                "tokens_used": result.tokens_used,
                "success": result.success,
                "error_message": result.error_message,
                "product_info": {},
            }
            self._context.db.save_optimization_record(db_record)
        except Exception as e:
            self._logger.error(f"保存优化记录失败: {e}")

        # 添加到历史
        self._history.insert(0, result)
        self._add_to_history_table(result)

        # 更新批量结果表
        row = self._multi_table.rowCount()
        self._multi_table.insertRow(row)
        self._multi_table.setItem(row, 0, QTableWidgetItem(
            result.original_title[:40] + ("..." if len(result.original_title) > 40 else "")
        ))
        self._multi_table.setItem(row, 1, QTableWidgetItem(
            result.optimized_title[:40] + ("..." if len(result.optimized_title) > 40 else "")
        ))
        self._multi_table.setItem(row, 2, QTableWidgetItem(result.style_name))
        status = "✅ 成功" if result.success else f"❌ {result.error_message}"
        item = QTableWidgetItem(status)
        item.setForeground(QColor("#2ecc71" if result.success else "#e74c3c"))
        self._multi_table.setItem(row, 3, item)

    def _on_multi_all_finished(self, results: list[OptimizeResult]):
        """多标题批量优化全部完成"""
        total = len(results)
        success_count = sum(1 for r in results if r.success)
        total_tokens = sum(r.tokens_used for r in results if r.success)
        self._on_worker_done()
        self._multi_summary_label.setText(
            f"批量优化完成: 共 {total} 个, 成功 {success_count}, Token 消耗: {total_tokens}"
        )
        self._status_label.setText(f"多标题优化完成: 成功 {success_count}/{total}")
        self._logger.info(f"多标题优化完成: {success_count}/{total}, tokens={total_tokens}")

    def _add_to_history_table(self, result: OptimizeResult):
        """仅添加到历史表格（不重复保存 DB）"""
        table = self._history_table
        table.insertRow(0)
        now = datetime.now().strftime("%H:%M:%S")
        table.setItem(0, 0, QTableWidgetItem(now))
        table.setItem(0, 1, QTableWidgetItem(result.style_name))
        table.setItem(0, 2, QTableWidgetItem(
            result.original_title[:50] + ("..." if len(result.original_title) > 50 else "")
        ))
        table.setItem(0, 3, QTableWidgetItem(
            result.optimized_title[:50] + ("..." if len(result.optimized_title) > 50 else "")
        ))

    def _set_ui_enabled(self, enabled: bool):
        if self._optimize_btn:
            self._optimize_btn.setEnabled(enabled)
        if self._title_input:
            self._title_input.setEnabled(enabled)

    # ===================== 结果展示 =====================

    def _display_result(self, result: OptimizeResult):
        self._empty_result.setVisible(False)
        self._result_stack.setVisible(True)

        self._original_title_label.setText(result.original_title)
        self._optimized_title_label.setText(result.optimized_title)

        if result.seo_keywords:
            self._keywords_label.setText(", ".join(result.seo_keywords))
        else:
            self._keywords_label.setText("未提取到关键词")

        if result.keyword_layout:
            self._keyword_layout_label.setText(result.keyword_layout)
        else:
            self._keyword_layout_label.setText("-")

        self._reason_browser.setPlainText(result.improvement_reason or "无")
        self._tokens_label.setText(f"风格: {result.style_name} | Token 用量: {result.tokens_used}")

    def _show_empty_result(self):
        self._empty_result.setVisible(True)
        self._result_stack.setVisible(False)

    # ===================== 历史记录 =====================

    def on_show(self):
        """页面显示时刷新历史记录"""
        self._load_history_from_db()

    def _load_history_from_db(self):
        """从数据库加载优化历史"""
        try:
            db = self._context.db
            records = db.get_optimization_history(limit=50)
            self._history.clear()
            self._history_table.setRowCount(0)
            for record in records:
                # 将 DB 记录转为 OptimizeResult 兼容格式
                result = OptimizeResult(
                    original_title=record.get("original_title", ""),
                    optimized_title=record.get("optimized_title", ""),
                    style=record.get("style_key", ""),
                    style_name=record.get("style_name", ""),
                    seo_keywords=record.get("seo_keywords", []),
                    improvement_reason=record.get("improvement_reason", ""),
                    keyword_layout=record.get("keyword_layout", ""),
                    tokens_used=record.get("tokens_used", 0),
                    success=record.get("success", True),
                    error_message=record.get("error_message", ""),
                )
                self._history.append(result)
                row = self._history_table.rowCount()
                self._history_table.insertRow(row)
                self._history_table.setItem(row, 0, QTableWidgetItem(
                    record.get("created_at", "")[-8:] if record.get("created_at") else ""
                ))
                self._history_table.setItem(row, 1, QTableWidgetItem(record.get("style_name", "")))
                self._history_table.setItem(row, 2, QTableWidgetItem(
                    result.original_title[:50] + ("..." if len(result.original_title) > 50 else "")
                ))
                self._history_table.setItem(row, 3, QTableWidgetItem(
                    result.optimized_title[:50] + ("..." if len(result.optimized_title) > 50 else "")
                ))
        except Exception as e:
            self._logger.error(f"加载优化历史失败: {e}")

    def _add_to_history(self, result: OptimizeResult):
        # 保存到数据库
        try:
            db_record = {
                "original_title": result.original_title,
                "optimized_title": result.optimized_title,
                "style_key": result.style,
                "style_name": result.style_name,
                "seo_keywords": result.seo_keywords,
                "improvement_reason": result.improvement_reason,
                "keyword_layout": result.keyword_layout,
                "tokens_used": result.tokens_used,
                "success": result.success,
                "error_message": result.error_message,
                "product_info": {},
            }
            self._context.db.save_optimization_record(db_record)
        except Exception as e:
            self._logger.error(f"保存优化记录到数据库失败: {e}")

        self._history.insert(0, result)
        table = self._history_table
        table.insertRow(0)

        now = datetime.now().strftime("%H:%M:%S")
        table.setItem(0, 0, QTableWidgetItem(now))
        table.setItem(0, 1, QTableWidgetItem(result.style_name))
        table.setItem(0, 2, QTableWidgetItem(
            result.original_title[:50] + ("..." if len(result.original_title) > 50 else "")
        ))
        table.setItem(0, 3, QTableWidgetItem(
            result.optimized_title[:50] + ("..." if len(result.optimized_title) > 50 else "")
        ))

        max_history = 50
        while table.rowCount() > max_history:
            table.removeRow(table.rowCount() - 1)
        while len(self._history) > max_history:
            self._history.pop()
