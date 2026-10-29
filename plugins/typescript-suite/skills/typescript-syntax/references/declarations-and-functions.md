# Declarations, functions, and documentation

## Naming and explicit variables

```ts
// Correct: named declarations carry contracts, even for primitive initializers.
const MAX_RETRY_COUNT: number = 3;
const customerName: string = 'Pablo';
const isActive: boolean = true;
let retryCount: number = 0;
const itemIds: readonly string[] = ['item-1'];
const labelsById: ReadonlyMap<string, string> = new Map<string, string>();

// Incorrect under this profile (some are legal TypeScript).
// const customerName = 'Pablo';         // missing explicit annotation
// var retryCount = 0;                  // var and implicit contract
// const name: String = 'Pablo';         // boxed primitive
// const IUser = {};                    // value named like an interface
```

Use descriptive business names. Boolean names normally start with is/has/can/should.
Avoid I-prefixed interfaces, T-prefixed ordinary types, and Class/Obj suffixes. Use
`T`, `TInput`, or `TResult` for generic parameters. Name units explicitly, for example
`timeoutMs`, `amountMinor`, or `createdAtIso`. Uppercase constants identify fixed named
limits or protocol values; a module-level dependency object is still camelCase.
Ordinary files use `order-repository.ts`; tests use the runner's established suffix.
Do not rename framework entry points to enforce a generic filename rule.

## Function contracts

```ts
type SendMessageOptions = Readonly<{
  recipientId: string;
  text: string;
  priority?: 'normal' | 'urgent';
}>;

function formatMessage({ text, priority = 'normal' }: SendMessageOptions): string {
  return `[${priority}] ${text}`;
}

type Normalize = (input: string) => string;
const normalize: Normalize = (input) => input.trim();
const lengths: readonly number[] = ['one', 'two'].map((value): number => value.length);

// Wrong: function normalize(input) { return input.trim(); }
// Wrong: sendMessage('user-1', 'hello', true, false); // opaque positional options
```

Prefer a direct parameter for one obvious value. Use an options object when several
similar primitives or flags make calls ambiguous, not for every single-argument helper.
Annotate optional/default parameters explicitly. Use `void` for an operation whose
return is not consumed, `undefined` when that exact value is the contract, and `never`
only for paths that cannot return normally. A `() => void` callback type can accept a
value-returning implementation; it does not prove the implementation returns nothing
or that passing an async callback is safe.

Use overloads only when call signatures genuinely differ and cannot be expressed
clearly with a union or generic. Keep overload implementations compatible with all
public signatures; implementation signatures are not additional public overloads.

## Collections and flow

Use `readonly T[]` at read-only boundaries and `T[]` for locally owned mutable arrays.
Use labeled readonly tuples for fixed-position values; ordinary arrays are not tuples.
Use `Map` for arbitrary keys and `Set` for membership. Do not use `Record<string, T>`
as proof every runtime string key exists. Handle missing indexed values.

```ts
function uniqueIds(ids: readonly string[]): readonly string[] {
  const seen: Set<string> = new Set<string>(ids);
  return [...seen];
}

function firstLabel(labels: readonly string[]): string {
  const label: string | undefined = labels[0];
  return label ?? 'Untitled';
}
```

Prefer guard clauses and `===`/`!==`. Use `??` for absent values when zero/false/empty
text is valid. Use map/filter for transformation and for...of for sequential effects;
never hide side effects in a chain of transformations. Sort a copy unless mutation
is explicitly owned. Readonly is shallow and compile-time; copy or freeze deliberately
when runtime aliasing matters. Avoid nested ternaries and multi-purpose callbacks.
Template strings are for textual composition, not SQL query construction; use bindings
for database values. Do not interpolate secrets into logs.

## Documentation and formatting

Follow the repository's configured formatter. For a new unconfigured project use
consistent two-space indentation, semicolons, single quotes, and trailing commas;
encode choices once in a formatter rather than policing whitespace manually.

```ts
/** Price calculations in minor currency units. */

/**
 * Apply a percentage discount without mutating the input amount.
 * @param amountMinor - Nonnegative safe-integer minor units.
 * @param discountPercent - A percentage between zero and one hundred.
 * @returns Rounded minor units after the discount.
 * @throws RangeError if inputs are outside the supported range.
 */
export function discountAmount(amountMinor: number, discountPercent: number): number {
  if (!Number.isSafeInteger(amountMinor) || amountMinor < 0
      || !Number.isFinite(discountPercent) || discountPercent < 0 || discountPercent > 100) {
    throw new RangeError('Invalid discount inputs');
  }
  return Math.round(amountMinor * (1 - discountPercent / 100));
}
```

Document rounding policy in real financial code; this example is not a currency model.
Exported types need a concise purpose/invariant comment, not redundant prose for every
obvious field. Internal comments explain decisions; remove misleading comments when
behavior changes. Do not annotate every local line with a narration of the syntax.
