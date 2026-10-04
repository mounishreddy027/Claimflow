# Business Case: ClaimFlow Claims Intake, Assessment & Settlement Platform
## Reference ID: BC-AINE-005 | Domain: Insurance — Claims Operations

---

## 1. Executive Summary & Problem Context

Horizon Insurance operates multi-line personal and commercial insurance across three core lines of business: **Motor**, **Health**, and **Life**. Historically, claims management across these business lines was hindered by fragmented legacy architectures, paper-heavy documentation workflows, disjointed underwriting lookups, and manual adjudication spreadsheets.

### Core Business Bottlenecks
1. **Prolonged First Notice of Loss (FNOL) Cycle Times:** Initial intake validation and policy coverage verification manually required 3 to 7 business days, resulting in customer dissatisfaction and high call-center overhead.
2. **Inconsistent Document Verification:** Intake validation lacked automated checklist enforcement. Motor claims frequently proceeded without verifiable Police First Information Reports (FIR), while Health and Life claims suffered from missing hospital discharge summaries or certified death certificates.
3. **Subjective Fraud Detection & High Loss Ratios:** Without deterministic screening against versioned policy fraud parameters, fraudulent or staged claims passed undetected, or legitimate claimants endured unwarranted review delays.
4. **Financial Discrepancies and Invariant Violations:** Manual calculations of deductibles and co-payments frequently resulted in negative payout anomalies or floating-point rounding drifts.
5. **Opaque Settlement and Dispute Bottlenecks:** Settled claims lacked an immutable, auditable payout ledger. When claimants disputed settlement amounts, claim handlers lacked automated sub-claim branching mechanisms, leading to corrupted claims history.

**ClaimFlow** resolves these operational challenges by delivering an automated, rule-governed, AI-native claims adjudication platform engineered from FNOL through settlement and dispute lifecycle.

---

## 2. Target User Personas & Workflows

| Persona | Role & Core Responsibilities | Key Platform Touchpoints |
|---|---|---|
| **Claimant / Policyholder** | Individuals filing a claim following an insurable event; tracking adjudication progress, receiving settlements, or raising disputes. | • Customer FNOL Portal (Submit incident details, upload documents)<br>• Self-service Claim Status Tracker<br>• Dispute / Reopen Submission Flow |
| **Claims Document Verifier** | Operations staff responsible for inspecting supporting documents against mandatory claim-type checklists. | • Document Verification Queue<br>• Document Status Adjudication (VERIFIED / REJECTED with reason) |
| **Claims Assessor** | Technical adjuster reviewing automated fraud signals, assessing insured coverage, and issuing adjudication decisions. | • Assessor Workbench (`ROLE_ASSESSOR`)<br>• Assessment Calculator Interface<br>• Adjudication Decision Submission (`AUTO_APPROVE`, `MANUAL_REVIEW`, `REJECT`) |
| **Claims Administrator / Superuser** | Executive authority supervising compliance, overriding anomalous decisions, and inspecting audit trails. | • Admin Control Dashboard (`ROLE_ADMIN`)<br>• Decision Override Console with mandatory justification<br>• Immutability and Settlement Ledger Audit Explorer |
| **System Orchestrator (Agents)** | Background automated processes conducting deterministic checks, policy status lookups, and payout generation. | • Automated Policy Status Evaluator<br>• Deterministic Fraud Screening Engine<br>• Immutable Settlement Ledger Service |

---

## 3. Product Scope & Functional Journeys

### 3.1 Supported Claim Types & Rules
ClaimFlow supports three distinct insurance product categories, each with tailored document requirements and adjudication logic:

1. **Motor Insurance:**
   - *Intake Event:* Vehicle accident, collision, theft, or third-party damage.
   - *Document Checklist:* Police FIR (`POLICE_FIR`) + Valid Repair Invoice (`REPAIR_INVOICE`).
   - *Adjudication Logic:* Deductible deducted from repaired vehicle claim amount subject to policy sum insured.

