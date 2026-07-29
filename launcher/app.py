"""应用启动入口：创建 QApplication，初始化上下文，启动主窗口"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon


def read_version(app_dir: str) -> str:
    """从 VERSION 文件读取版本号

    Args:
        app_dir: 应用根目录路径

    Returns:
        版本号字符串，如 "0.1.0"
    """
    version_file = Path(app_dir) / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"


def main():
    """应用主入口函数"""
    # 确定应用根目录（launcher/ 的上级目录）
    app_dir = str(Path(__file__).resolve().parent.parent)

    # 将应用根目录加入 sys.path，确保模块导入正常
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    # 创建 QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("AI电商工具箱")
    app.setApplicationVersion(read_version(app_dir))
    app.setOrganizationName("AI-Ecommerce-Toolkit")

    # 设置应用图标
    icon_path = Path(app_dir) / "resources" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # 初始化应用上下文（配置 + 日志 + 信号总线）
    from framework.app_context import AppContext

    context = AppContext()
    context.initialize(app_dir)

    logger = context.logger.get_logger("launcher")
    logger.info("=" * 50)
    logger.info(f"应用启动 - AI电商工具箱 V{read_version(app_dir)}")
    logger.info("=" * 50)

    try:
        # 创建并显示主窗口
        from framework.main_window import MainWindow

        window = MainWindow()
        window.show()

        context.signals.app_ready.emit()
        logger.info("应用就绪，进入事件循环")

        # 进入 Qt 事件循环
        exit_code = app.exec()

        logger.info(f"应用退出 - exit_code={exit_code}")
        logger.info("=" * 50)
        sys.exit(exit_code)

    except Exception as e:
        logger.error(f"应用启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
