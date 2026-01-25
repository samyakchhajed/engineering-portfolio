# Project 3 — Orchestrated Workloads on ECS / Fargate

**Batch Analytics & Time-Bound Streaming Execution**

---

## Overview

This project demonstrates the design and execution of **independent batch and streaming workloads** using **Amazon Elastic Container Service (ECS)** with **AWS Fargate**.

The system intentionally avoids long-running services, autoscaling, and workflow engines. Instead, it focuses on **execution contracts**: containers start, perform a bounded unit of work, persist artifacts, and exit.

The project was built and executed end-to-end on AWS, including containerization, IAM setup, runtime configuration, debugging, and validation through logs and artifacts.

---

## What This Project Proves

This project is designed to demonstrate:

* Correct use of **ECS Tasks vs ECS Services**
* Running **non-Lambda-suitable workloads** (long-running and heavy compute)
* Clean separation of:

  * infrastructure
  * execution logic
  * runtime configuration
* Practical debugging of:

  * IAM role passing
  * container command overrides
  * environment-driven failures
* Interpreting ECS task lifecycle states correctly (exit ≠ failure)

This is an **execution-focused** project, not a production system.

---

## High-Level Architecture

* **Orchestration**: Amazon ECS
* **Compute**: AWS Fargate
* **Storage / Artifacts**: Amazon S3
* **Logging & Observability**: Amazon CloudWatch

**Key architectural characteristics:**

* One ECS cluster (no services)
* Independent ECS tasks only
* No task-to-task dependencies
* No retries or auto-restarts
* One shared container image
* All execution behavior driven by environment variables

---

## Workload Types

### Batch Workloads (Run-and-Exit)

These tasks execute a finite unit of work and exit upon completion:

* Scientific computation & visualization
* E-commerce trend analysis (synthetic data)
* Weather data ingestion, processing, and modeling

**Execution semantics:**

* Start → compute → write artifacts to S3 → exit
* Exit with `EssentialContainerExited` = **success**

---

### Streaming Workloads (Time-Bound)

These tasks maintain live WebSocket connections, process events, and exit after a configured runtime:

* Cryptocurrency market data ingestion (BNB, BTC, ETH)

**Execution semantics:**

* Event-driven logging (not time-based)
* Time-bounded execution (e.g., 2 hours)
* Artifacts written to S3 near completion
* Exit with `EssentialContainerExited` = **success**

---

## Execution Status

* All **batch workloads** were executed successfully.
* One **streaming workload (BNB)** was executed and validated end-to-end:

  * Live WebSocket subscription
  * Event-driven logging
  * Long-running container behavior confirmed
* Remaining streaming workloads (BTC, ETH) were **intentionally not duplicated** to avoid unnecessary multi-hour runtime, as execution behavior was already validated.

This decision was deliberate and documented.

---

## Observability & Validation

Execution correctness was validated using:

* **CloudWatch Logs**

  * Task startup confirmation
  * Runtime behavior
  * Signal generation
* **ECS Task Lifecycle States**

  * Understanding that `EssentialContainerExited` indicates successful completion for tasks
* **S3 Artifacts**

  * Output files used as the primary success signal

* Streaming workload execution (BNB) is demonstrated using exported CloudWatch logs (evidence/stream-bnb-execution-logs.csv) to preserve full temporal continuity.

---

## What This Project Is NOT

* ❌ Not a production trading system
* ❌ Not a fault-tolerant or highly available pipeline
* ❌ Not auto-scaling
* ❌ Not using Step Functions or Lambda
* ❌ Not optimized for cost or latency

These omissions are **intentional** to keep the focus on execution fundamentals.

---

## Known Limitations

* No retries or checkpointing
* Streaming tasks are time-bounded, not resilient to mid-run failure
* Manual execution/scheduling used for clarity
* Designed for learning and validation, not production deployment

---

## Key Takeaway

> This project demonstrates **when ECS Tasks are the correct abstraction**, how execution contracts should be enforced, and how real-world container workloads behave when configuration, IAM, and runtime semantics are handled correctly.

---
