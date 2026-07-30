"""商品链接解析器：识别电商平台、提取商品ID、规范化链接

支持的平台:
    - 淘宝 (taobao.com)
    - 天猫 (tmall.com)
    - 京东 (jd.com)
    - 拼多多 (yangkeduo.com / pinduoduo.com)
    - 抖音 (jinritemai.com / douyin.com)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse, parse_qs, unquote


class Platform(Enum):
    """支持的电商平台"""
    TAOBAO = "淘宝"
    TMALL = "天猫"
    JD = "京东"
    PDD = "拼多多"
    DOUYIN = "抖音"
    UNKNOWN = "未知平台"


@dataclass
class ParsedLink:
    """解析后的商品链接信息"""
    original_url: str           # 原始输入链接
    platform: Platform          # 识别到的平台
    product_id: str             # 商品ID
    normalized_url: str         # 规范化后的商品链接
    is_valid: bool = False      # 是否为有效的商品链接
    error_message: str = ""     # 解析失败时的错误信息
    extra: dict = field(default_factory=dict)  # 额外信息（如店铺ID等）


class LinkParser:
    """商品链接解析器

    解析流程:
        1. 预处理：去除空格、处理短链等
        2. 平台识别：根据域名匹配平台
        3. 商品ID提取：根据平台特征提取商品ID
        4. 链接规范化：生成标准商品链接
    """

    # 平台域名映射
    PLATFORM_DOMAINS = {
        Platform.TAOBAO: [
            "item.taobao.com",
            "detail.taobao.com",
            "a.m.taobao.com",
            "m.taobao.com",
        ],
        Platform.TMALL: [
            "detail.tmall.com",
            "item.tmall.com",
            "tmall.com",
        ],
        Platform.JD: [
            "item.jd.com",
            "m.jd.com",
            "jd.com",
        ],
        Platform.PDD: [
            "mobile.yangkeduo.com",
            "yangkeduo.com",
            "pinduoduo.com",
            "mobile.pinduoduo.com",
        ],
        Platform.DOUYIN: [
            "haohuo.jinritemai.com",
            "jinritemai.com",
            "buyin.jinritemai.com",
            "haohuo.douyin.com",
        ],
    }

    # 短链域名（需要重定向才能获取真实链接）
    SHORT_LINK_DOMAINS = {
        "tb.cn": Platform.TAOBAO,
        "tm.cn": Platform.TMALL,
        "jd.cn": Platform.JD,
        "pdd.cn": Platform.PDD,
    }

    def parse(self, raw_url: str) -> ParsedLink:
        """解析商品链接

        Args:
            raw_url: 用户输入的原始链接

        Returns:
            ParsedLink: 解析结果
        """
        # 预处理
        url = self._preprocess(raw_url)
        if not url:
            return ParsedLink(
                original_url=raw_url,
                platform=Platform.UNKNOWN,
                product_id="",
                normalized_url="",
                is_valid=False,
                error_message="链接为空",
            )

        # 解析URL
        try:
            parsed = urlparse(url)
        except Exception:
            return ParsedLink(
                original_url=raw_url,
                platform=Platform.UNKNOWN,
                product_id="",
                normalized_url="",
                is_valid=False,
                error_message="URL格式无效",
            )

        host = parsed.hostname or ""

        # 识别平台
        platform = self._identify_platform(host)
        if platform == Platform.UNKNOWN:
            return ParsedLink(
                original_url=raw_url,
                platform=Platform.UNKNOWN,
                product_id="",
                normalized_url=url,
                is_valid=False,
                error_message=f"不支持的平台: {host}",
            )

        # 提取商品ID
        product_id = self._extract_product_id(platform, parsed, url)
        if not product_id:
            return ParsedLink(
                original_url=raw_url,
                platform=platform,
                product_id="",
                normalized_url=url,
                is_valid=False,
                error_message="无法从链接中提取商品ID",
            )

        # 规范化链接
        normalized = self._normalize_url(platform, product_id)

        return ParsedLink(
            original_url=raw_url,
            platform=platform,
            product_id=product_id,
            normalized_url=normalized,
            is_valid=True,
        )

    def _preprocess(self, raw_url: str) -> str:
        """预处理原始链接"""
        if not raw_url:
            return ""

        url = raw_url.strip()

        # 去除可能的前后引号
        url = url.strip("\"'`")

        # 去除可能的多余空格和换行
        url = url.strip()

        if not url:
            return ""

        # 如果没有协议头，添加 https://
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        return url

    def _identify_platform(self, host: str) -> Platform:
        """根据域名识别平台"""
        host = host.lower()

        # 检查短链
        for short_domain, platform in self.SHORT_LINK_DOMAINS.items():
            if short_domain in host:
                return platform

        # 检查各平台域名
        for platform, domains in self.PLATFORM_DOMAINS.items():
            for domain in domains:
                if domain in host:
                    return platform

        return Platform.UNKNOWN

    def _extract_product_id(self, platform: Platform, parsed, url: str) -> str:
        """根据平台特征提取商品ID

        各平台商品ID提取规则:
            - 淘宝: URL参数 id=xxx 或路径 /item.htm?id=xxx
            - 天猫: URL参数 id=xxx
            - 京东: 路径 /product/xxx.html 或 /xxx.html
            - 拼多多: URL参数 goods_id=xxx
            - 抖音: URL参数 product_id=xxx 或路径 /product/xxx
        """
        host = (parsed.hostname or "").lower()
        path = parsed.path or ""
        query_params = parse_qs(parsed.query or "")

        if platform == Platform.TAOBAO:
            return self._extract_taobao_id(query_params, path)

        elif platform == Platform.TMALL:
            return self._extract_tmall_id(query_params, path)

        elif platform == Platform.JD:
            return self._extract_jd_id(path, query_params)

        elif platform == Platform.PDD:
            return self._extract_pdd_id(query_params, path)

        elif platform == Platform.DOUYIN:
            return self._extract_douyin_id(query_params, path)

        return ""

    def _extract_taobao_id(self, query_params: dict, path: str) -> str:
        """提取淘宝商品ID"""
        # 优先从查询参数获取
        if "id" in query_params:
            return query_params["id"][0]

        # 从路径提取 /item.htm?id=xxx 已在query中处理
        # 处理 a.m.taobao.com/iXXX.htm 格式
        match = re.search(r"/i(\d+)\.htm", path)
        if match:
            return match.group(1)

        return ""

    def _extract_tmall_id(self, query_params: dict, path: str) -> str:
        """提取天猫商品ID"""
        if "id" in query_params:
            return query_params["id"][0]

        # 处理 /item/xxx.htm 格式
        match = re.search(r"/item/(\d+)", path)
        if match:
            return match.group(1)

        return ""

    def _extract_jd_id(self, path: str, query_params: dict) -> str:
        """提取京东商品ID"""
        # /product/xxx.html
        match = re.search(r"/product/(\d+)", path)
        if match:
            return match.group(1)

        # /xxx.html (直接ID)
        match = re.search(r"/(\d{6,})\.html", path)
        if match:
            return match.group(1)

        # 移动端 m.jd.com/products/xxx/xxx.html
        match = re.search(r"/products?/(\d+)", path)
        if match:
            return match.group(1)

        # 从查询参数获取
        if "sku" in query_params:
            return query_params["sku"][0]
        if "productUrl" in query_params:
            # productUrl 可能包含真实链接
            inner = unquote(query_params["productUrl"][0])
            inner_match = re.search(r"/product/(\d+)", inner)
            if inner_match:
                return inner_match.group(1)

        return ""

    def _extract_pdd_id(self, query_params: dict, path: str) -> str:
        """提取拼多多商品ID"""
        if "goods_id" in query_params:
            return query_params["goods_id"][0]

        # /goods_xxx.htm
        match = re.search(r"/goods_(\d+)", path)
        if match:
            return match.group(1)

        return ""

    def _extract_douyin_id(self, query_params: dict, path: str) -> str:
        """提取抖音商品ID"""
        if "product_id" in query_params:
            return query_params["product_id"][0]

        # /product/xxx
        match = re.search(r"/product/(\d+)", path)
        if match:
            return match.group(1)

        # /xxx.html
        match = re.search(r"/(\d{10,})\.html", path)
        if match:
            return match.group(1)

        return ""

    def _normalize_url(self, platform: Platform, product_id: str) -> str:
        """生成规范化的商品链接"""
        if platform == Platform.TAOBAO:
            return f"https://item.taobao.com/item.htm?id={product_id}"
        elif platform == Platform.TMALL:
            return f"https://detail.tmall.com/item.htm?id={product_id}"
        elif platform == Platform.JD:
            return f"https://item.jd.com/{product_id}.html"
        elif platform == Platform.PDD:
            return f"https://mobile.yangkeduo.com/goods.html?goods_id={product_id}"
        elif platform == Platform.DOUYIN:
            return f"https://haohuo.jinritemai.com/product/{product_id}"
        return ""
