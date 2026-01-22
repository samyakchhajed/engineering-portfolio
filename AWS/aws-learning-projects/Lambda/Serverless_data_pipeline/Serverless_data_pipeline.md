# Serverless Data Pipeline v1 (S3 → Lambda → S3)

## 1) What this teaches (Core Learning)
- **Push-based architecture**: Shifting from human-triggered actions to data-driven automation.
- **Permission Layering**: Understanding that **invocation permissions** (allowing S3 to start Lambda) are distinct from **execution permissions** (what Lambda can do once running).
- **Recursive Prevention**: Using prefix-based isolation to prevent infinite execution loops in serverless pipelines.
- **Invisible Execution**: Event-driven systems execute without human control, making CloudWatch logs the primary debugging and verification tool.

## 2) Goal (1–2 lines)
Build a fully event-driven serverless pipeline where uploading a CSV to an S3 bucket automatically triggers a Lambda function to generate and store a JSON summary.

## 3) Architecture / Flow (simple)
1. **Trigger**: An upstream system (Project 3 Lambda) uploads a CSV file to `s3://bucket/synthetic-data/`.
2. **Event**: S3 emits an `ObjectCreated` event.
3. **Invocation**: Lambda is automatically invoked by S3 via a resource-based policy.
4. **Processing**: Lambda downloads the CSV, processes it in `/tmp`, and generates a JSON summary.
5. **Persistence**: The JSON artifact is written back to `s3://bucket/summaries/`.

## 4) AWS Services + Why they were used
- **Amazon S3**: Acts as both the trigger source (via events) and the system of record for input/output artifacts.
- **AWS Lambda**: Provides the event-driven compute to process data automatically upon arrival.
- **IAM Roles**: Governs runtime permissions (Read/Write) for the Lambda function.
- **CloudWatch Logs**: Essential for monitoring and verifying the non-interactive execution flow.

## 5) Recreation Guide (Do-this checklist)
### Setup
- Create an **IAM Role for Lambda 2** with `s3:GetObject`, `s3:HeadObject`, and `s3:PutObject` permissions.
- Configure a **Resource-Based Policy** on Lambda 2 to allow `s3.amazonaws.com` to perform `lambda:InvokeFunction`.
- Set up an **S3 Event Notification** on the source bucket filtered by the prefix `synthetic-data/` and suffix `.csv`.

### Execution
- Ensure no manual "Test" invocation is used; trigger the pipeline by uploading a CSV to the `synthetic-data/` prefix.
- Lambda will automatically receive metadata about the file and begin processing.

### Verification (Proof checks)
- Verify that a JSON summary file appears in the `summaries/` prefix.
- Check CloudWatch logs to confirm the sequence: S3 event received → CSV downloaded → JSON uploaded.

### Cleanup
- Delete the test CSV and JSON artifacts from S3 to maintain cost discipline.
- System naturally returns to an idle state with no residual compute running.

## 6) IAM / Security notes (important only)
- **Permission Separation**: Ensure the execution role has `s3:GetObject` (read) and `s3:PutObject` (write) permissions, while the resource-based policy handles invocation.
- **Zero Credentials**: No access keys or credentials should be present in the code or environment variables.
- **No Cross-Role Sharing**: Each Lambda function must use its own specific IAM role.

## 7) Common errors & fixes
- **Error:** Recursive Invocation (Infinite Loop).
  **Cause:** Lambda writes its output to the same prefix that triggers it.
  **Fix:** Implement strict prefix isolation (Input: `synthetic-data/`, Output: `summaries/`).
- **Error:** 403 Forbidden during execution.
  **Cause:** Lambda execution role lacks `s3:GetObject` permission.
  **Fix:** Attach S3 read permissions to the Lambda execution role.
- **Error:** Silent Non-Invocation.
  **Cause:** Missing or stale resource-based policy preventing S3 from triggering Lambda.
  **Fix:** Recreate the S3 trigger to force permission regeneration.

## 8) Key commands / snippets (if any)
```python
# Lambda 2 logic: Reading from S3 and writing to a different prefix
import boto3
import json

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    # S3 event provides bucket and key metadata
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Download to /tmp
    download_path = f'/tmp/{key.split("/")[-1]}'
    s3.download_file(bucket, key, download_path)
    
    # ... processing logic ...
    
    # Upload JSON to non-triggering prefix
    output_key = f"summaries/summary_{key.split('/')[-1].replace('.csv', '.json')}"
    s3.upload_file('/tmp/summary.json', bucket, output_key)

```

## 9) Mini interview points (optional but useful)

* **Push vs. Pull**: This is a push-based architecture where S3 "pushes" work to Lambda, minimizing idle time and manual intervention.
* **Statelessness in Pipelines**: Lambda does not persist state between runs; S3 is the only persistence layer.
* **Prefix-Based Isolation**: This is a critical safety mechanism in S3-triggered pipelines to avoid the cost and resource exhaustion of infinite loops.
