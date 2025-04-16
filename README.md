# Notion MCP Client

A Model Context Protocol (MCP) client for interacting with the Notion API. This client is designed to be used in modern AI tools like Claude that support MCP for extended functionality.

## Features

- Asynchronous API operations with retry logic
- Concurrency control to respect Notion API rate limits
- Environment-based configuration
- JSON-based operation configuration
- Flexible server implementation with MCP support
- Fall back to standard HTTP API when MCP is not available

## Installation

```bash
pip install notion-mcp
```

Or install from source:

```bash
git clone https://github.com/yourusername/notion-mcp.git
cd notion-mcp
pip install -e .
```

For MCP support, install with the MCP extra:

```bash
pip install notion-mcp[mcp]
```

## Configuration

Create a `.env` file with your Notion API credentials and configuration:

```
NOTION_TOKEN=your_notion_token_here
ROOT_PAGE_ID=your_root_page_id_here
MAX_RETRIES=3
RETRY_DELAYS=1,3,5
CONCURRENCY_LIMIT=5
TIMEOUT_MS=30000
```

## Usage

### Command Line

Run with default configuration:

```bash
notion-mcp
```

Run with a custom JSON configuration file:

```bash
notion-mcp config.json
```

### Server

Start the server (with MCP support if available):

```bash
notion-mcp-server --host 0.0.0.0 --port 8000
```

The server will attempt to use the MCP protocol if available. If not, it will fall back to a standard HTTP server that accepts POST requests at `/notion`.

### HTTP API

When using the HTTP API, send a POST request to `/notion` with a JSON body:

```json
{
  "root_page_id": "your_page_id_here",
  "database_filter": ["Articles", "Resources"],
  "operation": {
    "type": "fill_web_url",
    "params": {
      "web_field": "网址"
    }
  }
}
```

Example using curl:

```bash
curl -X POST http://localhost:8000/notion \
  -H "Content-Type: application/json" \
  -d '{"root_page_id": "your_page_id_here", "operation": {"type": "fill_web_url"}}'
```

### JSON Configuration

Create a JSON configuration file to customize the behavior:

```json
{
  "root_page_id": "your_page_id_here",
  "database_filter": ["Articles", "Resources"],
  "operation": {
    "type": "fill_web_url",
    "params": {
      "web_field": "网址"
    }
  }
}
```

## Using with Claude

To use this MCP client with Claude, you'll need to set up the server and then configure Claude to use it. Here's an example of how to do that:

```json
{
  "mcp_configurations": [
    {
      "name": "notion",
      "endpoint": "http://localhost:8000/notion",
      "description": "Access and manipulate Notion databases and pages"
    }
  ]
}
```

Then, in your conversation with Claude, you can ask it to perform Notion operations like this:

```
Claude, please use the notion MCP to fill the web URL field in all pages of my Articles database.
```

## Integration with Other Frameworks

The `NotionRequestHandler` class provides a flexible way to integrate with different frameworks:

```python
from notion_mcp.handler import notion_handler

# Create an adapter for your framework
async def my_framework_handler(request):
    # Extract data from your framework's request object
    input_data = await request.json()
    
    # Process with Notion handler
    result = await notion_handler.handle_request(input_data)
    
    # Return in your framework's response format
    return MyFrameworkResponse(json=result)
```

## Available Operations

- `fill_web_url`: Finds URL fields in a page and copies values to a specified target URL field
- More operations coming soon!

## Development

To contribute to this project:

1. Fork the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install development dependencies: `pip install -e ".[dev]"`
5. Make your changes
6. Run tests: `pytest`
7. Submit a pull request

## License

MIT