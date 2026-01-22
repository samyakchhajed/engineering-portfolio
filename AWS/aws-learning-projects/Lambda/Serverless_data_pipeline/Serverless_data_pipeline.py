import json
import csv
import logging
import boto3
import os

# ---------- INIT PHASE ----------
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")

OUTPUT_PREFIX = "summaries/"

# ---------- INVOCATION PHASE ----------
def lambda_handler(event, context):
    logger.info("Week 3 Lambda triggered by S3")

    record = event["Records"][0]
    bucket_name = record["s3"]["bucket"]["name"]
    object_key = record["s3"]["object"]["key"]

    logger.info(f"Processing file: s3://{bucket_name}/{object_key}")

    # Safety guard
    if not object_key.endswith(".csv"):
        logger.info("Not a CSV file. Skipping.")
        return {"status": "ignored"}

    local_csv = "/tmp/input.csv"
    s3.download_file(bucket_name, object_key, local_csv)

    logger.info("CSV downloaded")

    row_count = 0
    total_revenue = 0.0

    with open(local_csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_count += 1
            total_revenue += float(row.get("Revenue", 0))

    summary = {
        "source_file": object_key,
        "total_rows": row_count,
        "total_revenue": total_revenue,
        "processed_request_id": context.aws_request_id
    }

    summary_name = f"summary_{os.path.basename(object_key)}.json"
    local_json = f"/tmp/{summary_name}"

    with open(local_json, "w") as f:
        json.dump(summary, f, indent=2)

    output_key = f"{OUTPUT_PREFIX}{summary_name}"

    s3.upload_file(local_json, bucket_name, output_key)

    logger.info(f"Summary uploaded to s3://{bucket_name}/{output_key}")

    return {
        "status": "success",
        "output": output_key
    }