2. **Health Insurance:**
   - *Intake Event:* Hospitalization, surgery, or emergency medical treatment.
   - *Document Checklist:* Itemized Hospital Bill (`HOSPITAL_BILL`) + Hospital Discharge Summary (`DISCHARGE_SUMMARY`).
   - *Adjudication Logic:* Incurred medical charges assessed against co-pay percentages and policy deductibles.

3. **Life Insurance:**
   - *Intake Event:* Policyholder demise.
   - *Document Checklist:* Official Death Certificate (`DEATH_CERTIFICATE`).
   - *Adjudication Logic:* Beneficiary claim assessed against maximum sum insured minus prior policy liens or deductibles.

---

## 4. Key Success Metrics & Business KPIs

| Metric Category | Target KPI | Measurement Baseline & Verification |
|---|---|---|
| **Straight-Through Processing (STP)** | ≥ 65% for standard low-risk claims | Percentage of eligible claims automatically adjudicated without manual intervention. |
| **FNOL Intake Validation Latency** | < 1.0 second response | Automated validation of policy active status on the incident date. |
| **Financial Computation Accuracy** | 100% exact fixed-point precision | Zero rounding or floating-point errors; 100% compliance with `payable_amount >= 0` invariant. |
| **Audit Compliance & Traceability** | 100% append-only audit trail | Zero destructive updates or deletions across claims, fraud scores, assessments, and payouts. |
| **Dispute Resolution Cycle Time** | Reduced by 75% | Automated branching of disputes into linked sub-claims without altering parent claim history. |
| **System Health & Availability** | 99.9% uptime; `/health` < 1s | Health readiness endpoint returns HTTP 200 within 1 second of cold startup. |

---

## 5. Domain Rules & Governing Policies

1. **Policy Active Rule (AC-02):** A claim is valid if and only if the associated policy is in `ACTIVE` status on the date of the insurable incident. If the policy is expired, lapsed, or pending inception on the incident date, the platform rejects the intake immediately with `PolicyNotActiveException`.
2. **Document Completeness Rule (AC-03):** An intake cannot transition to `UNDER_REVIEW` until all mandatory documents required for the specific claim type have been uploaded and verified.
3. **Deterministic Fraud Scoring Rule (AC-04):** Every claim must be evaluated by a deterministic fraud screening algorithm yielding a score between 0 and 100. Claims exceeding the configured threshold in the versioned policy are marked with a fraud flag and diverted to mandatory manual review.
4. **Financial Invariant Rule (AC-05):** The assessed payout must follow the formula:
   $$\text{payable\_amount} = \min(\text{claim\_amount}, \text{sum\_insured}) - \text{deductibles} - \text{co\_pay}$$
   The invariant $\text{payable\_amount} \ge 0$ is absolute. If deductions exceed the claim amount, the payable amount is clamped to zero.
5. **Immutable Settlement Rule (AC-07):** Once a claim is approved, settlement produces an immutable payout record where `payout_amount` is exactly equal to the assessed `payable_amount`. Payout records cannot be modified or deleted.
6. **Sub-Claim Dispute Rule (AC-08):** Settled claims cannot have their payout records modified. When a claimant disputes a settlement, the original claim transitions to `REOPENED` state, and a distinct child sub-claim is generated for supplemental adjudication.
7. **Audited Override Rule (AC-09):** Only users authenticated with `ROLE_ADMIN` may override an `AUTO_APPROVE` or `REJECT` decision. Every override mandates a reason code and justification note, permanently logged with the admin's actor ID and timestamp.

---

## 6. Value Proposition

ClaimFlow equips Horizon Insurance with a modern, high-assurance claims substrate. By codifying domain rules into strict, automated specifications and enforcing state-machine immutability, the platform:
- Eliminates processing leaks and unauthorized payout adjustments.
- Guarantees regulatory transparency and audit readiness under stringent insurance compliance standards.
- Delivers rapid, transparent turnaround times for honest claimants while deterministically isolating high-risk cases.
