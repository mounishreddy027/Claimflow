# .claude/CLAUDE.md — Claude Substrate Governance Rules

This document specifies conventions for configuring and maintaining agents, commands, skills, and hooks inside `.claude/`.

---

## 1. Substrate Architecture

The `.claude/` directory contains the AI-native orchestration substrate:
- **`agents/`:** Markdown agent definitions (`name.md`) with YAML frontmatter specifying name, description, and permitted tools.
- **`commands/`:** Markdown slash command definitions (`command.md`) with invocation instructions.
- **`skills/`:** Auto-discovered skill directories containing `SKILL.md` workflows.
- **`hooks/`:** Enforcement scripts executed at pre-commit, post-write, and evaluation gates.

---

## 2. Project-Specific Extensions for ClaimFlow

Beyond the foundation harness, ClaimFlow requires:
1. **Domain Agents:**
   - `claim-intake-agent.md`
   - `fraud-screening-agent.md`
   - `assessment-agent.md`
   - `settlement-agent.md`
2. **Technical Agents:**
   - `state-machine-validator-agent.md`
   - `audit-tracer-agent.md`
   - `archtest-author-agent.md`
3. **Custom Commands:**
   - `verify-ac.md`
   - `assess-claim.md`
   - `validate-state-machine.md`
   - `audit-trace.md`
4. **Custom Skills:**
   - `fraud-rule-evaluator/SKILL.md`
   - `payout-calculator/SKILL.md`
   - `document-checklist-generator/SKILL.md`
   - `state-machine-validator/SKILL.md`
   - `audit-tracer/SKILL.md`
   - `archtest-author/SKILL.md`

---

## 3. Authoring Guidelines

- Agent prompts must clearly declare role, model tiering (Sonnet for execution, Opus for evaluation/judgment), inputs, outputs, and quality gates.
- Skills must include explicit trigger conditions, step-by-step instructions, and verification checklists.
- Commands must clearly document invocation syntax and expected output reports.
