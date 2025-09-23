import aiohttp
import os

import app.config as config
from dotenv import load_dotenv
from langchain_core.tools import tool
from pydantic import BaseModel

# Load .env file
load_dotenv(override=True)

# we use the article object for parsing serpapi results later
class Article(BaseModel):
    title: str
    source: str
    link: str
    snippet: str

    @classmethod
    def from_serpapi_result(cls, result: dict) -> "Article":
        # Use .get() to safely access keys, preventing crashes if a key is missing.
        return cls(
            title=result.get("title", "No Title Available"),
            source=result.get("source", "No Source Available"),
            link=result.get("link", "No Link Available"),
            snippet=result.get("snippet", "No Snippet Available"),
        )

@tool
async def serpapi(query: str) -> str:
    """Use this tool to search the web for public information, like people or current events."""
    params = {
        "api_key": config.SERPAPI_API_KEY,
        "engine": "google",
        "q": query,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://serpapi.com/search", params=params, timeout=10) as response:
                if response.status != 200:
                    return f"SerpApi returned an error status: {response.status}"
                results = await response.json()
    except Exception as e:
        return f"An unexpected error occurred during web search: {e}"

    # Check for an API-level error.
    if "error" in results:
        return f"SerpApi returned an error: {results['error']}"
    
    # Prioritize the "Answer Box" for direct answers
    if answer_box := results.get("answer_box"):
        if answer := answer_box.get("answer"):
            return f"Direct Answer Found: {answer}"
        if snippet := answer_box.get("snippet"):
            return f"Found a Featured Snippet: {snippet}"

    # Fall back to organic results if no direct answer
    if organic_results := results.get("organic_results"):
        return str([Article.from_serpapi_result(result) for result in organic_results[:3]])

    # If nothing is found, state as such
    return "No relevant web search results found."