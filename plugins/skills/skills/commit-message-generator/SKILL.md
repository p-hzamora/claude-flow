---
name: commit-message-generator
description: |
  Generate proper conventional commit messages for staged files with intelligent grouping.
  
  Analyzes staged changes, groups related files by shared features (matching class names 
  and file paths), detects commit type from diff content (feat/fix/test/chore/etc), and 
  suggests commit titles following the pattern: type(scope): subject line.
  
  Use this skill whenever you need to create commits from staged changes, especially when 
  you have multiple unrelated changes and want to group them intelligently by feature. 
  Also use when you have many test files and want them consolidated into single test commits.
  
  User reviews suggested grouping and can adjust files before committing.

---

## How it works

**Requires:** a Git repository with staged files.

## Critical Format Constraint

Generate commit titles only: no description body, multiline content, or footer. Every
title must match this pattern exactly:

```text
(build|chore|docs|feat|fix|perf|refactor|style|test|update)(\(([a-zA-Z]+|([A-Z][A-Z]{1,32}-\d+))\))?: .*(.*\n*)*
```

- Type: one of `build`, `chore`, `docs`, `feat`, `fix`, `perf`, `refactor`, `style`,
  `test`, or `update`.
- Scope: optional lowercase letters or a Jira-style ticket, such as `EVA-123`.
- Subject: description after the colon and space.
- The title is one line only.

Examples: `feat(auth): add login endpoint`, `fix(rule-engine): correct permission
check`, `test(handlers): remove invalid test cases`, and `update(dependencies): upgrade
fastapi to v0.104`.

1. **Fetch staged files**: Runs `git diff --cached --name-only` to get staged files
2. **Analyze changes**: Runs `git diff --cached` to examine what changed in each file
3. **Extract metadata**: Gets class names, module names, file paths from staged files
4. **Group by feature**: Matches files that modify same classes/modules (same feature)
5. **Separate by directory**: Consolidates all changes in same directory type (e.g., all tests/) into single commits
6. **Detect type**: Analyzes diff content (additions vs deletions, test patterns, docs changes) to infer type
7. **Extract scope**: Uses file path or config filename as scope
8. **Generate titles**: Creates commit titles matching pattern: `type(scope): subject line`
9. **Present for review**: Shows suggested commits with file breakdowns, user adjusts as needed

## Commit types detected

- `feat` — New feature (file additions or significant new code)
- `fix` — Bug fix (targeted changes, error handling)
- `test` — Test files only (files in tests/ directories)
- `refactor` — Code reorganization (renames, moves, restructuring without new features)
- `docs` — Documentation (markdown, docstrings, comments)
- `chore` — Configuration, dependencies, tooling
- `style` — Formatting, linting (no logic changes)
- `perf` — Performance improvements

## Scope extraction

Scope is extracted from:
1. **Config files**: Filename without extension (e.g., `pyproject.toml` → `pyproject`, `.env.example` → `env`)
2. **Code files**: Second directory segment (e.g., `app/handlers/rule.py` → `handlers`)
3. **Fallback**: Dominant class name if identifiable across files
4. **Default**: If no match, use first meaningful path segment

Examples:
- `pyproject.toml` → `chore(pyproject):`
- `.github/workflows/test.yml` → `chore(workflows):`
- `app/handlers/rule.py` → `feat(handlers):`
- `tests/unit/services/test_rule.py` → `test(services):`

## Grouping rules

**By feature**: Files modifying same class names or modules group together
- Example: `app/handlers/rule.py` + `app/services/rule_service.py` → same feature

