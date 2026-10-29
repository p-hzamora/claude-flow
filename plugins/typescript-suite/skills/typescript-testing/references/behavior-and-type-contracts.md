# Behavioral and compile-time contracts

Choose unit tests for pure rules, contract tests for interchangeable implementations,
and integration tests for actual serialization/I/O boundaries. Test both valid and
invalid inputs, limits, missing values, and relevant rejection/retry behavior. A test
should continue to work after an internal refactor that preserves the contract.

Use a narrow typed fake rather than `{} as Repository` or `as unknown as Client`.
If a test needs a giant unrelated double, reconsider the consumer dependency.

```ts
type StoredName = Readonly<{ id: string; name: string }>;
interface NameStore {
  readonly save: (value: StoredName) => Promise<void>;
}

function createRecordingStore(recorded: StoredName[]): NameStore {
  return {
    save: async (value: StoredName): Promise<void> => {
      recorded.push(value);
    },
  };
}
```

Create fresh mutable state for each test. Inject time/randomness through an existing
seam or deliberately scoped clock control; restore timers and mocks. Await promises
and rejection assertions so a test cannot pass before the operation finishes. Avoid
sleep-based synchronization and broad snapshots of implementation structure. Test
cleanup and cancellation when the code owns them, including failure during cleanup.
Run common contract tests for adapters that promise the same behavior.

## Type tests

A transpiling runner does not prove types. Put negative cases in files included in a
deliberate no-emit/type-test project, never in an executable production entry point.

```ts
type ChangeName = Readonly<{ id: string; name: string }>;
const validChange: ChangeName = { id: 'user-1', name: 'Ada' };
// @ts-expect-error -- name must be text, not a numeric identifier.
const invalidChange: ChangeName = { id: 'user-1', name: 42 };
void validChange;
void invalidChange;
```

Verify a positive counterpart and one intended negative property at a time. The
compiler must report unused expect-error directives when the invalid case becomes
accepted. An unrelated error on the same line can satisfy the directive, so inspect
why it fails. Do not execute negative specimens to simulate runtime validation.

Use the installed runner's type assertions or a dedicated existing type-test harness
when more expressive API testing is needed. Avoid installing a type-test package for
one trivial assignment check. Test runtime parsing separately: assignability tests
cannot prove that a payload is valid at execution time.

For regressions, add the test that exposes the changed behavior and run the affected
scope. Broaden only when integration risk warrants it. Report the exact commands and
separate type failures, runtime failures, and missing infrastructure. Coverage measures
executed lines, not correct assertions; use risk-based gaps rather than a mandatory
percentage or tests that simply echo code.
