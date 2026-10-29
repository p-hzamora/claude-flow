# Classes, interfaces, and modules

Use a class for lifecycle, identity, or an invariant with controlled mutation. Use
records and functions for plain data and transformations. Do not mimic Python
inheritance or decorators mechanically in TypeScript.

```ts
/** Read capability needed by the consumer; no write operations are exposed. */
interface NameReader {
  readonly read: (id: string) => Promise<string | null>;
}

/** Resolves a display name through an injected read capability. */
class DisplayNameService {
  private readonly reader: NameReader;

  public constructor(reader: NameReader) {
    this.reader = reader;
  }

  public async resolve(id: string): Promise<string> {
    const name: string | null = await this.reader.read(id);
    return name ?? 'Unknown';
  }
}
```

Annotate fields, constructor parameters, and method results. Use explicit visibility
for class members. `private` is compile-time access control; choose `#private` when
runtime privacy is needed and supported. Neither encrypts data. Do not introduce
underscore prefixes in place of actual visibility. Mark stable dependencies readonly.
Avoid parameter properties when they violate an erase-only execution pipeline; explicit
fields and constructor assignment work across more environments.

Initialize fields in declarations or constructors; do not bypass initialization with
`!`. Use a factory for asynchronous construction, not an async constructor. `override`
must mark overrides when inheritance is necessary. Preserve the base contract;
`implements` checks shape, not behavioral correctness. Function-valued port properties
benefit from strict function parameter variance; method signatures have different
variance behavior. Keep callbacks from accidentally losing `this`; use a deliberate
bound wrapper or a field callback when needed.

## Imports and exports

```ts
// Illustrative file boundary; imported files must exist in the target project.
import type { Order } from './order.js';
import { parseOrder } from './parse-order.js';
export type { Order } from './order.js';
export { parseOrder } from './parse-order.js';
```

The `.js` specifier is suitable for TS compiled to Node ESM. A bundler or supported
TypeScript runtime may require a different convention: match the execution path,
not a universal import suffix rule. Use `node:` for Node built-ins. Group built-ins,
third-party imports, then local imports when not overridden by the project's sorter.
Separate type-only imports, avoid import cycles, and do not import through your own
public barrel from internal files. Public indexes explicitly list supported exports.

Prefer named exports. Framework-mandated default entry points are allowed. Side-effect
imports (styles, polyfills, registration) must be deliberate and owned by bootstrap;
do not remove them while converting imports to type-only syntax. Do not turn everything
into a barrel or create an alias without configuring runtime/test resolution.

New projects use ES modules unless the host requires otherwise. Existing CommonJS
compatibility is not permission for an incidental ESM migration. Distinguish package
`type`, emitted syntax, moduleResolution, file extensions, and export conditions.
Browser, Node, and dual-runtime library code have different APIs and declarations.
Do not include DOM types in a Node-only package to hide an incorrect dependency.
Do not introduce namespaces, new decorators, or runtime-emitting syntax without an
actual integration requirement and a compatible compiler/runtime pipeline.
