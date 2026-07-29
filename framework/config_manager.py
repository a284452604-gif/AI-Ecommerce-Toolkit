"""配置管理器：加载 default_config.json，合并 app_config.json"""

import json
import copy
from pathlib import Path
from typing import Any


class ConfigManager:
    """配置管理器：加载默认配置，合并用户配置，提供读写接口"""

    def __init__(self, app_dir: str):
        self._app_dir = Path(app_dir)
        self._default_path = self._app_dir / "config" / "default_config.json"
        self._user_path = self._app_dir / "config" / "app_config.json"
        self._config: dict = {}
        self._load()

    def _load(self):
        """先加载默认配置，再用用户配置深度合并"""
        # 1. 读取默认配置
        if self._default_path.exists():
            with open(self._default_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        else:
            self._config = {}

        # 2. 如果用户配置存在，深度合并
        if self._user_path.exists():
            try:
                with open(self._user_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                self._config = self._deep_merge(self._config, user_config)
            except (json.JSONDecodeError, IOError):
                pass  # 用户配置损坏时使用默认配置

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """深度合并两个字典，override 中的值覆盖 base"""
        result = copy.deepcopy(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """点分路径取值，如 config.get('ai_service.api_key')"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """点分路径设值，自动创建中间层级"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def save(self):
        """将当前配置保存到 app_config.json"""
        self._user_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._user_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, ensure_ascii=False, indent=4)

    def reset_to_default(self):
        """重置为默认配置"""
        if self._default_path.exists():
            with open(self._default_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        else:
            self._config = {}
        self.save()

    def get_all(self) -> dict:
        """返回完整配置字典"""
        return copy.deepcopy(self._config)
