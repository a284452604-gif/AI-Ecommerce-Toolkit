"""浏览器抓取器：基于 Playwright 的真实浏览器渲染抓取

电商详情页（淘宝/天猫等）普遍采用 JS 渲染 + 反爬，
纯 HTTP 请求拿不到价格/店铺等核心信息。本抓取器使用
Playwright 启动真实 Chromium 浏览器，渲染页面后提取数据，
并支持注入用户登录 Cookie 以绕过登录限制。

设计:
    - 浏览器实例懒加载并单例复用，降低每条链接的启动开销
    - 支持按平台注入 Cookie（从设置页复制而来）
    - 标题优先从 og:title / 页面内嵌 JSON 提取，价格/店铺用平台选择器
"""

from __future__ import annotations

import time
from typing import Optional

from apps.product_analyzer.product_scraper import ProductInfo
from apps.product_analyzer.link_parser import ParsedLink, Platform

try:
    from playwright.sync_api import sync_playwright
    _HAS_PLAYWRIGHT = True
except ImportError:
    _HAS_PLAYWRIGHT = False


# 各平台 Cookie 注入所需的域名
PLATFORM_COOKIE_DOMAIN: dict[Platform, str] = {
    Platform.TAOBAO: ".taobao.com",
    Platform.TMALL: ".tmall.com",
    Platform.JD: ".jd.com",
    Platform.PDD: ".yangkeduo.com",
    Platform.DOUYIN: ".douyin.com",
}


def parse_cookie_string(cookie_str: str, domain: str) -> list[dict]:
    """将浏览器复制的 Cookie 字符串解析为 Playwright 格式

    Args:
        cookie_str: 形如 "key1=val1; key2=val2" 的字符串
        domain: Cookie 作用的域名（含前导点）

    Returns:
        Playwright add_cookies 接受的字典列表
    """
    cookies: list[dict] = []
    cookie_str = (cookie_str or "").strip()
    if not cookie_str:
        return cookies
    for part in cookie_str.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        name = name.strip()
        value = value.strip()
        if not name:
            continue
        cookies.append({
            "name": name,
            "value": value,
            "domain": domain,
            "path": "/",
        })
    return cookies


