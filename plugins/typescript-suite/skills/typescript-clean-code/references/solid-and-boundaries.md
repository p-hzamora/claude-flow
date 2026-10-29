# SOLID in TypeScript

## Single responsibility

Separate code when it changes for different reasons: payload decoding changes with
transport; business eligibility changes with policy; persistence changes with storage.
Do not impose a file or class per function. A cohesive operation can remain small.
Keep side effects out of names that imply harmless queries or predicates.

## Open/closed

Add a composition seam when there are real alternative behaviors. A callable strategy
is often sufficient; avoid switch statements spread throughout consumers and avoid a
plugin registry for one case.

```ts
type ShippingCost = (weightGrams: number) => number;

function quoteTotal(
  subtotalMinor: number,
  weightGrams: number,
  shippingCost: ShippingCost,
): number {
  return subtotalMinor + shippingCost(weightGrams);
}
```

Changing a business rule may legitimately require editing code. Open/closed does not
mean anticipating every future requirement or banning ordinary maintenance.

## Liskov substitution

A structural type match is not enough. An implementation must accept the documented
inputs, preserve output meaning, avoid unexpected mutation, and honor failure/lifecycle
semantics. A read-only implementation of a read/write repository that throws on every
write violates the promised behavior. Split capabilities instead. Test different
implementations against the same behavioral contract, including absence and errors.
Avoid narrowing accepted input domains in a subclass or making previously optional
side effects mandatory. Prefer composition over inheritance for unrelated behavior.

## Interface segregation

```ts
type Customer = Readonly<{ id: string; name: string }>;

interface CustomerReader {
  readonly findById: (id: string) => Promise<Customer | null>;
}

interface CustomerWriter {
  readonly save: (customer: Customer) => Promise<void>;
}
```

A display operation should receive CustomerReader, not a service exposing billing,
mutation, and administration. Do not add one-method interfaces around every helper;
use a function type when a callable is the full useful contract.

## Dependency inversion

```ts
type RegisterInput = Readonly<{ id: string; name: string }>;

/** Register a customer using the caller's persistence capability. */
async function registerCustomer(
  input: RegisterInput,
  writer: CustomerWriter,
): Promise<Customer> {
  const name: string = input.name.trim();
  if (name.length === 0) {
    throw new RangeError('A name is required');
  }
  const customer: Customer = { id: input.id, name };
  await writer.save(customer);
  return customer;
}
```

The consumer's business contract does not expose a database client, fetch Response,
or framework Request object. An adapter translates those concerns; bootstrap constructs
it and supplies it. A global locator hides dependencies and complicates test isolation.
Passing a narrow function or object is sufficient; a container is not required.

## Clean code and refactoring choices

Use names from the domain, explicit units, guard clauses, and a single level of
abstraction within an operation. Split a function when its responsibilities or
invariants become difficult to describe, not at an arbitrary line count. Keep related
code together and public APIs small. Introduce a shared abstraction when semantics and
ownership align, not just when two blocks look similar.

Separate transport DTOs from domain values when they differ in meaning or invariants.
Do not serialize a class instance and assume its private invariants survive JSON.
Use a validated factory for invariant-bearing values; do not force all records into
classes. Make time, randomness, and I/O injectable at the boundary when deterministic
behavior matters. Prefer testing a pure policy over mocking its internal steps.

For review, cite a concrete file/line, violated contract, consequence, and minimal fix.
Do not report taste as a correctness defect. For implementation, make the smallest
coherent change, run the relevant checks, and disclose any remaining design debt.
