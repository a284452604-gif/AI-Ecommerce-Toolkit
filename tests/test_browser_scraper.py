"""浏览器抓取器测试：纯逻辑 + 可用性（不实际联网抓取）"""

from apps.product_analyzer.browser_scraper import (
    BrowserScraper,
    parse_cookie_string,
    PLATFORM_COOKIE_DOMAIN,
)
from apps.product_analyzer.link_parser import Platform


def test_is_available():
    """Playwright 已安装且浏览器已下载"""
    assert BrowserScraper.is_available() is True


def test_parse_cookie_string_empty():
    assert parse_cookie_string("", ".taobao.com") == []
    assert parse_cookie_string(None, ".taobao.com") == []


def test_parse_cookie_string_basic():
    cookies = parse_cookie_string("a=1; b=2", ".taobao.com")
    assert len(cookies) == 2
    assert cookies[0] == {"name": "a", "value": "1", "domain": ".taobao.com", "path": "/"}
    assert cookies[1]["name"] == "b"
    assert cookies[1]["value"] == "2"


def test_parse_cookie_string_skips_invalid():
    cookies = parse_cookie_string("valid=1; =bad; noeq", ".tmall.com")
    # 只应保留 valid=1
    assert len(cookies) == 1
    assert cookies[0]["name"] == "valid"
    assert cookies[0]["domain"] == ".tmall.com"


def test_platform_cookie_domain():
    assert PLATFORM_COOKIE_DOMAIN[Platform.TAOBAO] == ".taobao.com"
    assert PLATFORM_COOKIE_DOMAIN[Platform.TMALL] == ".tmall.com"
    assert PLATFORM_COOKIE_DOMAIN[Platform.JD] == ".jd.com"
    assert PLATFORM_COOKIE_DOMAIN[Platform.PDD] == ".yangkeduo.com"
    assert PLATFORM_COOKIE_DOMAIN[Platform.DOUYIN] == ".douyin.com"