class BrowserScraper:
    """基于 Playwright 的浏览器抓取器（浏览器单例复用）"""

    _playwright = None
    _browser = None

    @classmethod
    def is_available(cls) -> bool:
        """Playwright 是否可用（已安装且浏览器已下载）"""
        return _HAS_PLAYWRIGHT

    @classmethod
    def _ensure_browser(cls, headless: bool = True):
        """懒加载并缓存浏览器实例"""
        if cls._browser is None:
            cls._playwright = sync_playwright().start()
            cls._browser = cls._playwright.chromium.launch(headless=headless)
        return cls._browser

    @classmethod
    def shutdown(cls):
        """关闭浏览器实例（应用退出时调用）"""
        if cls._browser is not None:
            try:
                cls._browser.close()
            except Exception:
                pass
            cls._browser = None
        if cls._playwright is not None:
            try:
                cls._playwright.stop()
            except Exception:
                pass
            cls._playwright = None

    def __init__(
        self,
        timeout: float = 30.0,
        headless: bool = True,
        cookies: Optional[dict[str, str]] = None,
    ):
        """初始化浏览器抓取器

        Args:
            timeout: 页面加载超时（秒）
            headless: 是否无头模式
            cookies: 各平台 Cookie 字符串，键为平台英文名
                     （taobao/tmall/jd/pdd/douyin）
        """
        self._timeout = timeout
        self._headless = headless
        self._cookies = cookies or {}

    def scrape(self, parsed_link: ParsedLink) -> ProductInfo:
        """使用浏览器抓取商品信息

        Returns:
            ProductInfo: 抓取到的商品信息
        """
        if not _HAS_PLAYWRIGHT:
            return ProductInfo(
                platform=parsed_link.platform.value,
                product_id=parsed_link.product_id,
                url=parsed_link.normalized_url,
                success=False,
                error_message="浏览器抓取组件未安装（缺少 playwright）",
            )

        if not parsed_link.is_valid:
            return ProductInfo(
                platform=parsed_link.platform.value,
                product_id=parsed_link.product_id,
                url=parsed_link.normalized_url,
                success=False,
                error_message=parsed_link.error_message or "链接无效",
            )

        info = ProductInfo(
            platform=parsed_link.platform.value,
            product_id=parsed_link.product_id,
            url=parsed_link.normalized_url,
        )
        start_time = time.time()
        browser = self._ensure_browser(self._headless)
        context = None
        page = None
        try:
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                locale="zh-CN",
            )

            # 注入该平台登录 Cookie
            domain = PLATFORM_COOKIE_DOMAIN.get(parsed_link.platform)
            cookie_str = self._cookies.get(parsed_link.platform.value)
            if domain and cookie_str:
                context.add_cookies(parse_cookie_string(cookie_str, domain))

            page = context.new_page()
            page.goto(
                parsed_link.normalized_url,
                wait_until="domcontentloaded",
                timeout=self._timeout * 1000,
            )
            # 等待网络空闲（部分站点长连接，忽略超时）
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            # 给 JS 渲染一点时间
            page.wait_for_timeout(1500)

            self._extract(page, info)

            # 登录页检测：避免把登录页误判为成功
            if self._is_login_page(page, info):
                info.error_message = (
                    info.error_message
                    or "该商品页面要求登录后才能查看，请在「系统设置 → 商品抓取设置」"
                       "中填入对应平台的登录 Cookie。"
                )
                info.success = False
                if not info.title or info.title == "未知标题":
                    info.title = "未知标题"
            else:
                info.success = bool(info.title and info.title != "未知标题")
        except Exception as e:
            info.error_message = f"浏览器抓取失败: {type(e).__name__}: {e}"
            info.success = False
        finally:
            if page is not None:
                try:
                    page.close()
                except Exception:
                    pass
            if context is not None:
                try:
                    context.close()
                except Exception:
                    pass

        info.fetch_time = round(time.time() - start_time, 2)
        return info

    def _extract(self, page, info: ProductInfo):
        """从已加载页面提取商品信息"""
        # 通用：og:title
        og_title = page.query_selector('meta[property="og:title"]')
        if og_title:
            content = og_title.get_attribute("content")
            if content and content.strip():
                info.title = content.strip()

        # 通用：og:image
        og_image = page.query_selector('meta[property="og:image"]')
        if og_image:
            src = og_image.get_attribute("content")
            if src:
                if src.startswith("//"):
                    src = "https:" + src
                info.image_urls.append(src)

        platform = info.platform

        if platform in ("淘宝", "天猫"):
            self._extract_taobao(page, info)
        elif platform == "京东":
            self._extract_jd(page, info)
        elif platform == "拼多多":
            self._extract_pdd(page, info)
        elif platform == "抖音":
            self._extract_douyin(page, info)

        # 兜底标题
        if not info.title:
            try:
                t = page.title()
            except Exception:
                t = ""
            info.title = t.strip() if t else "未知标题"

        # 兜底图片
        if not info.image_urls:
            img = page.query_selector("img#J_ImgBooth, .tb-main-pic img, #spec-n1 img, .swiper-slide img")
            if img:
                src = img.get_attribute("src") or img.get_attribute("data-src")
                if src:
                    if src.startswith("//"):
                        src = "https:" + src
                    info.image_urls.append(src)

    def _extract_taobao(self, page, info: ProductInfo):
        """提取淘宝/天猫商品信息"""
        title = page.query_selector(
            "#J_Title h3.tb-main-title, .tb-detail-hd h1, .tb-main-title, h1"
        )
        if title:
            t = title.inner_text().strip()
            if t:
                info.title = t

        price = page.query_selector(
            "#J_PromoPriceNum, .tb-rmb-num, .tm-price, .tm-price-num, "
            "span[class*='price'], .price"
        )
        if price:
            p = price.inner_text().strip()
            if p:
                info.price = p

        shop = page.query_selector(
            ".shop-name, #J_ShopInfo .shop-name, .slogo-shop-name, "
            ".shop-info-head .shop-name"
        )
        if shop:
            s = shop.inner_text().strip()
            if s:
                info.shop_name = s

    def _extract_jd(self, page, info: ProductInfo):
        """提取京东商品信息"""
        title = page.query_selector(".sku-name, .itemInfo-wrap h1, #name h1")
        if title:
            t = title.inner_text().strip()
            if t:
                info.title = t

        price = page.query_selector(
            ".p-price .price, #price, span[class*='price'], .price"
        )
        if price:
            p = price.inner_text().strip()
            if p:
                info.price = p

        shop = page.query_selector(
            ".J-hove-wrap .name, .shop-name, #shop-info .name, .name a"
        )
        if shop:
            s = shop.inner_text().strip()
            if s:
                info.shop_name = s

    def _extract_pdd(self, page, info: ProductInfo):
        """提取拼多多商品信息"""
        title = page.query_selector(".goods-name, #goods-name, .detail-title, .pdd-title")
        if title:
            t = title.inner_text().strip()
            if t:
                info.title = t

        price = page.query_selector(".goods-price, .current-price, .price, .pay-price")
        if price:
            p = price.inner_text().strip()
            if p:
                info.price = p

        shop = page.query_selector(".shop-name, .mall-name, .pdd-shop-name")
        if shop:
            s = shop.inner_text().strip()
            if s:
                info.shop_name = s

    def _extract_douyin(self, page, info: ProductInfo):
        """提取抖音商品信息"""
        title = page.query_selector("#title, .title, .goods-title, .product-name")
        if title:
            t = title.inner_text().strip()
            if t:
                info.title = t

        price = page.query_selector(".price, .current-price, .pay-price, .goods-price")
        if price:
            p = price.inner_text().strip()
            if p:
                info.price = p

    def _is_login_page(self, page, info: ProductInfo) -> bool:
        """判断当前页面是否为登录/验证页"""
        title = (info.title or "").lower()
        login_markers = [
            "登录", "欢迎登录", "请登录", "账号登录", "login",
            "sign in", "signin", "用户登录", "会员登录",
        ]
        if any(m in title for m in login_markers):
            return True

        # 页面含登录表单或密码输入框
        try:
            if page.query_selector(
                "#login, .login, .login-form, .login-wrap, #form-login, "
                "input[type='password'], .passport"
            ):
                return True
        except Exception:
            pass
        return False
