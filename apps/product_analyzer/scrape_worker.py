"""异步抓取 Worker：在 QThread 中执行商品抓取，避免阻塞 UI"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from apps.product_analyzer.link_parser import LinkParser, ParsedLink
from apps.product_analyzer.product_scraper import ProductScraper, ProductInfo


class ScrapeWorker(QThread):
    """异步抓取工作线程

    在后台线程中执行链接解析和商品抓取，
    通过信号通知主线程结果。

    信号:
        parse_started(str)     — 开始解析
        parse_finished(object) — 解析完成 (ParsedLink)
        scrape_started(str)    — 开始抓取
        scrape_finished(object)— 抓取完成 (ProductInfo)
        error(str)             — 发生错误
    """

    parse_started = Signal(str)          # 参数: 原始链接
    parse_finished = Signal(object)      # 参数: ParsedLink
    scrape_started = Signal(str)         # 参数: 规范化链接
    scrape_finished = Signal(object)     # 参数: ProductInfo
    error = Signal(str)                  # 参数: 错误信息

    def __init__(self, url: str, parent=None):
        """初始化抓取 Worker

        Args:
            url: 要抓取的商品链接
            parent: 父 QObject
        """
        super().__init__(parent)
        self._url = url
        self._parser = LinkParser()
        self._scraper = ProductScraper()

    def run(self):
        """执行抓取流程"""
        try:
            # 1. 解析链接
            self.parse_started.emit(self._url)
            parsed = self._parser.parse(self._url)
            self.parse_finished.emit(parsed)

            if not parsed.is_valid:
                # 解析失败，直接返回错误信息
                self.scrape_finished.emit(ProductInfo(
                    platform=parsed.platform.value,
                    product_id=parsed.product_id,
                    url=parsed.normalized_url,
                    success=False,
                    error_message=parsed.error_message,
                ))
                return

            # 2. 抓取商品信息
            self.scrape_started.emit(parsed.normalized_url)
            info = self._scraper.scrape(parsed)
            self.scrape_finished.emit(info)

        except Exception as e:
            self.error.emit(f"抓取过程出错: {type(e).__name__}: {e}")
