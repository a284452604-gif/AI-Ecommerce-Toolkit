"""历史记录管理页面：统一浏览和管理分析/优化历史"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QPushButton, QTabWidget, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QAbstractItemView, QMessageBox, QComboBox,
)
from PySide6.QtCore import Qt

from framework.base_page import BasePage
from framework.app_context import AppContext


class HistoryPage(BasePage):
    """历史记录管理页面

    标签页:
        - 分析记录: 浏览、搜索、筛选、删除商品分析记录
        - 优化记录: 浏览、搜索、筛选、删除标题优化记录
    """

    def __init__(self, page_key: str, title: str, icon: str = ""):
        super().__init__(page_key, title, icon)
        self._context = AppContext()
        self._logger = self._context.logger.get_logger("history")

        self._analysis_table: QTableWidget | None = None
        self._analysis_search: QLineEdit | None = None
        self._analysis_platform_filter: QComboBox | None = None
        self._analysis_count_label: QLabel | None = None

        self._optimization_table: QTableWidget | None = None
        self._optimization_search: QLineEdit | None = None
        self._optimization_style_filter: QComboBox | None = None
        self._optimization_count_label: QLabel | None = None

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        title_label = QLabel("历史记录管理")
        title_label.setObjectName("PageTitle")
        main_layout.addWidget(title_label)

        tabs = QTabWidget()

        tab_analysis = self._create_analysis_tab()
        tab_optimization = self._create_optimization_tab()

        tabs.addTab(tab_analysis, "分析记录")
        tabs.addTab(tab_optimization, "优化记录")
        tabs.currentChanged.connect(self._on_tab_changed)

        main_layout.addWidget(tabs, stretch=1)

    # ===================== 分析记录 Tab =====================

    def _create_analysis_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self._analysis_search = QLineEdit()
        self._analysis_search.setPlaceholderText("搜索标题/商品ID/店铺...")
        self._analysis_search.setMinimumWidth(200)
        self._analysis_search.returnPressed.connect(self._refresh_analysis)
        toolbar.addWidget(self._analysis_search)

        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self._refresh_analysis)
        toolbar.addWidget(search_btn)

        self._analysis_platform_filter = QComboBox()
        self._analysis_platform_filter.addItem("全部平台", "")
        self._analysis_platform_filter.addItem("淘宝", "淘宝")
        self._analysis_platform_filter.addItem("天猫", "天猫")
        self._analysis_platform_filter.addItem("京东", "京东")
        self._analysis_platform_filter.addItem("拼多多", "拼多多")
        self._analysis_platform_filter.addItem("抖音", "抖音")
        self._analysis_platform_filter.currentIndexChanged.connect(self._refresh_analysis)
        toolbar.addWidget(QLabel("平台:"))
        toolbar.addWidget(self._analysis_platform_filter)

        toolbar.addStretch()

        delete_btn = QPushButton("删除选中")
        delete_btn.setStyleSheet("color: #e74c3c;")
        delete_btn.clicked.connect(self._delete_selected_analysis)
        toolbar.addWidget(delete_btn)

        clear_btn = QPushButton("清空全部")
        clear_btn.setStyleSheet("color: #e74c3c;")
        clear_btn.clicked.connect(self._clear_all_analysis)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        self._analysis_count_label = QLabel("")
        self._analysis_count_label.setStyleSheet("color: #888; font-size: 9pt;")
        layout.addWidget(self._analysis_count_label)

        self._analysis_table = QTableWidget(0, 7)
        self._analysis_table.setHorizontalHeaderLabels([
            "ID", "时间", "平台", "商品ID", "标题", "价格", "店铺"
        ])
        self._analysis_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._analysis_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._analysis_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._analysis_table.setAlternatingRowColors(True)
        self._analysis_table.verticalHeader().setVisible(False)

        ah = self._analysis_table.horizontalHeader()
        ah.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        ah.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        ah.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        ah.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        ah.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        ah.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        ah.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._analysis_table, stretch=1)
        return widget

    # ===================== 优化记录 Tab =====================

    def _create_optimization_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self._optimization_search = QLineEdit()
        self._optimization_search.setPlaceholderText("搜索原标题/优化标题...")
        self._optimization_search.setMinimumWidth(200)
        self._optimization_search.returnPressed.connect(self._refresh_optimization)
        toolbar.addWidget(self._optimization_search)

        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self._refresh_optimization)
        toolbar.addWidget(search_btn)

        self._optimization_style_filter = QComboBox()
        self._optimization_style_filter.addItem("全部风格", "")
        self._optimization_style_filter.addItem("搜索优化", "seo")
        self._optimization_style_filter.addItem("促销转化", "promotion")
        self._optimization_style_filter.addItem("品牌调性", "brand")
        self._optimization_style_filter.currentIndexChanged.connect(self._refresh_optimization)
        toolbar.addWidget(QLabel("风格:"))
        toolbar.addWidget(self._optimization_style_filter)

        toolbar.addStretch()

        delete_btn = QPushButton("删除选中")
        delete_btn.setStyleSheet("color: #e74c3c;")
        delete_btn.clicked.connect(self._delete_selected_optimization)
        toolbar.addWidget(delete_btn)

        clear_btn = QPushButton("清空全部")
        clear_btn.setStyleSheet("color: #e74c3c;")
        clear_btn.clicked.connect(self._clear_all_optimization)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        self._optimization_count_label = QLabel("")
        self._optimization_count_label.setStyleSheet("color: #888; font-size: 9pt;")
        layout.addWidget(self._optimization_count_label)

        self._optimization_table = QTableWidget(0, 7)
        self._optimization_table.setHorizontalHeaderLabels([
            "ID", "时间", "风格", "原标题", "优化标题", "SEO关键词", "Token"
        ])
        self._optimization_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._optimization_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._optimization_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._optimization_table.setAlternatingRowColors(True)
        self._optimization_table.verticalHeader().setVisible(False)

        oh = self._optimization_table.horizontalHeader()
        oh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        oh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        oh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        oh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        oh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        oh.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        oh.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._optimization_table, stretch=1)
        return widget

    # ===================== 生命周期 =====================

    def on_show(self):
        self._refresh_analysis()
        self._refresh_optimization()

    def _on_tab_changed(self, index: int):
        if index == 0:
            self._refresh_analysis()
        else:
            self._refresh_optimization()

    # ===================== 分析记录操作 =====================

    def _refresh_analysis(self):
        try:
            db = self._context.db
            platform = self._analysis_platform_filter.currentData() or ""
            search = self._analysis_search.text().strip() if self._analysis_search else ""
            records = db.get_analysis_history(limit=200, platform=platform, search=search)
            total = db.get_analysis_count(platform=platform) if not search else len(records)

            self._analysis_count_label.setText(
                f"共 {len(records)} 条" + (f" (筛选自 {total} 条)" if search or platform else "")
            )

            self._analysis_table.setRowCount(len(records))
            for row, r in enumerate(records):
                self._analysis_table.setItem(row, 0, QTableWidgetItem(str(r.get("id", ""))))
                self._analysis_table.setItem(row, 1, QTableWidgetItem(r.get("created_at", "")))
                self._analysis_table.setItem(row, 2, QTableWidgetItem(r.get("platform", "")))
                self._analysis_table.setItem(row, 3, QTableWidgetItem(r.get("product_id", "")))
                self._analysis_table.setItem(row, 4, QTableWidgetItem(r.get("title", "")))
                self._analysis_table.setItem(row, 5, QTableWidgetItem(r.get("price", "")))
                self._analysis_table.setItem(row, 6, QTableWidgetItem(r.get("shop_name", "")))
        except Exception as e:
            self._logger.error(f"刷新分析记录失败: {e}")

    def _delete_selected_analysis(self):
        rows = set()
        for item in self._analysis_table.selectedItems():
            rows.add(item.row())
        if not rows:
            QMessageBox.information(self, "提示", "请先选择要删除的记录")
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除选中的 {len(rows)} 条分析记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            db = self._context.db
            for row in sorted(rows, reverse=True):
                item = self._analysis_table.item(row, 0)
                if item:
                    db.delete_analysis_record(int(item.text()))
                self._analysis_table.removeRow(row)
            self._refresh_analysis()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败: {e}")

    def _clear_all_analysis(self):
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有分析记录吗？此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self._context.db.clear_analysis_history()
            self._refresh_analysis()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"清空失败: {e}")

    # ===================== 优化记录操作 =====================

    def _refresh_optimization(self):
        try:
            db = self._context.db
            style = self._optimization_style_filter.currentData() or ""
            search = self._optimization_search.text().strip() if self._optimization_search else ""
            records = db.get_optimization_history(limit=200, style=style, search=search)
            total = db.get_optimization_count(style=style) if not search else len(records)

            self._optimization_count_label.setText(
                f"共 {len(records)} 条" + (f" (筛选自 {total} 条)" if search or style else "")
            )

            self._optimization_table.setRowCount(len(records))
            for row, r in enumerate(records):
                keywords = r.get("seo_keywords", [])
                kw_str = ", ".join(keywords[:3]) if keywords else ""
                self._optimization_table.setItem(row, 0, QTableWidgetItem(str(r.get("id", ""))))
                self._optimization_table.setItem(row, 1, QTableWidgetItem(r.get("created_at", "")))
                self._optimization_table.setItem(row, 2, QTableWidgetItem(r.get("style_name", "")))
                self._optimization_table.setItem(row, 3, QTableWidgetItem(r.get("original_title", "")))
                self._optimization_table.setItem(row, 4, QTableWidgetItem(r.get("optimized_title", "")))
                self._optimization_table.setItem(row, 5, QTableWidgetItem(kw_str))
                self._optimization_table.setItem(row, 6, QTableWidgetItem(str(r.get("tokens_used", 0))))
        except Exception as e:
            self._logger.error(f"刷新优化记录失败: {e}")

    def _delete_selected_optimization(self):
        rows = set()
        for item in self._optimization_table.selectedItems():
            rows.add(item.row())
        if not rows:
            QMessageBox.information(self, "提示", "请先选择要删除的记录")
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除选中的 {len(rows)} 条优化记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            db = self._context.db
            for row in sorted(rows, reverse=True):
                item = self._optimization_table.item(row, 0)
                if item:
                    db.delete_optimization_record(int(item.text()))
                self._optimization_table.removeRow(row)
            self._refresh_optimization()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除失败: {e}")

    def _clear_all_optimization(self):
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有优化记录吗？此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self._context.db.clear_optimization_history()
            self._refresh_optimization()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"清空失败: {e}")
