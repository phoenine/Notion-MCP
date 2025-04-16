import asyncio
import logging
from typing import List
from env import CONCURRENCY_LIMIT
from operations import fill_web_url_from_other_urls, update_page_content

logger = logging.getLogger("NOTION")


async def process_page(client, page_id: str, operation_config: dict = None):
    """Process a single page with configured operations."""
    try:
        if not operation_config:
            # Default operation if none specified
            await fill_web_url_from_other_urls(client, page_id)
        else:
            # Use configuration to determine what operation to run
            if operation_config.get("operation") == "fill_web_url":
                web_field = operation_config.get("web_field", "网址")
                await fill_web_url_from_other_urls(client, page_id, web_field)
            elif operation_config.get("operation") == "update_content":
                new_content = operation_config.get("content", "")
                await update_page_content(client, page_id, new_content)
            # Add more operations as needed

        return True
    except Exception as e:
        logger.error(f"Failed to process page {page_id}: {e}")
        return False


async def process_pages_with_semaphore(
    client, pages_list: List[str], operation_config: dict = None
):
    """Process pages with a semaphore to limit concurrency."""
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def _process_with_limit(page_id):
        async with semaphore:
            return await process_page(client, page_id, operation_config)

    tasks = [_process_with_limit(page_id) for page_id in pages_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if isinstance(r, Exception))
    skipped = len(pages_list) - success - failed

    logger.info(
        f"Processed {len(pages_list)} pages, Success: {success}, Failed: {failed}, Skipped: {skipped}"
    )

    return {
        "total": len(pages_list),
        "success": success,
        "failed": failed,
        "skipped": skipped,
    }
