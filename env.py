import os
from dotenv import load_dotenv

load_dotenv()

# Notion API Token
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
ROOT_PAGE_ID = os.getenv("ROOT_PAGE_ID")

# Retry configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAYS = [int(x) for x in os.getenv("RETRY_DELAYS", "1,3,5").split(",")]
CONCURRENCY_LIMIT = int(os.getenv("CONCURRENCY_LIMIT", "5"))
TIMEOUT_MS = int(os.getenv("TIMEOUT_MS", "30000"))