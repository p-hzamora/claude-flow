---
name: api-rest-designer
description: Proactively apply when designing, reviewing, or discussing REST APIs. Triggers on endpoint design, URL structure, HTTP methods, status codes, resource modeling, API versioning, pagination, filtering, error responses, OpenAPI, Swagger, request/response schemas, API contracts, HATEOAS. Use as a reference for RESTful API design decisions, naming conventions, and architectural best practices. Language and framework agnostic.
---

# API-REST Designer

Comprehensive, language-agnostic guide for designing consistent, predictable, and well-structured RESTful APIs. All API design decisions MUST follow these conventions. This skill serves as the single source of truth for REST API design across the project.

---

## 1. REST Fundamentals

### Architectural Constraints

REST (Representational State Transfer) is defined by six architectural constraints. A truly RESTful API respects all of them:

| Constraint                      | Meaning                                                                                                                                        |
| ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Client-Server**               | Client and server are independent. The server does not know about the UI; the client does not know about data storage.                         |
| **Statelessness**               | Every request contains all information needed to process it. The server stores no client session state between requests.                       |
| **Cacheability**                | Responses must declare themselves cacheable or non-cacheable so clients and intermediaries can reuse them.                                     |
| **Uniform Interface**           | A standardized way to interact with resources (identification via URIs, manipulation via representations, self-descriptive messages, HATEOAS). |
| **Layered System**              | The client cannot tell whether it is connected directly to the server or through intermediaries (proxies, gateways, CDNs).                     |
| **Code on Demand** _(optional)_ | The server may extend client functionality by transferring executable code (e.g., JavaScript). Rarely used in API design.                      |

### Key Implications

- **Statelessness means no server-side sessions.** Authentication tokens, pagination cursors, and context travel with each request.
- **Uniform Interface means predictability.** A consumer who knows one endpoint can infer the shape of others.
- **Layered System means transparency.** API design must not depend on the client knowing infrastructure details.

### Resource Modeling

A **resource** is any concept the API exposes as a first-class addressable entity. Resources are nouns, not verbs.

#### How to Identify Resources

1. Start from the domain model: aggregates, entities, and significant value objects are natural candidates.
2. A resource has identity (a URI), state (a representation), and supported operations (HTTP methods).
3. Not every database table is a resource. Not every resource maps to a single table.

#### Resource Naming Rules

| Rule                           | Correct                | Wrong                                    |
| ------------------------------ | ---------------------- | ---------------------------------------- |
| Use nouns, never verbs         | `/orders`              | `/getOrders`                             |
| Use plural for collections     | `/customers`           | `/customer`                              |
| Use lowercase with hyphens     | `/order-items`         | `/orderItems`, `/OrderItems`             |
| Represent hierarchy with paths | `/customers/42/orders` | `/getCustomerOrders?id=42`               |
| Keep depth shallow (max 3)     | `/customers/42/orders` | `/customers/42/orders/7/items/3/reviews` |

#### Resource vs. Sub-resource vs. Relation

Use this decision tree:

1. **Does the entity exist independently?** (has its own lifecycle, can be created/deleted on its own)
   - Yes: Model it as a **top-level resource** (`/products`, `/customers`).
2. **Does the entity exist only in the context of a parent?** (created/deleted with the parent, no meaning alone)
   - Yes: Model it as a **sub-resource** (`/orders/42/line-items`).
3. **Is it an association between two independent resources?**
   - Yes: Model the relation as a **link endpoint** (`/users/42/roles` to manage user-role associations).
4. **Is it a computed view or cross-cutting query?**
   - Yes: Model it as a **dedicated read resource** (`/reports/monthly-sales`).

---

## 2. Endpoint Design

### URL Structure

```
/{api-prefix}/{version}/{resource}/{resource-id}/{sub-resource}/{sub-resource-id}
```

#### Structural Rules

- **API prefix:** Use a consistent prefix to separate the API namespace (e.g., `/api`).
- **Version segment:** Place the major version immediately after the prefix (e.g., `/api/v1`). See Section 5 for alternatives.
- **Resource segment:** Always plural nouns in lowercase kebab-case.
- **Identifier segment:** The unique identifier of a specific resource instance.
- **Sub-resource segment:** Nested resources that belong to the parent.
- **Maximum depth:** Do not exceed three levels of nesting. Beyond that, promote the deeply nested resource to a top-level resource and use query parameters to filter by parent.

