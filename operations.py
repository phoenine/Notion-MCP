import logging
from typing import Dict, List
from utils import retry_async

logger = logging.getLogger("NOTION")


async def query_page_for_databases(client, page_id: str) -> Dict[str, str]:
    """Query all databases within a page."""
    databases_dict = {}

    async def _get_blocks():
        return await client.blocks.children.list(page_id)

    blocks = await retry_async(_get_blocks)
    logger.info(f"Found {len(blocks['results'])} blocks in page {page_id}")

    for block in blocks["results"]:
        block_type = block["type"]
        logger.debug(f"Block type: {block_type}")

        if block_type == "child_database":
            database_id = block["id"]
            database_title = block["child_database"]["title"]
            databases_dict[database_title] = database_id
            logger.info(
                f"Found child database, ID: {database_id}, Title: {database_title}"
            )

        elif block_type == "child_page":
            child_page_id = block["id"]
            logger.info(f"Found child page, recursively querying: {child_page_id}")
            child_databases = await query_page_for_databases(client, child_page_id)
            databases_dict.update(child_databases)

    return databases_dict


async def query_database_for_all_pages(
    client, database_id: str, page_size: int = 100
) -> List[str]:
    """Query all pages in a database."""
    pages_list = []
    has_more = True
    start_cursor = None
    total = 0

    while has_more:
        body = {"page_size": page_size}
        if start_cursor:
            body["start_cursor"] = start_cursor

        async def _query_database():
            return await client.databases.query(database_id=database_id, **body)

        response = await retry_async(_query_database)
        results = response.get("results", [])

        logger.info(f"📄 Retrieved {len(results)} page records")

        for page in results:
            page_id = page["id"]
            try:
                page_title = page["properties"]["Name"]["title"][0]["text"]["content"]
            except (KeyError, IndexError):
                page_title = "(No title)"

            logger.info(f"🆔 Page ID: {page_id}, Title: {page_title}")
            pages_list.append(page_id)
            total += 1

        has_more = response.get("has_more", False)
        start_cursor = response.get("next_cursor")

    logger.info(f"✅ Pagination complete, total pages: {total}")
    return pages_list


async def update_page_content(client, page_id: str, new_content: str):
    """Update page content."""

    async def _update_page():
        await client.pages.update(
            page_id=page_id,
            properties={"Name": {"title": [{"text": {"content": new_content}}]}},
        )

    await retry_async(_update_page)
    logger.info(f"Page {page_id} updated successfully")


async def fill_web_url_from_other_urls(client, page_id: str, web_field: str = "网址"):
    """Fill web URL field from other URL fields."""

    async def _retrieve_page():
        return await client.pages.retrieve(page_id=page_id)

    try:
        page = await retry_async(_retrieve_page)
        props = page["properties"]

        if web_field not in props or props[web_field]["type"] != "url":
            logger.warning(f'❌ Field "{web_field}" does not exist or is not URL type')
            return

        if props[web_field].get("url"):
            logger.info(
                f"✅ \"{web_field}\" already has value: {props[web_field]['url']}, no update needed"
            )
            return

        for field_name, field_info in props.items():
            if field_name == web_field:
                continue

            if field_info["type"] == "url" and field_info.get("url"):
                logger.info(
                    f"🔄 Found available URL field \"{field_name}\" with value: {field_info['url']}, preparing to write to \"{web_field}\""
                )

                async def _update_url():
                    await client.pages.update(
                        page_id=page_id,
                        properties={web_field: {"url": field_info["url"]}},
                    )

                await retry_async(_update_url)
                logger.info(
                    f'✅ Successfully copied URL from "{field_name}" to "{web_field}"'
                )
                return

        logger.warning(
            f"⚠️ No URL fields with values found in page {page_id}, no update performed"
        )
    except Exception as e:
        logger.error(f"Error processing page {page_id}: {e}")
