import json
import os
import time
import uuid
import boto3
import numpy as np
import pandas as pd
from botocore.exceptions import ClientError
from datetime import datetime

# ======================
# AWS Clients
# ======================
ddb = boto3.client("dynamodb")
s3 = boto3.client("s3")
sns = boto3.client("sns")

# ======================
# Environment Variables
# ======================
DDB_TABLE = os.environ["DDB_TABLE"]
S3_BUCKET = os.environ["S3_BUCKET"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

# ======================
# Lambda Entry Point
# ======================
def lambda_handler(event, context):
    """
    One invocation = one date-keyed unit of work.
    Safe to retry. Stateless. Deterministic.
    """

    job_date = event.get("date")
    if not job_date:
        raise ValueError("Event must include 'date' (YYYY-MM-DD)")

    run_id = str(uuid.uuid4())
    start_ts = int(time.time())

    try:
        # 1️⃣ Idempotency guard
        mark_job_running(job_date, run_id, start_ts)

        # 2️⃣ Heavy computation
        result = run_scientific_computation(job_date)

        # 3️⃣ Write output to S3
        s3_key = f"project2/date={job_date}/result.json"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=json.dumps(result, indent=2),
            ContentType="application/json"
        )

        # 4️⃣ Mark success
        mark_job_success(job_date, s3_key)

        return {
            "status": "SUCCESS",
            "date": job_date,
            "s3_key": s3_key
        }

    except Exception as e:
        # Ensure failure path never crashes again
        try:
            mark_job_failed(job_date, str(e))
            notify_failure(job_date, str(e))
        except Exception as inner:
            print("Secondary failure while handling error:", inner)

        raise


# ======================
# Scientific Computation
# ======================
def run_scientific_computation(job_date: str) -> dict:
    """
    Bounded, deterministic computation.
    """

    np.random.seed(42)

    x = np.linspace(0, 10, 10_000)
    noise = np.random.normal(0, 0.3, size=len(x))
    y = np.sin(x) + noise

    df = pd.DataFrame({"x": x, "y": y})

    return {
        "date": job_date,
        "samples": int(len(df)),
        "mean": float(df["y"].mean()),
        "std_dev": float(df["y"].std()),
        "min": float(df["y"].min()),
        "max": float(df["y"].max()),
        "generated_at": datetime.utcnow().isoformat()
    }


# ======================
# DynamoDB Helpers
# ======================
def mark_job_running(job_date, run_id, start_ts):
    """
    Create record only if it does not exist.
    Enforces idempotency.
    """
    try:
        ddb.put_item(
            TableName=DDB_TABLE,
            Item={
                "date": {"S": job_date},
                "run_id": {"S": run_id},
                "status": {"S": "RUNNING"},
                "started_at": {"N": str(start_ts)}
            },
            ConditionExpression="attribute_not_exists(#d)",
            ExpressionAttributeNames={
                "#d": "date"
            }
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise RuntimeError(f"Job for {job_date} already exists")
        raise


def mark_job_success(job_date, s3_key):
    ddb.update_item(
        TableName=DDB_TABLE,
        Key={"date": {"S": job_date}},
        UpdateExpression="""
            SET #s = :success,
                completed_at = :ts,
                s3_key = :s3
        """,
        ExpressionAttributeNames={
            "#s": "status"
        },
        ExpressionAttributeValues={
            ":success": {"S": "SUCCESS"},
            ":ts": {"N": str(int(time.time()))},
            ":s3": {"S": s3_key}
        }
    )


def mark_job_failed(job_date, error_message):
    ddb.update_item(
        TableName=DDB_TABLE,
        Key={"date": {"S": job_date}},
        UpdateExpression="""
            SET #s = :failed,
                completed_at = :ts,
                #err = :err
        """,
        ExpressionAttributeNames={
            "#s": "status",
            "#err": "error_message"
        },
        ExpressionAttributeValues={
            ":failed": {"S": "FAILED"},
            ":ts": {"N": str(int(time.time()))},
            ":err": {"S": error_message[:500]}
        }
    )


# ======================
# SNS Notification
# ======================
def notify_failure(job_date, error_message):
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=f"Project 2 Failure — {job_date}",
        Message=f"Job failed for {job_date}\n\nError:\n{error_message}"
    )
