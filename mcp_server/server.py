"""MCP server (stdio) exposing the mock API. Tools are generated from the same
OpenAPI spec that produces docs/api.md, so conditions A/B/C see identical descriptions.

Run: uv run python -m mcp_server.server   (spawned by the agent's MCP client)
"""
import asyncio, json
import mcp.types as t
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mock_api.tools import call_tool, load_spec, to_tools

TOOLS = {tool["name"]: tool for tool in to_tools(load_spec())}


async def on_list_tools(ctx, params):
    return t.ListToolsResult(tools=[
        t.Tool(name=n, description=tool["description"], input_schema=tool["input_schema"]) for n, tool in TOOLS.items()])


async def on_call_tool(ctx, params):
    if params.name not in TOOLS:
        return t.CallToolResult(content=[t.TextContent(type="text", text=f"unknown tool {params.name}")], is_error=True)
    res = call_tool(TOOLS[params.name], params.arguments or {})
    return t.CallToolResult(content=[t.TextContent(type="text", text=json.dumps(res))], is_error=res["status"] >= 400)


server = Server("orderhub", on_list_tools=on_list_tools, on_call_tool=on_call_tool)


async def main():
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
