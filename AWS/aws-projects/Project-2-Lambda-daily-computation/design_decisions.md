# Design Decisions — Project 2

This document explains **why architectural choices were made**, not how to implement them.

---

## Why Lambda Was Previously Wrong

Inherited from Project 1:
- Long-running execution
- In-memory state
- Retry-unsafe logic
- Manual lifecycle control

Using Lambda without redesign would have caused:
- Partial re-execution
- Corrupted state
- Unpredictable retries

Lambda was correctly rejected in Project 1.

---

## What Changed in Project 2

The workload contract was redesigned:

| Aspect | Before | After |
|------|-------|------|
| Execution | Long-running | Per-day bounded |
| State | In-memory | DynamoDB |
| Output | Process memory | S3 JSON |
| Retries | Dangerous | Safe |
| Lifecycle | Manual | Platform-managed |

Lambda became **earned**, not assumed.

---

## Why DynamoDB Was Chosen

- Externalizes execution state
- Enables idempotency
- Prevents duplicate processing
- Makes retries safe and observable

DynamoDB replaces **process memory**, not databases.

---

## Why S3 Outputs Are Immutable

- Prevents overwrites
- Avoids shared mutable state
- Simplifies retries
- Produces auditable artifacts

One execution = one artifact.

---

## Why EventBridge Is Required

EventBridge provides:
- Deterministic scheduling
- No manual triggers
- Platform-managed lifecycle

Without EventBridge, the system would remain manual and incomplete.

---

## Key Takeaway

> **Lambda was not the goal. Correct execution semantics were.**

This project proves that serverless success depends on **workload design**, not service selection.
