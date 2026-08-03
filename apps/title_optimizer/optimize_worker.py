"""异步优化 Worker：QThread 中执行 AI 调用，避免阻塞 UI"""

from PySide6.QtCore import QThread, Signal
from apps.title_optimizer.title_optimizer import TitleOptimizer, OptimizeResult
from apps.title_optimizer.market_data_extractor import extract_market_rows


class OptimizeWorker(QThread):
    """后台执行标题优化的 QThread

    用法:
        worker = OptimizeWorker(optimizer, title, "seo", product_info)
        worker.finished_signal.connect(on_finished)
        worker.error_signal.connect(on_error)
        worker.start()
    """

    finished_signal = Signal(OptimizeResult)
    error_signal = Signal(str)

    def __init__(self, optimizer: TitleOptimizer, original_title: str,
                 style_key: str, product_info: dict | None = None,
                 market_data: list[dict] | None = None,
                 image_paths: list[str] | None = None):
        super().__init__()
        self._optimizer = optimizer
        self._original_title = original_title
        self._style_key = style_key
        self._product_info = product_info
        self._market_data = market_data
        self._image_paths = image_paths

    def run(self):
        """在后台线程执行优化"""
        try:
            result = self._optimizer.optimize(
                original_title=self._original_title,
                style_key=self._style_key,
                product_info=self._product_info,
                market_data=self._market_data,
                image_paths=self._image_paths,
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class BatchOptimizeWorker(QThread):
    """批量优化 Worker：依次执行多个风格的优化"""

    progress_signal = Signal(int, int)        # current, total
    result_signal = Signal(OptimizeResult)
    finished_signal = Signal(list)             # list[OptimizeResult]
    error_signal = Signal(str)

    def __init__(self, optimizer: TitleOptimizer, original_title: str,
                 style_keys: list[str], product_info: dict | None = None,
                 market_data: list[dict] | None = None,
                 image_paths: list[str] | None = None):
        super().__init__()
        self._optimizer = optimizer
        self._original_title = original_title
        self._style_keys = style_keys
        self._product_info = product_info
        self._market_data = market_data
        self._image_paths = image_paths

    def run(self):
        """依次执行所有风格的优化"""
        results = []
        total = len(self._style_keys)
        try:
            for i, key in enumerate(self._style_keys):
                self.progress_signal.emit(i + 1, total)
                result = self._optimizer.optimize(
                    original_title=self._original_title,
                    style_key=key,
                    product_info=self._product_info,
                    market_data=self._market_data,
                    image_paths=self._image_paths,
                )
                self.result_signal.emit(result)
                results.append(result)
            self.finished_signal.emit(results)
        except Exception as e:
            self.error_signal.emit(str(e))


class MarketExtractWorker(QThread):
    """后台从平台数据截图 / OCR 文字提取结构化搜索词榜单数据"""

    extracted_signal = Signal(list, str)   # rows: list[dict], error_message: str
    error_signal = Signal(str)

    def __init__(self, ai_service, image_paths: list[str] | None = None,
                 ocr_text: str | None = None):
        super().__init__()
        self._ai_service = ai_service
        self._image_paths = image_paths
        self._ocr_text = ocr_text

    def run(self):
        try:
            rows, error_msg = extract_market_rows(
                self._ai_service,
                image_paths=self._image_paths,
                ocr_text=self._ocr_text,
            )
            self.extracted_signal.emit(rows, error_msg)
        except Exception as e:
            self.error_signal.emit(str(e))
