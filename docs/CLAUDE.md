# docs/CLAUDE.md — Business & Architecture Documentation Rules

This document provides operational rules and authoring standards for files in `docs/`.

---

## 1. Documentation Responsibilities

- **`business-case.md`:** Primary entry point for reviewer evaluation plugins. Must comprehensively represent Horizon Insurance problem context, target personas, KPIs, domain rules, and business value proposition.
- **`architecture.md`:** Must contain complete C4 Context and Container diagrams (rendered via Mermaid), sequence flows for the FNOL-to-settlement lifecycle, Clean Architecture layer descriptions, and immutability ledger patterns.
- **`tdd.md`:** Governs test-driven development practices. Must document the Red-Green-Refactor loop and maintain a worked example demonstrating financial calculation invariance.
- **`knowledge-deposits.md`:** Permanent repository of learned failure modes (`KD-NNN`). Any bug or regression encountered by an agent must be encoded here with its permanent preventative rule.
- **`post-mortem.md` & `fix-loops/`:** Tangible audit evidence of autonomous debugging and fix-loop resolution.

---

## 2. Diagram & Formatting Standards

1. **Mermaid Diagrams Only:** Diagrams must be declared in standard `mermaid` fenced code blocks. Use `flowchart TD`/`LR`, `sequenceDiagram`, `stateDiagram-v2`, or `classDiagram`.
2. **Deterministic Markdown:** No unclosed code blocks, broken tables, or dead relative links.
3. **No Code Snippets Beyond Pseudocode:** Production implementations belong in `src/`, not in `docs/`.
