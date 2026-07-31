"""AI 服务层：提供统一的 AI 服务接口，支持多供应商切换"""

from abc import ABC, abstractmethod
import base64
import mimetypes
from pathlib import Path
from dataclasses import dataclass, field
from openai import OpenAI


@dataclass
class AIResponse:
    """AI 服务统一响应格式"""
    content: str                     # 生成的文本内容
    model: str = ""                   # 使用的模型名
    tokens_prompt: int = 0            # 输入 token 数
    tokens_completion: int = 0        # 输出 token 数
    tokens_total: int = 0             # 总 token 数
    finish_reason: str = ""           # 结束原因：stop / length
    success: bool = True              # 是否成功
    error_message: str = ""           # 错误信息


class BaseAIService(ABC):
    """AI 服务抽象基类

    所有 AI 服务供应商适配器都应继承此类，统一调用接口。
    """

    def __init__(self, api_key: str, model: str, base_url: str, timeout: int = 30):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._timeout = timeout
        self._initialized = False

    @property
    def model(self) -> str:
        return self._model

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @abstractmethod
    def initialize(self):
        """初始化服务：验证 API 连接"""
        pass

    @abstractmethod
    def chat(self, system_prompt: str, user_prompt: str,
             temperature: float = 0.7, max_tokens: int = 2048,
             image_paths: list[str] | None = None) -> AIResponse:
        """发送单轮对话请求

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户输入
            temperature: 创意程度 0-2
            max_tokens: 最大输出 token 数
            image_paths: 随用户消息一起上传的本地图片路径列表（可选）

        Returns:
            AIResponse: 统一响应
        """
        pass


class DeepSeekService(BaseAIService):
    """DeepSeek AI 服务适配器

    通过 OpenAI 兼容接口调用 DeepSeek API。
    配置:
        base_url: https://api.deepseek.com
        model: deepseek-chat (推荐) 或 deepseek-reasoner
    """

    DEFAULT_BASE_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-chat"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL,
                 base_url: str = DEFAULT_BASE_URL, timeout: int = 30):
        super().__init__(api_key, model, base_url, timeout)
        self._client: OpenAI | None = None

    def initialize(self):
        """初始化 DeepSeek 客户端"""
        if not self._api_key:
            raise ValueError("DeepSeek API Key 未配置，请在系统设置中填写 API Key")

        self._client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=self._timeout,
        )
        self._initialized = True

    def chat(self, system_prompt: str, user_prompt: str,
             temperature: float = 0.7, max_tokens: int = 2048,
             image_paths: list[str] | None = None) -> AIResponse:
        """调用 DeepSeek Chat API

        当传入 image_paths 时，将图片转为 base64 data URL 并作为 vision 输入。
        当前模型若不支持 vision，API 会返回错误，请改用结构化数据或 vision 模型。
        """
        if not self._initialized or self._client is None:
            self.initialize()

        user_content = self._build_user_content(user_prompt, image_paths or [])

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            choice = response.choices[0]
            usage = response.usage

            return AIResponse(
                content=choice.message.content or "",
                model=response.model,
                tokens_prompt=usage.prompt_tokens if usage else 0,
                tokens_completion=usage.completion_tokens if usage else 0,
                tokens_total=usage.total_tokens if usage else 0,
                finish_reason=choice.finish_reason or "stop",
                success=True,
            )

        except Exception as e:
            return AIResponse(
                content="",
                success=False,
                error_message=str(e),
            )

    def _build_user_content(self, user_prompt: str, image_paths: list[str]):
        """构建用户消息内容：纯文本或文本+图片列表"""
        if not image_paths:
            return user_prompt

        content: list[dict] = [{"type": "text", "text": user_prompt}]
        for path in image_paths:
            data_url = self._image_to_data_url(path)
            if data_url:
                content.append({"type": "image_url", "image_url": {"url": data_url}})
        return content

    @staticmethod
    def _image_to_data_url(path: str) -> str | None:
        """将本地图片文件转为 base64 data URL"""
        try:
            file_path = Path(path)
            if not file_path.exists():
                return None
            mime, _ = mimetypes.guess_type(str(file_path))
            mime = mime or "image/png"
            with file_path.open("rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"data:{mime};base64,{encoded}"
        except Exception:
            return None
