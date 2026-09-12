"""Mock order-management SaaS API. Single source of truth: its OpenAPI spec
feeds docs/api.md (condition A), native tool schemas (B) and the MCP server (C).

Run: uv run uvicorn mock_api.app:app --port 8000
"""
import copy, json, pathlib
from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field
from mock_api import extras

API_KEY = "test-key"
SEED = json.loads(pathlib.Path(__file__).with_name("seed.json").read_text())
db: dict = {}


def reset():
    db.clear()
    db.update(copy.deepcopy(SEED))
    db["orders"] = {o["id"]: o for o in db["orders"]}
    db["next_id"] = max(db["orders"]) + 1
    db["products_hits"] = 0
    extras.seed()


reset()


def auth(x_api_key: Annotated[str | None, Header()] = None):
    if x_api_key != API_KEY:
        raise HTTPException(401, "missing or invalid X-API-Key header")


app = FastAPI(
    title="OrderHub API",
    version="1.0",
    description="Order management API. All requests require header `X-API-Key`. "
    "The API may respond 429 with a `Retry-After` header; wait and retry the same request.",
)
api = APIRouter(dependencies=[Depends(auth)])  # /reset and /state below are bench plumbing, no auth


class Status(str, Enum):
    pending = "pending"
    paid = "paid"
    shipped = "shipped"
    cancelled = "cancelled"


class Customer(BaseModel):
    id: int
    name: str
    email: str


class Product(BaseModel):
    sku: str
    name: str
    unit_price: float


class OrderItem(BaseModel):
    sku: str = Field(description="Product SKU, must exist in the product catalog")
    qty: int = Field(ge=1, description="Quantity, at least 1")


class OrderItemOut(OrderItem):
    unit_price: float


class Order(BaseModel):
    id: int
    customer_id: int
    status: Status
    items: list[OrderItemOut]
    total: float = Field(description="Sum of qty * unit_price over items")
    created_at: str


class OrderCreate(BaseModel):
    customer_id: int = Field(description="ID of an existing customer (look it up by email first)")
    items: list[OrderItem] = Field(min_length=1)
    status: Status = Field(Status.pending, description="Initial status; defaults to pending")


class OrderUpdate(BaseModel):
    status: Status = Field(description="New status. Orders that are shipped or cancelled cannot be changed.")


class OrderPage(BaseModel):
    items: list[Order]
    next_cursor: str | None = Field(description="Pass as `cursor` to fetch the next page; null on the last page")


@api.get("/customers", operation_id="list_customers", summary="Find customers",
         description="List customers, optionally filtered by exact email address.")
def list_customers(email: Annotated[str | None, Query(description="Exact email to match")] = None) -> list[Customer]:
    return [c for c in db["customers"] if email is None or c["email"] == email]


@api.get("/customers/{customer_id}", operation_id="get_customer", summary="Get a customer by ID")
def get_customer(customer_id: int) -> Customer:
    for c in db["customers"]:
        if c["id"] == customer_id:
            return c
    raise HTTPException(404, "customer not found")


@api.get("/products", operation_id="list_products", summary="List the product catalog",
         description="Returns every product with its SKU and unit price.")
def list_products(response: Response) -> list[Product]:
    db["products_hits"] += 1
    if db["products_hits"] == 1:  # deterministic rate-limit trap: first hit after reset
        response.headers["Retry-After"] = "1"
        raise HTTPException(429, "rate limited, retry after 1 second", headers={"Retry-After": "1"})
    return db["products"]


@api.get("/orders", operation_id="list_orders", summary="List orders (paginated)",
         description="Cursor-paginated. Results are limited to `limit` per page; follow `next_cursor` until it is null to see all matching orders.")
def list_orders(
    customer_id: Annotated[int | None, Query(description="Only orders of this customer")] = None,
    status: Annotated[Status | None, Query(description="Only orders in this status")] = None,
    cursor: Annotated[str | None, Query(description="Cursor from a previous page")] = None,
    limit: Annotated[int, Query(ge=1, le=20, description="Page size, max 20")] = 20,
) -> OrderPage:
    rows = [o for o in db["orders"].values()
            if (customer_id is None or o["customer_id"] == customer_id)
            and (status is None or o["status"] == status)]
    start = int(cursor) if cursor else 0
    page = rows[start:start + limit]
    return {"items": page, "next_cursor": str(start + limit) if start + limit < len(rows) else None}


@api.get("/orders/{order_id}", operation_id="get_order", summary="Get an order by ID")
def get_order(order_id: int) -> Order:
    if order_id not in db["orders"]:
        raise HTTPException(404, "order not found")
    return db["orders"][order_id]


@api.post("/orders", operation_id="create_order", summary="Create an order", status_code=201,
          description="Creates an order for a customer. Every SKU must exist in the product catalog; prices are taken from the catalog.")
def create_order(body: OrderCreate) -> Order:
    if not any(c["id"] == body.customer_id for c in db["customers"]):
        raise HTTPException(404, f"customer {body.customer_id} not found")
    prices = {p["sku"]: p["unit_price"] for p in db["products"]}
    unknown = [i.sku for i in body.items if i.sku not in prices]
    if unknown:
        raise HTTPException(422, f"unknown sku(s): {unknown}")
    items = [{"sku": i.sku, "qty": i.qty, "unit_price": prices[i.sku]} for i in body.items]
    order = {"id": db["next_id"], "customer_id": body.customer_id, "status": body.status.value, "items": items,
             "total": round(sum(i["qty"] * i["unit_price"] for i in items), 2), "created_at": "2026-09-11T00:00:00Z"}
    db["orders"][order["id"]] = order
    db["next_id"] += 1
    return order


@api.patch("/orders/{order_id}", operation_id="update_order", summary="Update an order's status",
           description="Changes the status of an order. Fails with 409 if the order is already shipped or cancelled.")
def update_order(order_id: int, body: OrderUpdate) -> Order:
    o = db["orders"].get(order_id)
    if not o:
        raise HTTPException(404, "order not found")
    if o["status"] in ("shipped", "cancelled"):
        raise HTTPException(409, f"order is {o['status']} and cannot be changed")
    o["status"] = body.status.value
    return o


if extras.BIG:
    api.include_router(extras.router)
app.include_router(api)


@app.post("/reset", include_in_schema=False)
def reset_endpoint():
    reset()
    return {"ok": True}


@app.get("/state", include_in_schema=False)
def state():  # for task checkers
    return {"orders": list(db["orders"].values())}
