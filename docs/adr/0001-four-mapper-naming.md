# Four-mapper architecture and `to_x` method naming in `clean-ddd-hexagonal-python`

The skill's DDD/CQRS layering (`Model` → `Entity` → `DTO` → `Response`) needs a
consistent rule for how each pair of adjacent object kinds gets converted, and what
those converter methods are called. We settled this against a real production DDD
repo rather than designing it from theory, and corrected two assumptions the skill
briefly held (see below).

**Decided:**

- Four mapper types, one per adjacent pair: `{Entity}Mapper` (ORM ↔ Entity, in
  `infrastructure/db/mappers/`), `{Entity}ReadMapper` (ORM → DTO, skips Entity, same
  directory), `{Entity}Assembler` (Entity/VO → DTO only, one direction, in
  `application/mappers/`), `{Entity}ApiMapper` (DTO → Response, in
  `interfaces/api/v1/mappers/`).
- Every mapper method is named `to_[destination]` (`to_orm`, `to_entity`, `to_dto`,
  `to_schema`) — never `from_x`. The name always states what's produced.
- `{Entity}ApiMapper` is the exception, not a peer of the other three: the default for
  DTO → Response is `ResponseSchema.model_validate(dto)` called inline in the router,
  even when the Response's fields are a subset of the DTO's. A dedicated ApiMapper is
  warranted only when the mapping needs real transform logic (nested flattening,
  renames `model_validate` can't infer, computed fields) — not merely because the
  shapes differ.
- A Response is sourced from a DTO only, never straight from an Entity or Value
  Object — even a handler-less endpoint (e.g. an identity/auth "whoami" route) must
  still produce a DTO via an Assembler first. Skipping the Assembler removes the one
  seam that keeps a domain refactor from silently reshaping the API contract.

**Rejected during this session:** an early draft proposed mapping a VO straight to a
Response via a mapper (`from_value_object`) for handler-less endpoints, modeled on a
pattern found in the reference repo — that pattern turned out to be a mistake in that
codebase, not a sanctioned exception, and was dropped in favor of the DTO-only rule
above. A second draft proposed `{Entity}ApiMapper` as a standard fourth tier used
whenever DTO and Response shapes differ — the reference repo showed this is wrong too:
in practice `model_validate` is the default even for differing shapes, and a dedicated
mapper is rare.
