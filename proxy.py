import asyncio
from fastmcp import FastMCP

# Connect to the remote/local MCP server and create a proxy
async def main():
    """Proxy for connecting to the Property Management MCP server remotely."""
    # For local stdio transport (default)
    mcp = FastMCP("PropertyManager Proxy")
    
    # If running remotely, configure the transport here
    # Example: mcp = FastMCP("PropertyManager Proxy", transport="sse", host="0.0.0.0", port=8000)
    
    print("Starting Property Manager MCP Proxy...")
    mcp.run()

if __name__ == "__main__":
    asyncio.run(main())
