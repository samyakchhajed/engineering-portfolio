import boto3
from botocore.exceptions import ProfileNotFound, NoCredentialsError, ClientError
from datetime import datetime, timezone
import sys

# =========================
# CONFIGURATION
# =========================
AWS_PROFILE = "phase1"

# Service-Specific Thresholds (In Days)
EC2_THRESHOLD = 2    # Aggressive: EC2 should be disposable 
S3_THRESHOLD = 30     # Moderate: Buckets often survive project phases 
CW_THRESHOLD = 7      # Weekly: Logs should have retention set

def print_header():
    print("=" * 85)
    print("AWS CLEANER — HYGIENE & REASONING TOOL")
    print(f"AWS Profile : {AWS_PROFILE}")
    print(f"Thresholds  : EC2={EC2_THRESHOLD}d, S3={S3_THRESHOLD}d, CloudWatch={CW_THRESHOLD}d")
    print("=" * 85)

def create_session():
    try:
        return boto3.Session(profile_name=AWS_PROFILE)
    except (ProfileNotFound, NoCredentialsError):
        print("ERROR: AWS credentials/profile not found.")
        sys.exit(1)

def get_age_days(creation_date):
    now = datetime.now(timezone.utc)
    delta = now - creation_date
    return delta.days

def check_ec2_hygiene(session):
    print("\n[ EC2 HYGIENE CHECK ]")
    print(f"{'Instance ID':<20} {'State':<12} {'Age (Days)':<12} {'Reasoning Signal'}")
    print("-" * 85)
    ec2 = session.client('ec2')
    instances = ec2.describe_instances()
    
    for reservation in instances['Reservations']:
        for inst in reservation['Instances']:
            name = inst.get('InstanceId')
            state = inst['State']['Name']
            age = get_age_days(inst['LaunchTime'])
            
            signal = "OK"
            if state == 'stopped' and age >= EC2_THRESHOLD:
                signal = f"COST RISK (Stopped for {age} days. Delete EBS?)"
            elif state == 'running' and age >= EC2_THRESHOLD:
                signal = f"DISCIPLINE ALERT (Running for {age} days. Is work done?)"
                
            print(f"{name:<20} {state:<12} {age:<12} {signal}")

def check_s3_hygiene(session):
    print("\n[ S3 HYGIENE CHECK ]")
    print(f"{'Bucket Name':<35} {'Age (Days)':<12} {'Reasoning Signal'}")
    print("-" * 85)
    s3 = session.client('s3')
    buckets = s3.list_buckets()['Buckets']
    
    for b in buckets:
        name = b['Name']
        age = get_age_days(b['CreationDate'])
        objects = s3.list_objects_v2(Bucket=name, MaxKeys=1)
        is_empty = 'Contents' not in objects
        
        signal = "OK"
        if is_empty and age >= S3_THRESHOLD:
            signal = "ABANDONED (Empty and Old)"
        elif is_empty:
            signal = "IDLE (Empty but New)"
            
        print(f"{name:<35} {age:<12} {signal}")

def check_cloudwatch_hygiene(session):
    print("\n[ CLOUDWATCH LOGS HYGIENE CHECK ]")
    print(f"{'Log Group Name':<45} {'Retention':<12} {'Reasoning Signal'}")
    print("-" * 85)
    logs = session.client('logs')
    groups = logs.describe_log_groups()['logGroups']
    
    for g in groups:
        name = g['logGroupName']
        retention = g.get('retentionInDays', 'Never')
        
        signal = "OK"
        if retention == 'Never':
            signal = "HYGIENE RISK (Infinite storage enabled)"
        
        print(f"{name:<45} {retention:<12} {signal}")

def main():
    session = create_session()
    print_header()
    check_ec2_hygiene(session)
    check_s3_hygiene(session)
    check_cloudwatch_hygiene(session)
    print("\n" + "=" * 85)
    print("ANALYSIS COMPLETE. Use Manager scripts to perform cleanup.")
    print("=" * 85)

if __name__ == "__main__":
    main()