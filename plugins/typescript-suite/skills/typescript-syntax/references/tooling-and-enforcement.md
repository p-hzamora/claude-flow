# Compiler profile and enforcement

## Baseline

The reference examples target TypeScript 5.0+ syntax and ES2022 libraries unless noted.
This is a compatibility floor for the examples, not a request to install that version
or permission to upgrade. Use the project's installed supported compiler/runtime. For
older projects, identify unsupported constructs and use a safe compatible equivalent;
report the deviation instead of changing dependencies incidentally.

New projects following this profile must enable:

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

This is a mergeable type-checking fragment, not a complete tsconfig. Select target,
lib, module, moduleResolution, JSX, emit, and project references for the host.
For compatible ESM pipelines use `verbatimModuleSyntax` with type-only imports;
do not paste it into a CommonJS project without understanding the resulting errors.
Preserve an established framework configuration. For strictness migration in an
existing project, scope the change and report remaining gaps; do not disable checks
or claim the whole repository meets this profile when it does not.

A bundler or test runner may strip TypeScript without checking it. Run the actual
project type-check script, or a suitable installed compiler command. With project
references respect the project's build arrangement; tsc against a single source file
can ignore the intended config. Never use `npx` as if it were guaranteed to be local:
check installed tools before invoking anything that could download code.

## Lint mapping and honest limits

Use existing ESLint/typescript-eslint or an equivalent supported tool. Enable typed
rules with the installed version's project configuration; do not install a new linter
solely to make a small code change. Relevant rule families include:

| Requirement | Candidate enforcement |
|---|---|
| No explicit any or unsafe propagation | no-explicit-any; no-unsafe-assignment/argument/return/call/member-access |
| Typed functions and boundaries | explicit-function-return-type; explicit-module-boundary-types |
| Type-only imports | consistent-type-imports; consistent-type-exports |
| Promise ownership | no-floating-promises; no-misused-promises; await-thenable |
| Exhaustive variants | switch-exhaustiveness-check plus a never branch |
| Unsafe assertions/suppressions | no-non-null-assertion; ban-ts-comment and targeted review |
| Stable values and comparisons | prefer-const; no-var; eqeqeq |

These names are from typescript-eslint unless a core ESLint rule is named. Check their
availability and options against the installed version. Configure annotation-related
rules to agree with this profile's explicit types; a conflicting no-inferrable-types
rule cannot simultaneously enforce annotations on primitive declarations.

Explicit local-variable annotations and all exception conditions require manual review
unless a maintained compatible rule/custom checker covers them. Do not install a
deprecated typedef rule blindly, and do not claim strict mode enforces annotations:
inference is valid TypeScript. No compiler or linter proves good naming, SOLID, complete
runtime validation, error ownership, or behavioral substitutability.

Verify enforcement with representative accepted/rejected snippets when changing its
configuration. Never advertise a grep or regex check as semantic TypeScript validation.
Preserve formatter ownership; use targeted formatting rather than rewriting the repo.
