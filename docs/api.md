# OrderHub API v1.0

Order management API. All requests require header `X-API-Key`. The API may respond 429 with a `Retry-After` header; wait and retry the same request.

Base URL: `http://127.0.0.1:8000`. Header `X-API-Key: test-key` is required on every request. Request and response bodies are JSON. Validation errors return 422 with a `detail` field explaining the problem.

## Endpoints

### GET /customers

Find customers

List customers, optionally filtered by exact email address.

Parameters:
- `email`: string — Exact email to match (in query)

Response: array of objects:
- `id`: integer
- `name`: string
- `email`: string

### GET /customers/{customer_id}

Get a customer by ID

Parameters:
- `customer_id`: integer (required) (in path)

Response:
- `id`: integer
- `name`: string
- `email`: string

### GET /products

List the product catalog

Returns every product with its SKU and unit price.

Response: array of objects:
- `sku`: string
- `name`: string
- `unit_price`: number

### GET /orders

List orders (paginated)

Cursor-paginated. Results are limited to `limit` per page; follow `next_cursor` until it is null to see all matching orders.

Parameters:
- `customer_id`: integer — Only orders of this customer (in query)
- `status`: `pending` | `paid` | `shipped` | `cancelled` — Only orders in this status (in query)
- `cursor`: string — Cursor from a previous page (in query)
- `limit`: integer — Page size, max 20 [minimum=1, maximum=20, default=20] (in query)

Response:
- `items`: array of object
  - `id`: integer
  - `customer_id`: integer
  - `status`: `pending` | `paid` | `shipped` | `cancelled`
  - `items`: array of object
    - `sku`: string — Product SKU, must exist in the product catalog
    - `qty`: integer — Quantity, at least 1 [minimum=1.0]
    - `unit_price`: number
  - `total`: number — Sum of qty * unit_price over items
  - `created_at`: string
- `next_cursor`: string — Pass as `cursor` to fetch the next page; null on the last page

### POST /orders

Create an order

Creates an order for a customer. Every SKU must exist in the product catalog; prices are taken from the catalog.

Request body (JSON):
- `customer_id`: integer (required) — ID of an existing customer (look it up by email first)
- `items`: array of object (required)
  - `sku`: string (required) — Product SKU, must exist in the product catalog
  - `qty`: integer (required) — Quantity, at least 1 [minimum=1.0]
- `status`: `pending` | `paid` | `shipped` | `cancelled`

Response:
- `id`: integer
- `customer_id`: integer
- `status`: `pending` | `paid` | `shipped` | `cancelled`
- `items`: array of object
  - `sku`: string — Product SKU, must exist in the product catalog
  - `qty`: integer — Quantity, at least 1 [minimum=1.0]
  - `unit_price`: number
- `total`: number — Sum of qty * unit_price over items
- `created_at`: string

### GET /orders/{order_id}

Get an order by ID

Parameters:
- `order_id`: integer (required) (in path)

Response:
- `id`: integer
- `customer_id`: integer
- `status`: `pending` | `paid` | `shipped` | `cancelled`
- `items`: array of object
  - `sku`: string — Product SKU, must exist in the product catalog
  - `qty`: integer — Quantity, at least 1 [minimum=1.0]
  - `unit_price`: number
- `total`: number — Sum of qty * unit_price over items
- `created_at`: string

### PATCH /orders/{order_id}

Update an order's status

Changes the status of an order. Fails with 409 if the order is already shipped or cancelled.

Parameters:
- `order_id`: integer (required) (in path)

Request body (JSON):
- `status`: `pending` | `paid` | `shipped` | `cancelled` (required)

Response:
- `id`: integer
- `customer_id`: integer
- `status`: `pending` | `paid` | `shipped` | `cancelled`
- `items`: array of object
  - `sku`: string — Product SKU, must exist in the product catalog
  - `qty`: integer — Quantity, at least 1 [minimum=1.0]
  - `unit_price`: number
- `total`: number — Sum of qty * unit_price over items
- `created_at`: string