#### Naming Conventions

| Convention               | Example                                          |
| ------------------------ | ------------------------------------------------ |
| Plural nouns             | `/invoices`, `/line-items`                       |
| Kebab-case (hyphenated)  | `/payment-methods`                               |
| No trailing slashes      | `/orders` not `/orders/`                         |
| No file extensions       | `/orders/42` not `/orders/42.json`               |
| No CRUD verbs in the URL | `DELETE /orders/42` not `POST /orders/42/delete` |

#### Action Endpoints (Exceptions)

For operations that do not map cleanly to CRUD, use a verb as the **last** segment:

```
POST /orders/42/cancel
POST /payments/99/refund
POST /accounts/7/lock
```

These are acceptable ONLY when the action represents a domain command that cannot be expressed as a state change via PUT/PATCH.

### HTTP Methods

| Method    | Semantics                        | Request Body | Response Body | Idempotent | Safe |
| --------- | -------------------------------- | ------------ | ------------- | ---------- | ---- |
| `GET`     | Read resource(s)                 | No           | Yes           | Yes        | Yes  |
| `POST`    | Create resource / trigger action | Yes          | Yes           | No         | No   |
| `PUT`     | Full replacement of resource     | Yes          | Yes           | Yes        | No   |
| `PATCH`   | Partial update of resource       | Yes          | Yes           | No\*       | No   |
| `DELETE`  | Remove resource                  | No           | Optional      | Yes        | No   |
| `HEAD`    | Same as GET, no body             | No           | No            | Yes        | Yes  |
| `OPTIONS` | Describe available methods       | No           | Yes           | Yes        | Yes  |

\*PATCH can be made idempotent if using merge-patch semantics, but is not guaranteed to be.

#### Idempotency Rules

- **Idempotent** means calling the same request N times produces the same result as calling it once.
- `GET`, `PUT`, `DELETE`, `HEAD`, `OPTIONS` MUST be idempotent.
- `POST` is NOT idempotent by default. To enable safe retries, implement idempotency keys (a client-generated unique token sent in a header).
- `PATCH` idempotency depends on implementation. Prefer merge-patch (RFC 7396) for predictable behavior.

#### Safety Rules

- **Safe** means the method does not modify server state.
- `GET`, `HEAD`, `OPTIONS` MUST be safe. They MUST NOT create, modify, or delete data.
- Never use `GET` to trigger side effects (sending emails, modifying records, incrementing counters).

#### Method Selection Decision Guide

1. **Retrieving data?** Use `GET`.
2. **Creating a new resource?** Use `POST` (server assigns ID) or `PUT` (client provides ID).
3. **Replacing an entire resource?** Use `PUT`. The request body must represent the complete resource.
4. **Updating specific fields?** Use `PATCH`. The request body contains only changed fields.
5. **Removing a resource?** Use `DELETE`.
6. **Triggering a non-CRUD operation?** Use `POST` to an action endpoint.
7. **Checking if a resource exists without fetching it?** Use `HEAD`.

---

## 3. Request Design

### Path Parameters vs. Query Parameters vs. Request Body

| Mechanism           | Use When                                             | Examples                                   |
| ------------------- | ---------------------------------------------------- | ------------------------------------------ |
| **Path parameter**  | Identifying a specific resource or sub-resource      | `/orders/42`, `/customers/7/addresses/3`   |
| **Query parameter** | Filtering, sorting, paginating, or selecting fields  | `?status=active&sort=-created_at&limit=20` |
| **Request body**    | Sending structured data for creation or modification | JSON payload on POST, PUT, PATCH           |

#### Rules

- Path parameters are ALWAYS required. They identify what you are operating on.
- Query parameters are ALWAYS optional (except for required filter on certain list endpoints). They modify how the result is returned.
- Never put sensitive data (passwords, tokens, secrets) in path or query parameters. These appear in server logs, browser history, and proxy caches.
- Request bodies are used with `POST`, `PUT`, and `PATCH`. Never send a body with `GET` or `DELETE`.

