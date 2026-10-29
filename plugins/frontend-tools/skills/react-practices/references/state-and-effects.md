# State, effects, and rendering

Keep transient UI state close to its consumer. Lift it only to the nearest owner that
needs to coordinate consumers. Derive filtered lists and totals during render instead
of storing a second copy. Represent mutually exclusive phases with one status or
union. Store selected IDs when storing an entire object would duplicate changing data.
Use a reducer when explicit transitions make complex related updates easier to reason
about; context distributes values but does not automatically provide a server cache.

Separate local UI state, shareable URL state, remote server state, and truly global
client state. Use the existing router/loader/query cache for remote data when present;
do not mirror query results into another store without a concrete editing requirement.
Editable drafts need an explicit reset and conflict policy.

Compute during render, perform user-triggered actions in event handlers, and reserve
Effects for synchronization with external systems. Pair subscriptions, timers, and
connections with cleanup. Include reactive dependencies; stale closures are bugs, not
a reason to turn off lint. Strict Mode's development setup/cleanup cycle should leave
resources correct. Do not use a ref to suppress that cycle instead of fixing cleanup.

For unavoidable manual fetching in an Effect, abort when supported and guard stale
results, including errors and loading updates. Do not let a slower previous request
replace the current result. Abort is not a server transaction rollback. Cache lifetime,
deduplication, and mutations are reasons to use existing data tooling instead of
inventing a general fetch Hook. Show useful loading, empty, error, and retry behavior.

Use stable domain IDs as list keys when items reorder. Keys also express deliberate
state resets. Define component functions at module scope; nesting their definitions
can reset state. Avoid mutating props, state, or values shared between renders.

Measure before adding memoization, virtualization, or a new global store. Memoization
is an optimization, not a correctness guarantee. Respect an existing React Compiler
setup; do not assume it is installed or remove useful memoization without checking.
Route-level lazy loading is useful for large independent screens; preserve the
framework's loading and error handling conventions.
