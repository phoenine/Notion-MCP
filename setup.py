from setuptools import setup, find_packages

setup(
    name="notion-mcp",
    version="0.1.0",
    description="Model Context Protocol (MCP) client for Notion API",
    author="Evan Yang",
    author_email="sparkbye@hotmail.com",
    packages=find_packages(),
    install_requires=[
        "notion-client>=1.0.0",
        "python-dotenv>=0.19.0",
        "aiohttp>=3.8.0",
    ],
    extras_require={
        "mcp": ["mcp>=0.1.0"],  # Optional MCP dependency
        "dev": [
            "pytest>=6.0.0",
            "black>=21.5b2",
            "isort>=5.9.1",
            "flake8>=3.9.2",
        ],
    },
    entry_points={
        "console_scripts": [
            "notion-mcp=notion_mcp.main:main",
            "notion-mcp-server=notion_mcp.mcp_server:main",
        ],
    },
    python_requires=">=3.7",
)
