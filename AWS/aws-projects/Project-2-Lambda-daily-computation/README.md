# Project 2 — Refactoring a Stateful System into a Serverless Platform

## Overview

This project demonstrates **how and why a workload originally unsuitable for AWS Lambda can be redesigned to make Lambda the correct compute choice**.

The goal is **not serverless adoption**, but **engineering judgment** — knowing when Lambda is wrong, and how to refactor a system so that it becomes right.

This project is a direct continuation of **Project 1 (EC2 by Necessity)**.

---

## Core Idea

> **Lambda becomes correct only after the workload contract is intentionally redesigned.**

Instead of forcing the same execution model onto Lambda, the system is re-architected to:
- Remove in-memory state
- Remove long-running execution
- Externalize state
- Embrace retries as a feature

---

## High-Level Architecture

EventBridge (daily schedule)  
→ Lambda (stateless, per-day execution)  
→ DynamoDB (execution state + idempotency)  
→ S3 (immutable JSON artifacts)  
→ CloudWatch Logs  
→ SNS (failure notification)

---

## What This Project Proves

- Ability to **redesign workloads**, not just deploy them
- Deep understanding of **Lambda execution semantics**
- Correct handling of **retries and idempotency**
- Clear separation of **compute, state, and artifacts**
- Cost-aware, minimal serverless architecture

This project complements Project 1 by showing the **intentional transition from EC2 to Lambda**.
