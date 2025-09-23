import json
from typing import List
from redis import Redis
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage

import app.config as config

r = Redis(
    host=config.REDIS_HOST, 
    port=config.REDIS_PORT,
    db=0, 
    decode_responses=True
)

def get(key: str):
    try:
        return r.get(key)
    except Exception as e:
        print(f"Redis get failed: {e}")
        return None

def set(key: str, value, ex: int = None):
    try:
        r.set(key, value, ex=ex)
    except Exception as e:
        print(f"Redis put failed: {e}")

def get_list(key: str, start: int = 0, end: int = -1):
    try:
        return r.lrange(key, start, end)
    except Exception as e:
        print(f"Redis get_list failed: {e}")
        return []

def append_list(key: str, value, max_val:int = None, ex: int = None):
    try:
        r.rpush(key, value)
        if max_val is not None and max_val > 0: r.ltrim(key, -max_val, -1)  # set max limit
        if ex is not None: r.expire(key, ex)  # set expiration
    except Exception as e:
        print(f"Redis append failed: {e}")

def delete(key: str):
    try:
        r.delete(key)
    except Exception as e:
        print(f"Redis delete failed: {e}")