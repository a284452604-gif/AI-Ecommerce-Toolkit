"""标题优化器：封装 AI prompt 模板和优化策略"""

from dataclasses import dataclass, field
from framework.ai_service import AIResponse
from utils.image_ocr import extract_text_from_images, is_ocr_available


# ── 优化风格定义 ───────────────────────────────────────────

@dataclass
class OptimizeStyle:
    """优化风格配置"""
    key: str
    name: str
    description: str
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 1024


OPTIMIZE_STYLES = [
    OptimizeStyle(
        key="seo",
        name="搜索优化",
        description="优化关键词密度和排序，提升搜索结果排名",
        system_prompt="你是一个电商SEO专家，专注于优化商品标题以提升搜索引擎排名。"
                      "你需要分析原标题的关键词，保留核心卖点，补充高频搜索词，"
                      "确保标题长度在30-60字之间，关键词出现在靠前位置。"
                      "禁止堆砌无关关键词，禁止使用违禁词。",
        temperature=0.5,
        max_tokens=800,
    ),
    OptimizeStyle(
        key="promotion",
        name="促销转化",
        description="增强购买欲望，突出优惠和紧迫感，提升点击转化率",
        system_prompt="你是一个电商文案专家，擅长撰写高转化率的促销标题。"
                      "你需要从用户心理出发，突出产品核心卖点、优惠力度、使用场景，"
                      "制造适度的紧迫感（如限时、限量），但不过度夸张。"
                      "标题應控制在20-50字，情感化但不虚假宣传。",
        temperature=0.7,
        max_tokens=800,
    ),
    OptimizeStyle(
        key="brand",
        name="品牌调性",
        description="打造品牌化标题，建立品牌认知和专业形象",
        system_prompt="你是一个品牌策划专家，擅长撰写有品牌调性的商品标题。"
                      "你需要提炼产品的品牌价值主张，使用简洁、高级、有质感的语言，"
                      "避免使用'爆款''秒杀'等低端促销词汇。"
                      "标题应控制在15-40字，注重品牌感和专业度。",
        temperature=0.8,
        max_tokens=800,
    ),
    OptimizeStyle(
        key="data_driven",
        name="数据驱动优化",
        description="结合平台搜索词榜单数据与截图，优化关键词布局",
        system_prompt="你是一位数据驱动的电商 SEO 专家。"
                      "你会结合平台后台的搜索词榜单数据（搜索人气、搜索增速、搜索增量等）"
                      "以及用户上传的平台数据截图，为商品标题给出关键词布局建议。"
                      "优先使用高搜索人气、高增速、高增量的搜索词；"
                      "合理搭配核心词、趋势词、修饰词；避免关键词堆砌和违禁词。"
                      "标题长度控制在30-60字，核心关键词尽量前置。",
        temperature=0.5,
        max_tokens=1200,
    ),
]


# ── 标题优化器 ─────────────────────────────────────────────

@dataclass
class OptimizeResult:
    """单次优化结果"""
    original_title: str
    optimized_title: str
    style: str                    # 优化风格 key
    style_name: str               # 优化风格显示名
    seo_keywords: list[str] = field(default_factory=list)
    improvement_reason: str = ""  # 优化理由
    keyword_layout: str = ""      # 数据驱动优化中的关键词布局建议
    tokens_used: int = 0
    success: bool = True
    error_message: str = ""


