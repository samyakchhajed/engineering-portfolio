# Design Decisions and Rationale

This document explains **why specific services were chosen or rejected**, based strictly on workload semantics.

---

## Why EC2 Was Chosen

EC2 was selected **by necessity**, not preference.

It provides:
- Absolute lifecycle authority
- Deterministic execution windows
- Persistent in-memory state
- Direct process control
- No implicit retries or schedulers

The operational overhead of EC2 is accepted deliberately to preserve correctness.

---

## Why AWS Lambda Was Rejected

Lambda was rejected without implementation because it violates the workload contract:

- Freeze/thaw breaks in-memory state
- Retry semantics are unsafe
- Hard execution time limits
- No guaranteed execution continuity

This is a **semantic mismatch**, not a limitation workaround.

---

## Why ECS / Fargate Was Rejected

While technically capable, ECS/Fargate was rejected because it:

- Introduces orchestration without benefit
- Reduces direct lifecycle control
- Adds control-plane complexity
- Obscures failure semantics for single-run workloads

The workload does not benefit from container orchestration.

---

## Why SSM Was Used

SSM was used strictly as a **control plane**:

- No SSH access
- Fully auditable execution
- Explicit operator intent
- No interactive dependency

SSM does not host logic or state.

---

## Why Docker Was Not Used

Docker was intentionally excluded because it:

- Adds abstraction without value here
- Pushes the design toward orchestration
- Weakens the EC2-by-necessity argument
- Conflicts with the failure and lifecycle model

Raw EC2 execution is more honest for this workload.