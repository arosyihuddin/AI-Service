import httpx
from typing import List, Dict
from app.utils.logging import log
from app.core.config import settings
from fastapi import HTTPException
from together import AsyncTogether
from ollama import AsyncClient
from openai import AsyncOpenAI, OpenAIError

ollamaClient = AsyncClient()
togetgerClient = AsyncTogether(api_key=settings.together_api_key)
openrouterClient = AsyncOpenAI(
    base_url=settings.openrouter_baseurl,
    api_key=settings.openrouter_api_key,
)
openaiClient = AsyncOpenAI(api_key=settings.openai_api_key)


async def ollama_deepseek(messages: List[Dict[str, str]]):
    try:
        async for chuck in await ollamaClient.chat(
            model="deepseek-r1", messages=messages, stream=True
        ):
            yield chuck["message"]["content"]

    except Exception as e:
        print(f"Error during Ollama chat: {str(e)}")


async def openai(messages):
    try:
        async for response in await openaiClient.chat.completions.create(
            model="gpt-4o",
            store=True,
            messages=messages,
            # max_tokens=200
            stream=True,
        ):
            if response.choices and response.choices[0].delta.content:
                yield response.choices[0].delta.content

    except Exception as e:
        raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))


async def together_llama(messages):
    try:
        stream = await togetgerClient.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",  # Gunakan parameter model
            messages=messages,
            temperature=0.7,
            # max_tokens=200,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
            stop=["<|eot_id|>", "<|eom_id|>"],
            stream=True,
        )

        async for response in stream:
            if response.choices and response.choices[0].delta.content:
                yield response.choices[0].delta.content
    except Exception as e:
        log.error(f"Error during async chat completion: {str(e)}")
        raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))


async def together_deepseek(messages):
    try:
        stream = await togetgerClient.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=messages,
            temperature=0.7,
            # max_tokens=200,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
            stop=["<|eot_id|>", "<|eom_id|>"],
            stream=True,
        )

        async for response in stream:
            if response.choices and response.choices[0].delta.content:
                yield response.choices[0].delta.content

    except Exception as e:
        log.error(f"Error during async chat completion: {str(e)}")
        raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))


async def openrouter_deepseek_distil_llama(messages):
    try:
        async for response in await openrouterClient.chat.completions.create(
            model="deepseek/deepseek-r1-distill-llama-70b:free",
            messages=messages,
            stream=True,
        ):
            if response.choices and response.choices[0].delta.content:
                yield response.choices[0].delta.content

    except OpenAIError as e:
        # Tangani kesalahan spesifik dari OpenAI
        raise HTTPException(500, f"OpenAI API error: {str(e)}")
    except Exception as e:
        # Tangani kesalahan umum
        raise HTTPException(500, f"Gagal menghasilkan jawaban. Error: {str(e)}")


async def openrouter_deepseek(messages):
    try:
        async for response in await openrouterClient.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=messages,
            stream=True,
        ):
            if response.choices and response.choices[0].delta.content:
                yield response.choices[0].delta.content

    except OpenAIError as e:
        # Tangani kesalahan spesifik dari OpenAI
        raise HTTPException(500, f"OpenAI API error: {str(e)}")
    except Exception as e:
        # Tangani kesalahan umum
        raise HTTPException(500, f"Gagal menghasilkan jawaban. Error: {str(e)}")
