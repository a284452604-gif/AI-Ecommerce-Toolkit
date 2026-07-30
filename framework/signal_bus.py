"""全局信号总线：所有跨组件通信信号集中在此定义"""

from PySide6.QtCore import QObject, Signal


class SignalBus(QObject):
    """全局信号总线：集中定义跨组件通信信号，实现松耦合

    所有需要跨模块通信的信号都定义在这里，
    组件之间不直接 import 对方，而是通过 SignalBus 通信。
    """

    # 导航相关
    navigate_to = Signal(str)               # 参数: page_key — 请求切换到指定页面
    page_changed = Signal(str)              # 参数: page_key — 页面已切换

    # 配置相关
    config_changed = Signal(str, object)    # 参数: key, new_value — 配置项已变更
    config_saved = Signal()                 # 配置已保存

    # 主题相关
    theme_changed = Signal(str)             # 参数: theme_name ("light"/"dark") — 主题已切换

    # 应用相关
    app_ready = Signal()                    # 应用初始化完成
    app_closing = Signal()                  # 应用即将关闭

    # 功能联动
    title_optimize_request = Signal(str)    # 参数: title — 请求对指定标题进行 AI 优化

    # 状态栏消息
    status_message = Signal(str)            # 参数: message — 向状态栏发送消息
