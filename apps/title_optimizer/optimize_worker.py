"""异步优化 Worker：QThread 中执行 AI 调用，避免阻塞 UI"""

from PySide6.QtCore import QThread, Signal
from apps.title_optimizer.title_optimizer import TitleOptimizer, OptimizeResult


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
                 style_key: str, product_info: dict | None = None):
        super().__init__()
        self._optimizer = optimizer
        self._original_title = original_title
        self._style_key = style_key
        self._product_info = product_info

    def run(self):
        """在后台线程执行优化"""
        try:
            result = self._optimizer.optimize(
                original_title=self._original_title,
                style_key=self._style_key,
                product_info=self._product_info,
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
                 style_keys: list[str], product_info: dict | None = None):
        super().__init__()
        self._optimizer = optimizer
        self._original_title = original_title
        self._style_keys = style_keys
        self._product_info = product_info

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
                )
                self.result_signal.emit(result)
                results.append(result)
            self.finished_signal.emit(results)
        except Exception as e:
            self.error_signal.emit(str(e))
