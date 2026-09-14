# Bounded Contexts and Subdomains

> Sources:
> - [Domain-Driven Design: The Blue Book](https://www.domainlanguage.com/ddd/blue-book/) — Eric Evans (2003)
> - [DDD Resources](https://www.domainlanguage.com/ddd/) — Domain Language (Eric Evans)
> - [Bounded Context](https://martinfowler.com/bliki/BoundedContext.html) — Martin Fowler
> - [Domain Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html) — Martin Fowler
> - [Anti-Corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/acl.html) — AWS
> - [Domain Analysis for Microservices](https://learn.microsoft.com/en-us/azure/architecture/microservices/model/domain-analysis) — Microsoft

## Overview

Strategic DDD patterns help decompose large systems into manageable parts with clear boundaries. This guide answers: **"Where does one domain model stop and another begin?"**

**DDD is fundamentally collaborative.** The patterns below emerge from conversations, whiteboarding, and modeling sessions with domain experts—not from coding alone.

---

## Domain Discovery Techniques

### Event Storming

A workshop technique for discovering domain events, aggregates, and bounded contexts.

```
Orange sticky: Domain Event (past tense: "OrderPlaced")
Blue sticky: Command (imperative: "Place Order")
Yellow sticky: Aggregate (noun: "Order")
Pink sticky: External System / Policy
Purple sticky: Problem / Question
```

**Workshop flow:**
1. **Chaotic exploration** — Everyone adds events they know about
2. **Timeline ordering** — Arrange events chronologically
3. **Identify aggregates** — Group related events
4. **Find boundaries** — Where language changes = bounded context boundary
5. **Surface problems** — Mark unclear areas for follow-up

### Context Mapping Workshop

For existing systems, map how bounded contexts currently interact:
1. List all systems/services
2. Identify which team owns each
3. Draw relationships (upstream/downstream)
4. Label relationship types (ACL, Conformist, etc.)
5. Identify pain points in current integrations

---

## Ubiquitous Language

The foundation of DDD. A shared vocabulary between developers and domain experts that appears in:
- Code (class names, method names)
- Documentation
- Conversations
- UI labels

### Principles

1. **One language per bounded context** - Different contexts may use the same word differently
2. **Code reflects the language** - `Order.confirm()` not `Order.set_status("confirmed")`
3. **Evolve together** - When language changes, code changes

### Example

```
❌ Technical language:
   "Set the order entity's status field to 2 and insert a record"

✅ Ubiquitous language:
   "Confirm the order and record that it was confirmed"
```

```python
# ❌ Technical, not ubiquitous
class Order:
    def set_status(self, status: int) -> None:
        self.status = status


# ✅ Ubiquitous language
class Order:
    def confirm(self) -> None:
        if self.status != OrderStatusEnum.PENDING:
            raise OrderCannotBeConfirmedException(self.id)

        self.status = OrderStatusEnum.CONFIRMED
        self.confirmed_at = datetime.now(timezone.utc)
        self.add_domain_event(OrderConfirmed(self.id))
```

---

## Bounded Contexts

A **semantic boundary** where a particular domain model applies. Within a bounded context, terms have precise, unambiguous meaning.

> **Key insight:** Polysemy (same word, different meanings) across departments is natural, not a problem. The same term meaning different things in different contexts is expected—"the dominant boundary factor is human culture and language variation." — Martin Fowler

### Key Concepts

- Each bounded context has its **own ubiquitous language**
- Each bounded context has its **own model**
- The same real-world concept may have **different representations** in different contexts

### Example: E-Commerce System

```mermaid
flowchart TB
    subgraph ECommerce["E-Commerce System"]
        subgraph Sales["Sales Context"]
            SC1["Customer: id, email, preferences"]
            SC2["Order: items, total, status"]
        end
        subgraph Shipping["Shipping Context"]
            SH1["Recipient: name, address, phone"]
            SH2["Shipment: packages, carrier, trackingNo"]
        end
        subgraph Billing["Billing Context"]
            BC1["Payer: name, billingAddress, paymentMethod"]
            BC2["Invoice: lineItems, total, dueDate"]
        end
        subgraph Catalog["Catalog Context"]
            CC1["Product: name, description, price"]
            CC2["(no customer concept)"]
        end
    end

    style Sales fill:#3b82f6,stroke:#2563eb,color:white
    style Shipping fill:#10b981,stroke:#059669,color:white
    style Billing fill:#f59e0b,stroke:#d97706,color:white
    style Catalog fill:#8b5cf6,stroke:#7c3aed,color:white
```

**"Customer" means different things:**
- **Sales**: Email, preferences, order history
- **Shipping**: Delivery address, phone number
- **Billing**: Payment methods, billing address

### Bounded Context = Microservice Boundary

In microservices, each bounded context typically becomes a separate service:

```mermaid
flowchart LR
    subgraph Sales["Sales Service"]
        S1["Orders DB"]
        S2["Order API"]
    end
    subgraph Shipping["Shipping Service"]
        SH1["Shipments DB"]
        SH2["Shipping API"]
    end
    subgraph Billing["Billing Service"]
        B1["Invoices DB"]
        B2["Billing API"]
    end

    Sales -->|events| Shipping
    Shipping -->|events| Billing
    Sales -.->|Integration Events| Events[("Event Bus")]
    Shipping -.-> Events
    Billing -.-> Events

    style Sales fill:#3b82f6,stroke:#2563eb,color:white
    style Shipping fill:#10b981,stroke:#059669,color:white
    style Billing fill:#f59e0b,stroke:#d97706,color:white
```

---

## Subdomains

Areas of business expertise. Subdomains are **discovered**, not designed.

### Types

| Type | Description | Investment | Example |
|------|-------------|------------|---------|
| **Core** | Competitive advantage | High | Product recommendation engine |
| **Supporting** | Necessary but not unique | Medium | Order management |
| **Generic** | Commodity, buy/outsource | Low | Email sending, payments |

### Identification Questions

1. What makes us different from competitors? → **Core**
2. What do we need but isn't our specialty? → **Supporting**
3. What does everyone need the same way? → **Generic**

### Example: E-Commerce

```mermaid
flowchart TB
    subgraph Subdomains["Subdomains"]
        subgraph Core["CORE"]
            C1["Product search & recommendations"]
            C2["Pricing engine"]
            C3["Personalization"]
        end
        subgraph Supporting["SUPPORTING"]
            S1["Order management"]
            S2["Inventory"]
            S3["Customer support"]
            S4["Reporting"]
        end
        subgraph Generic["GENERIC"]
            G1["Authentication (Auth0)"]
            G2["Payments (Stripe)"]
            G3["Email (SendGrid)"]
            G4["File storage (S3)"]
        end
    end

    Core --> CoreStrat["Build in-house\nBest developers"]
    Supporting --> SuppStrat["Build or buy\nSolid but simple"]
    Generic --> GenStrat["Use third-party\nDon't reinvent"]

    style Core fill:#ef4444,stroke:#dc2626,color:white
    style Supporting fill:#f59e0b,stroke:#d97706,color:white
    style Generic fill:#6b7280,stroke:#4b5563,color:white
```

---
