# Lambda Synthetic Data Generator

## 1) What this teaches 
- Lambda is **ephemeral compute**, not just "Python in the cloud".
- **Execution roles** are the primary authority; IAM user permissions do not affect Lambda at runtime.
- The `/tmp` directory is the only writable filesystem available during execution.
- **IAM is the primary failure domain** in AWS; most issues are resolved via configuration, not code.
- Success is defined by artifacts and structured logs, not standard output or interactive debugging.

## 2) Goal 
Build a serverless, stateless generator that produces synthetic tabular data, persists it to S3, and utilizes IAM roles for all execution permissions.

## 3) Architecture / Flow 
1. **Invocation:** Lambda is triggered manually via a test event.
2. **Generation:** Synthetic data is generated in-memory.
3. **Local Write:** A temporary CSV file is written to the `/tmp` directory.
4. **Persistence:** The CSV artifact is uploaded to Amazon S3 using `boto3`.
5. **Cleanup:** The execution ends with no retained state or persistent compute.

## 4) AWS Services + Why they were used
- **AWS Lambda:** Provides ephemeral, serverless compute that runs code on-demand.
- **Amazon S3:** Serves as the permanent system of record for generated artifacts.
- **IAM Roles:** Controls runtime permissions following serverless security best practices.
- **CloudWatch Logs:** Captures structured logs and provides execution visibility.

## 5) Recreation Guide 
### Setup
- Create an IAM Role named `lambda-week2-s3-role` with `AWSLambdaBasicExecutionRole` and `AmazonS3FullAccess`.
- Ensure the role's Trusted Entity is set to `lambda.amazonaws.com`.
- Prepare an S3 bucket (e.g., `tic-tac-toe-testtrial`) for storage.

### Execution
- Deploy the Python script using `boto3` to handle S3 uploads.
- Use the `RequestID` in the filename to ensure each invocation produces a unique artifact.
- Trigger the function using a manual test event in the AWS Console.

### Verification (Proof checks)
- Confirm the Lambda execution status is "Success".
- Check CloudWatch logs for the full execution flow and structured log entries.
- Verify the presence of the CSV file in S3 at the `synthetic-data/` prefix.

### Cleanup
- No manual compute cleanup is required; Lambda terminates automatically.
- Delete S3 artifacts if they are no longer needed for cost discipline.

## 6) IAM / Security notes
- **Role Separation:** The IAM User is for configuration; the IAM Role is for runtime execution.
- **Zero Credentials:** No access keys or sensitive data are stored in code or environment variables.
- **Assumed Identity:** Lambda always runs as an assumed role, not as the user who created it.

## 7) Common errors & fixes
- **Error:** `AccessDenied` during S3 upload.
  **Cause:** Missing `s3:PutObject` permission on the **execution role** (often mistaken for user permission issues).
  **Fix:** Add appropriate S3 permissions to `lambda-week2-s3-role`.
- **Error:** File write failure.
  **Cause:** Attempting to write to a directory other than `/tmp`.
  **Fix:** Ensure all local file operations target the `/tmp/` path.

## 8) Key commands / snippets
```python
# Boto3 logic for uploading from Lambda's temporary filesystem
import boto3
import os

def lambda_handler(event, context):
    file_path = '/tmp/sales_data.csv'
    # ... logic to generate data and save to file_path ...
    
    s3 = boto3.client('s3')
    s3.upload_file(file_path, 'tic-tac-toe-testtrial', f'synthetic-data/sales_data_{context.aws_request_id}.csv')

```

## 9) Mini interview points (optional but useful)

* **Idempotency:** Using the `Request ID` for filenames ensures that retries or multiple invocations do not overwrite data.
* **Statelessness:** Since Lambda is ephemeral, any data that must persist must be moved to a service like S3 before the function ends.
* **Performance:** Generating data in-memory and writing only once to `/tmp` optimizes execution time and reduces costs.