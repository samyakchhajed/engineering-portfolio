import boto3
from botocore.exceptions import ProfileNotFound, NoCredentialsError, ClientError
import sys, os
from datetime import datetime

# =========================
# CONFIGURATION (EXPLICIT)
# =========================
AWS_PROFILE = "phase1"


def print_header():
    print("=" * 70)
    print("S3 MANAGER — PHASE A (READ-ONLY)")
    print(f"AWS Profile : {AWS_PROFILE}")
    print("Mode        : READ-ONLY (No changes will be made)")
    print("=" * 70)


def create_s3_client():
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        return session.client("s3")
    except ProfileNotFound:
        print("ERROR: AWS profile not found.")
        sys.exit(1)
    except NoCredentialsError:
        print("ERROR: AWS credentials not available.")
        sys.exit(1)


def get_bucket_region(s3_client, bucket_name):
    try:
        response = s3_client.get_bucket_location(Bucket=bucket_name)
        region = response.get("LocationConstraint")
        return region if region else "us-east-1"
    except ClientError:
        return "Unknown"


def get_public_access_status(s3_client, bucket_name):
    try:
        response = s3_client.get_public_access_block(Bucket=bucket_name)
        config = response.get("PublicAccessBlockConfiguration", {})
        if not config:
            return "NOT CONFIGURED"
        try:
            if all(config.values()):
                return "BLOCKED"
            return "PARTIAL / CUSTOM"
        except Exception:
            return "PARTIAL / CUSTOM"
    except ClientError:
        return "NOT CONFIGURED"


def get_public_access_config(s3_client, bucket_name):
    try:
        response = s3_client.get_public_access_block(Bucket=bucket_name)
        return response["PublicAccessBlockConfiguration"]
    except ClientError:
        return None


def set_public_access(s3_client, bucket_name, block=True):
    config = {
        "BlockPublicAcls": block,
        "IgnorePublicAcls": block,
        "BlockPublicPolicy": block,
        "RestrictPublicBuckets": block,
    }

    try:
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration=config
        )
    except ClientError as e:
        print(f"ERROR: Failed to update public access: {e}")
        sys.exit(1)


def get_object_count(s3_client, bucket_name, max_keys=1000):
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            MaxKeys=max_keys
        )
        return response.get("KeyCount", 0)
    except ClientError:
        return "ACCESS DENIED"


def list_buckets(s3_client):
    try:
        return s3_client.list_buckets().get("Buckets", [])
    except ClientError as e:
        print(f"ERROR: Unable to list buckets: {e}")
        sys.exit(1)


def confirm_s3_action(action, details):
    print("\nACTION CONFIRMATION")
    print("-" * 40)
    print(f"Action : {action}")
    for k, v in details.items():
        print(f"{k:<12}: {v}")
    print("-" * 40)
    choice = input("Type YES to continue: ")
    return choice == "YES"


def confirm_bucket_deletion(bucket_name):
    print("\n!!! BUCKET DELETION WARNING !!!")
    print("=" * 50)
    print("YOU ARE ABOUT TO DELETE AN S3 BUCKET")
    print("THIS ACTION IS IRREVERSIBLE")
    print("BUCKET MUST BE EMPTY")
    print("=" * 50)
    print(f"Bucket Name : {bucket_name}")
    print("=" * 50)

    typed = input(f"Type DELETE {bucket_name} to confirm: ")
    return typed == f"DELETE {bucket_name}"


def confirm_empty_bucket(bucket_name):
    print("\n!!! DATA DESTRUCTION WARNING !!!")
    print("=" * 50)
    print("YOU ARE ABOUT TO PERMANENTLY DELETE ALL OBJECTS")
    print("THIS ACTION IS IRREVERSIBLE")
    print("=" * 50)
    print(f"Bucket Name : {bucket_name}")
    print("=" * 50)

    typed = input(f"Type EMPTY {bucket_name} to confirm: ")
    return typed == f"EMPTY {bucket_name}"


def create_bucket(s3_client, bucket_name, region):
    try:
        if region == "us-east-1":
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region}
            )
    except ClientError as e:
        print(f"ERROR: Failed to create bucket: {e}")
        sys.exit(1)

def upload_file(s3_client, bucket_name, file_path):
    try:
        key = os.path.basename(file_path)
        s3_client.upload_file(file_path, bucket_name, key)
    except ClientError as e:
        print(f"ERROR: Failed to upload file: {e}")
        sys.exit(1)


def empty_bucket(s3_client, bucket_name):
    try:
        print(f"\nStarting deletion for bucket: {bucket_name}")
        while True:
            # List objects
            response = s3_client.list_objects_v2(Bucket=bucket_name)
            
            if 'Contents' not in response:
                print("Bucket is already empty.")
                break
                
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            
            if not objects_to_delete:
                break
                
            print(f"Deleting batch of {len(objects_to_delete)} objects...")
            
            # Delete batch
            s3_client.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': objects_to_delete}
            )
            
            # If not truncated, we are done
            if not response.get('IsTruncated'):
                print("Bucket emptied successfully.")
                break
                
    except ClientError as e:
        print(f"ERROR: Failed to empty bucket: {e}")
        sys.exit(1)


