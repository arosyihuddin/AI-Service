from together import AsyncTogether
from app.core.config import settings
from fastapi import HTTPException

togetgerClient = AsyncTogether(api_key=settings.together_api_key)


async def together_llama_autocorrect(messages):
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
