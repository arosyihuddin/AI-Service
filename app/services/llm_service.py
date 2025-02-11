from langchain_huggingface import HuggingFaceEmbeddings
from openai import OpenAI
from app.core.config import settings
from fastapi import HTTPException
from app.utils.logging import log
from together import AsyncTogether
from typing import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
import asyncio
from openai import AsyncOpenAI, OpenAIError

embeddings =  HuggingFaceEmbeddings(
        model_name="LazarusNLP/all-indo-e5-small-v4",     # Provide the pre-trained model's path
        model_kwargs={'device':'cpu'}, # Pass the model configuration options
        encode_kwargs={'normalize_embeddings': False}, # Pass the encoding options
        # show_progress=True
    )

# Executor untuk menjalankan tugas di thread terpisah
executor = ThreadPoolExecutor()

async def generate_embeddings(texts):
    """
    Fungsi asynchronous untuk menghasilkan embeddings dari teks.
    :param texts: List of strings (teks yang akan di-embed)
    :return: List of embeddings
    """
    try:
        # Jalankan operasi embedding dalam thread terpisah
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            embeddings,  # Fungsi embedding dari HuggingFaceEmbeddings
            texts
        )
        return result
    except Exception as e:
        # Tangani kesalahan jika terjadi
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")


async def llm_chat(messages, model) -> AsyncGenerator[str, None]:
    if model == "llama":
        client = AsyncTogether(api_key=settings.together_api_key)
        try:
            stream = await client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",  # Gunakan parameter model
                messages=messages,
                temperature=0.7,
                max_tokens=200,
                top_p=0.7,
                top_k=50,
                repetition_penalty=1,
                stop=["<|eot_id|>", "<|eom_id|>"],
                stream=True
            )
            
            async for response in stream:
                if response.choices and response.choices[0].delta.content:
                    yield response.choices[0].delta.content
            
            log.info("Chat completion done")
        except Exception as e:
            log.error(f"Error during async chat completion: {str(e)}")
            raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))
        
    if model == "deepseek-together":
        client = AsyncTogether(api_key=settings.together_api_key)
        try:
            stream = await client.chat.completions.create(
                model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",  # Gunakan parameter model
                messages=messages,
                temperature=0.7,
                max_tokens=200,
                top_p=0.7,
                top_k=50,
                repetition_penalty=1,
                stop=["<|eot_id|>", "<|eom_id|>"],
                stream=True
            )
            
            async for response in stream:
                if response.choices and response.choices[0].delta.content:
                    yield response.choices[0].delta.content
            
            log.info("Chat completion done")
        except Exception as e:
            log.error(f"Error during async chat completion: {str(e)}")
            raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))
        
    elif model == "deepseek-openrouter-distill-llama":
        try:
            # Inisialisasi AsyncOpenAI client
            client = AsyncOpenAI(
                base_url=settings.openrouter_baseurl,
                api_key=settings.openrouter_api_key
            )
            
            async for response in await client.chat.completions.create(
                model="deepseek/deepseek-r1-distill-llama-70b:free",
                messages=messages,
                stream=True
            ):
                if response.choices and response.choices[0].delta.content:
                    yield response.choices[0].delta.content
                    
            log.info("Chat completion done")
        except OpenAIError as e:
            # Tangani kesalahan spesifik dari OpenAI
            raise HTTPException(500, f"OpenAI API error: {str(e)}")
        except Exception as e:
            # Tangani kesalahan umum
            raise HTTPException(500, f"Gagal menghasilkan jawaban. Error: {str(e)}")
        
    elif model == "deepseek-openrouter":
        try:
            # Inisialisasi AsyncOpenAI client
            client = AsyncOpenAI(
                base_url=settings.openrouter_baseurl,
                api_key=settings.openrouter_api_key
            )
            
            async for response in await client.chat.completions.create(
                model="deepseek/deepseek-r1:free",
                messages=messages,
                stream=True
            ):
                if response.choices and response.choices[0].delta.content:
                    yield response.choices[0].delta.content
                    
            log.info("Chat completion done")
        except OpenAIError as e:
            # Tangani kesalahan spesifik dari OpenAI
            raise HTTPException(500, f"OpenAI API error: {str(e)}")
        except Exception as e:
            # Tangani kesalahan umum
            raise HTTPException(500, f"Gagal menghasilkan jawaban. Error: {str(e)}")

async def llm(messages, model):
    if model == "llama":
        try:
            client = AsyncTogether(api_key=settings.together_api_key)
            response = await client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                messages=messages,
                # max_tokens=null,
                temperature=0.7,
                top_p=0.7,
                top_k=50,
                repetition_penalty=1,
                stop=["<|eot_id|>","<|eom_id|>"],
                stream=False
            )

            model_result = str(response.choices[0].message.content)
            # model_result = "".join([token.choices[0].delta.content for token in response]).strip()
            cleaned_data = model_result.replace("json\n", "")
            log.info("Chat completion done")
            return cleaned_data
        except Exception as e:
            raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))
    
    elif model == "openai":
        try:
            client = OpenAI(api_key=settings.openai_api_key)

            # Panggil API OpenAI untuk mendapatkan jawaban
            completion = client.chat.completions.create(
                model="gpt-4o",  # Gunakan model yang sesuai (gpt-4o-mini atau gpt-3.5-turbo)
                store=True,
                messages=messages,
                # max_tokens=200
                
            )

            model_result = completion.choices[0].message.content.strip()
            cleaned_data = model_result.replace("json\n", "")
            return cleaned_data
        except Exception as e:
            raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))
    
    elif model == "deepseek-openrouter":
        try:
            client = OpenAI(
                base_url=settings.openrouter_baseurl,
                api_key=settings.openrouter_api_key
            )

            completion = client.chat.completions.create(
                model="deepseek/deepseek-r1:free",
                messages=messages,
                stream=True
            )

            model_result = completion.choices[0].message.content.strip()
            cleaned_data = model_result.replace("json\n", "")
            return cleaned_data

        except Exception as e:
            raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))
        
    elif model == "deepseek-openrouter-distill-llama":
        try:
            client = OpenAI(
                base_url=settings.openrouter_baseurl,
                api_key=settings.openrouter_api_key
            )

            completion = client.chat.completions.create(
                model="deepseek/deepseek-r1-distill-llama-70b:free",
                messages=messages
            )

            model_result = completion.choices[0].message.content.strip()
            cleaned_data = model_result.replace("json\n", "")
            return cleaned_data

        except Exception as e:
            raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))
        
    elif model == "qwen-vl-plus":
        try:
            client = OpenAI(
                base_url=settings.openrouter_baseurl,
                api_key=settings.openrouter_api_key
            )

            completion = client.chat.completions.create(
                model="qwen/qwen2.5-vl-72b-instruct:free",
                messages=messages
            )

            model_result = completion.choices[0].message.content.strip()
            cleaned_data = model_result.replace("json\n", "")
            return cleaned_data

        except Exception as e:
            raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))
    
    elif model == "deepseek-together":
        try:
            client = AsyncTogether(api_key=settings.together_api_key)
            response = await client.chat.completions.create(
                model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
                messages=messages,
                # max_tokens=null,
                temperature=0.7,
                top_p=0.7,
                top_k=50,
                repetition_penalty=1,
                stop=["<|eot_id|>","<|eom_id|>"],
                stream=False
            )
            
            model_result = "".join([token.choices[0].delta.content for token in response]).strip()
            cleaned_data = model_result.replace("json\n", "").split("</think>")[1].strip()
            return cleaned_data
        except Exception as e:
            raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))