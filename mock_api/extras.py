"""Distractor resources for the 'big API' condition (ORDERHUB_BIG=1): 8 plausible-but-irrelevant
resources x 4 routes = 32 extra endpoints. Tasks never need them; they exist to bloat the docs/tool list."""
import inspect, os
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query
from pydantic import Field, create_model

BIG = os.environ.get("ORDERHUB_BIG") == "1"

# plural, singular, filter field, fields {name: (type, description)}, blurb
RESOURCES = [
    ("shipments", "shipment", "order_id", {"order_id": (int, "Order being shipped"), "carrier": (str, "Carrier code, e.g. UPS"), "tracking_no": (str, "Carrier tracking number"), "shipped_at": (str, "ISO timestamp")}, "Physical shipments. One order can have several shipments."),
    ("invoices", "invoice", "order_id", {"order_id": (int, "Order being invoiced"), "amount": (float, "Invoiced amount"), "issued_at": (str, "ISO timestamp"), "paid": (bool, "Whether the invoice has been settled")}, "Invoices issued for orders."),
    ("returns", "return", "order_id", {"order_id": (int, "Order being returned"), "reason": (str, "Free-text reason"), "refund_amount": (float, "Amount refunded"), "approved": (bool, "Approved by support")}, "Return requests filed by customers."),
    ("payments", "payment", "order_id", {"order_id": (int, "Order being paid"), "method": (str, "card | bank | wallet"), "amount": (float, "Captured amount"), "captured_at": (str, "ISO timestamp")}, "Payment captures against orders."),
    ("coupons", "coupon", "code", {"code": (str, "Coupon code"), "percent_off": (int, "Discount percentage"), "expires_at": (str, "ISO timestamp"), "active": (bool, "Can still be redeemed")}, "Discount coupons."),
    ("warehouses", "warehouse", "region", {"region": (str, "Region code, e.g. tw-north"), "name": (str, "Display name"), "capacity": (int, "Pallet capacity")}, "Fulfilment warehouses."),
    ("addresses", "address", "customer_id", {"customer_id": (int, "Owning customer"), "line1": (str, "Street address"), "city": (str, "City"), "postal_code": (str, "Postal code"), "is_default": (bool, "Default shipping address")}, "Customer shipping addresses."),
    ("webhooks", "webhook", "event", {"event": (str, "Event name, e.g. order.created"), "url": (str, "Callback URL"), "active": (bool, "Deliveries enabled")}, "Webhook subscriptions for event notifications."),
]

router = APIRouter()
store: dict[str, dict[int, dict]] = {}
KW = inspect.Parameter.KEYWORD_ONLY


def seed():
    store.clear()
    for plural, _, _, fields, _ in RESOURCES:
        store[plural] = {i: {"id": i, **{f: {int: i * 7 + 1000, float: round(i * 19.5, 2), bool: i % 2 == 0, str: f"{f}-{i}"}[t]
                                          for f, (t, _) in fields.items()}} for i in range(1, 6)}


def with_sig(fn, **params):
    """Give a **kw handler an explicit signature so FastAPI documents the params."""
    fn.__signature__ = inspect.Signature([inspect.Parameter(n, KW, annotation=a, default=d) for n, (a, d) in params.items()])
    return fn


def register(plural, singular, filt, fields, blurb):
    In = create_model(f"{singular.title()}In", **{f: (t, Field(description=d)) for f, (t, d) in fields.items()})
    Out = create_model(singular.title(), id=(int, ...), **{f: (t, Field(description=d)) for f, (t, d) in fields.items()})
    Patch = create_model(f"{singular.title()}Update", **{f: (t | None, Field(None, description=d)) for f, (t, d) in fields.items()})
    pid, path = f"{singular}_id", f"/{plural}/{{{singular}_id}}"

    def get_row(rid):
        if rid not in store[plural]:
            raise HTTPException(404, f"{singular} not found")
        return store[plural][rid]

    def list_(**kw):
        v = kw[filt]
        return [r for r in store[plural].values() if v is None or r[filt] == v]

    def create_(**kw):
        rid = max(store[plural], default=0) + 1
        store[plural][rid] = {"id": rid, **kw["body"].model_dump()}
        return store[plural][rid]

    def update_(**kw):
        r = get_row(kw[pid])
        r.update(kw["body"].model_dump(exclude_none=True))
        return r

    ftype, fdesc = fields[filt]
    router.add_api_route(f"/{plural}", with_sig(list_, **{filt: (Annotated[ftype | None, Query(description=fdesc)], None)}), methods=["GET"],
                         operation_id=f"list_{plural}", summary=f"List {plural}", description=f"{blurb} Optionally filter by `{filt}`.", response_model=list[Out])
    router.add_api_route(path, with_sig(lambda **kw: get_row(kw[pid]), **{pid: (int, inspect.Parameter.empty)}), methods=["GET"],
                         operation_id=f"get_{singular}", summary=f"Get a {singular} by ID", response_model=Out)
    router.add_api_route(f"/{plural}", with_sig(create_, body=(In, inspect.Parameter.empty)), methods=["POST"], status_code=201,
                         operation_id=f"create_{singular}", summary=f"Create a {singular}", response_model=Out)
    router.add_api_route(path, with_sig(update_, **{pid: (int, inspect.Parameter.empty)}, body=(Patch, inspect.Parameter.empty)), methods=["PATCH"],
                         operation_id=f"update_{singular}", summary=f"Update a {singular}", description="Partial update; only provided fields change.", response_model=Out)


for spec in RESOURCES:
    register(*spec)
seed()
