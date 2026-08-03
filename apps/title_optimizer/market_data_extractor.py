"""从平台数据截图 / OCR 文字中提取结构化搜索词榜单数据

流程：
    截图路径 -> (OCR 提取文字，若 OCR 不可用则依赖 vision 模型直接看图)
             -> 调用 AI 将文字整理为 8 列搜索词榜单 JSON 数组
             -> 校验并清洗为 list[dict]

注意：本模块不依赖 PySide，可单独在测试中调用。
"""

import json

from framework.ai_service import AIResponse
from utils.image_ocr import extract_text_from_images, is_ocr_available


# 8 列字段（与 UI 表格、title_optimizer._build_user_prompt 保持一致）
MARKET_KEYS = [
    "rank_type", "search_term", "search_popularity", "trend_word",
    "search_growth", "core_word", "search_increment", "modifier_word",
]


EXTRACT_SYSTEM_PROMPT = (
    "你是电商数据整理助手。下面是一张平台『搜索词榜单』截图的文字识别结果"
    "（可能含有噪点、错字或换行错位）。请将其整理为结构化数据，"
    "输出一个 JSON 数组，不要输出任何解释性文字，也不要使用 Markdown 代码块。\n\n"
    "数组中每个元素是一个对象，字段如下：\n"
    "- rank_type: 榜单类型（如 热搜榜、飙升榜、潜力榜 等；没有则为空字符串）\n"
    "- search_term: 搜索词（必填，最核心的搜索关键词）\n"
    "- search_popularity: 搜索人气（数字或带 + 的量；没有则为空字符串）\n"
    "- trend_word: 趋势词（没有则为空字符串）\n"
    "- search_growth: 搜索增速（百分比或数字；没有则为空字符串）\n"
    "- core_word: 核心词（没有则为空字符串）\n"
    "- search_increment: 搜索增量（数字；没有则为空字符串）\n"
    "- modifier_word: 修饰词（没有则为空字符串）\n"
    "只输出 JSON 数组本身。"
)


def extract_market_rows(ai_service, image_paths: list[str] | None = None,
                        ocr_text: str | None = None) -> tuple[list[dict], str]:
    """从截图 / OCR 文字提取 8 列搜索词榜单数据。

    Args:
        ai_service: 已初始化的 BaseAIService 实例
        image_paths: 本地平台数据截图路径列表
        ocr_text: 已识别的文字（若为空则尝试 OCR 或从 vision 模型直接看图）

    Returns:
        (rows, error_message)
        rows: 清洗后的 list[dict]，每行含 MARKET_KEYS 全部字段
        error_message: 失败原因（成功时为空字符串）
    """
    if not image_paths and not ocr_text:
        return [], "未提供任何截图或文字，无法提取平台数据"

    # 1) 准备 OCR 文字
    if not ocr_text:
        if is_ocr_available():
            extracted = extract_text_from_images(image_paths or [])
            ocr_text = "\n\n".join(
                f"[截图 {idx + 1} 文字识别结果]\n{text}"
                for idx, text in enumerate(extracted.values())
            )
        elif getattr(ai_service, "supports_vision", False):
            # 没有 OCR 但模型支持看图，直接把图交给模型整理
            ocr_text = ""
        else:
            return [], ("OCR 引擎不可用且当前模型不支持图片输入。"
                        "请安装 rapidocr-onnxruntime，或手动填写榜单数据。")

    if not ocr_text.strip():
        # 纯 vision 路径：没有文字，仅靠图片
        if not (image_paths and getattr(ai_service, "supports_vision", False)):
            return [], "未能从截图中识别出任何文字，请上传更清晰的截图或手动填写"

    # 2) 调用 AI 结构化
    vision_images = (
        image_paths if getattr(ai_service, "supports_vision", False) else None
    )
    user_prompt = (
        "以下是平台搜索词榜单的截图文字识别结果，请整理为 JSON 数组：\n\n"
        f"{ocr_text}"
        if ocr_text.strip() else
        "请直接分析这张平台搜索词榜单截图，整理为 JSON 数组。"
    )

    response: AIResponse = ai_service.chat(
        system_prompt=EXTRACT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,
        max_tokens=2048,
        image_paths=vision_images,
    )
    if not response.success:
        return [], f"结构化失败：{response.error_message}"

    # 3) 解析 JSON
    rows = _parse_json_array(response.content)
    if not rows:
        return [], ("AI 返回的内容无法解析为有效的搜索词榜单 JSON，"
                    "请手动填写，或重新上传更清晰的截图。")
    return rows, ""


def _parse_json_array(text: str) -> list[dict]:
    """从模型返回中解析出 JSON 数组并清洗为 8 列字典"""
    try:
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1 or end <= start:
            return []
        raw = text[start:end + 1]
        data = json.loads(raw)
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    cleaned: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        row = {k: str(item.get(k, "")).strip() for k in MARKET_KEYS}
        # 至少要有搜索词，否则视为噪点丢弃
        if row.get("search_term"):
            cleaned.append(row)
    return cleaned
