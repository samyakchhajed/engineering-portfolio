import json
import random
import csv
import os
from datetime import datetime
import logging
import boto3

# ---------- INIT PHASE (runs on cold start) ----------
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")

BUCKET_NAME = "tic-tac-toe-testtrial"
S3_PREFIX = "synthetic-data/"

PRODUCTS = [
    ("Laptop", 50000),
    ("Smartphone", 20000),
    ("Tablet", 30000),
    ("Headphones", 1500),
    ("Smartwatch", 3000),
    ("Camera", 25000),
    ("Printer", 20000),
    ("Monitor", 4000),
    ("Keyboard", 1500),
    ("Gaming Console", 5000),
    ("PS5", 45000),
    ("Xbox", 40000),
]

# ---------- INVOCATION PHASE ----------
def lambda_handler(event, context):
    logger.info("Lambda invocation started")

    num_orders = 500
    today = datetime.utcnow().date()

    tmp_file_path = "/tmp/sales_data.csv"

    logger.info("Generating synthetic order data")

    with open(tmp_file_path, mode="w", newline="") as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow([
            "OrderID",
            "CustomerID",
            "Product",
            "Price",
            "Quantity",
            "OrderDate",
            "Revenue"
        ])

        for i in range(num_orders):
            product, price = random.choice(PRODUCTS)
            quantity = random.randint(1, 5)
            revenue = price * quantity

            writer.writerow([
                f"ORD{i+1:04d}",
                f"CUST{random.randint(1,200):04d}",
                product,
                price,
                quantity,
                today.isoformat(),
                revenue
            ])

    logger.info("CSV written to /tmp")

    s3_key = f"{S3_PREFIX}sales_data_{context.aws_request_id}.csv"

    logger.info("Uploading CSV to S3")

    s3.upload_file(
        Filename = tmp_file_path,
        Bucket = "tic-tac-toe-testtrial",
        Key = s3_key
    )

    logger.info(f"Upload successful: s3://{"tic-tac-toe-testtrial"}/{s3_key}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Synthetic data generated successfully",
            "s3_key": s3_key
        })
    }
