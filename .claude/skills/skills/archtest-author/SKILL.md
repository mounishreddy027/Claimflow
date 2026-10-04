---
name: archtest-author
description: Authors and maintains automated architectural tests, layer isolation checks, and structural invariants (NFR-08).
---

# ArchTest Author Skill

This skill guides the authoring and maintenance of automated architectural tests (`ArchUnit`, `dependency-cruiser`, `import-linter`) to enforce **NFR-08**.

---

## 1. When to Use This Skill
- Adding new modules or services to verify layering rules.
- Writing tests that prevent architectural drift, layer bypassing, or circular dependencies.
- Enforcing domain purity and primitive precision constraints.

---

## 2. Core Architecture Rules to Implement

### Rule 1: Layer Separation
- **`domain`** may only depend on standard language libraries (no web, no database, no services).
- **`services`** may depend on `domain` and `repositories`.
- **`controllers`** may depend on `services` and DTOs; never directly on `repositories`.
- **`repositories`** may depend on `domain` and persistence drivers; never on `controllers`.

### Rule 2: Precision Guardrail (NFR-01)
- Classes in `src/domain/` must NOT contain fields, parameters, or return types of `float`, `double`, `Float`, or `Double`.
- All monetary attributes must use fixed-point types.

### Rule 3: Immutability of Finalized Entities
- Entities in `payout_records` and `assessments` must have no public setter methods or mutable collections.
- Settled claims cannot have status mutated without creating an audit record.

---

## 3. Verification Command
To verify architecture compliance:
```bash
mvn test -Dtest=*ArchTest*
# or
pytest tests/architecture/
# or
npx depcruise --config .dependency-cruiser.js src
```
All checks must pass with zero violations.
