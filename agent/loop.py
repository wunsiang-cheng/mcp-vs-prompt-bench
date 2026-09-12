"""One agent loop, three tool backends. The loop is identical; only where tools come from differs.

A prompt_doc : docs (markdown) in the system prompt + generic http_request tool
B native     : OpenAI tools[] generated from the OpenAPI spec
C mcp        : tools discovered from the MCP server over stdio
"""
import json, os, time
import httpx
from openai import AsyncOpenAI
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mock_api.tools import BASE_URL, HEADERS, call_tool, load_spec, stale_spec, to_markdown, to_tools

MAX_TURNS = 15
SYSTEM = ("You are an assistant operating the OrderHub API through the provided tools. "
          "Complete the user's task. Call tools as needed; if a call fails, read the error and fix your request. "
          "When the task is done, reply with a short final answer (numbers as plain digits).")


def _oai(tools):
    return [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
            for t in tools]


class PromptDoc:
    name = "prompt_doc"
    HTTP_TOOL = {"name": "http_request", "description": "Send an HTTP request to the OrderHub API. Auth header is added automatically.",
                 "input_schema": {"type": "object", "properties": {
                     "method": {"type": "string", "enum": ["GET", "POST", "PATCH"]},
                     "path": {"type": "string", "description": "Path, e.g. /orders/1001"},
                     "query": {"type": "object", "description": "Query parameters"},
                     "body": {"type": "object", "description": "JSON body for POST/PATCH"}},
                     "required": ["method", "path"]}}

    def __init__(self, spec):
        self.system = SYSTEM + "\n\n# API documentation\n\n" + to_markdown(spec)
        self.tools = _oai([self.HTTP_TOOL])

    async def __aenter__(self): return self
    async def __aexit__(self, *a): pass

    async def call(self, name, args):
        if name != "http_request":
            return {"status": 0, "body": f"unknown tool {name}"}
        r = httpx.request(args["method"], BASE_URL + args["path"], params=args.get("query"), json=args.get("body"), headers=HEADERS)
        try:
            body = r.json()
        except ValueError:
            body = r.text
        out = {"status": r.status_code, "body": body}
        if "Retry-After" in r.headers:
            out["retry_after"] = r.headers["Retry-After"]
        return out


class Native:
    name = "native"

    def __init__(self, spec):
        self.system = SYSTEM
        self._tools = {t["name"]: t for t in to_tools(spec)}
        self.tools = _oai(self._tools.values())

    async def __aenter__(self): return self
    async def __aexit__(self, *a): pass

    async def call(self, name, args):
        if name not in self._tools:
            return {"status": 0, "body": f"unknown tool {name}"}
        return call_tool(self._tools[name], args)


class Mcp:
    name = "mcp"
    system = SYSTEM

    async def __aenter__(self):
        self._ctx = stdio_client(StdioServerParameters(command="uv", args=["run", "python", "-m", "mcp_server.server"], env=dict(os.environ)))
        r, w = await self._ctx.__aenter__()
        self._sess = await ClientSession(r, w).__aenter__()
        await self._sess.initialize()
        self.tools = _oai([{"name": t.name, "description": t.description, "input_schema": t.input_schema}
                           for t in (await self._sess.list_tools()).tools])
        return self

    async def __aexit__(self, *a):
        await self._sess.__aexit__(*a)
        await self._ctx.__aexit__(*a)

    async def call(self, name, args):
        res = await self._sess.call_tool(name, args)
        try:
            return json.loads(res.content[0].text)
        except (ValueError, IndexError):
            return {"status": 0, "body": res.content[0].text if res.content else ""}


def make_backend(condition: str):
    base, _, suffix = condition.rpartition("_stale")
    base = base or condition
    spec = stale_spec(2 if suffix == "2" else 1) if _ else load_spec()
    return {"prompt_doc": PromptDoc, "native": Native, "mcp": lambda _: Mcp()}[base](spec)


async def run(prompt: str, condition: str, model: str, thinking: bool) -> dict:
    client = AsyncOpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
    t0 = time.time()
    rec = {"condition": condition, "model": model, "thinking": thinking, "turns": 0, "tool_calls": [],
           "usage": {"prompt": 0, "completion": 0, "cache_hit": 0, "reasoning": 0}, "final": None, "error": None}
    async with make_backend(condition) as be:
        messages = [{"role": "system", "content": be.system}, {"role": "user", "content": prompt}]
        try:
            for _ in range(MAX_TURNS):
                rec["turns"] += 1
                resp = await client.chat.completions.create(
                    model=model, messages=messages, tools=be.tools, temperature=0,
                    extra_body={"thinking": {"type": "enabled" if thinking else "disabled"}})
                u = resp.usage
                rec["usage"]["prompt"] += u.prompt_tokens
                rec["usage"]["completion"] += u.completion_tokens
                rec["usage"]["cache_hit"] += getattr(u, "prompt_cache_hit_tokens", 0) or 0
                rec["usage"]["reasoning"] += getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", 0) or 0
                msg = resp.choices[0].message
                messages.append(msg.model_dump(exclude_none=True))  # keeps reasoning_content for thinking mode
                if not msg.tool_calls:
                    rec["final"] = msg.content or ""
                    break
                for tc in msg.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                        result = await be.call(tc.function.name, args)
                    except (ValueError, KeyError, TypeError) as e:
                        args, result = tc.function.arguments, {"status": 0, "body": f"bad arguments: {e}"}
                    rec["tool_calls"].append({"name": tc.function.name, "args": args, "status": result.get("status")})
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})
            else:
                rec["error"] = "max_turns"
        except Exception as e:  # ponytail: one catch-all so a single bad run never kills the matrix
            rec["error"] = f"{type(e).__name__}: {e}"
        rec["messages"] = messages
    rec["elapsed"] = round(time.time() - t0, 2)
    return rec
