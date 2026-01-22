import os
import time
import boto3
from botocore.exceptions import ClientError

TABLE_NAME = os.environ["TABLE_NAME"]
JOB_ID = os.environ["JOB_ID"]
SORT_KEY = "STATE"

COOLDOWN_SECONDS = 3600
FAILURE_BACKOFF = 300

dynamodb = boto3.client("dynamodb")


def lambda_handler(event, context):
    now = int(time.time())

    # 1. Read state
    response = dynamodb.get_item(
        TableName=TABLE_NAME,
        Key={
            "PK": {"S": JOB_ID},
            "SK": {"S": SORT_KEY}
        },
        ConsistentRead=True
    )

    if "Item" not in response:
        print("STATE ITEM MISSING — EXIT")
        return

    item = response["Item"]

    status = item["status"]["S"]
    next_allowed = int(item["next_allowed_run"]["N"])
    version = int(item["version"]["N"])

    print(f"STATE CHECK → status={status}, next_allowed={next_allowed}, version={version}")

    # 2. Gate execution
    if status == "RUNNING":
        print("JOB ALREADY RUNNING — EXIT")
        return

    if now < next_allowed:
        print("RATE LIMITED — EXIT")
        return

    # 3. Acquire lock
    try:
        dynamodb.update_item(
            TableName=TABLE_NAME,
            Key={
                "PK": {"S": JOB_ID},
                "SK": {"S": SORT_KEY}
            },
            ConditionExpression="#s = :idle AND version = :v",
            UpdateExpression="""
                SET #s = :running,
                    last_run_ts = :now,
                    version = :v_next
            """,
            ExpressionAttributeNames={
                "#s": "status"
            },
            ExpressionAttributeValues={
                ":idle": {"S": "IDLE"},
                ":running": {"S": "RUNNING"},
                ":now": {"N": str(now)},
                ":v": {"N": str(version)},
                ":v_next": {"N": str(version + 1)}
            }
        )
    except ClientError as e:
        print("LOCK FAILED — EXIT", e)
        return

    # 4. Execute job
    try:
        print("JOB EXECUTION STARTED")
        time.sleep(1)

        # 5. Mark success
        dynamodb.update_item(
            TableName=TABLE_NAME,
            Key={
                "PK": {"S": JOB_ID},
                "SK": {"S": SORT_KEY}
            },
            UpdateExpression="""
                SET #s = :idle,
                    last_success_ts = :now,
                    run_count = run_count + :one,
                    next_allowed_run = :next,
                    version = :v_next
            """,
            ExpressionAttributeNames={
                "#s": "status"
            },
            ExpressionAttributeValues={
                ":idle": {"S": "IDLE"},
                ":now": {"N": str(now)},
                ":one": {"N": "1"},
                ":next": {"N": str(now + COOLDOWN_SECONDS)},
                ":v_next": {"N": str(version + 2)}
            }
        )

        print("JOB COMPLETED SUCCESSFULLY")

    except Exception as e:
        print("JOB FAILED:", str(e))

        dynamodb.update_item(
            TableName=TABLE_NAME,
            Key={
                "PK": {"S": JOB_ID},
                "SK": {"S": SORT_KEY}
            },
            UpdateExpression="""
                SET #s = :idle,
                    last_error = :err,
                    next_allowed_run = :next,
                    version = :v_next
            """,
            ExpressionAttributeNames={
                "#s": "status"
            },
            ExpressionAttributeValues={
                ":idle": {"S": "IDLE"},
                ":err": {"S": str(e)},
                ":next": {"N": str(now + FAILURE_BACKOFF)},
                ":v_next": {"N": str(version + 2)}
            }
        )
