"""Main MCP server implementation."""

import os
import logging

from mcp.server.fastmcp import FastMCP

from .models import LLMRequest
from .client import query_openshift_lightspeed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastMCP server instance
mcp = FastMCP("openshift-lightspeed-mcp")


@mcp.tool()
async def openshift_lightspeed(query: str, conversation_id: str | None = None) -> str:
    """Query OpenShift LightSpeed for assistance with OpenShift, Kubernetes, and related technologies."""
    try:
        request = LLMRequest(query=query, conversation_id=conversation_id)
        response = await query_openshift_lightspeed(request)
        return response.response
    except Exception as e:
        logger.error(f"Error calling OpenShift LightSpeed: {e}")
        return f"Error: {str(e)}"


def main():
    """Main entry point for the MCP server."""
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