### Filtering

Filtering narrows a collection based on field values.

#### Conventions

| Pattern                  | Example                                               |
| ------------------------ | ----------------------------------------------------- |
| Equality                 | `?status=active`                                      |
| Multiple values (OR)     | `?status=active,pending`                              |
| Range (gt, gte, lt, lte) | `?created_at_gte=2025-01-01&created_at_lt=2025-02-01` |
| Negation                 | `?status_ne=cancelled`                                |
| Pattern match            | `?name_like=acme`                                     |

#### Rules

- Use the field name as the query parameter name.
- Use suffixes for operators: `_gt`, `_gte`, `_lt`, `_lte`, `_ne`, `_like`.
- Document which fields are filterable. Not every field should accept filters.
- Reject unknown filter parameters with `400 Bad Request` rather than silently ignoring them.

### Sorting

Sorting defines the order of results in a collection.

#### Conventions

| Pattern             | Example                      | Meaning                               |
| ------------------- | ---------------------------- | ------------------------------------- |
| Ascending (default) | `?sort=created_at`           | Oldest first                          |
| Descending          | `?sort=-created_at`          | Newest first                          |
| Multiple fields     | `?sort=-priority,created_at` | By priority desc, then created_at asc |

#### Rules

- Use a single `sort` parameter with comma-separated fields.
- Prefix with `-` for descending order.
- Document which fields are sortable.
- Define a deterministic default sort (e.g., `-created_at,id`) to ensure stable pagination.

### Pagination

Pagination limits the number of results returned per request.

#### Offset-Based Pagination

```
GET /orders?offset=40&limit=20
```

- **Pros:** Simple, supports jumping to arbitrary pages.
- **Cons:** Inconsistent results under concurrent writes (skipped or duplicate items). Degrades on large offsets (database must scan and discard rows).
- **Use when:** Data is relatively static, total count is needed, users need arbitrary page access.

#### Cursor-Based Pagination

```
GET /orders?cursor=eyJpZCI6NDJ9&limit=20
```

- **Pros:** Consistent results regardless of concurrent writes. Constant performance regardless of depth.
- **Cons:** Cannot jump to arbitrary pages. Cursor is opaque to the client.
- **Use when:** Data changes frequently, infinite scroll UIs, real-time feeds, large datasets.

#### Rules

- Always set a default and maximum `limit` (e.g., default 20, max 100).
- Return pagination metadata in the response (next cursor, total count if applicable, links to next/previous pages).
- Never return unbounded collections. Every list endpoint MUST paginate.

### Search

For full-text or complex search across multiple fields:

```
GET /orders/search?q=acme+widget&status=active&sort=-relevance
```

#### Rules

- Use a dedicated `/search` sub-path or a `q` parameter for free-text search.
- Combine search with standard filtering and sorting parameters.
- Return relevance scores when applicable.

### Input Validation Rules

- Validate at the API boundary, before the request reaches business logic.
- Return `400 Bad Request` for malformed requests (invalid JSON, wrong types, missing required fields).
- Return `422 Unprocessable Entity` for well-formed requests that violate business rules.
- Validate content types: reject requests with unexpected `Content-Type` headers.
- Enforce size limits on request bodies.
- Sanitize string inputs to prevent injection attacks.

---

## 4. Response Design

### HTTP Status Codes

#### 2xx Success

| Code  | Name       | When to Use                                                               |
| ----- | ---------- | ------------------------------------------------------------------------- |
| `200` | OK         | Successful GET, PUT, PATCH, or DELETE that returns a body                 |
| `201` | Created    | Successful POST that creates a resource. Include `Location` header        |
| `202` | Accepted   | Request accepted for asynchronous processing. Processing not complete yet |
| `204` | No Content | Successful DELETE or PUT/PATCH that returns no body                       |

#### 3xx Redirection

| Code  | Name               | When to Use                                            |
| ----- | ------------------ | ------------------------------------------------------ |
| `301` | Moved Permanently  | Resource has a new permanent URI                       |
| `304` | Not Modified       | Conditional GET: resource unchanged since last request |
| `307` | Temporary Redirect | Temporary redirect preserving method                   |
| `308` | Permanent Redirect | Permanent redirect preserving method                   |

