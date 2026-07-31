"""标题优化器测试"""

import pytest
from unittest.mock import MagicMock

from apps.title_optimizer.title_optimizer import (
    TitleOptimizer, OptimizeStyle, OPTIMIZE_STYLES,
)
from framework.ai_service import AIResponse


class FakeAIService:
    """模拟 AI 服务"""

    def __init__(self):
        self.last_image_paths = None
        self.last_user_prompt = None

    def chat(self, system_prompt: str, user_prompt: str,
             temperature: float = 0.7, max_tokens: int = 2048,
             image_paths: list[str] | None = None) -> AIResponse:
        self.last_user_prompt = user_prompt
        self.last_image_paths = image_paths
        return AIResponse(
            content=(
                "优化标题：测试优化标题\n"
                "SEO关键词：关键词A, 关键词B\n"
                "关键词布局：核心词+修饰词+属性词\n"
                "优化理由：测试理由"
            ),
            success=True,
            tokens_total=100,
        )


@pytest.fixture
def optimizer():
    return TitleOptimizer(FakeAIService())


def test_data_driven_style_exists():
    """数据驱动优化风格已注册"""
    keys = [s.key for s in OPTIMIZE_STYLES]
    assert "data_driven" in keys


def test_optimize_with_market_data(optimizer):
    """优化器能接收并传递市场数据"""
    market_data = [
        {
            "rank_type": "飙升榜",
            "search_term": "连衣裙",
            "search_popularity": "1000+",
            "trend_word": "碎花",
            "search_growth": "120%",
            "core_word": "连衣裙",
            "search_increment": "500+",
            "modifier_word": "夏季",
        }
    ]
    result = optimizer.optimize(
        "女装连衣裙",
        style_key="data_driven",
        market_data=market_data,
        image_paths=["fake.png"],
    )

    assert result.success
    assert result.optimized_title == "测试优化标题"
    assert result.keyword_layout == "核心词+修饰词+属性词"
    assert "连衣裙" in optimizer._ai.last_user_prompt
    assert "飙升榜" in optimizer._ai.last_user_prompt
    assert optimizer._ai.last_image_paths == ["fake.png"]


def test_build_user_prompt_without_market_data(optimizer):
    """无市场数据时 prompt 正常构建"""
    prompt = optimizer._build_user_prompt("原标题", {"category": "手机"}, None)
    assert "原标题：原标题" in prompt
    assert "商品类目：手机" in prompt
    assert "平台搜索词榜单数据" not in prompt


def test_build_user_prompt_with_market_data(optimizer):
    """有市场数据时 prompt 包含表格"""
    market_data = [
        {"rank_type": "热搜榜", "search_term": "T恤", "search_popularity": "5000+",
         "trend_word": "纯棉", "search_growth": "30%", "core_word": "T恤",
         "search_increment": "1000+", "modifier_word": "男"},
    ]
    prompt = optimizer._build_user_prompt("男T恤", None, market_data)
    assert "平台搜索词榜单数据" in prompt
    assert "热搜榜" in prompt
    assert "T恤" in prompt


def test_parse_response_keyword_layout():
    """解析器能提取关键词布局"""
    opt = TitleOptimizer(FakeAIService())
    parsed = opt._parse_response(
        "优化标题：A\nSEO关键词：x, y\n关键词布局：核心+修饰\n优化理由：B"
    )
    assert parsed["title"] == "A"
    assert parsed["keyword_layout"] == "核心+修饰"
    assert parsed["reason"] == "B"


def test_unknown_style_returns_error():
    """未知风格返回错误结果"""
    opt = TitleOptimizer(FakeAIService())
    result = opt.optimize("标题", style_key="not_exist")
    assert not result.success
    assert "未知" in result.error_message
