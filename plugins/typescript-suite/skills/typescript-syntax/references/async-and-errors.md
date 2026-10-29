# Async operations and errors

## Promises and concurrency

```ts
type SaveItem = (id: string) => Promise<void>;

async function saveSequentially(ids: readonly string[], save: SaveItem): Promise<void> {
  for (const id of ids) {
    await save(id);
  }
}

async function saveSmallIndependentBatch(
  ids: readonly string[],
  save: SaveItem,
): Promise<void> {
  await Promise.all(ids.map((id): Promise<void> => save(id)));
}

// Wrong: ids.forEach(async (id) => { await save(id); }); // caller cannot await batch
// Wrong: void save('item-1');                           // unowned rejection
```

Use sequential execution when ordering or shared resources require it. Promise.all
starts independent work and rejects when one member rejects; it does not cancel other
members. Bound concurrency for unbounded inputs. Use allSettled when every outcome
must be examined, and actually inspect each failure. Do not catch errors only to
return an apparent success value. Returning a promise transfers ownership to the
caller; fire-and-forget needs a known lifecycle and a non-throwing error reporter.

```ts
type FailureReporter = (error: unknown) => void;

function startTrackedTask(task: Promise<void>, reportFailure: FailureReporter): void {
  // Contract: reportFailure must not throw; caller owns task lifetime/shutdown.
  void task.catch(reportFailure);
}
```

A retry policy must specify retryable errors, attempt limits, cancellation, and whether
repeating an operation is safe. Do not retry every exception or non-idempotent mutation.

## Error contracts

```ts
class StorageError extends Error {
  public readonly code: 'storage-unavailable' = 'storage-unavailable';

  public constructor(cause: unknown) {
    super('Storage is unavailable', { cause });
    this.name = 'StorageError';
  }
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Unexpected failure';
}

type ReserveResult =
  | Readonly<{ ok: true; reservationId: string }>
  | Readonly<{ ok: false; reason: 'out-of-stock' | 'invalid-quantity' }>;
```

Error cause requires compatible runtime/library support. Throw Error instances instead
of strings. Handle expected domain rejection with a result union when consumers need
to branch; unexpected infrastructure failures may remain exceptions. Match an existing
application convention rather than mixing both mechanisms arbitrarily. A Promise<T>
type does not type its rejection channel. Never assume a catch value is an Error.
User-facing messages and logs require their own disclosure policy; do not display raw
server errors or credentials. Preserve the original cause when wrapping; avoid catch,
log, and rethrow at every layer.

## Cancellation, cleanup, and streams

Use AbortSignal only with APIs that support it. Cancellation means the caller stopped
waiting or requested cancellation, not that the remote side effect was rolled back.
For a manually owned operation, clean up timers/listeners/resources in finally.

```ts
interface Session {
  readonly run: () => Promise<void>;
  readonly close: () => Promise<void>;
}

async function runSession(session: Session): Promise<void> {
  try {
    await session.run();
  } finally {
    await session.close();
  }
}
```

This minimal example lets a cleanup failure replace an original error. In operations
where both matter, preserve both explicitly (for example with a supported AggregateError)
and test the chosen error contract. Do not claim cleanup cannot fail without evidence.
Use async iteration for streams when supported and close iterators/resources on early
exit. Annotate generators as `Generator<Yield, Return, Next>` or
`AsyncGenerator<Yield, Return, Next>` when those channels are part of the API.
Only use explicit resource-management syntax when compiler, libraries, and runtime
support it; no upgrade is implied by this skill.
