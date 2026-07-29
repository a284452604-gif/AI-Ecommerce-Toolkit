"""主题颜色常量定义"""


class Theme:
    """主题颜色常量

    所有 UI 颜色集中管理，便于统一调整主题风格。
    QSS 文件中的颜色值应与此处保持一致。
    """

    # 主色调
    PRIMARY = "#4a47a3"
    PRIMARY_HOVER = "#5a57b3"
    PRIMARY_PRESSED = "#3a3793"

    # 背景色
    BG_MAIN = "#f5f5f7"
    BG_SIDEBAR = "#ffffff"
    BG_CARD = "#ffffff"

    # 文字颜色
    TEXT_PRIMARY = "#1a1a2e"
    TEXT_SECONDARY = "#555555"
    TEXT_MUTED = "#999999"
    TEXT_ON_PRIMARY = "#ffffff"

    # 边框
    BORDER = "#e0e0e0"
    BORDER_LIGHT = "#e8e8e8"

    # 侧边栏
    SIDEBAR_ACTIVE_BG = "#e8e8ff"
    SIDEBAR_HOVER_BG = "#f0f0f5"

    # 卡片
    CARD_TITLE_COLOR = "#1a1a2e"
    CARD_DESC_COLOR = "#666666"
    CARD_STATUS_COLOR = "#999999"

    # 状态
    SUCCESS = "#52c41a"
    WARNING = "#faad14"
    ERROR = "#ff4d4f"
