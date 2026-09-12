"""One runnable check: mock API traps + MCP round-trip. Needs the mock server running on :8000."""
import asyncio, os, httpx
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mock_api.tools import BASE_URL, HEADERS, call_tool, load_spec, to_tools

T = {t["name"]: t for t in to_tools(load_spec())}
httpx.post(BASE_URL + "/reset")
assert httpx.get(BASE_URL + "/orders").status_code == 401                       # auth enforced
assert call_tool(T["list_products"], {})["status"] == 429                        # first hit trapped
assert len(call_tool(T["list_products"], {})["body"]) == 6                       # second hit ok
alice = call_tool(T["list_customers"], {"email": "alice@example.com"})["body"]
assert alice[0]["id"] == 1
p1 = call_tool(T["list_orders"], {"status": "shipped"})["body"]
assert len(p1["items"]) == 20 and p1["next_cursor"] == "20"                      # pagination forced
p2 = call_tool(T["list_orders"], {"status": "shipped", "cursor": "20"})["body"]
assert len(p2["items"]) == 14 and p2["next_cursor"] is None
bad = call_tool(T["create_order"], {"customer_id": 1, "items": [{"sku": "NOPE", "qty": 1}]})
assert bad["status"] == 422 and "NOPE" in str(bad["body"])
bad = call_tool(T["create_order"], {"customer_id": 1, "items": [{"sku": "KB-01", "qty": 0}]})
assert bad["status"] == 422                                                     # pydantic qty>=1
ok = call_tool(T["create_order"], {"customer_id": 1, "items": [{"sku": "KB-01", "qty": 2}, {"sku": "CB-06", "qty": 1}]})
assert ok["status"] == 201 and ok["body"]["total"] == 190.0 and ok["body"]["status"] == "pending"
assert call_tool(T["update_order"], {"order_id": ok["body"]["id"], "status": "paid"})["body"]["status"] == "paid"
shipped = p1["items"][0]["id"]
assert call_tool(T["update_order"], {"order_id": shipped, "status": "paid"})["status"] == 409
print("mock api: ok")


async def mcp_check():
    async with stdio_client(StdioServerParameters(command="uv", args=["run", "python", "-m", "mcp_server.server"], env=dict(os.environ))) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = (await s.list_tools()).tools
            assert {t.name for t in tools} == set(T)
            res = await s.call_tool("get_order", {"order_id": 1001})
            assert '"id": 1001' in res.content[0].text and not res.is_error
            res = await s.call_tool("get_order", {"order_id": 1})
            assert res.is_error
            print(f"mcp: ok ({len(tools)} tools via stdio)")

asyncio.run(mcp_check())
