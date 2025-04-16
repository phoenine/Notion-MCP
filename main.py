# main.py
"""
Main module for Notion MCP client.
"""
import asyncio
import time
import logging
from typing import Dict, Any

from env import ROOT_PAGE_ID
from client import get_notion_client
from operations import query_page_for_databases, query_database_for_all_pages
from processor import process_pages_with_semaphore

# Configure logging
logger = logging.getLogger("NOTION")
logger.setLevel(logging.DEBUG)
_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Add console handler
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_formatter)
logger.addHandler(_console_handler)


async def run_notion_task(config: Dict[str, Any] = None):
    """
    Run Notion tasks based on configuration.

    Args:
        config: Configuration dictionary with the following structure:
        {
            "root_page_id": str,  # Override ROOT_PAGE_ID from env if provided
            "database_filter": [str],  # Optional filter for database titles
            "operation": {
                "type": str,  # Operation type (e.g., "fill_web_url")
                "params": {}  # Operation-specific parameters
            }
        }
    """
    start_time = time.time()
    results = {
        "status": "success",
        "databases_processed": 0,
        "pages_processed": 0,
        "success_count": 0,
        "failure_count": 0,
        "skipped_count": 0,
        "elapsed_time": 0,
    }

    try:
        config = config or {}
        page_id = config.get("root_page_id", ROOT_PAGE_ID)
        db_filter = config.get("database_filter", [])
        operation_config = config.get("operation", {})

        async with get_notion_client() as notion:
            # Query all databases
            databases_dict = await query_page_for_databases(notion, page_id)

            # Apply database filter if provided
            if db_filter:
                filtered_dict = {
                    k: v for k, v in databases_dict.items() if k in db_filter
                }
                databases_dict = filtered_dict

            results["databases_processed"] = len(databases_dict)
            total_pages = 0
            total_success = 0
            total_failed = 0
            total_skipped = 0

            for database_title, database_id in databases_dict.items():
                logger.info(f"Processing database: {database_title}, ID: {database_id}")

                # Get all pages in the database
                pages_list = await query_database_for_all_pages(notion, database_id)

                if not pages_list:
                    logger.warning(f"No pages found in database {database_title}")
                    continue

                # Process pages concurrently
                process_result = await process_pages_with_semaphore(
                    notion, pages_list, operation_config
                )

                total_pages += process_result["total"]
                total_success += process_result["success"]
                total_failed += process_result["failed"]
                total_skipped += process_result["skipped"]

            results["pages_processed"] = total_pages
            results["success_count"] = total_success
            results["failure_count"] = total_failed
            results["skipped_count"] = total_skipped

    except Exception as e:
        logger.error(f"Error during execution: {e}")
        results["status"] = "error"
        results["error_message"] = str(e)

    elapsed = time.time() - start_time
    results["elapsed_time"] = round(elapsed, 2)
    logger.info(f"Task completed in {elapsed:.2f} seconds")

    return results


def main():
    """Entry point for command line use."""
    import json
    import sys

    # Check if a config file is provided
    config = {}
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            sys.exit(1)

    # Run the task
    result = asyncio.run(run_notion_task(config))

    # Print result
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
