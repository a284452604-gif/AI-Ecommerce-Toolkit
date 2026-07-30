"""批量抓取 Worker：在 QThread 中依次抓取多个商品链接，避免阻塞 UI"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from apps.product_analyzer.link_parser import LinkParser, ParsedLink
from apps.product_analyzer.product_scraper import ProductScraper, ProductInfo


class BatchScrapeWorker(QThread):
    """批量异步抓取工作线程

    在后台线程中依次解析和抓取多个商品链接，
    通过信号逐个通知主线程每个结果。

    信号:
        progress(int, int)       — 进度 (current, total)
        url_started(int, str)    — 第 i 个 URL 开始处理
        item_finished(int, dict) — 第 i 个结果完成
        all_finished(list)       — 全部完成
        error(str)               — 发生错误
    """

    progress = Signal(int, int)
    url_started = Signal(int, str)
    item_finished = Signal(int, object)   # (index, dict)
    all_finished = Signal(list)           # list[dict]
    error = Signal(str)

    def __init__(self, urls: list[str], parent=None):
        """初始化批量抓取 Worker

        Args:
            urls: 要抓取的商品链接列表
            parent: 父 QObject
        """
        super().__init__(parent)
        self._urls = urls
        self._parser = LinkParser()
        self._scraper = ProductScraper()

    def run(self):
        """依次执行批量抓取"""
        results = []
        total = len(self._urls)

        try:
            for i, url in enumerate(self._urls):
                self.progress.emit(i, total)
                self.url_started.emit(i, url)

                # 解析链接
                parsed = self._parser.parse(url)
                if not parsed.is_valid:
                    result = {
                        "url": url,
                        "platform": parsed.platform.value,
                        "product_id": parsed.product_id,
                        "title": "",
                        "price": "",
                        "shop_name": "",
                        "description": "",
                        "fetch_time": 0.0,
                        "success": False,
                        "error_message": parsed.error_message or "链接无效",
                    }
                    results.append(result)
                    self.item_finished.emit(i, result)
                    continue

                # 抓取商品信息
                info = self._scraper.scrape(parsed)
                result = {
                    "url": info.url or parsed.normalized_url,
                    "platform": info.platform,
                    "product_id": info.product_id,
                    "title": info.title,
                    "price": info.price,
                    "shop_name": info.shop_name,
                    "description": info.description,
                    "fetch_time": info.fetch_time,
                    "success": info.success,
                    "error_message": info.error_message,
                }
                results.append(result)
                self.item_finished.emit(i, result)

            self.progress.emit(total, total)
            self.all_finished.emit(results)

        except Exception as e:
            self.error.emit(f"批量抓取出错: {type(e).__name__}: {e}")
            self.all_finished.emit(results)
