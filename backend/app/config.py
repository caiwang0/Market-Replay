import os
from dotenv import load_dotenv

load_dotenv()

# Frontend Configuration
HOST_NAME = os.getenv("HOST_NAME")
FE_PATH_PREFIX = os.getenv("FE_PATH_PREFIX")

# Backend Configuration
EXECUTOR_MAX_ITERATIONS = int(os.getenv("EXECUTOR_MAX_ITERATIONS"))

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 6 # 6 days

# MySQL Database Configuration
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Lark Configuration
LARK_APP_ID = os.getenv("LARK_APP_ID")
LARK_APP_SECRET = os.getenv("LARK_APP_SECRET")
LARK_BASE_URL = os.getenv("LARK_BASE_URL", "https://open.larksuite.com")
LARK_ENCRYPT_KEY = os.getenv("LARK_ENCRYPT_KEY")

# ChromaDB Configuration
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME")
CHROMA_HOST = os.getenv("CHROMA_HOST")
CHROMA_PORT = os.getenv("CHROMA_PORT")

# SERPAPI Configuration
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")