#### 4xx Client Errors

| Code  | Name                   | When to Use                                                        |
| ----- | ---------------------- | ------------------------------------------------------------------ |
| `400` | Bad Request            | Malformed syntax, invalid parameters, missing required fields      |
| `401` | Unauthorized           | Missing or invalid authentication credentials                      |
| `403` | Forbidden              | Authenticated but insufficient permissions                         |
| `404` | Not Found              | Resource does not exist at the given URI                           |
| `405` | Method Not Allowed     | HTTP method not supported on this endpoint. Include `Allow` header |
| `409` | Conflict               | Request conflicts with current state (duplicate, version mismatch) |
| `410` | Gone                   | Resource existed but has been permanently removed                  |
| `415` | Unsupported Media Type | Request content type not supported                                 |
| `422` | Unprocessable Entity   | Valid syntax but semantic validation failure (business rules)      |
| `429` | Too Many Requests      | Rate limit exceeded. Include `Retry-After` header                  |

#### 5xx Server Errors

| Code  | Name                  | When to Use                                                            |
| ----- | --------------------- | ---------------------------------------------------------------------- |
| `500` | Internal Server Error | Unhandled server exception. Never leak stack traces                    |
| `502` | Bad Gateway           | Upstream service returned invalid response                             |
| `503` | Service Unavailable   | Server temporarily overloaded or in maintenance. Include `Retry-After` |
| `504` | Gateway Timeout       | Upstream service did not respond in time                               |

#### Status Code Selection Rules

- Use the most specific code applicable. Prefer `409 Conflict` over generic `400 Bad Request` for duplicate resources.
- Never return `200 OK` with an error payload. Use proper 4xx/5xx codes.
- Never return `500` for client errors. A bad input is always 4xx.
- Always return `404` for missing individual resources, never an empty `200`.
- For collections, return `200` with an empty array when no results match, not `404`.

### Response Envelope

Use a consistent wrapper structure for all responses.

#### Single Resource Response

