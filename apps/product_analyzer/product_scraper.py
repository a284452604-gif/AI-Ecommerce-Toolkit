"""商品数据抓取器：从电商平台商品页面提取商品信息

使用 httpx 发送 HTTP 请求，BeautifulSoup 解析 HTML，
提取商品标题、价格、图片、店铺等信息。

注意:
    电商平台有反爬机制，本抓取器采用以下策略:
    1. 使用浏览器 User-Agent
    2. 从 meta 标签提取 og:title、og:image 等信息
    3. 从页面内嵌 JSON 数据提取结构化信息
    4. 抓取失败时返回已解析的链接信息，不阻断流程
"""

from __future__ import annotations

import re
import json
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from apps.product_analyzer.link_parser import ParsedLink, Platform


@dataclass
class ProductInfo:
    """商品信息"""
    platform: str = ""               # 平台名称
    product_id: str = ""             # 商品ID
    title: str = ""                  # 商品标题
    price: str = ""                  # 商品价格
    original_price: str = ""         # 原价
    image_urls: list[str] = field(default_factory=list)  # 商品图片URL列表
    shop_name: str = ""              # 店铺名称
    shop_url: str = ""               # 店铺链接
    description: str = ""            # 商品描述
    url: str = ""                    # 商品链接
    fetch_time: float = 0.0          # 抓取耗时(秒)
    success: bool = False            # 是否成功抓取
    error_message: str = ""          # 错误信息
    raw_data: dict = field(default_factory=dict)  # 原始数据


