import asyncio
from chromadb import Client as ChromaClient
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings

import app.config as config

client = ChromaClient(
    Settings(
        chroma_api_impl="chromadb.api.fastapi.FastAPI",
        chroma_server_host=config.CHROMA_HOST,
        chroma_server_http_port=config.CHROMA_PORT,
    )
)

collection = client.get_or_create_collection(
    name=config.CHROMA_COLLECTION_NAME
)

embedder = OpenAIEmbeddings(
    model="text-embedding-ada-002",
    openai_api_key=config.OPENAI_API_KEY
)

async def query_collection(query: str, top_k: int = 100, where: dict = None):
    q_emb = await embedder.aembed_query(query)

    query_args = {
        "query_embeddings": [q_emb],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        query_args["where"] = where

    results = await asyncio.to_thread(
        collection.query,
        **query_args
    )
    
    return results["documents"][0], results["metadatas"][0], results["distances"][0]