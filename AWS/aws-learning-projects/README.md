# Learning Projects — AWS Foundations & Serverless Concepts

## Purpose

This section contains **small, focused learning projects** built to understand **AWS fundamentals, control planes, and safe operational behavior**.
These are **not production systems** and **not portfolio showcases**. They exist to internalize **mental models**, not to demonstrate scale or polish.

Each project isolates **one or two core AWS concepts** and validates them through deliberate experimentation and cleanup.

---

## Design Intent

* **Learning-first, not outcome-first** 
* **Small scope, clear boundaries**
* **Manual execution to build intuition**
* **Safe-by-default mindset**
* **Cleanup is part of learning, not optional**

These projects prioritize *understanding why AWS behaves the way it does* over building projects or reusable tooling.

---

## Covered Learning Areas

### Compute & Access

* EC2 access patterns (SSH vs SSM)
* Instance control and session safety
* IAM trust relationships in practice

### Networking

* VPC fundamentals
* Subnets, routing, and isolation boundaries
* How networking decisions affect reachability and security

### Serverless & Eventing

* Lambda execution model
* Event-driven invocation
* State handling in stateless systems

### Infrastructure Ownership

* Infrastructure as Code (CloudFormation)
* Stack lifecycle and deletion safety
* Resource ownership and drift

---

## Representative Learning Exercises

### Infrastructure Ownership & Lifecycle (CloudFormation)

* Learn that **a stack is the unit of ownership**
* Observe safe deletion failures for data-bearing resources
* Understand why deletion failure is a **protection signal**, not an error
* Internalize why updates are riskier than creation


---

### Stateful Control in Serverless Systems

* Separate **control plane** from **workload**
* Use DynamoDB as a behavioral authority
* Enforce idempotency and concurrency deterministically
* Design systems that exit early to save cost


---

### EC2 Access Patterns (SSH vs SSM)

* Compare key-based access vs identity-based access
* Understand blast radius and auditability
* Learn why SSM reduces credential sprawl

---

### Lambda Fundamentals (Multiple Small Experiments)

* Invocation behavior
* Retry semantics
* Failure handling
* Cost-aware early exits

---

## What These Projects Are NOT

* ❌ Production-ready systems
* ❌ Optimized for scale or performance
* ❌ Automation-heavy
* ❌ Resume padding

They are intentionally **small, disposable, and instructional**.

---

## Evaluation Criteria (For Self-Review)

A learning project is considered **successful** if:

* The AWS behavior is clearly understood
* Failure modes were observed intentionally
* Cleanup was performed correctly
* A clear mental model was gained

Code quality is secondary. **Understanding is the deliverable.**

---

## Final Note

These projects exist to build **operator judgment**.

Once the mental models are correct, tooling and automation can be built safely.
Skipping this phase leads to fragile systems and costly mistakes.

---