**By directory type**: All files in same directory type consolidate
- Example: All test files (tests/unit/*, tests/integration/*) → single `test(scope)` commit
- Example: All config files (pyproject.toml, .env.example) → single `chore` commit

**Separate by type**: Feature code and test code always separate
- Example: `app/handlers/rule.py` (feat) and `tests/handlers/test_rule.py` (test) → two commits

## User review workflow

After analysis, skill presents:

```
COMMIT 1: feat(handlers): implement rule creation
	- app/handlers/rule.py
	- app/application/services/rule_service.py
	- app/domain/entities/rule.py

COMMIT 2: test(handlers): add rule handler tests
	- tests/unit/handlers/test_rule_handler.py
	- tests/unit/application/test_rule_service.py

---
Does this grouping look good?
- Move files between commits (format: "move file.py from commit 2 to commit 1")
- Delete files from a commit (format: "remove file.py from commit 2")
- Change a title (format: "change commit 1 title to: feat(domain): ...")
- Confirm when ready (type: "confirm")
```

User can interactively adjust before final output.

## Output

Final output shows:
- Commit titles with files
- Ready to execute in order

## Algorithm: Class/Module Extraction

To detect shared features across files:

1. **Extract identifiers**: Look for class names, function names, module names in staged diffs
2. **Build dependency graph**: Track which files touch same classes/modules
3. **Find clusters**: Group files that share identifiers (same feature likely)
4. **Resolve conflicts**: If file belongs to multiple features, assign to most prevalent
5. **Apply type rules**: Separate tests from code, group by directory type

Example:
```
File A: RuleHandler class
File B: RuleService class (uses RuleHandler)
File C: test_RuleHandler (tests RuleHandler)
File D: test_RuleService (tests RuleService)

Result:
- Cluster 1: A, B (share Rule* identifiers) → feat(handlers/services)
- Cluster 2: C, D (test versions of Cluster 1) → test(handlers/services)
```

## Notes

- Skill runs in git repository only (will fail if not in repo)
- Analyzes staged files only (`git index`)
- User always reviews before committing
- Generated titles follow conventional commits pattern strictly
- Scope detection is deterministic based on file paths and identifiers

## CRITICAL: Title-Only Commits — MANDATORY

**GENERATE TITLE-ONLY COMMITS. NO DESCRIPTION. NO BODY. NO FOOTER.**

Each commit generated MUST:
1. Match regex exactly: `(build|chore|docs|feat|fix|perf|refactor|style|test|update)(\(([a-zA-Z]+|([A-Z][A-Z]{1,32}-\d+))\))?: .*(.*\n*)*`
2. Be a SINGLE LINE title only
3. Have NO description body
4. Have NO multiline content
5. Have NO footer
6. Use only these commit types: build, chore, docs, feat, fix, perf, refactor, style, test, update
7. Have scope in lowercase letters OR JIRA ticket format (EVA-123, TAR-456)

### What is allowed:
- Single line: `type(scope): concise description`
- Examples:
  - `feat(auth): add login endpoint`
  - `fix(rule-engine): correct permission check`
  - `test(handlers): remove invalid test cases`
  - `update(dependencies): upgrade fastapi to v0.104`

### What is FORBIDDEN:
- ❌ Multiline commits with descriptions
- ❌ Commit bodies (anything after blank line)
- ❌ Commit footers (Closes #123, Co-Authored-By, etc.)
- ❌ Blank lines in the commit message
- ❌ Additional paragraphs

### Example outputs:
```
COMMIT 1: test(dependencies): remove route-level permission guard tests
  - tests/unit/interfaces/api/v1/dependencies/test_role_authorization.py

COMMIT 2: fix(routers): add app-access guards to app-scoped endpoints
  - app/interfaces/api/v1/routers/rule_app.py
```

### Incorrect (will fail):
❌ `test(dependencies): remove tests\n\nThis commit removes the old permission guard tests.`

### Correct (will pass):
✅ `test(dependencies): remove route-level permission guard tests`

## Review Checklist

- [ ] Staged changes were inspected and grouped by one coherent purpose per commit.
- [ ] The proposed conventional-commit type, scope, and imperative subject reflect the actual diff.
- [ ] Unrelated changes were kept out of the commit or presented as separate commits.
- [ ] The final title satisfies the documented format without a body that violates the repository convention.
