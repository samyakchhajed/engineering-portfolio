#!/usr/bin/env python3

import boto3
import sys
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

# =========================
# CONFIGURATION
# =========================
DEFAULT_PROFILE = "phase1"

def create_session(profile: str):
    try:
        session = boto3.Session(profile_name=profile)
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        print(f"\n[ACCOUNT VERIFIED]")
        print(f"Profile: {profile}")
        print(f"Account: {identity.get('Account')}")
        print(f"ARN:     {identity.get('Arn')}\n")
        return session
    except (NoCredentialsError, PartialCredentialsError):
        print("[ERROR] No credentials found.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Session failed: {e}")
        sys.exit(1)

def get_enabled_regions(session):
    """Dynamically discovers all enabled regions in the account."""
    ec2 = session.client('ec2', region_name='us-east-1')
    try:
        regions = [r['RegionName'] for r in ec2.describe_regions()['Regions']]
        return regions
    except ClientError as e:
        print(f"[ERROR] Could not discover regions: {e}")
        return ['ap-south-1'] # Fallback

def is_protected(tags):
    """Checks for the KeepUntil tag logic."""
    if not tags: return False
    for tag in tags:
        if tag['Key'] == 'KeepUntil':
            try:
                keep_date = datetime.strptime(tag['Value'], '%Y-%m-%d')
                if keep_date > datetime.now():
                    return True
            except ValueError:
                continue
    return False

def manual_confirm(prompt_text: str, code: str) -> bool:
    print(f"\n>>> {prompt_text}")
    print(f"To authorize, type exactly: {code} (or press Enter to skip)")
    val = input("> ").strip()
    return val == code

# =========================
# PHASE A: THE SWEEP
# =========================

def global_sweep(session, regions):
    inventory = {}
    print("Performing Global Discovery Sweep (Fast & Quiet)...")
    
    # S3 is Global
    s3_client = session.client('s3')
    inventory['global'] = {'s3': [b['Name'] for b in s3_client.list_buckets().get('Buckets', [])]}

    for region in regions:
        region_data = {}
        
        # EC2 & Orphans
        ec2 = session.client('ec2', region_name=region)
        instances = ec2.describe_instances()
        region_data['ec2'] = [i['InstanceId'] for r in instances.get('Reservations', []) 
                              for i in r.get('Instances', []) if i['State']['Name'] != 'terminated' 
                              and not is_protected(i.get('Tags', []))]
        
        volumes = ec2.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
        region_data['ebs'] = [v['VolumeId'] for v in volumes.get('Volumes', [])]
        
        eips = ec2.describe_addresses()
        region_data['eip'] = [a['AllocationId'] for a in eips.get('Addresses', []) if 'InstanceId' not in a]

        # Lambda
        lam = session.client('lambda', region_name=region)
        region_data['lambda'] = [f['FunctionName'] for f in lam.list_functions().get('Functions', [])]
        
        # DynamoDB
        ddb = session.client('dynamodb', region_name=region)
        region_data['ddb'] = ddb.list_tables().get('TableNames', [])
        
        # CloudWatch Logs
        logs = session.client('logs', region_name=region)
        region_data['logs'] = [g['logGroupName'] for g in logs.describe_log_groups().get('logGroups', [])]

        # Only add region to inventory if it has resources
        if any(region_data.values()):
            inventory[region] = region_data
            
    return inventory

def print_summary(inventory):
    print("\n" + "="*80)
    print(f"{'REGION':<15} | {'SERVICE':<12} | {'COUNT':<5} | {'RESOURCES'}")
    print("-"*80)
    for loc, services in inventory.items():
        for svc, items in services.items():
            if items:
                print(f"{loc:<15} | {svc:<12} | {len(items):<5} | {items}")
    print("="*80 + "\n")

# =========================
# PHASE B: APPROVALS
# =========================

def process_cleanup(session, inventory):
    # S3 Approval
    buckets = inventory.get('global', {}).get('s3', [])
    if buckets:
        print("[ ACTION REQUIRED: GLOBAL S3 ]")
        for b in buckets:
            if manual_confirm(f"Empty and Delete S3 Bucket '{b}'?", "DELETE-BUCKET"):
                s3_res = session.resource('s3')
                bucket = s3_res.Bucket(b)
                bucket.object_versions.delete()
                bucket.delete()
                print(f"  [OK] {b} removed.")

    # Regional Approvals
    for region in [r for r in inventory if r != 'global']:
        print(f"\n[ ACTION REQUIRED: {region} ]")
        data = inventory[region]

        # 1. Compute
        if data['ec2'] or data['lambda']:
            if manual_confirm(f"Stop EC2s {data['ec2']} and Delete Lambdas {data['lambda']}?", "SHUTDOWN-BATCH"):
                if data['ec2']: session.client('ec2', region_name=region).stop_instances(InstanceIds=data['ec2'])
                if data['lambda']: 
                    l_client = session.client('lambda', region_name=region)
                    for f in data['lambda']: l_client.delete_function(FunctionName=f)
                print("  [OK] Compute cleaned.")

        # 2. Orphans
        if data['ebs'] or data['eip']:
            if manual_confirm(f"Delete Volumes {data['ebs']} and Release IPs {data['eip']}?", "PURGE-ORPHANS"):
                ec2 = session.client('ec2', region_name=region)
                for v in data['ebs']: ec2.delete_volume(VolumeId=v)
                for i in data['eip']: ec2.release_address(AllocationId=i)
                print("  [OK] Orphans purged.")

        # 3. Database & Logs
        if data['ddb'] or data['logs']:
            if manual_confirm(f"Delete Tables {data['ddb']} and Logs {data['logs']}?", "PURGE-DATA"):
                if data['ddb']:
                    db = session.client('dynamodb', region_name=region)
                    for t in data['ddb']: db.delete_table(TableName=t)
                if data['logs']:
                    lg = session.client('logs', region_name=region)
                    for g in data['logs']: lg.delete_log_group(logGroupName=g)
                print("  [OK] Data purged.")

# =========================
# MAIN EXECUTION
# =========================

def main():
    session = create_session(DEFAULT_PROFILE)
    regions = get_enabled_regions(session)
    
    inventory = global_sweep(session, regions)
    
    if not any(any(v) for v in inventory.values()):
        print("No resources found in any enabled region. Account is clean!")
        return

    print_summary(inventory)
    process_cleanup(session, inventory)
    
    print("\nPerforming Final Verification Audit...")
    final_inv = global_sweep(session, regions)
    print_summary(final_inv)

if __name__ == "__main__":
    main()