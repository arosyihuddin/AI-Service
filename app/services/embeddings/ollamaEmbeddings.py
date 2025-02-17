from typing import List
from langchain_core.embeddings import Embeddings
from pydantic import BaseModel, Field
import httpx
import asyncio


class OllamaEmbeddings(BaseModel, Embeddings):
    """
    Embedding class untuk menggunakan endpoint /api/embeddings dari Ollama.
    """

    model_name: str = Field(default="deepseek-r1", alias="model")
    """Nama model yang digunakan (misalnya 'deepseek-r1')."""
    ollama_url: str = Field(default="http://localhost:11434/api/embeddings")
    """URL endpoint Ollama untuk embeddings."""

    async def _embed_single(self, text: str) -> List[float]:
        """
        Menghasilkan embedding untuk satu teks menggunakan endpoint Ollama.
        Args:
            text: Teks yang akan diembed.
        Returns:
            Vektor embedding sebagai list float.
        """
        async with httpx.AsyncClient() as client:
            payload = {"model": self.model_name, "prompt": text}
            response = await client.post(
                self.ollama_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code != 200:
                raise ValueError(f"Error from Ollama API: {response.text}")
            data = response.json()
            return data.get("embedding", [])

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Menghasilkan embedding untuk daftar teks.
        Args:
            texts: Daftar teks yang akan diembed.
        Returns:
            Daftar embedding, satu untuk setiap teks.
        """
        tasks = [self._embed_single(text) for text in texts]
        embeddings = await asyncio.gather(*tasks)
        return embeddings

    async def embed_query(self, text: str) -> List[float]:
        """
        Menghasilkan embedding untuk satu query.
        Args:
            text: Query yang akan diembed.
        Returns:
            Embedding untuk query.
        """
        return await self._embed_single(text)