class TitleOptimizer:
    """标题优化器

    根据指定的优化风格，调用 AI 服务生成优化后的标题。
    可多次调用 optimize() 生成多种风格的优化结果。

    用法:
        optimizer = TitleOptimizer(ai_service)
        result = optimizer.optimize("苹果手机壳硅胶全包防摔", style_key="seo")
    """

    def __init__(self, ai_service):
        """初始化优化器

        Args:
            ai_service: BaseAIService 实例（已初始化）
        """
        self._ai = ai_service
        self._styles: dict[str, OptimizeStyle] = {
            s.key: s for s in OPTIMIZE_STYLES
        }

    @property
    def available_styles(self) -> list[OptimizeStyle]:
        """获取所有可用的优化风格"""
        return list(OPTIMIZE_STYLES)

    def get_style(self, key: str) -> OptimizeStyle | None:
        """根据 key 获取风格配置"""
        return self._styles.get(key)

    def optimize(self, original_title: str, style_key: str = "seo",
                 product_info: dict | None = None,
                 market_data: list[dict] | None = None,
                 image_paths: list[str] | None = None) -> OptimizeResult:
        """优化商品标题

        Args:
            original_title: 原标题
            style_key: 优化风格 (seo / promotion / brand / data_driven)
            product_info: 可选的商品信息字典，如 {"category": "手机配件", "price": "29.9"}
            market_data: 平台搜索词榜单数据行列表，每行包含
                rank_type, search_term, search_popularity, trend_word,
                search_growth, core_word, search_increment, modifier_word
            image_paths: 本地平台数据截图路径列表（需要模型支持 vision）

        Returns:
            OptimizeResult: 优化结果
        """
        style = self._styles.get(style_key)
        if style is None:
            return OptimizeResult(
                original_title=original_title,
                optimized_title="",
                style=style_key,
                style_name=style_key,
                success=False,
                error_message=f"未知的优化风格: {style_key}",
            )

        # 处理截图：vision 模型直接传图；非 vision 模型尝试 OCR 提取文字追加到 prompt
        images_for_model: list[str] | None = image_paths
        ocr_text = ""
        if image_paths and not self._ai.supports_vision:
            images_for_model = None
            extracted = extract_text_from_images(image_paths)
            if extracted:
                ocr_text = "\n\n".join(
                    f"[截图 {idx + 1} 文字识别结果]\n{text}"
                    for idx, text in enumerate(extracted.values())
                )
            elif not is_ocr_available():
                ocr_text = "[提示：当前模型不支持图片输入，且 OCR 引擎未安装，截图内容无法被 AI 使用。请安装 rapidocr-onnxruntime 或手动填写下方搜索词榜单数据。]"

        user_prompt = self._build_user_prompt(
            original_title, product_info, market_data, ocr_text
        )

        response: AIResponse = self._ai.chat(
            system_prompt=style.system_prompt,
            user_prompt=user_prompt,
            temperature=style.temperature,
            max_tokens=style.max_tokens,
            image_paths=images_for_model,
        )

        if not response.success:
            # 若是因 image_url 不被支持导致的失败，给出更明确的提示
            error_msg = response.error_message
            if "image_url" in error_msg.lower() or "unknown variant" in error_msg.lower():
                error_msg = (
                    f"{error_msg}\n\n当前模型 '{self._ai.model}' 不支持图片输入。"
                    "如上传了截图，请切换至支持 vision 的模型（如 gpt-4o），"
                    "或安装 OCR 依赖后重试。"
                )
            return OptimizeResult(
                original_title=original_title,
                optimized_title="",
                style=style_key,
                style_name=style.name,
                success=False,
                error_message=error_msg,
            )

        parsed = self._parse_response(response.content)
        return OptimizeResult(
            original_title=original_title,
            optimized_title=parsed["title"],
            style=style_key,
            style_name=style.name,
            seo_keywords=parsed["keywords"],
            improvement_reason=parsed["reason"],
            keyword_layout=parsed.get("keyword_layout", ""),
            tokens_used=response.tokens_total,
            success=True,
        )

    def _build_user_prompt(self, title: str, product_info: dict | None,
                           market_data: list[dict] | None,
                           ocr_text: str = "") -> str:
        """构建用户 prompt"""
        lines = [f"原标题：{title}"]
        if product_info:
            if product_info.get("category"):
                lines.append(f"商品类目：{product_info['category']}")
            if product_info.get("price"):
                lines.append(f"价格：{product_info['price']}")
            if product_info.get("brand"):
                lines.append(f"品牌：{product_info['brand']}")
            if product_info.get("shop"):
                lines.append(f"店铺：{product_info['shop']}")

        # 平台搜索词榜单数据
        if market_data:
            lines.append("")
            lines.append("平台搜索词榜单数据：")
            lines.append(
                "榜单类型 | 搜索词 | 搜索人气 | 趋势词 | 搜索增速 | 核心词 | 搜索增量 | 修饰词"
            )
            for row in market_data:
                if not isinstance(row, dict):
                    continue
                cells = [
                    str(row.get("rank_type", "")),
                    str(row.get("search_term", "")),
                    str(row.get("search_popularity", "")),
                    str(row.get("trend_word", "")),
                    str(row.get("search_growth", "")),
                    str(row.get("core_word", "")),
                    str(row.get("search_increment", "")),
                    str(row.get("modifier_word", "")),
                ]
                lines.append(" | ".join(cells))

        # OCR 提取的截图文字
        if ocr_text:
            lines.append("")
            lines.append("平台数据截图文字识别结果：")
            lines.append(ocr_text)

        lines.append("")
        lines.append("请按以下格式输出（不要输出任何其他内容）：")
        lines.append("优化标题：<优化后的标题>")
        lines.append("SEO关键词：<关键词1>, <关键词2>, <关键词3>")
        lines.append("关键词布局：<核心词>+<修饰词>+<属性词>/<趋势词>（用'+'连接，简明展示布局）")
        lines.append("优化理由：<简要说明优化思路，2-3句话>")
        return "\n".join(lines)

    def _parse_response(self, content: str) -> dict:
        """解析 AI 返回的结构化内容"""
        result = {"title": content, "keywords": [], "reason": "", "keyword_layout": ""}

        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("优化标题：") or line.startswith("优化标题:"):
                result["title"] = line.split("：", 1)[-1].split(":", 1)[-1].strip()
            elif line.startswith("SEO关键词：") or line.startswith("SEO关键词:"):
                kw_str = line.split("：", 1)[-1].split(":", 1)[-1].strip()
                result["keywords"] = [k.strip() for k in kw_str.split(",") if k.strip()]
            elif line.startswith("关键词布局：") or line.startswith("关键词布局:"):
                result["keyword_layout"] = line.split("：", 1)[-1].split(":", 1)[-1].strip()
            elif line.startswith("优化理由：") or line.startswith("优化理由:"):
                result["reason"] = line.split("：", 1)[-1].split(":", 1)[-1].strip()

        return result
