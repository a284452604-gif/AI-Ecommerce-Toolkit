"""AI 服务管理器：根据配置创建对应的 AI 服务实例"""

from framework.ai_service import BaseAIService, DeepSeekService


# 注册已知的 AI 服务供应商
_AI_SERVICE_REGISTRY: dict[str, type[BaseAIService]] = {
    "deepseek": DeepSeekService,
}


def create_ai_service(config: dict) -> BaseAIService | None:
    """根据配置创建 AI 服务实例

    Args:
        config: ai_service 配置字典，包含 provider, api_key, model, base_url, timeout

    Returns:
        BaseAIService 实例，如果 provider 不支持或未配置则返回 None
    """
    provider = config.get("provider", "").lower()
    api_key = config.get("api_key", "")
    model = config.get("model", "")
    base_url = config.get("base_url", "")
    timeout = config.get("timeout", 30)

    if not provider or not api_key:
        return None

    service_cls = _AI_SERVICE_REGISTRY.get(provider)
    if service_cls is None:
        return None

    # 只传非空值，让服务类使用默认值
    kwargs = {"api_key": api_key, "timeout": timeout}
    if model:
        kwargs["model"] = model
    if base_url:
        kwargs["base_url"] = base_url

    return service_cls(**kwargs)


def get_available_providers() -> list[str]:
    """获取所有已注册的 AI 服务供应商列表"""
    return list(_AI_SERVICE_REGISTRY.keys())
