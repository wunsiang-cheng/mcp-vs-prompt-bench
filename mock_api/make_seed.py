"""Deterministic seed data. Run once: uv run python -m mock_api.make_seed"""
import json, random, pathlib

r = random.Random(42)
PRODUCTS = [
    {"sku": "KB-01", "name": "Mechanical Keyboard", "unit_price": 89.0},
    {"sku": "MS-02", "name": "Wireless Mouse", "unit_price": 35.0},
    {"sku": "MN-03", "name": "27in Monitor", "unit_price": 249.0},
    {"sku": "HS-04", "name": "USB Headset", "unit_price": 59.0},
    {"sku": "DK-05", "name": "USB-C Dock", "unit_price": 129.0},
    {"sku": "CB-06", "name": "HDMI Cable 2m", "unit_price": 12.0},
]
NAMES = ["Alice Chen", "Bob Lin", "Carol Wang", "Dave Huang", "Eve Liu", "Frank Wu", "Grace Tsai", "Henry Yang"]
customers = [{"id": i + 1, "name": n, "email": n.split()[0].lower() + "@example.com"} for i, n in enumerate(NAMES)]

orders = []
for oid in range(1001, 1076):  # 75 orders → shipped filter spans >20 → forces pagination
    items = [{"sku": p["sku"], "qty": r.randint(1, 3), "unit_price": p["unit_price"]}
             for p in r.sample(PRODUCTS, r.randint(1, 3))]
    orders.append({
        "id": oid,
        "customer_id": r.randint(1, len(customers)),
        "status": r.choice(["pending", "paid", "shipped", "shipped", "cancelled"]),
        "items": items,
        "total": round(sum(i["qty"] * i["unit_price"] for i in items), 2),
        "created_at": f"2026-0{r.randint(1, 8)}-{r.randint(10, 28)}T10:00:00Z",
    })

pathlib.Path(__file__).with_name("seed.json").write_text(
    json.dumps({"products": PRODUCTS, "customers": customers, "orders": orders}, indent=1))
print(f"{len(customers)} customers, {len(orders)} orders, shipped={sum(o['status']=='shipped' for o in orders)}")
