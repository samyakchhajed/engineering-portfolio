# Execution Steps and Observed Behavior

This document records **exactly how the system was executed**, including the bootstrap mechanism, commands used, and the observed runtime behavior.

It is intentionally factual and reproducible.

---

## Environment

- **Operating System:** Amazon Linux 2023
- **Compute:** Amazon EC2 (t3.micro)
- **Execution trigger:** AWS Systems Manager (Run Command)
- **Observability:** CloudWatch Logs
- **Access model:** No SSH, no interactive shell

---

## Step 1 — Instance Bootstrap (One-Time)

At instance launch, **EC2 User Data** was used as a one-time bootstrap mechanism.
This ran automatically on first boot and was not re-run later.

### Bootstrap responsibilities

- Update the system
- Install Python and required libraries
- Place the application code on disk
- Exit without executing the workload

### Bootstrap commands (User Data)

```bash
#!/bin/bash
set -e

dnf update -y
dnf install -y python3 python3-pip

pip3 install --no-cache-dir websockets boto3

mkdir -p /opt/project1
chmod 755 /opt/project1

# Application code written to /opt/project1/runner.py
# (logic execution intentionally excluded)

chmod 755 /opt/project1/runner.py
````

**Important:**
The bootstrap **does not run the application**. It only prepares the instance so that execution can be triggered later.

---

## Step 2 — Execution Trigger (SSM Run Command)

The workload was started explicitly using **AWS Systems Manager → Run Command** with the document `AWS-RunShellScript`.
No interactive session was used.

### Command executed via SSM

```bash
export S3_BUCKET=all-project-bucket-general-use
export S3_PREFIX=project1/run-$(date +%s)/
export MAX_RUNTIME_SECONDS=600

python3 /opt/project1/runner.py
```

### Execution semantics

* SSM issued the command and exited immediately
* The Python process ran independently on the instance
* No retries or restarts were configured
* Execution lifecycle remained under operator control

---

## Step 3 — Observed Runtime Behavior

From CloudWatch Logs:

* WebSocket subscription succeeded
* One candlestick event was received **per minute**
* Total runtime window: **10 minutes**
* Exactly **10 candles** were processed
* No retries occurred
* Process exited cleanly after the time window expired

This behavior matches the workload contract.

---

## Step 4 — Output Behavior (Important Clarification)

### Generated outputs

* **Runtime logs** were emitted to STDOUT
* Logs were visible in **CloudWatch Logs**
* Command stdout/stderr were persisted automatically by **SSM**

### Conditional output file

A secondary output file is written **only after 100 candles are processed**.

```text
Condition: equity file written every 100 candles
Observed candles: 10
Result: file not generated
```

Because the execution window was intentionally limited to **10 minutes**, the 100-candle threshold was **not reached**.

### Conclusion

The absence of the secondary output file is:

* **Expected**
* **Correct**
* **A direct result of bounded execution**

No output was skipped or lost.

---

## Step 5 — Execution Completion

* The process exited after the configured runtime
* EC2 instance remained running (by design)
* Instance lifecycle control remained with the operator

No automatic teardown was configured intentionally.