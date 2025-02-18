from langchain_huggingface import HuggingFaceEmbeddings
from app.utils.logging import log
from typing import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from app.services.models.model_chat import (
    ollama_deepseek,
    together_llama,
    together_deepseek,
    openrouter_deepseek,
    openrouter_deepseek_distil_llama,
    openai,
)

from app.services.models.model_quiz import (
    ollama_deepseek_quiz,
    together_llama_quiz,
    together_deepseek_quiz,
    openai_quiz,
    openrouter_deepseek_quiz,
    openrouter_deepseek_distill_llama_quiz,
)
from app.services.models.model_autocorrect import (
    together_llama_autocorrect,
    openai_autocorrect,
    together_deepseek_autocorrect,
    ollama_deepseek_autocorrect,
)

embeddings = HuggingFaceEmbeddings(
    model_name="LazarusNLP/all-indo-e5-small-v4",  # Provide the pre-trained model's path
    model_kwargs={"device": "cpu"},  # Pass the model configuration options
    encode_kwargs={"normalize_embeddings": False},  # Pass the encoding options
)

# Executor untuk menjalankan tugas di thread terpisah
executor = ThreadPoolExecutor()


async def llm_chat(messages, model) -> AsyncGenerator[str, None]:
    log.warn("Use Model: " + model)
    if model == "llama":
        async for chunk in together_llama(messages):
            yield chunk
        log.warn("Chat completion done")

    elif model == "ollama-deepseek":
        async for chunk in ollama_deepseek(messages):
            yield chunk
        log.warn("Chat completion done")

    elif model == "openai":
        async for chunk in openai(messages):
            yield chunk
        log.warn("Chat completion done")

    if model == "deepseek-together":
        async for chunk in together_deepseek(messages):
            yield chunk
        log.warn("Chat completion done")

    elif model == "deepseek-openrouter-distill-llama":
        async for chunk in openrouter_deepseek_distil_llama(messages):
            yield chunk
        log.warn("Chat completion done")

    elif model == "deepseek-openrouter":
        async for chunk in openrouter_deepseek(messages):
            yield chunk
        log.warn("Chat completion done")


async def llm(messages, model):
    log.warn("Use Model: " + model)
    if model == "llama":
        result = await together_llama_quiz(messages)
        log.warn("Chat completion done")
        return result

    elif model == "ollama-deepseek":
        result = await ollama_deepseek_quiz(messages)
        log.warn("Chat completion done")
        return result

    elif model == "openai":
        result = await openai_quiz(messages)
        log.warn("Chat completion done")
        return result

    elif model == "deepseek-openrouter":
        result = await openrouter_deepseek_quiz(messages)
        log.warn("Chat completion done")
        return result

    elif model == "deepseek-openrouter-distill-llama":
        result = await openrouter_deepseek_distill_llama_quiz(messages)
        log.warn("Chat completion done")
        return result

    elif model == "deepseek-together":
        result = await together_deepseek_quiz(messages)
        log.warn("Chat completion done")
        return result


async def llm_autocorrect(messages, model):
    log.warn("Use Model: " + model)
    if model == "llama":
        result = await together_llama_autocorrect(messages)
        log.warn("Chat completion done")
        return result
    elif model == "deepseek-together":
        result = await together_deepseek_autocorrect(messages)
        log.warn("Chat completion done")
        return result
    elif model == "openai":
        result = await openai_autocorrect(messages)
        log.warn("Chat completion done")
        return result
    elif model == "ollama-deepseek":
        result = await ollama_deepseek_autocorrect(messages)
        log.warn("Chat completion done")
        return result
