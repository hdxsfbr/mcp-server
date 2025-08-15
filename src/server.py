from __future__ import annotations

import json
import asyncio
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Dict, List
import tempfile
import os

from fastmcp import FastMCP
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# Initialize FastMCP application
app = FastMCP(
    name="fastmcp-demo",
    version="0.1.0",
)

# Global browser management
_browser: Optional[Browser] = None
_browser_context: Optional[BrowserContext] = None

async def get_browser() -> Browser:
    """Get or create a browser instance."""
    global _browser
    if _browser is None:
        playwright = await async_playwright().start()
        _browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
            ]
        )
    return _browser

async def get_browser_context() -> BrowserContext:
    """Get or create a browser context."""
    global _browser_context
    if _browser_context is None:
        browser = await get_browser()
        _browser_context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    return _browser_context

# ------------------
# Original Tools
# ------------------

@app.tool("echo")
def echo(text: str) -> str:
    """Echo back the provided text."""
    return text


@app.tool("add")
def add(a: float, b: float) -> float:
    """Add two numbers and return the sum."""
    return a + b


@app.tool("get_time")
def get_time(iso: bool = True) -> str:
    """Get current UTC time. If iso is True, return ISO8601 string; otherwise a human format."""
    now = datetime.now(timezone.utc)
    return now.isoformat() if iso else now.strftime("%Y-%m-%d %H:%M:%S %Z")


@app.tool("read_resource")
def read_resource(name: str) -> str:
    """Read a static file from resources directory by name."""
    resource_path = Path(__file__).resolve().parent.parent / "resources" / name
    if not resource_path.exists() or not resource_path.is_file():
        raise FileNotFoundError(f"Resource not found: {name}")
    return resource_path.read_text(encoding="utf-8")


@app.tool()
def execute_command(command: str) -> str:
    """Execute a shell command and return its output."""
    import subprocess

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed with error: {e.stderr.strip()}")

# ------------------
# Prompts
# ------------------

@app.prompt("hello")
def hello_prompt(name: str = "world") -> str:
    """A simple templated greeting prompt."""
    return f"Hello, {name}! I am an MCP server with browser capabilities. How can I help?"


@app.prompt("sum")
def sum_prompt(numbers: list[float]) -> str:
    """Prompt template that asks the model to sum a list of numbers."""
    nums = ", ".join(str(n) for n in numbers)
    return (
        "You are a calculator. Sum the following numbers and return only the number.\n"
        f"Numbers: {nums}"
    )

@app.prompt("web_scrape")
def web_scrape_prompt(url: str, data_type: str = "general") -> str:
    """Prompt template for web scraping tasks."""
    return f"""You are a web scraping assistant. Please analyze the website at {url} and extract {data_type} information. 

Use the browse_website tool to:
1. First take a screenshot to see the layout
2. Get the page content
3. Extract relevant {data_type} data
4. Format the results in a structured way

Focus on extracting clean, useful data while respecting the website's structure."""

# ------------------
# Resources
# ------------------

@app.resource("res://greeting.txt", mime_type="text/plain")
def greeting_resource() -> str:
    path = Path(__file__).resolve().parent.parent / "resources" / "greeting.txt"
    content = path.read_text(encoding="utf-8")
    return content


@app.resource("res://time.json", mime_type="application/json")
def time_resource() -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "utc": now.isoformat(),
        "epoch": now.timestamp(),
    }
    return json.dumps(payload, indent=2)


if __name__ == "__main__":
    try:
        app.run(transport="stdio")
    except TypeError:
        app.run()