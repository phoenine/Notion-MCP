import json
import logging
from typing import Dict, Any, Optional, Union, Callable
import asyncio

from main import run_notion_task

logger = logging.getLogger("NOTION_HANDLER")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)


class NotionRequestHandler:
    """A flexible handler for Notion API requests."""

    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a Notion API request."""
        logger.info(f"Processing Notion request")

        # Add request validation if needed
        if not isinstance(request_data, dict):
            error_msg = "Invalid request format: expected a JSON object"
            logger.error(error_msg)
            return {"status": "error", "error": error_msg}

        # Process the request
        try:
            result = await run_notion_task(request_data)
            return result
        except Exception as e:
            logger.exception("Error processing request")
            return {"status": "error", "error": str(e)}

    def create_adapter(
        self, input_extractor: Callable = None, output_formatter: Callable = None
    ):
        """
        Create an adapter function for different server frameworks.

        Args:
            input_extractor: Function to extract input data from request object
            output_formatter: Function to format output for response
        """

        async def adapter(request_obj):
            # Extract input data
            if input_extractor:
                try:
                    input_data = input_extractor(request_obj)
                except Exception as e:
                    logger.error(f"Error extracting input: {e}")
                    result = {"status": "error", "error": "Invalid request format"}
            else:
                # Default extraction - assume request_obj is already the input data
                input_data = request_obj

            # Process the request
            result = await self.handle_request(input_data)

            # Format the output
            if output_formatter:
                try:
                    return output_formatter(result)
                except Exception as e:
                    logger.error(f"Error formatting output: {e}")
                    return result
            else:
                # Default - return result directly
                return result

        return adapter


# Singleton instance
notion_handler = NotionRequestHandler()
