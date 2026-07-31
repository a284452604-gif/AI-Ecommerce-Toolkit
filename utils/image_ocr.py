"""图片 OCR 文字提取工具

为不支持 vision 的模型（如 deepseek-chat）提供截图文字提取能力。
使用 rapidocr-onnxruntime 作为底层 OCR 引擎，支持中英混合识别。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rapidocr_onnxruntime import RapidOCR


class OCREngine:
    """OCR 引擎封装（懒加载）"""

    def __init__(self):
        self._engine: "RapidOCR | None" = None
        self._available: bool | None = None
        self._error_message: str = ""

    @property
    def available(self) -> bool:
        """OCR 是否可用"""
        if self._available is None:
            self._init_engine()
        return bool(self._available)

    @property
    def error_message(self) -> str:
        """初始化失败时的错误信息"""
        return self._error_message

    def _init_engine(self):
        """初始化 rapidocr 引擎"""
        try:
            from rapidocr_onnxruntime import RapidOCR

            self._engine = RapidOCR()
            self._available = True
            self._error_message = ""
        except Exception as e:
            self._engine = None
            self._available = False
            self._error_message = str(e)

    def extract_text(self, image_path: str) -> str:
        """从单张图片中提取文字

        Args:
            image_path: 图片文件路径

        Returns:
            提取到的文字，失败返回空字符串
        """
        if not self.available:
            return ""

        path = Path(image_path)
        if not path.exists():
            return ""

        try:
            result, _ = self._engine(str(path))
            if not result:
                return ""
            # rapidocr 返回结果格式: [[box, text, confidence], ...]
            texts = []
            for item in result:
                if isinstance(item, (list, tuple)) and len(item) > 1:
                    text = item[1]
                    if isinstance(text, str):
                        texts.append(text)
            return "\n".join(texts)
        except Exception:
            return ""


# 全局单例
_ocr_engine = OCREngine()


def is_ocr_available() -> bool:
    """OCR 是否可用"""
    return _ocr_engine.available


def get_ocr_error() -> str:
    """获取 OCR 初始化错误信息"""
    return _ocr_engine.error_message


def extract_text_from_image(image_path: str) -> str:
    """从图片中提取文字（便捷函数）"""
    return _ocr_engine.extract_text(image_path)


def extract_text_from_images(image_paths: list[str]) -> dict[str, str]:
    """从多张图片中提取文字

    Args:
        image_paths: 图片路径列表

    Returns:
        路径到提取文字的映射，未提取到文字的条目会被过滤
    """
    result: dict[str, str] = {}
    for path in image_paths:
        text = extract_text_from_image(path)
        if text.strip():
            result[path] = text.strip()
    return result