```
{
  "data": {
    "id": "ord-42",
    "type": "order",
    "attributes": { ... }
  },
  "meta": {
    "request_id": "req-abc123",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

#### Collection Response

```
{
  "data": [
    { "id": "ord-42", ... },
    { "id": "ord-43", ... }
  ],
  "meta": {
    "total_count": 142,
    "page_size": 20,
    "current_page": 3,
    "request_id": "req-abc123"
  },
  "links": {
    "self": "/api/v1/orders?page=3&limit=20",
    "next": "/api/v1/orders?page=4&limit=20",
    "prev": "/api/v1/orders?page=2&limit=20",
    "first": "/api/v1/orders?page=1&limit=20",
    "last": "/api/v1/orders?page=8&limit=20"
  }
}
```

#### Rules

- Always wrap responses in a consistent envelope. Do not return naked arrays or objects at the top level.
- The `data` field contains the primary response payload.
- The `meta` field contains metadata about the response (request ID, timestamps, pagination info).
- The `links` field contains navigational hypermedia links (for collections and related resources).
- Include a `request_id` in every response for traceability and debugging.

### Error Response Structure

All error responses MUST follow a consistent structure with both machine-readable codes and human-readable messages.

```
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "The request contains invalid fields.",
    "details": [
      {
        "field": "email",
        "code": "INVALID_FORMAT",
        "message": "Must be a valid email address."
      },
      {
        "field": "age",
        "code": "OUT_OF_RANGE",
        "message": "Must be between 18 and 120."
      }
    ],
    "request_id": "req-abc123",
    "documentation_url": "https://api.example.com/docs/errors/VALIDATION_FAILED"
  }
}
```

#### Error Response Rules

- **`code`**: A stable, machine-readable string (UPPER_SNAKE_CASE). Clients use this for programmatic handling. Never change these once published.
- **`message`**: A human-readable explanation. May change across versions. Intended for developers, not end users.
- **`details`**: An array of field-level errors for validation failures. Each entry includes the field path, a specific error code, and a message.
- **`request_id`**: Correlates with server-side logs for debugging.
- **`documentation_url`**: Optional link to documentation about this error type.
- Never expose internal implementation details (stack traces, SQL queries, internal service names) in error responses.
- Use the same error structure for all 4xx and 5xx responses. Consistency helps clients implement a single error-handling path.

---

## 5. Versioning

### Strategies

| Strategy                  | Mechanism                             | Example                                 |
| ------------------------- | ------------------------------------- | --------------------------------------- |
| **URL versioning**        | Version in the URL path               | `/api/v1/orders`                        |
| **Header versioning**     | Custom request header                 | `API-Version: 2`                        |
| **Media type versioning** | Version in Accept/Content-Type header | `Accept: application/vnd.myapi.v2+json` |
| **Query parameter**       | Version as a query parameter          | `/api/orders?version=2`                 |

### Tradeoffs

| Strategy                  | Pros                                           | Cons                                                   |
| ------------------------- | ---------------------------------------------- | ------------------------------------------------------ |
| **URL versioning**        | Simple, visible, easy to route, cache-friendly | Pollutes the URI space, implies different resources    |
| **Header versioning**     | Clean URLs, separates content from versioning  | Less discoverable, harder to test in browser           |
| **Media type versioning** | Most RESTful, fine-grained control             | Complex, poor tooling support                          |
| **Query parameter**       | Simple, visible                                | Harder to route, pollutes query string, caching issues |

### Decision Guidelines

- **Default choice:** URL versioning (`/api/v1/...`). It is the most widely understood, easiest to implement, and best supported by API gateways, documentation tools, and caching infrastructure.
- **Use header versioning** when you need to maintain a single URI space and your clients are sophisticated enough to set custom headers.
- **Use media type versioning** when you need per-resource version granularity and are building a hypermedia API.
- **Avoid query parameter versioning.** It combines the worst tradeoffs of URL and header versioning.

### Versioning Rules

- Version only at the major level. Minor and patch changes should be backward-compatible.
- A new major version is required ONLY when you introduce a breaking change (removing fields, changing response structure, altering method semantics).
- Support at most two major versions simultaneously (current and previous). Publish a deprecation timeline.
- Adding new optional fields, new endpoints, or new query parameters is NOT a breaking change.
- Removing fields, renaming fields, changing field types, or removing endpoints IS a breaking change.

---

## 6. Security Principles

### Authentication vs. Authorization

| Concept            | Question it answers           | Where it happens                  |
| ------------------ | ----------------------------- | --------------------------------- |
| **Authentication** | "Who are you?"                | Before any endpoint logic         |
| **Authorization**  | "Are you allowed to do this?" | At the endpoint or resource level |

#### Authentication Rules

- Use standard mechanisms: Bearer tokens (OAuth 2.0 / JWT), API keys, or mutual TLS.
- Tokens belong in the `Authorization` header, never in the URL.
- Return `401 Unauthorized` when credentials are missing or invalid.
- Do not distinguish between "no credentials" and "bad credentials" in the response. Both return `401` to prevent credential enumeration.

#### Authorization Rules

- Return `403 Forbidden` when the user is authenticated but lacks permission.
- Implement authorization at the resource level, not just the endpoint level. A user may access `/orders` but only see their own orders.
- Never rely on client-side authorization checks. Always enforce on the server.

### Principle of Least Privilege

- Each API consumer (user, service, API key) should have access to only the endpoints and resources required for its function.
- Scope API keys and tokens narrowly: read-only keys should not allow writes.
- Default to deny. Explicitly grant access rather than explicitly restricting it.
- Use role-based or attribute-based access control. Avoid ad-hoc permission checks scattered through the code.

### Sensitive Data Exposure Prevention

| Rule                                     | Rationale                                                     |
| ---------------------------------------- | ------------------------------------------------------------- |
| Never return passwords, secrets, or keys | Even hashed passwords should not appear in API responses      |
| Never log sensitive request data         | Tokens, credentials, PII must be redacted from logs           |
| Never include sensitive data in URLs     | URLs appear in server logs, browser history, referrer headers |
| Use HTTPS exclusively                    | Unencrypted traffic exposes all data in transit               |
| Implement rate limiting                  | Prevents brute-force attacks and abuse                        |
| Set appropriate CORS policies            | Restrict which origins can call the API                       |
| Return minimal data                      | Only include fields the client actually needs                 |
| Use response field filtering             | Allow `?fields=id,name` to limit exposed attributes           |

### Security Headers

Every API response SHOULD include:

- `X-Content-Type-Options: nosniff` -- Prevent MIME-type sniffing.
- `X-Frame-Options: DENY` -- Prevent clickjacking.
- `Strict-Transport-Security` -- Enforce HTTPS.
- `Cache-Control: no-store` -- For responses containing sensitive data.
- `X-Request-ID` -- For tracing and debugging.

---

## 7. Contract and Documentation Standards

### OpenAPI / Swagger Structure

Every API MUST have a machine-readable contract defined using OpenAPI Specification (v3.0+).

#### Required Sections

| Section      | Purpose                                                           |
| ------------ | ----------------------------------------------------------------- |
| `info`       | API title, version, description, contact, license                 |
| `servers`    | Base URLs for each environment (dev, staging, production)         |
| `paths`      | Every endpoint with methods, parameters, request/response schemas |
| `components` | Reusable schemas, parameters, responses, security schemes         |
| `security`   | Default security requirements for all endpoints                   |
| `tags`       | Logical grouping of endpoints by domain concept                   |

#### Documentation Rules

- Every endpoint MUST have a summary (short) and description (detailed).
- Every parameter MUST have a description, type, and required/optional indicator.
- Every response code MUST be documented with its schema and an example.
- Every request body MUST have a schema with field descriptions and validation constraints.
- Use `tags` to group endpoints by domain concept (Orders, Customers, Payments), not by technical layer.

### Schema Naming Conventions

Use clear, consistent names for request and response schemas (DTOs).

| Pattern                    | Example                         |
| -------------------------- | ------------------------------- |
| Create request             | `CreateOrderRequest`            |
| Update request (full)      | `UpdateOrderRequest`            |
| Update request (partial)   | `PatchOrderRequest`             |
| Response (single)          | `OrderResponse`                 |
| Response (collection item) | `OrderSummaryResponse`          |
| Response (detailed)        | `OrderDetailResponse`           |
| Query parameters object    | `ListOrdersQuery`               |
| Enum type                  | `OrderStatus`                   |
| Embedded object            | `Address`, `Money`, `DateRange` |

#### Naming Rules

- Suffix request schemas with `Request`.
- Suffix response schemas with `Response`.
- Do NOT use generic names like `OrderDTO`, `OrderModel`, `OrderPayload`.
- Separate read and write models. The create request schema and the response schema are rarely identical.
- Shared value types (Address, Money, Coordinate) need no Request/Response suffix.

### Consistency Rules Across the API Surface

- **Same resource, same shape.** An `Order` returned from `GET /orders/42` must have the same structure as each item in `GET /orders` (or a documented subset).
- **Same conventions everywhere.** If one endpoint uses `created_at` as a timestamp field, all endpoints must use `_at` suffix for timestamps.
- **Same error format everywhere.** Every error response follows the same structure regardless of the endpoint.
- **Same pagination format everywhere.** All collection endpoints use the same pagination parameters and response metadata.
- **Same naming case everywhere.** Pick one (snake_case is recommended for JSON) and apply it to all field names across all endpoints.
- **Same date format everywhere.** Use ISO 8601 (`2025-01-15T10:30:00Z`) for all date-time fields.
- **Same ID format everywhere.** If using UUIDs, use them for all resources. If using integer IDs, be consistent.

---

## 8. Common Anti-Patterns

### Chatty APIs

**Problem:** Requiring multiple round trips to accomplish a single logical operation.

**Symptoms:**

- Client must call `GET /users/42`, then `GET /users/42/preferences`, then `GET /users/42/recent-orders` to render a single page.
- N+1 request patterns where a list endpoint returns IDs and the client must fetch each related resource individually.

**Solutions:**

- Design compound responses that include related data.
- Support field expansion (`?include=preferences,recent_orders` or `?expand=items.product`).
- Create purpose-built read endpoints for common access patterns.

### Over-Fetching

**Problem:** Returning far more data than the client needs.

**Symptoms:**

- Every endpoint returns every field of the resource, including large nested objects.
- Mobile clients receive the same massive payload as desktop dashboards.

**Solutions:**

- Support sparse fieldsets (`?fields=id,name,status`).
- Provide summary vs. detail variants of resources (`OrderSummaryResponse` vs. `OrderDetailResponse`).
- Do not embed large related objects by default; use links or opt-in expansion.

### Under-Fetching

**Problem:** Returning too little data, forcing clients to make additional requests.

**Symptoms:**

- Response contains only IDs for related resources, no inline data.
- No way to request embedded resources in a single call.

**Solutions:**

- Include commonly needed related data by default.
- Support `?include` or `?expand` parameters for optional embedding.
- Balance between over-fetching and under-fetching based on known client needs.

### Verb-Based URLs

**Problem:** Using verbs in endpoint paths instead of leveraging HTTP methods.

**Examples of violations:**

- `POST /createOrder` instead of `POST /orders`
- `GET /getOrderById?id=42` instead of `GET /orders/42`
- `POST /deleteOrder` instead of `DELETE /orders/42`
- `POST /orders/42/updateStatus` instead of `PATCH /orders/42`

**Rule:** The HTTP method IS the verb. The URL identifies the noun (resource).

### Inconsistent Naming

**Problem:** Mixed conventions across the API surface.

**Examples of violations:**

- `/orders` (plural) vs. `/product` (singular)
- `created_at` vs. `updatedDate` vs. `deletion-time` in the same API
- `/api/v1/orders` vs. `/v2/products` vs. `/inventory/api/items`
- camelCase JSON fields in one endpoint, snake_case in another

**Rule:** Pick one convention for each dimension (pluralization, casing, date format, path structure) and enforce it everywhere.

### Leaking Internal Models

**Problem:** Exposing internal implementation details through the API.

**Examples of violations:**

- Database column names appearing as API fields (`_internal_flag`, `created_by_fk`, `version_seq`)
- Internal service names in error messages ("UserServiceV2 returned null")
- Database IDs that reveal information (auto-incrementing integers that expose total count)
- Implementation-specific fields (`hibernate_lazy_load`, `__sqlalchemy_instance_state`)

**Rule:** The API contract is a public interface. Design it from the consumer's perspective, not from the database schema. Map between internal and external representations explicitly.

### Ignoring Idempotency

**Problem:** Non-idempotent operations that cause duplicate side effects on retry.

**Examples of violations:**

- Retrying a `POST /payments` creates a duplicate charge.
- Network timeout on `POST /orders` leaves the client unsure if the order was created.

**Solutions:**

- Accept an `Idempotency-Key` header on `POST` requests.
- Store the key server-side and return the cached response on duplicate requests.
- Design state transitions to be naturally idempotent when possible.

### Missing or Improper Pagination

**Problem:** Returning all results in a single response.

**Examples of violations:**

- `GET /logs` returns 500,000 records.
- No `limit`, `offset`, or `cursor` support on collection endpoints.
- Default page size of 1,000 or unlimited.

**Rule:** Every collection endpoint MUST support pagination with sensible defaults (20-50 items) and enforced maximums (100-200 items).

### Swallowing Errors

**Problem:** Returning `200 OK` for failures, embedding error information in the response body.

**Examples of violations:**

- `200 OK` with `{ "success": false, "error": "Not found" }`
- `200 OK` with `{ "data": null }` when the resource does not exist

**Rule:** Use proper HTTP status codes. `200` means success. Errors get 4xx or 5xx codes with the standard error envelope.

---

## Review Checklist

Before publishing any endpoint, verify:

- [ ] URL uses plural nouns, no verbs, kebab-case
- [ ] HTTP method matches the operation semantics
- [ ] Path parameters identify resources; query parameters filter/sort/paginate
- [ ] Request body schema is documented with validation rules
- [ ] All possible response status codes are documented
- [ ] Error responses use the standard envelope with machine-readable codes
- [ ] Pagination is implemented for all collection endpoints
- [ ] Authentication and authorization requirements are specified
- [ ] Sensitive data is not exposed in URLs, logs, or responses
- [ ] The endpoint is consistent with all other endpoints in naming, casing, and structure
- [ ] The OpenAPI specification is updated to reflect the new endpoint
- [ ] Idempotency is considered for non-safe methods
