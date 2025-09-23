from langchain_openai import ChatOpenAI
from langchain_core.runnables import ConfigurableField
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.config import OPENAI_API_KEY

# LLM and Prompt Setup
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0,
    streaming=True,
    api_key=OPENAI_API_KEY
).configurable_fields(
    callbacks=ConfigurableField(
        id="callbacks",
        name="callbacks",
        description="A list of callbacks to use for streaming",
    )
)

prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are Sofi, a helpful chatbot assistant for Gotrade staff. When answering a user's "
        "question you should first use one of the tools provided. After using a "
        "tool the tool output will be provided back to you. When you have "
        "all the information you need, you MUST use the final_answer tool "
        "to provide a final answer to the user. Use tools to answer the "
        "user's CURRENT question, not previous questions."
        "Today's time date is {time_now}. Convert any query that relates to time like `Today, Last Year, Next Friday` "
        "into time and date"
    )),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

import json
from typing import List, Dict
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def select_document(query: str, documents: List[Dict[str, str]]) -> List[str]:
    """
    Select the most relevant document tokens from the list based on the user query.
    """
    system_msg = {
        "role": "system",
        "content": (
            "You are a document selector. The user will provide a query and a list of document summaries. "
            "Your job is to return a JSON array of `file_token`s (e.g., [\"abc123\", \"def456\"]) "
            "that are most relevant to answering the question. Do not include anything else. "
            "If no documents are relevant, return an empty array, we will iterate the next batch of documents. "
        )
    }

    summary_text = "\n".join([
        f"{i+1}. [Token: {doc['file_token']}] [File: {doc['file']}] {doc['summary']}"
        for i, doc in enumerate(documents)
    ])
    user_msg = {
        "role": "user",
        "content": (
            f"Query: {query}\n\n"
            f"Document summaries:\n{summary_text}\n\n"
            "Return only the JSON list of relevant file_tokens."
        )
    }

    try:
        resp = await client.chat.completions.create(
            model="gpt-4",
            messages=[system_msg, user_msg],
            temperature=0,
        )
        content = resp.choices[0].message.content.strip()
        # Try to parse JSON from response
        return json.loads(content)
    except Exception as e:
        print(f"[select_document] error: {e}")
        return [documents[0]["file_token"]] if documents else []
    
async def generate_chat_title(query: str) -> str:
    """
    Generate a concise chat title based on the user's query.
    """
    system_msg = {
        "role": "system",
        "content": (
            "You are a helpful assistant that generates concise, descriptive chat titles. "
            "Given a user's query, return a short title (max 7 words) summarizing the topic. "
            "Return only the title, no extra text or formatting or punctuation."
        )
    }
    user_msg = {
        "role": "user",
        "content": f"User query: {query}\nTitle:"
    }
    try:
        resp = await client.chat.completions.create(
            model="gpt-4",
            messages=[system_msg, user_msg],
            temperature=0.2,
            max_tokens=16,
        )
        title = resp.choices[0].message.content
        return title
    except Exception as e:
        print(f"[generate_chat_title] error: {e}")
        return "Chat"