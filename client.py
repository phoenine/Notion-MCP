import logging
from contextlib import asynccontextmanager
from notion_client import AsyncClient as NotionAsyncClient
from env import NOTION_TOKEN, TIMEOUT_MS

logger = logging.getLogger("NOTION")

@asynccontextmanager
async def get_notion_client():
    """Create an async context manager for Notion client."""
    client = NotionAsyncClient(
        auth=NOTION_TOKEN,
        logger=logger,
        log_level=logging.DEBUG,
        timeout_ms=TIMEOUT_MS,
    )
    try:
        yield client
    finally:
        await client.aclose()