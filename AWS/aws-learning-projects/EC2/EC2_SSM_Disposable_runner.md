# EC2 Disposable Runner

## 1) What this teaches (Core Learning)
- EC2 should be treated as disposable, stateless compute.
- IAM roles are mandatory for secure automation, replacing the need for static access keys.
- Systems Manager (SSM) can fully replace SSH for controlled, non-interactive execution.
- Using S3 as the "system of record" for all persistent data and logs.
- SDK-based access (boto3) is safer and more reliable for automation than CLI dependencies.
- Understanding when to choose EC2 over Lambda (e.g., for longer jobs or custom dependencies).

## 2) Goal (1–2 lines)
Build a secure, temporary EC2-based automation runner that executes a Data Analysis (DA) job without SSH, persists outputs to S3, and terminates compute resources to enforce cost discipline.

## 3) Architecture / Flow (simple)
1. Launch EC2 instance with the attached IAM role `EC2-Automation-Runner-Role`.
2. Instance registers automatically with Systems Manager (SSM).
3. Execute Python DA script via SSM Run Command (no interactive login).
4. Script generates dataset, CSV output, plot (PNG), and execution logs.
5. Artifacts are uploaded to S3 using `boto3`.
6. EC2 instance is terminated immediately after verification.

## 4) AWS Services + Why they were used
- **EC2:** Used as temporary compute for jobs requiring custom dependencies or longer runtimes.
- **S3:** Acts as the system of record for storing output artifacts (plot, CSV, logs).
- **IAM:** Controls permissions via roles and policies following least-privilege principles.
- **Systems Manager (SSM):** Replaces SSH for secure command execution without inbound security rules.
- **CloudWatch Logs:** Provides visibility into execution status.

## 5) Recreation Guide (Do-this checklist)
### Setup
- Create `EC2-Automation-Runner-Role` with `AmazonSSMManagedInstanceCore`, `CloudWatchLogsFullAccess`, and `S3-ReadWrite-Automation-Scoped` policies.
- Create `PassRole-For-EC2-SSM` policy with `iam:PassRole` permissions to the IAM User.
- Prepare an S3 bucket or specific prefix for artifacts.

### Execution
- Launch an EC2 instance (Amazon Linux, `t2.micro`/`t3.micro`) with no key pair and no inbound security group rules.
- Attach the `EC2-Automation-Runner-Role` during launch.
- Use SSM Run Command with the `AWS-RunShellScript` document to execute the Python script.

### Verification (Proof checks)
- Confirm SSM command status is "Success".
- Verify `plot.png`, `output.csv`, and `run.log` are present in the designated S3 bucket.

### Cleanup
- Terminate the EC2 instance immediately after verification to enforce cost discipline.

## 6) IAM / Security notes (important only)
- **Zero-Trust Model:** No SSH keys, no inbound security group rules, and no access keys inside EC2.
- **PassRole Policy:** Allows the user to attach specific IAM roles to EC2 instances; explicitly limited to approved execution roles.
- **S3 Scoped Policy:** Limits EC2 access (GetObject, PutObject, ListBucket) to a single bucket or prefix.

## 7) Common errors & fixes
- **Error:** EC2 launch failed.
  **Cause:** Missing `iam:PassRole` permissions for the IAM user.
  **Fix:** Attach the `PassRole-For-EC2-SSM` policy to the user.
- **Error:** AWS CLI dependency broke.
  **Cause:** Issues with CLI environment or path during automation.
  **Fix:** Switch to `boto3` for uploading artifacts as it uses the IAM role automatically.
- **Error:** SSM registration issues.
  **Cause:** Missing required IAM permissions or network connectivity.
  **Fix:** Ensure `AmazonSSMManagedInstanceCore` is attached to the instance role.

## 8) Key commands / snippets (if any)
```python
# Boto3 upload example (preferred for automation)
import boto3
s3 = boto3.client('s3')
s3.upload_file('plot.png', 'all-project-bucket-general-use', 'da-runs/run-001/plot.png')

```

## 9) Mini interview points (optional but useful)

* **Why use SSM instead of SSH?** SSM follows zero-trust (no open ports) and provides a centralized audit trail via IAM.
* **What is the benefit of "Disposable Compute"?** It enforces statelessness, cost safety, and reproducibility.
* **When should you use Lambda instead of EC2?** Use Lambda for short, event-driven jobs that don't require custom environment dependencies.