## AWS Work Overview

This folder contains **all AWS-related work** in this portfolio.

The AWS content is intentionally divided into **learning**, **tools**, and **projects** to avoid mixing experimentation with operational code.

No destructive automation is performed without safeguards.

---

## Folder Breakdown

### `aws-learning-projects/`

Purpose: **Learning and mental model building**

* Small, focused experiments
* Manual execution
* Clear scope
* Cleanup is part of the exercise

These projects exist to understand **why AWS behaves the way it does**, not to showcase scale.

---

### `aws-tools/`

Purpose: **Reusable operator tooling**

* Safety-first
* Explicit confirmations
* No blind automation
* Designed to reduce AWS console risk

These tools reflect **operational maturity**, not experimentation.

---

### `aws-projects/`

Purpose: **Higher-level AWS systems**

* Multiple services involved
* Clear architecture
* Defined intent and teardown story
* Treated as systems, not scripts

---

### `Personal_Snippet_Library/`

Purpose: **Personal reference snippets**

* Short, reusable AWS patterns
* Not full projects
* Not production claims
* Exists for speed and consistency

---

## What This AWS Work Is NOT

* ❌ No production claims
* ❌ No cost-unsafe automation
* ❌ No “one-click magic” scripts
* ❌ No copy-paste tutorials

Everything here prioritizes **understanding, safety, and intent**.

---

## How to Review AWS Content

Recommended order:

1. `aws-tools/`
2. `aws-projects/`
3. `aws-learning-projects/` (optional, for fundamentals)

This mirrors real-world progression:
**learn → operate → design systems**

---

## AWS Design Principles Used

* Explicit regions and profiles
* Read-only inspection before action
* Human-in-the-loop for destructive steps
* Predictable teardown paths

These principles are applied consistently across AWS work.

---
