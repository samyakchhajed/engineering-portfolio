# Execution Steps — Project 2

This document records the **actual execution steps** used to build and validate Project 2.

---

## 1. Lambda Function

- Function name: `project2-daily-scientific-computation`
- Runtime: Python 3.11
- Memory: 1024 MB
- Timeout: 30 seconds
- Package type: Zip
- Architecture: x86_64

The function performs a **bounded scientific computation** and produces a JSON output per execution.

---

## 2. Lambda Layer (NumPy + Pandas)

- Layer name: `lambda-numpy-pandas`
- Purpose: Enable bounded scientific computation
- Runtime compatibility: Python 3.11
- Built using Linux-compatible wheels
- Attached to the Lambda function

No visualization libraries were included.

---

## 3. DynamoDB

- Table name: `project2_execution_state`
- Partition key: `date` (String)
- Capacity mode: On-demand

The table stores:
- Execution status
- Start and completion timestamps
- S3 artifact reference
- Run metadata

---

## 4. S3 Output

- Bucket contains immutable artifacts
- Path format:

  `project2/date=YYYY-MM-DD/result.json`

Each execution produces **one JSON file**.

---

## 5. EventBridge

- Schedule name: `project2-daily-4pm-trigger`
- Schedule type: Fixed rate (daily)
- Time zone: Asia/Kolkata
- Target: Lambda function

EventBridge automates execution with no manual intervention.

---

## 6. Observability

- CloudWatch Logs capture each invocation
- Logs confirm start, execution, and completion
- No silent failures

---

## 7. Execution Result

- Lambda invocation succeeded
- DynamoDB updated with `SUCCESS`
- JSON artifact written to S3
- End-to-end automation verified

---

## 8. Lambda Layer Packaging (NumPy + Pandas)

To support bounded scientific computation in AWS Lambda, NumPy and Pandas were packaged into a custom Lambda Layer using a Linux-compatible build environment.

### Build Environment
- Host OS: Windows
- Linux environment: WSL (Ubuntu)
- Python version: 3.11 (to match Lambda runtime)
- Architecture: x86_64

---

### Commands Used

A clean directory structure was created following Lambda Layer conventions:

```bash
mkdir -p lambda-layer/python/lib/python3.11/site-packages
cd lambda-layer
````

Required libraries were installed directly into the target directory:

```bash
pip install numpy pandas \
  --platform manylinux2014_x86_64 \
  --target python/lib/python3.11/site-packages \
  --implementation cp \
  --python-version 3.11 \
  --only-binary=:all: \
  --upgrade
```

After installation, the directory was compressed into a zip archive:

```bash
zip -r lambda-numpy-pandas.zip python
```

---

### Deployment

* The generated `lambda-numpy-pandas.zip` file was uploaded as a Lambda Layer.
* The layer was attached to the Lambda function `project2-daily-scientific-computation`.
* No dependency code was bundled inside the Lambda function itself.

---

### Design Notes

* Libraries were packaged separately to keep function deployments small.
* Only required computation libraries were included.
* Linux-compatible wheels were enforced to avoid runtime incompatibilities.

This process ensures compatibility with the Lambda execution environment while maintaining clean separation between application logic and dependencies.

---