# Context Mapping and Integration

> Sources:
> - [Domain-Driven Design: The Blue Book](https://www.domainlanguage.com/ddd/blue-book/) — Eric Evans (2003)
> - [DDD Resources](https://www.domainlanguage.com/ddd/) — Domain Language (Eric Evans)
> - [Bounded Context](https://martinfowler.com/bliki/BoundedContext.html) — Martin Fowler
> - [Domain Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html) — Martin Fowler
> - [Anti-Corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/acl.html) — AWS
> - [Domain Analysis for Microservices](https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis) — Microsoft

Use this guide after identifying genuine bounded contexts. It explains their upstream/downstream relationships and the translation, event, and contract boundaries that prevent one context's model from leaking into another.

## Context Mapping

Describes relationships between bounded contexts.

### Relationship Patterns

#### Partnership
Two contexts succeed or fail together. Teams coordinate closely.

```mermaid
flowchart LR
    A["Context A"] <-->|"Partnership\nJoint planning\nShared success"| B["Context B"]

    style A fill:#3b82f6,stroke:#2563eb,color:white
    style B fill:#3b82f6,stroke:#2563eb,color:white
```

#### Shared Kernel
Two contexts share a subset of the domain model.

```mermaid
flowchart LR
    subgraph A["Context A"]
        SK["Shared Kernel"]
    end
    subgraph B["Context B"]
        B1[" "]
    end

    SK <-->|shared| B

    style A fill:#3b82f6,stroke:#2563eb,color:white
    style B fill:#10b981,stroke:#059669,color:white
    style SK fill:#f59e0b,stroke:#d97706,color:white
```

**Warning:** Shared kernels create coupling. Use sparingly.

#### Customer-Supplier
Upstream context provides what downstream needs.

```mermaid
flowchart LR
    U["Upstream\n(Supplier)"] -->|"Provides API"| D["Downstream\n(Customer)"]

    style U fill:#3b82f6,stroke:#2563eb,color:white
    style D fill:#10b981,stroke:#059669,color:white
```

#### Conformist
Downstream conforms to upstream's model with no negotiation power.

```mermaid
flowchart LR
    U["Upstream\n(Dictator)"] -->|"Take it or leave it"| D["Downstream\n(Conformist)\nUses their model"]

    style U fill:#ef4444,stroke:#dc2626,color:white
    style D fill:#6b7280,stroke:#4b5563,color:white
```

**Example:** Integrating with a third-party API (Stripe, AWS).

#### Anti-Corruption Layer (ACL)
Translation layer protecting your model from external models.

```mermaid
flowchart LR
    Ext["External\nContext"] --> ACL["ACL\nTranslator + Adapter"]
    ACL --> Your["Your\nContext"]

    ACL -.->|"Translates external\nmodel to your model"| Note[" "]

    style Ext fill:#ef4444,stroke:#dc2626,color:white
    style ACL fill:#f59e0b,stroke:#d97706,color:white
    style Your fill:#10b981,stroke:#059669,color:white
    style Note fill:none,stroke:none
```

**Use when:**
- Integrating with legacy systems
- Integrating with third-party APIs
- External model is messy or poorly designed

```python
# Anti-Corruption Layer Example
# infrastructure/external/stripe/stripe_payment_acl.py

import stripe
from typing import Protocol


class StripePaymentACL:
    def __init__(self, stripe_client: stripe.StripeClient):
        self._stripe = stripe_client

    async def create_payment(self, payment: Payment) -> str:
        """Translates domain Payment to Stripe PaymentIntent."""
        payment_intent = await self._stripe.payment_intents.create(
            amount=payment.amount.cents,
            currency=payment.amount.currency.lower(),
            metadata={
                "order_id": payment.order_id.value,
                "customer_id": payment.customer_id.value,
            },
        )
        return payment_intent.id

    def translate_status(self, stripe_status: str) -> PaymentStatusEnum:
        """Translates Stripe status to domain PaymentStatusEnum."""
        mapping = {
            "requires_payment_method": PaymentStatusEnum.PENDING,
            "requires_confirmation": PaymentStatusEnum.PENDING,
            "requires_action": PaymentStatusEnum.PENDING,
            "processing": PaymentStatusEnum.PROCESSING,
            "succeeded": PaymentStatusEnum.COMPLETED,
            "canceled": PaymentStatusEnum.CANCELLED,
            "requires_capture": PaymentStatusEnum.AUTHORIZED,
        }
        return mapping.get(stripe_status, PaymentStatusEnum.UNKNOWN)

    def translate_webhook(self, event: stripe.Event) -> DomainEvent | None:
        """Translates Stripe webhook to domain event."""
        match event.type:
            case "payment_intent.succeeded":
                intent = event.data.object
                return PaymentCompleted(
                    payment_id=PaymentId(intent.metadata["order_id"]),
                    amount=Money.from_cents(intent.amount, intent.currency.upper()),
                )
            case "payment_intent.payment_failed":
                return None
            case _:
                return None
```

#### Open Host Service / Published Language
Expose a well-defined protocol for integration.

```mermaid
flowchart TB
    subgraph OHS["Open Host Service"]
        PL["Published Language\n(REST API, gRPC, Events Schema)"]
        BC["Your Bounded Context"]
    end

    PL --> A["Consumer A"]
    PL --> B["Consumer B"]
    PL --> C["Consumer C"]

    style OHS fill:#3b82f6,stroke:#2563eb,color:white
    style PL fill:#10b981,stroke:#059669,color:white
    style A fill:#6b7280,stroke:#4b5563,color:white
    style B fill:#6b7280,stroke:#4b5563,color:white
    style C fill:#6b7280,stroke:#4b5563,color:white
```

---

## Context Map Diagram

Visual representation of all bounded contexts and their relationships:

```mermaid
flowchart TB
    Identity["Identity Context\n(Generic - Auth0)"]
    Legacy["Legacy Catalog\n(Legacy)"]
    Sales["Sales Context\n(Core)"]
    Shipping["Shipping Context\n(Supporting)"]
    Billing["Billing Context\n(Supporting)"]
    Stripe["Stripe Gateway\n(Generic)"]

    Identity -->|Conformist| Sales
    Legacy -->|ACL| Sales
    Sales <-->|Customer-Supplier| Shipping
    Sales -->|Open Host Service| Billing
    Billing -->|Conformist| Stripe

    style Identity fill:#6b7280,stroke:#4b5563,color:white
    style Legacy fill:#9ca3af,stroke:#6b7280,color:white
    style Sales fill:#ef4444,stroke:#dc2626,color:white
    style Shipping fill:#f59e0b,stroke:#d97706,color:white
    style Billing fill:#f59e0b,stroke:#d97706,color:white
    style Stripe fill:#6b7280,stroke:#4b5563,color:white
```

---

## Integration Patterns

### Domain Events for Context Integration

```python
# application/integration_events/order_placed_event.py
from pydantic import BaseModel


class AddressSchema(BaseModel):
    street: str
    city: str
    postal_code: str
    country: str


class OrderItemSchema(BaseModel):
    product_id: str
    quantity: int
    price: float


class OrderPlacedEvent(BaseModel):
    event_type: str = "sales.order.placed"
    order_id: str
    customer_id: str
    items: list[OrderItemSchema]
    total: float
    shipping_address: AddressSchema
    occurred_at: str


# shipping/event_handlers/order_placed_handler.py
class ShippingOrderPlacedHandler:
    def __init__(self, shipment_repo: IShipmentRepository):
        self._shipment_repo = shipment_repo

    async def handle(self, event: OrderPlacedEvent) -> None:
        shipment = Shipment.create(
            order_id=ShipmentOrderId(event.order_id),
            recipient=Recipient.from_address(event.shipping_address),
            packages=self._calculate_packages(event.items),
        )
        await self._shipment_repo.save(shipment)


# billing/event_handlers/order_placed_handler.py
class BillingOrderPlacedHandler:
    def __init__(self, invoice_repo: IInvoiceRepository):
        self._invoice_repo = invoice_repo

    async def handle(self, event: OrderPlacedEvent) -> None:
        invoice = Invoice.create(
            order_id=InvoiceOrderId(event.order_id),
            customer_id=BillingCustomerId(event.customer_id),
            line_items=[
                LineItem(
                    description=f"Product {item.product_id}",
                    quantity=item.quantity,
                    unit_price=Money.from_float(item.price),
                )
                for item in event.items
            ],
            total=Money.from_float(event.total),
        )
        await self._invoice_repo.save(invoice)
```

### Event Schema Registry

Define and version integration event schemas:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://api.company.com/events/sales/order-placed/v1.json",
  "title": "OrderPlaced",
  "description": "Published when an order is successfully placed",
  "type": "object",
  "required": ["eventType", "eventId", "orderId", "occurredAt"],
  "properties": {
    "eventType": { "const": "sales.order.placed" },
    "eventId": { "type": "string", "format": "uuid" },
    "orderId": { "type": "string", "format": "uuid" },
    "customerId": { "type": "string", "format": "uuid" },
    "total": { "type": "number", "minimum": 0 },
    "occurredAt": { "type": "string", "format": "date-time" }
  }
}
```

---

## Strategic Design Checklist

- [ ] Identify ubiquitous language terms with domain experts
- [ ] Map subdomains (core, supporting, generic)
- [ ] Define bounded context boundaries
- [ ] Document context map with relationships
- [ ] Design anti-corruption layers for external systems
- [ ] Define integration event schemas
- [ ] Ensure each context has its own data store
