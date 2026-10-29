# Types, validation, and generics

## Records, absence, and alternatives

Use readonly type aliases for data and interfaces for behavioral ports. An absent
property, a present undefined value, and a null value may mean different things.
With exact optional properties, `label?: string` allows omission, not assignment of
undefined. Add `| undefined` only when explicit undefined has meaning. Use null for
an explicit domain/API empty value; do not indiscriminately mix null and undefined.

```ts
type Rename = Readonly<{ label?: string }>;
const unchanged: Rename = {};
const renamed: Rename = { label: 'Ada' };
// Incorrect: const ambiguous: Rename = { label: undefined };

type LoadState<T> =
  | Readonly<{ status: 'idle' }>
  | Readonly<{ status: 'ready'; value: T }>
  | Readonly<{ status: 'failed'; message: string }>;

function assertNever(value: never): never {
  throw new Error(`Unexpected variant: ${String(value)}`);
}

function message(state: LoadState<string>): string {
  switch (state.status) {
    case 'idle': return 'Waiting';
    case 'ready': return state.value;
    case 'failed': return state.message;
    default: return assertNever(state);
  }
}
```

Do not replace mutually exclusive states with isLoading/isError/data flags. Prefer
literal unions to new enums; keep generated and public compatibility enums where an
existing contract requires them. Do not introduce const enums into published contracts.

## Unknown at the edge

```ts
type User = Readonly<{ id: string; name: string }>;

function parseUser(value: unknown): User {
  if (typeof value !== 'object' || value === null
      || !('id' in value) || typeof value.id !== 'string'
      || !('name' in value) || typeof value.name !== 'string') {
    throw new TypeError('Invalid user payload');
  }
  return { id: value.id, name: value.name };
}

function parseUserJson(text: string): User {
  const value: unknown = JSON.parse(text);
  return parseUser(value);
}

// Wrong: return JSON.parse(text) as User;
// Wrong: function decode<T>(text: string): T { return JSON.parse(text); }
```

Use the project's schema validator for complex/nested payloads, including element types,
required fields, ranges, and domain invariants. The simple example projects just its
supported fields; decide deliberately whether a real contract rejects extra fields.
JSON parsing proves syntax only. Validate storage, network, environment, command-line,
and message data before assigning domain types. A predicate's declared `value is T`
must be backed by complete checks, not merely a cast. Unknown arrays need each element
checked; Array.isArray alone does not prove the element type.

An assertion function must throw if its condition fails. Assertion syntax, `satisfies`,
and generic arguments perform no runtime checking. `as unknown as T`, `value!`, and
`field!: T` are not acceptable ways to avoid proving an invariant.

## Literal tables and derived contracts

```ts
type RetryPolicy = Readonly<{ attempts: number; delayMs: number }>;
const RETRY_POLICIES = {
  interactive: { attempts: 1, delayMs: 0 },
  background: { attempts: 3, delayMs: 250 },
} as const satisfies Record<'interactive' | 'background', RetryPolicy>;
type RetryMode = keyof typeof RETRY_POLICIES;
```

This literal-table form is an explicit exception to variable annotations: preserving
literal keys/values is the purpose. Do not annotate it as a broad string index record
and then cast back to regain information. `as const` is not deep runtime freezing.

## Generics and utility types

```ts
function getProperty<TObject, TKey extends keyof TObject>(
  value: TObject,
  key: TKey,
): TObject[TKey] {
  return value[key];
}

type Page<TItem> = Readonly<{
  items: readonly TItem[];
  nextCursor: string | null;
}>;

type UserSummary = Pick<User, 'id' | 'name'>;
```

A generic should relate values or preserve meaningful type information. A generic that
appears only in a claimed return type usually hides a missing parser or unsafe cast.
Constrain what operations require, not more. Prefer a concrete domain type when there
is no real variation. Avoid a universal Repository<T> that erases domain operations.

Use Pick/Omit when the derived contract intentionally tracks its source. Define a
separate command when it has distinct semantics; `Partial<Entity>` is rarely a precise
update command. Mapped/conditional/template-literal types must simplify a real public
contract and include a readable name and type tests. Do not introduce recursive type
machinery for an ordinary runtime check. Remember conditional distribution over unions;
wrap operands in tuples when testing a whole union is the intended behavior.

Use brands only when confusing structurally identical values is a demonstrated risk.
Centralize their validated construction and justify the one necessary assertion there;
never brand unchecked input at each call site. A brand is not runtime validation.
