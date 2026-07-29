"""pytest 配置与 fixtures"""

import sys
import tempfile
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def temp_app_dir():
    """创建临时应用目录，包含默认配置文件

    用于测试 ConfigManager 和 LogManager，测试后自动清理。
    """
    temp_dir = tempfile.mkdtemp(prefix="aikit_test_")
    app_dir = Path(temp_dir)

    # 创建子目录
    (app_dir / "config").mkdir(parents=True)
    (app_dir / "logs").mkdir(parents=True)

    # 复制默认配置
    project_root = Path(__file__).resolve().parent.parent
    default_config_path = project_root / "config" / "default_config.json"
    if default_config_path.exists():
        shutil.copy2(str(default_config_path), str(app_dir / "config" / "default_config.json"))

    # 将项目根目录加入 sys.path（确保 framework 等模块可导入）
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    yield str(app_dir)

    # 清理
    shutil.rmtree(temp_dir, ignore_errors=True)