def delete_bucket(s3_client, bucket_name):
    try:
        s3_client.delete_bucket(Bucket=bucket_name)
    except ClientError as e:
        print(f"ERROR: Failed to delete bucket: {e}")
        sys.exit(1)


def main():
    print_header()
    s3 = create_s3_client()

    buckets = list_buckets(s3)

    if not buckets:
        print("No S3 buckets found.")
        return

    print(
        f"{'Bucket Name':<30} {'Region':<15} {'Created':<20} "
        f"{'Public Access':<20} {'Object Count'}"
    )
    print("-" * 120)

    public_buckets = 0

    for bucket in buckets:
        name = bucket["Name"]
        created = bucket["CreationDate"].strftime("%Y-%m-%d %H:%M:%S")
        region = get_bucket_region(s3, name)
        public_status = get_public_access_status(s3, name)
        obj_count = get_object_count(s3, name)

        if public_status != "BLOCKED":
            public_buckets += 1

        print(
            f"{name:<30} {region:<15} {created:<20} "
            f"{public_status:<20} {obj_count}"
        )

    print("-" * 120)
    print(f"Total buckets          : {len(buckets)}")
    print(f"Public access enabled  : {public_buckets}")
    print("\nS3 inspection complete. No changes were performed.")

    if len(sys.argv) == 1:
        return

    if len(sys.argv) < 3:
        print("Usage:")  # Always use path of aws_s3_manager.py
        print("  python aws_s3_manager.py")
        print("  python aws_s3_manager.py create-bucket <bucket-name> <region>")
        print("  python aws_s3_manager.py upload <bucket-name> <local-file-path>")
        print("  python aws_s3_manager.py empty-bucket <bucket-name>")
        print("  python aws_s3_manager.py delete-bucket <bucket-name>")
        print("  python aws_s3_manager.py toggle-public-access <bucket-name> <on|off>")
        sys.exit(1)

    action = sys.argv[1]

    if action == "create-bucket":
        if len(sys.argv) != 4:
            print("ERROR: create-bucket requires <bucket-name> <region>")
            sys.exit(1)

        bucket_name = sys.argv[2]
        region = sys.argv[3]

        if confirm_s3_action(
            "CREATE BUCKET",
            {"Bucket": bucket_name, "Region": region}
        ):
            create_bucket(s3, bucket_name, region)
            print("\nBucket created successfully.")
        else:
            print("\nAction cancelled.")

    elif action == "upload":
        if len(sys.argv) != 4:
            print("ERROR: upload requires <bucket-name> <local-file-path>")
            sys.exit(1)

        bucket_name = sys.argv[2]
        file_path = sys.argv[3]

        if not os.path.exists(file_path):
            print("ERROR: File does not exist.")
            sys.exit(1)

        if confirm_s3_action(
            "UPLOAD FILE",
            {"Bucket": bucket_name, "File": file_path}
        ):
            upload_file(s3, bucket_name, file_path)
            print("\nFile uploaded successfully.")
        else:
            print("\nAction cancelled.")

    elif action == "empty-bucket":
        if len(sys.argv) != 3:
            print("ERROR: empty-bucket requires <bucket-name>")
            sys.exit(1)

        bucket_name = sys.argv[2]

        if confirm_empty_bucket(bucket_name):
            empty_bucket(s3, bucket_name)
        else:
            print("\nEmpty bucket action cancelled.")

    elif action == "delete-bucket":
        if len(sys.argv) != 3:
            print("ERROR: delete-bucket requires <bucket-name>")
            sys.exit(1)

        bucket_name = sys.argv[2]

        if confirm_bucket_deletion(bucket_name):
            delete_bucket(s3, bucket_name)
            print("\nBucket deleted successfully.")
        else:
            print("\nBucket deletion cancelled.")
    
    elif action == "toggle-public-access":
        if len(sys.argv) != 4:
            print("ERROR: toggle-public-access requires <bucket-name> <on|off>")
            sys.exit(1)

        bucket_name = sys.argv[2]
        mode = sys.argv[3]

        current = get_public_access_config(s3, bucket_name)
        print("\nCURRENT PUBLIC ACCESS CONFIG:")
        print(current if current else "NOT CONFIGURED")

        if mode not in ["on", "off"]:
            print("ERROR: Mode must be 'on' or 'off'")
            sys.exit(1)

        block = True if mode == "on" else False

        if confirm_s3_action(
            "TOGGLE PUBLIC ACCESS",
            {"Bucket": bucket_name, "Set Block": block}
        ):
            set_public_access(s3, bucket_name, block)
            print("\nPublic access configuration updated.")
        else:
            print("\nAction cancelled.")

    else:
        print("ERROR: Invalid action.")
        sys.exit(1)


if __name__ == "__main__":
    main()
