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


async def ollama_deepseek_quiz(messages):
    try:

        model_result = (
            "".join(
                [
                    chuck["message"]["content"]
                    async for chuck in await ollamaClient.chat(
                        model="deepseek-r1", messages=messages, stream=True
                    )
                ]
            )
            .split("</think>")[1]
            .strip()
        )

        cleaned_data = model_result.replace("json\n", "")
        print(cleaned_data)
        return cleaned_data
    except Exception as e:
        raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))


async def together_llama_quiz(messages):
    try:
        response = await togetgerClient.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            messages=messages,
            # max_tokens=null,
            temperature=0.7,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
            stop=["<|eot_id|>", "<|eom_id|>"],
            stream=True,
        )

        model_result = "".join(
            [token.choices[0].delta.content async for token in response]
        ).strip()
        cleaned_data = model_result.replace("json\n", "").strip()
        return cleaned_data
    except Exception as e:
        raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))


async def together_deepseek_quiz(messages):
    try:
        response = await togetgerClient.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=messages,
            # max_tokens=null,
            temperature=0.7,
            top_p=0.7,
            top_k=50,
            repetition_penalty=1,
            stop=["<|eot_id|>", "<|eom_id|>"],
            stream=True,
        )

        model_result = "".join(
            [token.choices[0].delta.content async for token in response]
        ).strip()
        cleaned_data = model_result.replace("json\n", "").split("</think>")[1].strip()
        return cleaned_data
    except Exception as e:
        raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))


async def openai_quiz(messages):
    try:
        completion = await openaiClient.chat.completions.create(
            model="gpt-4o",
            store=True,
            messages=messages,
            # max_tokens=200
        )

        model_result = completion.choices[0].message.content.strip()
        cleaned_data = model_result.replace("json\n", "")
        return cleaned_data
    except Exception as e:
        raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))


async def openrouter_deepseek_quiz(messages):
    try:
        completion = await openrouterClient.chat.completions.create(
            model="deepseek/deepseek-r1:free", messages=messages, stream=True
        )

        model_result = completion.choices[0].message.content.strip()
        cleaned_data = model_result.replace("json\n", "")
        return cleaned_data
    except Exception as e:
        raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))


async def openrouter_deepseek_distill_llama_quiz(messages):
    try:
        completion = await openrouterClient.chat.completions.create(
            model="deepseek/deepseek-r1-distill-llama-70b:free",
            messages=messages,
            stream=True,
        )

        model_result = completion.choices[0].message.content.strip()
        cleaned_data = model_result.replace("json\n", "")
        return cleaned_data
    except Exception as e:
        raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))
