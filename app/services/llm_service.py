from langchain_huggingface import HuggingFaceEmbeddings
from together import Together
from openai import OpenAI
from app.core.config import settings
from fastapi import HTTPException
from app.utils.logging import log

embeddings =  HuggingFaceEmbeddings(
        model_name="LazarusNLP/all-indo-e5-small-v4",     # Provide the pre-trained model's path
        model_kwargs={'device':'cpu'}, # Pass the model configuration options
        encode_kwargs={'normalize_embeddings': False}, # Pass the encoding options
        # show_progress=True
    )

def llm(messages, model):
    if model == "llama":
        try:
            client = Together(api_key=settings.together_api_key)
            response = client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                messages=messages,
                # max_tokens=null,
                temperature=0.7,
                top_p=0.7,
                top_k=50,
                repetition_penalty=1,
                stop=["<|eot_id|>","<|eom_id|>"],
                stream=True
            )
            
            model_result = "".join([token.choices[0].delta.content for token in response]).strip()
            cleaned_data = model_result.replace("json\n", "")
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
                messages=messages
            )

            model_result = completion.choices[0].message.content.strip()
            cleaned_data = model_result.replace("json\n", "")
            return cleaned_data

        except Exception as e:
            raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))
    
    elif model == "deepseek-together":
        try:
            client = Together(api_key=settings.together_api_key)
            response = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
                messages=messages,
                # max_tokens=null,
                temperature=0.7,
                top_p=0.7,
                top_k=50,
                repetition_penalty=1,
                stop=["<|eot_id|>","<|eom_id|>"],
                stream=True
            )
            
            model_result = "".join([token.choices[0].delta.content for token in response]).strip()
            cleaned_data = model_result.replace("json\n", "").split("</think>")[1].strip()
            return cleaned_data
        except Exception as e:
            raise HTTPException(500, "Gagal menghasilkan jawaban. Error: " + str(e))