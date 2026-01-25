# Execution Steps — Project 3

This document records the **actual execution steps** used to build, debug, and validate Project 3 using **Amazon ECS with Fargate**.

---

## 1. ECS Cluster

* Cluster name: `project3-ecs-cluster`
* Launch type: Fargate
* Capacity providers: None
* Services: None

The cluster was used **only as an execution boundary**. No long-running services were created.

---

## 2. IAM Roles

### 2.1 ECS Task Execution Role

* Role name: `ecs-task-execution-role`
* Trusted entity: `ecs-tasks.amazonaws.com`
* Attached policy:

  * `AmazonECSTaskExecutionRolePolicy`

Purpose:

* Pull container images from ECR
* Write logs to CloudWatch

---

### 2.2 ECS Task Roles

Two separate task roles were created to avoid permission overlap.

#### Batch Task Role

* Role name: `ecs-batch-task-role`
* Permissions:

  * Read access to S3 input bucket (where required)
  * Write access to S3 output prefixes

#### Streaming Task Role

* Role name: `ecs-streaming-task-role`
* Permissions:

  * Write access to streaming S3 prefixes only

No wildcard permissions were granted.

---

## 3. S3 Storage

* Bucket name: `project3-artifacts`

Prefixes used:

* `batch/` — batch task outputs
* `streaming/` — streaming task outputs

S3 served as the **sole success indicator** for task completion.

---

## 4. Container Image

### 4.1 Dockerfile

* Base image: Python
* All dependencies installed via `requirements.txt`
* No `ENTRYPOINT` or `CMD`

Runtime behavior was controlled exclusively via ECS command overrides.

---

### 4.2 Local Build Commands

```bash
docker build -t project3-ecs-image .
```

Local validation was performed using:

```bash
docker run --rm \
  -e OUTPUT_BUCKET=test \
  -e OUTPUT_PREFIX=test \
  project3-ecs-image python computation-generator.py
```

---

## 5. ECR Repository

* Repository name: `project3-ecs-image`

Commands used:

```bash
aws ecr create-repository --repository-name project3-ecs-image

aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com

docker tag project3-ecs-image:latest <account>.dkr.ecr.<region>.amazonaws.com/project3-ecs-image:latest

docker push <account>.dkr.ecr.<region>.amazonaws.com/project3-ecs-image:latest
```

---

## 6. ECS Task Definitions

Six task definitions were created, all using the **same container image**.

### Common Settings

* CPU: 1 vCPU
* Memory: 3 GB
* Launch type: Fargate
* Network mode: awsvpc
* Logging: CloudWatch

---

### Task Definitions

| Task Name           | Script                         |
| ------------------- | ------------------------------ |
| `batch-computation` | `computation-generator.py`     |
| `batch-ecommerce`   | `E-commerce-trends.py`         |
| `batch-weather`     | `weather-data-pipeline.py`     |
| `stream-bnb`        | `web-sockets-runner-bnbusd.py` |
| `stream-btc`        | `web-sockets-runner-btcusd.py` |
| `stream-eth`        | `web-sockets-runner-ethusd.py` |

---

## 7. Batch Task Execution

Batch tasks were executed using **Run new task** in ECS.

### Example: Computation Task

Command override:

```text
python
computation-generator.py
```

Environment variables:

```text
OUTPUT_BUCKET=project3-artifacts
OUTPUT_PREFIX=batch/computation/
```

Result:

* Task completed successfully
* Artifacts written to S3
* Task stopped with `EssentialContainerExited`

The same execution pattern was followed for the e-commerce and weather tasks, with additional variables such as `INPUT_BUCKET` where required.

---

## 8. Streaming Task Execution

### Representative Execution: BNB Stream

Command override:

```text
python
web-sockets-runner-bnbusd.py
```

Environment variables:

```text
S3_BUCKET=project3-artifacts
S3_PREFIX=streaming/bnbusd/
MAX_RUNTIME_SECONDS=7200
```

Observed behavior:

* WebSocket connection established
* Event-driven logs emitted
* Task remained running for extended duration

BTC and ETH streams were not re-executed due to identical execution characteristics.

---

## 9. Observability

* CloudWatch Logs used for runtime inspection
* ECS task state transitions monitored
* S3 artifacts used as final success confirmation

`EssentialContainerExited` was treated as a **successful terminal state**.

---

## 10. Execution Result

* All batch workloads executed successfully
* Streaming workload pattern validated via representative run
* ECS/Fargate execution semantics confirmed

This project validates ECS Tasks as the correct abstraction for mixed batch and streaming workloads.
