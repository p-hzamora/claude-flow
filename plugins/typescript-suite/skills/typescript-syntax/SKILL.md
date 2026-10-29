---
name: typescript-syntax
description: Proactively apply when writing or reviewing TypeScript, including TSX, Node services, libraries, and scripts. Enforces explicit typing, naming, imports, nullability, generics, classes, async/error handling, and documentation conventions. Single source of truth for TypeScript language rules; independent of React and folder architecture.
---

# TypeScript syntax and conventions

This is the mandatory TypeScript coding profile for authored or changed code, analogous
to `python-syntax`. It is a project convention, not a claim that TypeScript requires
this style. User instructions and explicit repository rules take precedence; identify
conflicts instead of silently selecting the weaker rule. Do not reformat unrelated
legacy code or edit generated/vendor files just to apply this skill.

## Application procedure

1. Inspect package.json, the lockfile, tsconfig inheritance, runtime, and lint/format
   configuration. Establish the installed compiler and module system.
2. Apply the hard rules below. Read the reference for every language area being changed;
   the examples and exception conditions there are normative, not optional inspiration.
3. Use [typescript-clean-code](../typescript-clean-code/SKILL.md) for responsibility,
   dependency, and SOLID decisions; language rules stay here.
4. Run the project's actual type check, lint, and relevant tests. Review the semantic
   rules not covered by tools. Report command results and deviations separately.

## Hard rules

| Area | Required convention |
|---|---|
| Typing | Annotate named variables, properties, function parameters, and function/method return types. Explicit `Promise<T>` for async functions and `void` for no result. See the narrow exceptions below. |
| Safety | No explicit `any`, double casts, non-null assertions, definite-assignment assertions, `@ts-ignore`, or disabled strictness to make authored code compile. Validate unknown input. |
| Naming | camelCase values/functions/methods; PascalCase types/classes; UPPER_SNAKE_CASE module constants with fixed configuration/domain meaning; kebab-case ordinary `.ts` files. Framework-required filenames and TSX component filenames retain their established conventions. |
| Values | `const` by default, `let` only for reassignment, never `var`. Primitive types, never boxed `String`, `Number`, `Boolean`, `Object`, or broad `Function`. |
| Contracts | `type` for records, unions, and aliases; `interface` for behavioral ports or intentional extension. Readonly input records/collections by default; mutation must have an explicit owner. |
| Functions | Named options objects for ambiguous multi-parameter calls. No unexplained boolean switches or positional primitive puzzles. Prefer named function declarations for named operations. |
| Alternatives | Literal unions/discriminated unions rather than new enums or contradictory flags. Exhaustive switches end in a checked `never` branch. |
| Modules | Named exports and `import type`; explicit public exports, no wildcard re-export trees. Required framework default exports and intentional side-effect imports are exceptions. |
| Async | Every promise is awaited, returned, or handled through a deliberate rejection path. Bare `void promise` is not error handling. |
| Errors | Throw Error objects, catch `unknown`, preserve causes where supported; use explicit result unions for expected business outcomes when appropriate. |
| Documentation | A short responsibility comment for authored modules and TSDoc for exported contracts/operations; document invariants, units, mutation, failures, and cancellation rather than restating types. |

### Explicit typing exceptions — closed list

- Inline callbacks may use contextual parameter types when the receiving typed API
  supplies them; annotate callback returns unless an explicit function type already
  supplies the whole signature. Extracted named callbacks require explicit contracts.
- Destructuring, catch bindings, and `for...of`/`for...in` bindings use the typed source
  or `unknown` catch semantics where per-binding annotations are illegal or misleading.
  Annotate the source/options contract instead; never force `any`.
- Literal tables may use `as const satisfies Contract` instead of an annotation when
  preserving exact keys/values is necessary. `satisfies` alone is not an annotation
  shortcut for ordinary variables and does not validate runtime data.
- Constructors and setters have no return annotation; a function expression assigned
  an explicit callable type need not repeat that type on each parameter and return.
- A narrowly isolated assertion or third-party `any` declaration is allowed only when
  an actual unexpressible invariant or broken external declaration requires it. Explain
  the evidence next to the boundary, contain it, and test the invariant. Convenience,
  unvalidated JSON, and mocking incomplete objects do not qualify.
- `@ts-expect-error` is for intentional negative type tests or a documented upstream
  defect with a removal condition. Never use it to silence a real application error.

## Required local references by task

- [Declarations and functions](references/declarations-and-functions.md): names,
  annotations, function signatures, collections, control flow, and documentation.
- [Types and boundaries](references/types-and-boundaries.md): unknown, validation,
  nullability, unions, generics, utility types, and assertions.
- [Classes and modules](references/classes-and-modules.md): access, lifecycle,
  behavioral interfaces, imports/exports, and runtime module compatibility.
- [Async and errors](references/async-and-errors.md): promises, concurrency,
  cancellation, errors, cleanup, and async iteration.
- [Tooling and enforcement](references/tooling-and-enforcement.md): strict compiler
  profile, lint mapping, runtime targets, and manual enforcement gaps.
- [Sources](references/sources.md): local provenance and compatibility scope.

## Review Checklist

- [ ] Installed compiler/runtime and repository overrides were identified; no incidental upgrade occurred.
- [ ] Named declarations and signatures are explicitly typed, or a listed exception is evidenced.
- [ ] Naming, imports/exports, readonly contracts, and documentation follow this profile.
- [ ] Unknown inputs are validated; null/missing states and union cases are handled.
- [ ] No unsafe escape hatch or suppressed diagnostic conceals an application defect.
- [ ] Async work has a rejection owner, cancellation/cleanup where needed, and meaningful failures.
- [ ] Relevant reference rules and semantic checks were applied, including what lint cannot prove.
- [ ] Type check, lint, and relevant tests passed, or the exact unverified checks/blockers are reported.
