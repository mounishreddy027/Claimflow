---
name: document-checklist-generator
description: Generates and validates mandatory document verification checklists across Motor, Health, and Life claims (AC-03).
---

# Document Checklist Generator Skill

This skill governs the initialization and enforcement of line-of-business document checklists to satisfy **AC-03**.

---

## 1. When to Use This Skill
- Implementing intake document binding or document queue endpoints.
- Verifying whether a claim is permitted to transition from `FILED` to `UNDER_REVIEW`.

---

## 2. Checklist Matrix by Claim Type

```
MOTOR:
  ├── POLICE_FIR        (Mandatory Police First Information Report)
  └── REPAIR_INVOICE    (Mandatory Workshop Repair Invoice)

HEALTH:
  ├── HOSPITAL_BILL     (Mandatory Final Itemized Hospital Bill)
  └── DISCHARGE_SUMMARY (Mandatory Medical Discharge Summary)

LIFE:
  └── DEATH_CERTIFICATE (Mandatory Official Certified Death Certificate)
```

---

## 3. Checklist Verification Algorithm

```
function isChecklistComplete(claim):
    required_types = getRequiredDocumentTypes(claim.type)
    for doc_type in required_types:
        doc = findDocumentByType(claim.id, doc_type)
        if doc == null or doc.status != "VERIFIED":
            return false
    return true
```

> **State Gate Enforcement:** If `isChecklistComplete(claim) == false`, any call to advance claim state to `UNDER_REVIEW` must be blocked and raise `IncompleteDocumentChecklistException`.
