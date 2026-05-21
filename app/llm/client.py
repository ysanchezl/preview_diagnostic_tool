from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from app.core.config import settings


def get_chat_model() -> BaseChatModel | None:
    provider = settings.llm_provider.lower()

    if provider == "groq" and settings.groq_api_key:
        return ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0.2,
        )

    if provider == "openai" and settings.openai_api_key:
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=0.2,
        )

    if provider == "azure_openai" and settings.azure_openai_api_key:
        return AzureChatOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            azure_deployment=settings.azure_openai_deployment,
            api_version=settings.azure_openai_api_version,
            temperature=0.2,
        )

    return None
