from langchain_openai import ChatOpenAI

from src.settings import LlmConfig


def build_chat_model(config: LlmConfig) -> ChatOpenAI:
    """Build a LangChain chat model from application settings."""
    extra_body = None
    if config.ADD_EXTRA_BODY:
        extra_body = {"chat_template_kwargs": {"enable_thinking": config.ENABLE_THINKING}}

    return ChatOpenAI(
        model_name=config.MODEL_NAME,
        openai_api_key=config.API_KEY.get_secret_value(),
        openai_api_base=str(config.BASE_URL),
        temperature=config.TEMPERATURE,
        top_p=config.TOP_P,
        max_tokens=config.MAX_TOKENS,
        request_timeout=config.RESPONSE_TIMEOUT,
        extra_body=extra_body,
    )
