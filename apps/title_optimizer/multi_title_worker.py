"""多标题批量优化 Worker：在 QThread 中依次优化多个标题"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from apps.title_optimizer.title_optimizer import TitleOptimizer, OptimizeResult


class MultiTitleOptimizeWorker(QThread):
    """多标题批量优化工作线程

    依次对多个标题使用同一种风格进行 AI 优化。

    信号:
        progress(int, int)         — 进度 (current, total)
        item_finished(object)      — 单个标题优化完成 (OptimizeResult)
        all_finished(list)         — 全部完成 (list[OptimizeResult])
        error(str)                 — 发生错误
    """

    progress = Signal(int, int)
    item_finished = Signal(object)
    all_finished = Signal(list)
    error = Signal(str)

    def __init__(self, optimizer: TitleOptimizer, titles: list[str],
                 style_key: str, product_info: dict | None = None, parent=None):
        super().__init__(parent)
        self._optimizer = optimizer
        self._titles = titles
        self._style_key = style_key
        self._product_info = product_info

    def run(self):
        results = []
        total = len(self._titles)

        try:
            for i, title in enumerate(self._titles):
                self.progress.emit(i + 1, total)
                result = self._optimizer.optimize(
                    title.strip(),
                    style_key=self._style_key,
                    product_info=self._product_info,
                )
                results.append(result)
                self.item_finished.emit(result)

            self.all_finished.emit(results)
        except Exception as e:
            self.error.emit(f"批量优化出错: {type(e).__name__}: {e}")
            self.all_finished.emit(results)
