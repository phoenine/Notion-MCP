# utils.py
"""
Utility functions for the Notion API client.
"""
import asyncio
import logging
import random
from env import MAX_RETRIES, RETRY_DELAYS

logger = logging.getLogger("NOTION")


async def retry_async(func, *args, **kwargs):
    """Async retry decorator with exponential backoff and jitter."""
    last_exception = None
    for attempt, delay in enumerate(RETRY_DELAYS[:MAX_RETRIES]):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            logger.warning(
                f"Attempt {attempt+1}/{MAX_RETRIES} failed: {e}. Retrying after {delay} seconds..."
            )
            # Add random jitter to avoid synchronized retry attempts
            jitter = random.uniform(0, 1)
            await asyncio.sleep(delay + jitter)

    # All retries failed
    logger.error(f"Max retries ({MAX_RETRIES}) reached, last error: {last_exception}")
    raise last_exception
