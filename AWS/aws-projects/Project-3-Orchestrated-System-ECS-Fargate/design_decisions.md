# Design Decisions — Project 3 (ECS / Fargate Orchestrated Workloads)

This document explains **why architectural and platform decisions were made** for Project 3, and how those decisions **evolved from Project 1 and Project 2**. The focus is on **execution semantics, lifecycle control, and correctness**, not on convenience or trend-following. 

---

## Context: Evolution Across Projects

This project is the **third step in an intentional progression**, not an isolated build.

## Context: Evolution Across Projects

This project is the **third step in an intentional progression**, not an isolated build.

| Project   | Primary Platform        | Core Constraint                         | Key Lesson                                  |
| --------- | ----------------------- | --------------------------------------- | ------------------------------------------- |
| Project 1 | AWS EC2 (via SSM)       | Long-running, stateful execution        | Infrastructure control exposes ops overhead |
| Project 2 | Lambda + DynamoDB       | Retry safety, idempotency               | Serverless must be earned                   |
| Project 3 | ECS / Fargate           | Mixed batch + streaming workloads       | Containers are the correct abstraction      |


Project 3 exists because **neither Lambda nor raw EC2 fully matched the new workload contract**.

---

## Why ECS Was Chosen

**Decision**: Use Amazon ECS as the orchestration control plane.

**Rationale**:

* Workloads require explicit start and stop boundaries
* Execution duration exceeds Lambda limits
* In-memory processing is required during execution
* Failure must be observable and final (not auto-retried)
* Multiple independent workloads must coexist without coupling

ECS provides:

* Explicit task lifecycle control
* Clear separation between orchestration and execution
* Observable failure semantics
* No implicit retries

ECS was chosen **for semantic alignment**, not scale.

---

## Why Fargate Instead of EC2

**Decision**: Use Fargate as the ECS launch type.

**Rationale**:

* No requirement for host-level tuning
* No benefit from SSH or instance persistence
* Execution is sporadic and time-bounded
* Infrastructure should disappear when tasks complete

**Accepted trade-offs**:

* Slightly higher cost per compute unit
* Reduced visibility into host internals

These trade-offs are acceptable because **execution correctness matters more than host control** for this project.

---

## Why ECS Tasks, Not ECS Services

**Decision**: Use ECS Tasks exclusively. No Services.

**Rationale**:

* All workloads are finite or time-bounded
* Desired count semantics are meaningless here
* Automatic restarts would violate correctness
* Exit = success is a valid outcome

This directly contrasts with ECS Services, which assume:

* Long-lived workloads
* Continuous availability
* Restart-on-failure semantics

In this project:

> `EssentialContainerExited` is a **successful terminal state**, not an error.

---

## Why Batch and Streaming Share One Container Image

**Decision**: Build and use a single container image for all workloads.

**Rationale**:

* Ensures a consistent runtime environment
* Reduces build and versioning complexity
* Makes behavior a function of configuration, not image selection

Execution differences are controlled by:

* Command override
* Environment variables

**Trade-off accepted**:

* Larger image size

This trade-off is intentional and aligns with **operational simplicity over micro-optimization**.

---

## Why Execution Is Environment-Driven

**Decision**: All runtime behavior is controlled via environment variables.

**Rationale**:

* Makes execution contracts explicit
* Enables the same image to serve multiple roles
* Forces correctness at runtime
* Prevents silent default behavior

Environment variables define:

* Input and output locations
* Execution duration
* Streaming vs batch behavior

---

## Why Fail-Fast Behavior Was Preserved

**Decision**: Do not guard against missing configuration in code.

**Rationale**:

* Missing configuration should surface immediately
* Silent defaults create partial execution risks
* Early failure is safer than incorrect success

Observed early failures during execution were **signals of misconfiguration**, not defects. Preserving fail-fast behavior improved system correctness.

---

## Why S3 Is the Artifact Boundary

**Decision**: Use S3 for all outputs and artifacts.

**Rationale**:

* Containers are stateless by design
* Artifacts provide a deterministic success signal
* No shared filesystem coupling
* Easy post-run validation

S3 acts as:

* Output store
* Execution proof
* Audit boundary

---

## Why EventBridge Scheduler Was Abandoned

**Decision**: Do not use EventBridge Scheduler for execution.

**Rationale**:

* Added IAM role-passing complexity
* Silent invocation failures increased debugging cost
* Introduced an orchestration layer without execution benefit

Switching to **ECS-native task execution**:

* Reduced IAM surface area
* Improved observability
* Simplified mental model

Abandoning EventBridge Scheduler was a **corrective design decision**, not a workaround.

---

## Why Only One Streaming Workload Was Fully Executed

**Decision**: Fully execute one representative streaming workload (BNB).

**Rationale**:

* Streaming workloads are configuration-identical
* Multi-hour execution is time-expensive
* One successful execution validates the pattern

This follows the principle of:

> **Representative validation over redundant duplication**

---

## Observability Philosophy

**Decision**: Use logs and artifacts, not dashboards.

**Rationale**:

* Tasks are ephemeral
* Event-driven workloads produce irregular logs
* Artifact presence is the primary success signal

Log silence between events is expected and correct for streaming systems.

---

## Decisions Explicitly Rejected

The following were intentionally not used:

* AWS Step Functions (over-orchestration)
* Auto-scaling (no long-lived services)
* Retry logic (risk of duplicate work)
* Stateful containers

Minimalism here is **intentional**, not incomplete.

---

## Final Design Philosophy

Project 3 prioritizes:

* Correct execution semantics
* Honest failure modes
* Explicit lifecycle boundaries
* Engineering clarity over feature count

This project demonstrates **when containers are the right abstraction**, and how orchestration should serve execution—not obscure it.

---