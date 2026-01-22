# AWS Operator Toolkit

## Overview

This repository contains a **governed AWS operator toolkit** designed for **safe visibility, controlled operations, hygiene reasoning, and final account cleanup**. The tools are intentionally conservative, human-in-the-loop, and optimized to prevent accidental cost leaks or destructive mistakes.

This is **not automation-first** tooling. It is **operator-first** tooling.

---

## Core Design Principles

* **Explicit intent over speed** 
* **Read-only before action** 
* **No silent defaults or background execution**
* **Strong confirmations for irreversible actions**
* **Explicit AWS profile and region usage only**

Each script has a **clear boundary**. Overlap is avoided by design.

---

## Tooling Summary (Different Use Cases)

### 1. `aws_health_check.py` — Account & Region Diagnostics (Read-Only)

**Use case:** First tool to run in any session.

* Validates AWS identity, credentials, and region
* Surfaces basic health indicators across EC2, S3, Lambda, CloudWatch, CloudFormation, and DynamoDB
* Highlights alarms, failed stacks, backup gaps, and AccessDenied issues

**Never does:** Any write or destructive operation

---

### 2. `aws_cleaner.py` — Hygiene & Reasoning Engine (Read-Only)

**Use case:** Deciding *whether* something should still exist.

* Adds **time-based context** to EC2, S3, and CloudWatch resources
* Flags abandoned, idle, or hygiene-risk resources using configurable age thresholds
* Produces **signals**, not decisions

**Never does:** Delete, stop, or modify resources

---

### 3. `aws_iam_manager.py` — IAM Structure Visibility (Read-Only)

**Use case:** Understanding IAM blast radius safely.

* Lists IAM users, roles, customer-managed policies, and orphan policies
* Shows trust relationships and attachment counts
* Avoids all credential-level data

**Never does:** Modify IAM, inspect credentials, or expose secrets

---

### 4. `aws_ec2_manager.py` — Safe EC2 Operations

**Use case:** Day-to-day EC2 control without console risk.

* Read-only listing by default
* Controlled start, stop, and reboot (single-instance only)
* Heavy confirmation flow for termination

**Never does:** Create instances, modify networking, or batch destructive actions

---

### 5. `aws_s3_manager.py` — Guarded S3 Operations

**Use case:** Inspecting and operating on S3 buckets intentionally.

* Read-only inspection of buckets and public access block status
* Controlled bucket creation and single-file upload
* High-friction flows for emptying or deleting buckets

**Never does:** Modify bucket policies, ACLs, or perform recursive uploads

---

### 6. `aws_shutdown.py` — Final Account Cleanup Protocol

**Use case:** Forcing a **zero-cost** AWS account state.

* Scans **all enabled regions** dynamically
* Groups resources into supervised, batch-approved cleanup phases
* Respects `KeepUntil` tags as safety overrides

**Never does:** Auto-delete without explicit authorization codes

---

## Intended Operator Flow

1. **Start with visibility** → `aws_health_check.py`
2. **Add reasoning & age context** → `aws_cleaner.py`
3. **Inspect IAM safely (if needed)** → `aws_iam_manager.py`
4. **Operate specific services deliberately** → EC2 / S3 managers
5. **End with full account cleanup** → `aws_shutdown.py`

Each step answers a different question:

* *Can I see the account?*
* *Is this still intentional?*
* *What exists and who can access it?*
* *What should I operate?*
* *How do I guarantee zero surprise cost?*

---
Below is **only the section content**.
You can paste this **directly above `## Explicit Non-Goals`**.
No other part of the README is modified.

---

## Why This Exists vs AWS Console

The AWS Console is powerful, but it is **not designed for safe, repeatable operator workflows**. It optimizes for feature access, not for intent, governance, or cost discipline.

This toolkit exists to address those gaps.

### AWS Console Limitations

* Easy to click the wrong region or account
* Destructive actions are often one-click away
* Weak visibility into *why* a resource still exists
* No age-based or hygiene reasoning
* Encourages ad-hoc, memory-driven operations
* Console fatigue leads to mistakes

### What This Toolkit Provides Instead

* **Explicit context first** (profile, region, identity printed every run)
* **Read-only diagnostics and reasoning** before any action
* **High-friction confirmations** for irreversible operations
* **Age-based signals** to answer “Is this still intentional?”
* **Single-resource, scoped actions** instead of bulk clicks
* **Final-protocol cleanup** to guarantee zero surprise costs

### Design Tradeoff (Intentional)

This toolkit is **slower than the Console** for casual clicks.
That is a deliberate choice.

In AWS, speed without intent leads to:

* Orphaned resources
* Hidden regional costs
* IAM blast-radius mistakes
* “I don’t remember creating this” infrastructure

This toolkit prioritizes **operator control over convenience**.

---

## AWS Console vs This Toolkit 

| Dimension                   | AWS Console                  | This Toolkit                            |
| --------------------------- | ---------------------------- | --------------------------------------- |
| **Primary Design Goal**     | Feature access & flexibility | Operator safety & intent                |
| **Default Mode**            | Action-first                 | Read-only first                         |
| **Region Awareness**        | Easy to misclick             | Explicitly printed and enforced         |
| **Account Context**         | Implicit, easy to forget     | Always validated and displayed          |
| **Destructive Actions**     | Often one-click              | Multi-step, high-friction confirmations |
| **Age / Hygiene Reasoning** | Not available                | Built-in (time-based signals)           |
| **IAM Blast Radius Safety** | High risk if misused         | Visibility-only, zero mutation          |
| **Batch Operations**        | Easy to do accidentally      | Explicitly restricted or supervised     |
| **Cost Leak Protection**    | Reactive                     | Proactive (cleanup & shutdown protocol) |
| **Human-in-the-Loop**       | Optional                     | Mandatory                               |
| **Speed**                   | Fast                         | Intentionally slower                    |
| **Failure Mode**            | Silent mistakes              | Loud, explicit, cancel-safe             |

**Summary:**
The AWS Console optimizes for **capability**.
This toolkit optimizes for **control, safety, and accountability**.

That tradeoff is intentional.

---

## Explicit Non-Goals

* ❌ No Infrastructure-as-Code replacement
* ❌ No background automation or schedulers
* ❌ No cost prediction or billing engine
* ❌ No AI-driven decisions

---

## Final Note

These tools are conservative by design. If something feels slow or strict, that is intentional. In AWS, **friction is a safety mechanism**, not a flaw.
