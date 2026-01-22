# EC2 by Necessity — Compute Selection Case Study

## Overview

This project is a **compute selection and lifecycle discipline case study**, not a trading or ML system.  
Its purpose is to demonstrate **why EC2 is the correct choice only when a workload contract forces it**, and how to operate such a workload with **explicit control, bounded cost, and zero hidden automation**.

The project intentionally prioritizes **engineering judgment** over service convenience.

---

## Workload Contract

The following constraints existed **before** any compute decision:

- **Execution model:** Single long-running process
- **Runtime:** Bounded, but longer than Lambda limits
- **State model:** In-memory rolling state (unsafe to reset)
- **Connection model:** Persistent WebSocket stream
- **Failure model:** Partial outputs acceptable, retries dangerous
- **Lifecycle authority:** Operator must explicitly start and stop execution

These constraints are non-negotiable.

---

## Architecture Summary

- **EC2:** Execution authority (chosen reluctantly, by necessity)
- **AWS Systems Manager (SSM):** Control plane for execution
- **CloudWatch Logs:** Runtime observability
- **S3:** Used only for command execution logs (via SSM)

No schedulers, no retries, no orchestration layers.
The application logic is included under `/code` only to make the workload contract explicit; it is intentionally simple and not the focus of this project.

---

## What This Project Proves

- Ability to **reject Lambda and ECS correctly**
- Clear understanding of **state vs execution semantics**
- Explicit lifecycle and cost control
- Separation of provisioning, execution, and observability
- Discipline in avoiding unnecessary abstractions

---

## What This Project Is Not

- Not a production trading system
- Not an ML inference pipeline
- Not optimized for profitability
- Not designed for automatic scaling or retries

This is a **decision-making case study**, not a feature showcase.
