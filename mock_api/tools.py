"""OpenAPI → (1) tool definitions shared by the native backend and the MCP server,
(2) docs/api.md for the prompt-doc backend. One source, three consumers.

Run: uv run python -m mock_api.tools   # regenerates docs/api.md
"""
import copy, json, pathlib, httpx

BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"X-API-Key": "test-key"}


def load_spec() -> dict:
    from mock_api.app import app
    spec = app.openapi()
    spec["paths"] = dict(sorted(spec["paths"].items()))  # alphabetical: no positional advantage for the core routes
    return spec


def resolve(spec: dict, schema: dict) -> dict:
    """Inline every $ref so consumers see a self-contained JSON schema."""
    if "$ref" in schema:
        schema = spec["components"]["schemas"][schema["$ref"].rsplit("/", 1)[1]]
    schema = copy.deepcopy(schema)
    for k in ("properties",):
        if k in schema:
            schema[k] = {n: resolve(spec, s) for n, s in schema[k].items()}
    if "items" in schema:
        schema["items"] = resolve(spec, schema["items"])
    if "anyOf" in schema:  # Optional[X] → X, nullable
        opts = [o for o in schema.pop("anyOf") if o.get("type") != "null"]
        schema.update(resolve(spec, opts[0]) if len(opts) == 1 else {"anyOf": [resolve(spec, o) for o in opts]})
    schema.pop("title", None)
    return schema


def to_tools(spec: dict) -> list[dict]:
    """[{name, description, input_schema, method, path, locations:{arg: path|query|body}}]"""
    tools = []
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            props, required, loc = {}, [], {}
            for p in op.get("parameters", []):
                if p["in"] == "header":
                    continue
                s = resolve(spec, p["schema"])
                if "description" in p:
                    s["description"] = p["description"]
                props[p["name"]] = s
                loc[p["name"]] = p["in"]
                if p.get("required"):
                    required.append(p["name"])
            if "requestBody" in op:
                body = resolve(spec, op["requestBody"]["content"]["application/json"]["schema"])
                props.update(body["properties"])
                required += body.get("required", [])
                loc.update({n: "body" for n in body["properties"]})
            desc = op["summary"] + ("\n" + op["description"] if op.get("description") else "")
            tools.append({"name": op["operationId"], "description": desc, "method": method.upper(), "path": path,
                          "input_schema": {"type": "object", "properties": props, "required": required},
                          "locations": loc})
    return tools


def call_tool(tool: dict, args: dict, base_url: str = BASE_URL) -> dict:
    """Execute a tool against the mock API. Returns {"status": int, "body": ...}."""
    path, query, body = tool["path"], {}, {}
    for k, v in args.items():
        where = tool["locations"].get(k)
        if where == "path":
            path = path.replace("{%s}" % k, str(v))
        elif where == "query":
            if v is not None:
                query[k] = v
        else:
            body[k] = v
    r = httpx.request(tool["method"], base_url + path, params=query, json=body or None, headers=HEADERS)
    try:
        payload = r.json()
    except ValueError:
        payload = r.text
    out = {"status": r.status_code, "body": payload}
    if "Retry-After" in r.headers:
        out["retry_after"] = r.headers["Retry-After"]
    return out


def _fmt_schema(s: dict, indent: int = 0, show_required: bool = True) -> list[str]:
    pad = "  " * indent
    lines = []
    for n, p in s.get("properties", {}).items():
        t = p.get("type", "object")
        if "enum" in p:
            t = " | ".join(f"`{e}`" for e in p["enum"])
        elif t == "array":
            t = f"array of {p['items'].get('type', 'object')}"
        req = " (required)" if show_required and n in s.get("required", []) else ""
        extra = ", ".join(f"{k}={p[k]}" for k in ("minimum", "maximum", "default", "minLength") if k in p)
        lines.append(f"{pad}- `{n}`: {t}{req}{' — ' + p['description'] if p.get('description') else ''}{' [' + extra + ']' if extra else ''}")
        if p.get("type") == "array" and "properties" in p.get("items", {}):
            lines += _fmt_schema(p["items"], indent + 1, show_required)
        elif "properties" in p:
            lines += _fmt_schema(p, indent + 1, show_required)
    return lines


def to_markdown(spec: dict) -> str:
    md = [f"# {spec['info']['title']} v{spec['info']['version']}", "", spec["info"]["description"], "",
          f"Base URL: `{BASE_URL}`. Header `X-API-Key: {HEADERS['X-API-Key']}` is required on every request. "
          "Request and response bodies are JSON. Validation errors return 422 with a `detail` field explaining the problem.", "",
          "## Endpoints", ""]
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            md += [f"### {method.upper()} {path}", "", op["summary"] + ("\n\n" + op["description"] if op.get("description") else ""), ""]
            params = [p for p in op.get("parameters", []) if p["in"] != "header"]
            if params:
                md.append("Parameters:")
                for p in params:
                    s = resolve(spec, p["schema"])
                    s["description"] = p.get("description", "")
                    md += _fmt_schema({"properties": {p["name"]: s}, "required": [p["name"]] if p.get("required") else []})
                    md[-1] += f" (in {p['in']})"
                md.append("")
            if "requestBody" in op:
                md += ["Request body (JSON):"] + _fmt_schema(resolve(spec, op["requestBody"]["content"]["application/json"]["schema"])) + [""]
            ok = next(v for k, v in op["responses"].items() if k.startswith("2"))
            rs = resolve(spec, ok["content"]["application/json"]["schema"])
            if rs.get("type") == "array":
                md += ["Response: array of objects:"] + _fmt_schema(rs["items"], show_required=False) + [""]
            else:
                md += ["Response:"] + _fmt_schema(rs, show_required=False) + [""]
    return "\n".join(md)


if __name__ == "__main__":
    spec = load_spec()
    out = pathlib.Path(__file__).parents[1] / "docs" / "api.md"
    out.write_text(to_markdown(spec), encoding="utf-8")
    print(f"wrote {out} ({len(to_tools(spec))} tools)")


def stale_spec(level: int = 1) -> dict:
    """The spec as it was 'documented last quarter'. Static docs/tools (A, B) go wrong; MCP (C) stays live.
    level 1: two query params renamed -> API silently ignores them (superset results, recoverable)
    level 2: + body fields renamed (422 names the right field) + /products moved to /catalog (404, no hint)"""
    spec = copy.deepcopy(load_spec())
    for p in spec["paths"]["/customers"]["get"]["parameters"]:
        if p["name"] == "email":
            p["name"] = "customer_email"
    for p in spec["paths"]["/orders"]["get"]["parameters"]:
        if p["name"] == "status":
            p["name"] = "state"
    if level >= 2:
        for model, old, new in (("OrderCreate", "items", "line_items"), ("OrderUpdate", "status", "new_status")):
            props = spec["components"]["schemas"][model]
            props["properties"] = {new if k == old else k: v for k, v in props["properties"].items()}
            props["required"] = [new if r == old else r for r in props.get("required", [])]
        spec["paths"]["/catalog"] = spec["paths"].pop("/products")
    return spec
