from mcp.server import FastMCP
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import logging
import asyncio
import time
import random

from notion_client import AsyncClient as NotionAsyncClient

app = FastMCP()

# 日志设置
logger = logging.getLogger("NOTION")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)

# 配置
ARTICLE_COLLATION_TOKEN = "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"
MAX_RETRIES = 3
RETRY_DELAYS = [1, 3, 5]
CONCURRENCY_LIMIT = 5

@asynccontextmanager
async def get_notion_client():
    client = NotionAsyncClient(auth=ARTICLE_COLLATION_TOKEN, logger=logger)
    try:
        yield client
    finally:
        await client.aclose()


async def retry_async(func, *args, **kwargs):
    last_exception = None
    for attempt, delay in enumerate(RETRY_DELAYS[:MAX_RETRIES]):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            logger.warning(f"尝试 {attempt + 1}/{MAX_RETRIES} 失败: {e}，重试中...")
            await asyncio.sleep(delay + random.uniform(0, 1))
    raise last_exception


@app.tool()
async def query_all_databases(page_id: str) -> Dict[str, str]:
    """查询页面中所有子数据库的标题和ID"""

    async def _get_blocks(client, pid):
        return await client.blocks.children.list(pid)

    async def _recursive(client, pid, result):
        blocks = await retry_async(_get_blocks, client, pid)
        for block in blocks["results"]:
            if block["type"] == "child_database":
                db_id = block["id"]
                title = block["child_database"]["title"]
                result[title] = db_id
            elif block["type"] == "child_page":
                await _recursive(client, block["id"], result)

    async with get_notion_client() as client:
        result: Dict[str, str] = {}
        await _recursive(client, page_id, result)
        return result


@app.tool()
async def list_database_pages(database_id: str, page_size: Optional[int] = 100) -> List[str]:
    """列出数据库中的所有页面ID"""
    result = []
    has_more = True
    cursor = None

    async with get_notion_client() as client:
        while has_more:
            body = {"page_size": page_size}
            if cursor:
                body["start_cursor"] = cursor
            res = await retry_async(client.databases.query, database_id=database_id, **body)
            result += [page["id"] for page in res.get("results", [])]
            has_more = res.get("has_more", False)
            cursor = res.get("next_cursor")

    return result


@app.tool()
async def update_page_title(page_id: str, new_title: str) -> Dict[str, Any]:
    """更新页面标题（Name字段）"""
    async with get_notion_client() as client:
        await retry_async(client.pages.update, page_id=page_id, properties={
            "Name": {"title": [{"text": {"content": new_title}}]}
        })
        return {"status": "success", "page_id": page_id, "new_title": new_title}


@app.tool()
async def fill_url_from_existing(page_id: str, target_field: str = "网址") -> Dict[str, Any]:
    """将页面中其他 URL 字段填入目标字段"""
    async with get_notion_client() as client:
        page = await retry_async(client.pages.retrieve, page_id=page_id)
        props = page["properties"]

        if target_field not in props or props[target_field]["type"] != "url":
            return {"status": "error", "message": f"{target_field} 字段不存在或类型不是 URL"}

        if props[target_field].get("url"):
            return {"status": "skipped", "message": f"{target_field} 已有值"}

        for name, prop in props.items():
            if name == target_field:
                continue
            if prop["type"] == "url" and prop.get("url"):
                await retry_async(client.pages.update, page_id=page_id, properties={
                    target_field: {"url": prop["url"]}
                })
                return {"status": "success", "copied_from": name, "url": prop["url"]}

        return {"status": "skipped", "message": "未找到可用的 URL 字段"}


@app.tool()
async def batch_process_fill_url(database_id: str, web_field: str = "网址") -> Dict[str, Any]:
    """对数据库中所有页面执行URL字段填充"""
    async with get_notion_client() as client:
        pages = await list_database_pages(database_id)
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

        async def _handle(page_id):
            async with semaphore:
                return await fill_url_from_existing(page_id, web_field)

        results = await asyncio.gather(*[_handle(pid) for pid in pages])
        summary = {"success": 0, "skipped": 0, "error": 0}
        for r in results:
            if r["status"] == "success":
                summary["success"] += 1
            elif r["status"] == "skipped":
                summary["skipped"] += 1
            else:
                summary["error"] += 1
        return summary


def start_server():
    print("🚀 启动 Notion 工具服务...")
    print("✅ 可用工具: query_all_databases, list_database_pages, update_page_title, fill_url_from_existing, batch_process_fill_url")
    app.run(transport="stdio")


if __name__ == "__main__":
    start_server()