class ProductScraper:
    """商品数据抓取器

    抓取流程:
        1. 根据平台构造请求
        2. 发送 HTTP GET 请求获取页面 HTML
        3. 使用 BeautifulSoup 解析 HTML
        4. 根据平台特征提取商品信息
        5. 返回 ProductInfo
    """

    # 通用请求头
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    # 各平台额外请求头
    PLATFORM_HEADERS = {
        Platform.TAOBAO: {
            "Referer": "https://www.taobao.com/",
        },
        Platform.TMALL: {
            "Referer": "https://www.tmall.com/",
        },
        Platform.JD: {
            "Referer": "https://www.jd.com/",
        },
        Platform.PDD: {
            "Referer": "https://mobile.yangkeduo.com/",
        },
        Platform.DOUYIN: {
            "Referer": "https://www.douyin.com/",
        },
    }

    def __init__(self, timeout: float = 15.0, max_redirects: int = 5):
        """初始化抓取器

        Args:
            timeout: 请求超时时间（秒）
            max_redirects: 最大重定向次数
        """
        self._timeout = timeout
        self._max_redirects = max_redirects

    def scrape(self, parsed_link: ParsedLink) -> ProductInfo:
        """抓取商品信息

        Args:
            parsed_link: 解析后的链接信息

        Returns:
            ProductInfo: 商品信息
        """
        if not parsed_link.is_valid:
            return ProductInfo(
                platform=parsed_link.platform.value,
                product_id=parsed_link.product_id,
                url=parsed_link.normalized_url,
                success=False,
                error_message=parsed_link.error_message or "链接无效",
            )

        start_time = time.time()
        url = parsed_link.normalized_url
        platform = parsed_link.platform

        info = ProductInfo(
            platform=platform.value,
            product_id=parsed_link.product_id,
            url=url,
        )

        try:
            # 发送请求
            html = self._fetch_page(url, platform)

            if not html:
                info.error_message = "页面内容为空"
                info.fetch_time = round(time.time() - start_time, 2)
                return info

            # 解析HTML
            soup = BeautifulSoup(html, "lxml")

            # 通用提取：从 meta 标签获取信息
            self._extract_from_meta(soup, info)

            # 按平台提取
            if platform == Platform.TAOBAO:
                self._extract_taobao(soup, info)
            elif platform == Platform.TMALL:
                self._extract_tmall(soup, info)
            elif platform == Platform.JD:
                self._extract_jd(soup, info)
            elif platform == Platform.PDD:
                self._extract_pdd(soup, info)
            elif platform == Platform.DOUYIN:
                self._extract_douyin(soup, info)

            # 补全信息
            if not info.title:
                info.title = soup.title.string.strip() if soup.title and soup.title.string else "未知标题"
            if not info.image_urls:
                self._extract_images(soup, info)

            info.success = bool(info.title)
            info.fetch_time = round(time.time() - start_time, 2)

        except httpx.TimeoutException:
            info.error_message = f"请求超时（{self._timeout}秒）"
            info.fetch_time = round(time.time() - start_time, 2)
        except httpx.HTTPStatusError as e:
            info.error_message = f"HTTP错误: {e.response.status_code}"
            info.fetch_time = round(time.time() - start_time, 2)
        except Exception as e:
            info.error_message = f"抓取失败: {type(e).__name__}: {e}"
            info.fetch_time = round(time.time() - start_time, 2)

        return info

    def _fetch_page(self, url: str, platform: Platform) -> Optional[str]:
        """发送HTTP请求获取页面HTML"""
        headers = {**self.DEFAULT_HEADERS}
        if platform in self.PLATFORM_HEADERS:
            headers.update(self.PLATFORM_HEADERS[platform])

        with httpx.Client(
            follow_redirects=True,
            max_redirects=self._max_redirects,
            timeout=self._timeout,
            verify=False,
        ) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()

            # 尝试检测编码
            encoding = response.encoding or "utf-8"
            if encoding.lower() in ("gb2312", "gbk"):
                encoding = "gbk"

            return response.content.decode(encoding, errors="replace")

    def _extract_from_meta(self, soup: BeautifulSoup, info: ProductInfo):
        """从 meta 标签提取通用信息"""
        # og:title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content") and not info.title:
            info.title = og_title["content"].strip()

        # og:image
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            info.image_urls.append(og_image["content"].strip())

        # og:description
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content") and not info.description:
            info.description = og_desc["content"].strip()

        # keywords
        keywords = soup.find("meta", attrs={"name": "keywords"})
        if keywords and keywords.get("content") and not info.description:
            info.description = keywords["content"].strip()

    def _extract_images(self, soup: BeautifulSoup, info: ProductInfo):
        """从页面提取图片"""
        for img in soup.find_all("img", limit=10):
            src = img.get("src") or img.get("data-src") or ""
            if src and ("http" in src or src.startswith("//")):
                if src.startswith("//"):
                    src = "https:" + src
                if src not in info.image_urls:
                    info.image_urls.append(src)
            if len(info.image_urls) >= 5:
                break

    def _extract_from_json(self, soup: BeautifulSoup, patterns: list[str]) -> Optional[dict]:
        """从 script 标签中提取 JSON 数据

        Args:
            soup: BeautifulSoup 对象
            patterns: 要匹配的正则模式列表

        Returns:
            解析后的 JSON 字典，未找到返回 None
        """
        for script in soup.find_all("script"):
            text = script.string or ""
            if not text:
                continue

            for pattern in patterns:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    try:
                        json_str = match.group(1).strip()
                        # 去除末尾多余的分号等
                        json_str = json_str.rstrip(";")
                        return json.loads(json_str)
                    except (json.JSONDecodeError, IndexError):
                        continue
        return None

    def _extract_taobao(self, soup: BeautifulSoup, info: ProductInfo):
        """提取淘宝商品信息"""
        # 尝试从页面 JSON 数据提取
        data = self._extract_from_json(soup, [
            r'"title"\s*:\s*"([^"]+)"',
            r'g_page_config\s*=\s*({.*?});\s*</script',
        ])

        if data:
            if isinstance(data, dict):
                item = data.get("item", data)
                if not info.title and "title" in item:
                    info.title = str(item["title"])

        # 提取价格
        price_tag = soup.find("span", class_=re.compile(r"price|tb-rmb-num"))
        if price_tag:
            info.price = price_tag.get_text(strip=True)

        # 提取店铺名
        shop_tag = soup.find("a", class_=re.compile(r"shopname|seller|J_ShopInfo"))
        if shop_tag:
            info.shop_name = shop_tag.get_text(strip=True)

    def _extract_tmall(self, soup: BeautifulSoup, info: ProductInfo):
        """提取天猫商品信息（与淘宝类似）"""
        self._extract_taobao(soup, info)

    def _extract_jd(self, soup: BeautifulSoup, info: ProductInfo):
        """提取京东商品信息"""
        # 标题
        if not info.title:
            title_tag = soup.find("div", class_="sku-name") or soup.find("div", class_="itemInfo-wrap")
            if title_tag:
                info.title = title_tag.get_text(strip=True)

        # 价格
        price_tag = soup.find("span", class_="price") or soup.find("span", class_=re.compile(r"p-price"))
        if price_tag:
            price_text = price_tag.get_text(strip=True)
            # 清理价格文本
            price_text = re.sub(r"[^\d.¥￥]", "", price_text)
            if price_text:
                info.price = price_text

        # 从嵌入的 JSON 提取
        for script in soup.find_all("script"):
            text = script.string or ""
            if not text:
                continue

            # colorSize 数据包含价格和图片
            if "colorSize" in text:
                # 提取图片
                img_matches = re.findall(r'"skuImg"\s*:\s*"(//img\d+\.360buyimg\.com[^"]+)"', text)
                for img_url in img_matches[:3]:
                    full_url = "https:" + img_url if img_url.startswith("//") else img_url
                    if full_url not in info.image_urls:
                        info.image_urls.append(full_url)

            # 提取店铺名
            if not info.shop_name and "shopName" in text:
                shop_match = re.search(r'"shopName"\s*:\s*"([^"]+)"', text)
                if shop_match:
                    info.shop_name = shop_match.group(1)

        # 店铺名
        if not info.shop_name:
            shop_tag = soup.find("div", class_="J-hove-wrap") or soup.find("a", class_=re.compile(r"shop"))
            if shop_tag:
                info.shop_name = shop_tag.get_text(strip=True)

    def _extract_pdd(self, soup: BeautifulSoup, info: ProductInfo):
        """提取拼多多商品信息"""
        # 拼多多页面高度 JS 渲染，尝试从 JSON 提取
        data = self._extract_from_json(soup, [
            r'window\.__rawData\s*=\s*({.*?})\s*;?\s*</script',
            r'"goodsName"\s*:\s*"([^"]+)"',
        ])

        if data and isinstance(data, dict):
            if not info.title and "goodsName" in data:
                info.title = data["goodsName"]
            if not info.price:
                price_info = data.get("minNormalPrice") or data.get("minGroupPrice")
                if price_info:
                    # 拼多多价格通常以分为单位
                    info.price = f"¥{int(price_info) / 100:.2f}"
            if not info.shop_name and "mallName" in data:
                info.shop_name = data["mallName"]

    def _extract_douyin(self, soup: BeautifulSoup, info: ProductInfo):
        """提取抖音商品信息"""
        # 尝试从 JSON 提取
        data = self._extract_from_json(soup, [
            r'"product_name"\s*:\s*"([^"]+)"',
            r'window\._SSR_DATA\s*=\s*({.*?})\s*;?\s*</script',
        ])

        if data and isinstance(data, dict):
            if not info.title:
                info.title = data.get("product_name", data.get("title", ""))
            if not info.price:
                price = data.get("price") or data.get("min_price")
                if price:
                    info.price = f"¥{int(price) / 100:.2f}"
