# Name of the OpenAI model used for embedding text
OPENAI_EMBEDDING_MODEL_NAME = "text-embedding-3-small"
COST_PER_TOKEN = 0.020 / 1_000_000  # 1,000,000 토큰당 $0.020 (text-embedding-3-small 모델의 가격)

# Directory for storing Chroma vector database files
CHROMA_DB_DIR = "chroma_dir"