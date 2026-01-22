#!/usr/bin/env python3

import argparse, sys, traceback
from typing import Optional
from datetime import datetime, timedelta, timezone
import time

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

# ---------- Helpers ----------

# Create a boto3 client from a session; wrap in try/except at call sites.
def safe_client(session: boto3.Session, service: str, region_name: Optional[str] = None):
    try:
        if region_name:
            return session.client(service, region_name=region_name)
        return session.client(service)
    except Exception:
        # Let caller handle missing permissions / other errors
        return None

def print_header(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

# ---------- Checks ----------

# Returns identity dict or None on error.
def check_identity(session: boto3.Session):
    print_header("Identity")
    try:
        sts = safe_client(session, "sts")
        if sts is None:
            print("Unable to create STS client (unexpected).")
            return None
        identity = sts.get_caller_identity()
        print(f"Account: {identity.get('Account')}")
        print(f"UserId : {identity.get('UserId')}")
        print(f"ARN    : {identity.get('Arn')}")
        return identity
    except (NoCredentialsError, PartialCredentialsError):
        print("ERROR: No credentials found for the provided profile.")
    except ClientError as e:
        print(f"ERROR calling STS: {e}")
    except Exception:
        print("Unexpected error in check_identity:")
        traceback.print_exc()
    return None

# Report the session region and compare to expected if provided.
def check_region(session: boto3.Session, expected_region: Optional[str]):
    print_header("Region")
    region = session.region_name or "(no default region configured)"
    print(f"Session region: {region}")
    if expected_region:
        if region != expected_region:
            print(f"WARNING: Session region != expected region ({expected_region}).")
            print("  - Some resources you expect may be in another region.")
        else:
            print("Region matches expected region.")

def check_s3(session: boto3.Session):
    print_header("S3")
    try:
        s3 = safe_client(session, "s3")
        if s3 is None:
            print("Unable to create S3 client.")
            return
        resp = s3.list_buckets()
        buckets = resp.get("Buckets", [])
        print(f"Buckets found: {len(buckets)}")
        for b in buckets:
            print(f"  - {b.get('Name')}")
        if not buckets:
            print("No S3 buckets in this account/region (S3 buckets are global to the account).")
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        print(f"S3 ClientError: {code} - {e}")
        if code == "AccessDenied":
            print("  -> You do not have permission to list S3 buckets. Attach AmazonS3ReadOnlyAccess or AmazonS3FullAccess.")
    except Exception:
        print("Unexpected error in check_s3:")
        traceback.print_exc()

# Describe instances in the region. EC2 is regional.
def check_ec2(session: boto3.Session, region: Optional[str]):
    print_header("EC2")
    try:
        ec2 = safe_client(session, "ec2", region_name=region)
        if ec2 is None:
            print("Unable to create EC2 client.")
            return
        resp = ec2.describe_instances()
        reservations = resp.get("Reservations", [])
        instances = []
        for r in reservations:
            instances.extend(r.get("Instances", []))
        print(f"EC2 instances found in region {region}: {len(instances)}")
        running = 0
        for i in instances:
            iid = i.get("InstanceId")
            state = i.get("State", {}).get("Name")
            inst_type = i.get("InstanceType")
            public_ip = i.get("PublicIpAddress", "N/A")
            print(f"  - {iid} : {state} ({inst_type}) IP:{public_ip}")
            if state == "running":
                running += 1
        if running > 0:
            print("WARNING: Running instances detected. Free-tier users should verify instance types and stop/terminate as needed.")
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        print(f"EC2 ClientError: {code} - {e}")
        if code == "AuthFailure" or code == "UnauthorizedOperation" or code == "AccessDenied":
            print("  -> You likely lack EC2 permissions. Attach AmazonEC2ReadOnlyAccess / AmazonEC2FullAccess for Phase-1 tasks.")
    except Exception:
        print("Unexpected error in check_ec2:")
        traceback.print_exc()

def check_lambda(session: boto3.Session, region: Optional[str]):
    print_header("Lambda")
    try:
        lam = safe_client(session, "lambda", region_name=region)
        if lam is None:
            print("Unable to create Lambda client.")
            return
        resp = lam.list_functions(MaxItems=50)
        functions = resp.get("Functions", [])
        print(f"Lambda functions found in region {region}: {len(functions)}")
        for f in functions:
            name = f.get("FunctionName")
            arn = f.get("FunctionArn")
            runtime = f.get("Runtime")
            last_mod = f.get("LastModified")
            print(f"  - {name}  ({runtime})  LastModified: {last_mod}")
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        print(f"Lambda ClientError: {code} - {e}")
        if code == "AccessDenied":
            print("  -> You likely lack Lambda permissions. Attach AWSLambdaReadOnlyAccess / AWSLambda_FullAccess.")
    except Exception:
        print("Unexpected error in check_lambda:")
        traceback.print_exc()

def check_Cloudwatch(session: boto3.Session, region: Optional[str]):
    print_header("CloudWatch")
    try:
        cw = safe_client(session, "cloudwatch", region_name=region)
        logs = safe_client(session, "logs", region_name=region)
        if cw is None:
            print("Unable to create CloudWatch client.")
        else:
            # Describe alarms in ALARM state
            try:
                alarms = cw.describe_alarms(StateValue='ALARM')
                alarm_list = alarms.get('MetricAlarms', [])
                print(f"Alarms in ALARM state: {len(alarm_list)}")
                for a in alarm_list[:20]:
                    print(f"  - {a.get('AlarmName')} : {a.get('StateValue')} (AlarmArn: {a.get('AlarmArn')})")
                if len(alarm_list) > 20:
                    print(f"  ... {len(alarm_list)-20} more alarms elided")
            except ClientError as e:
                code = e.response.get('Error', {}).get('Code', '')
                print(f"CloudWatch.describe_alarms ClientError: {code} - {e}")

            # List dashboards
            try:
                d = cw.list_dashboards()
                entries = d.get('DashboardEntries', [])
                print(f"Dashboards found: {len(entries)}")
                for de in entries[:20]:
                    print(f"  - {de.get('DashboardName')}")
                if len(entries) > 20:
                    print(f"  ... {len(entries)-20} more dashboards elided")
            except ClientError as e:
                print(f"CloudWatch.list_dashboards error: {e}")

            # Helper to fetch a single metric statistic
            def fetch_metric(namespace, metric_name, dimensions, period_seconds, start_delta):
                try:
                    end = datetime.now(timezone.utc)
                    start = end - start_delta
                    params = {
                        'Namespace': namespace,
                        'MetricName': metric_name,
                        'StartTime': start,
                        'EndTime': end,
                        'Period': period_seconds,
                        'Statistics': ['Average'],
                    }
                    if dimensions:
                        params['Dimensions'] = dimensions
                    resp = cw.get_metric_statistics(**params)
                    dps = resp.get('Datapoints', [])
                    # sort by Timestamp
                    dps_sorted = sorted(dps, key=lambda x: x.get('Timestamp'))
                    if dps_sorted:
                        last = dps_sorted[-1]
                        return last.get('Average'), last.get('Timestamp')
                    return None, None
                except ClientError as e:
                    print(f"get_metric_statistics error for {namespace}/{metric_name}: {e}")
                    return None, None

            # EC2: CPUUtilization (last 10 minutes)
            try:
                avg, ts = fetch_metric('AWS/EC2', 'CPUUtilization', [], 300, timedelta(minutes=10))
                if avg is not None:
                    print(f"EC2 CPUUtilization (avg last datapoint at {ts}): {avg:.2f}%")
                else:
                    print("EC2 CPUUtilization: No datapoints found (instances may be idle or no metrics published).")
            except Exception:
                traceback.print_exc()

            # Lambda: Invocations & Errors (last 1 hour)
            try:
                inv, its = fetch_metric('AWS/Lambda', 'Invocations', [], 300, timedelta(hours=1))
                err, ets = fetch_metric('AWS/Lambda', 'Errors', [], 300, timedelta(hours=1))
                if inv is not None:
                    print(f"Lambda Invocations (last datapoint at {its}): {inv}")
                else:
                    print("Lambda Invocations: No datapoints found.")
                if err is not None:
                    print(f"Lambda Errors (last datapoint at {ets}): {err}")
                else:
                    print("Lambda Errors: No datapoints found.")
            except Exception:
                traceback.print_exc()

            # S3: AllRequests (may not be enabled)
            try:
                s3metric, sts = fetch_metric('AWS/S3', 'AllRequests', [], 300, timedelta(hours=1))
                if s3metric is not None:
                    print(f"S3 AllRequests (last datapoint at {sts}): {s3metric}")
                else:
                    print("S3 AllRequests: No datapoints found (S3 request metrics are per-bucket and must be enabled).")
            except Exception:
                traceback.print_exc()

        # Describe log groups
        if logs is None:
            print("Unable to create CloudWatch Logs client.")
        else:
            try:
                lg = logs.describe_log_groups(limit=50)
                groups = lg.get('logGroups', [])
                print(f"Log groups found: {len(groups)}")
                for g in groups[:50]:
                    print(f"  - {g.get('logGroupName')}")
            except ClientError as e:
                print(f"CloudWatch Logs describe_log_groups error: {e}")
    except (NoCredentialsError, PartialCredentialsError):
        print("ERROR: No credentials found for CloudWatch checks.")
    except Exception:
        print("Unexpected error in check_Cloudwatch:")
        traceback.print_exc()

def check_CloudFormation(session: boto3.Session, region: Optional[str], run_drift: bool = False):
    print_header("CloudFormation")
    try:
        cf = safe_client(session, "cloudformation", region_name=region)
        if cf is None:
            print("Unable to create CloudFormation client.")
            return
        try:
            resp = cf.describe_stacks()
            stacks = resp.get('Stacks', [])
            print(f"CloudFormation stacks found: {len(stacks)}")
            if not stacks:
                print("No CloudFormation stacks found in this account/region.")
                return
            failing = []
            for s in stacks:
                name = s.get('StackName')
                status = s.get('StackStatus')
                reason = s.get('StackStatusReason', '')
                print(f"  - {name} : {status}")
                # Flag non-COMPLETE states (except ROLLBACK_COMPLETE is considered complete)
                if not (str(status).endswith('COMPLETE')):
                    failing.append((name, status, reason))
            if failing:
                print("\nALERT: The following stacks are NOT in a COMPLETE state (investigate):")
                for name, status, reason in failing:
                    print(f"  - {name} : {status}  Reason: {reason}")
            else:
                print("All stacks are in COMPLETE states.")
        except ClientError as e:
            print(f"CloudFormation.describe_stacks error: {e}")

        # Optionally start drift detection (costly & async) — we only start and poll briefly if requested
        if run_drift:
            try:
                for s in stacks:
                    name = s.get('StackName')
                    status = s.get('StackStatus')
                    if not str(status).endswith('COMPLETE'):
                        continue
                    try:
                        det = cf.detect_stack_drift(StackName=name)
                        det_id = det.get('StackDriftDetectionId')
                        print(f"Started drift detection for {name}: {det_id}")
                        # Poll briefly (non-blocking long wait)
                        for _ in range(10):
                            time.sleep(2)
                            st = cf.describe_stack_drift_detection_status(StackDriftDetectionId=det_id)
                            dstatus = st.get('DetectionStatus')
                            if dstatus == 'DETECTION_COMPLETE' or dstatus == 'DETECTION_FAILED':
                                sd = st.get('StackDriftStatus')
                                print(f"Drift detection for {name} finished: {dstatus} / {sd}")
                                break
                        else:
                            print(f"Drift detection for {name} is in progress (poll limit reached). Check console later.")
                    except ClientError as e:
                        print(f"detect_stack_drift error for {name}: {e}")
            except Exception:
                traceback.print_exc()

    except (NoCredentialsError, PartialCredentialsError):
        print("ERROR: No credentials found for CloudFormation checks.")
    except Exception:
        print("Unexpected error in check_CloudFormation:")
        traceback.print_exc()

def check_DynamoDB(session: boto3.Session, region: Optional[str], backup_warn_hours: int = 72):
    print_header("DynamoDB")
    try:
        ddb = safe_client(session, "dynamodb", region_name=region)
        cw = safe_client(session, "cloudwatch", region_name=region)
        if ddb is None:
            print("Unable to create DynamoDB client.")
            return
        try:
            lt = ddb.list_tables()
            tables = lt.get('TableNames', [])
            print(f"DynamoDB tables found: {len(tables)}")
            if not tables:
                print("No DynamoDB tables found in this account/region.")
                return
            critical_tables = []

            # local metric fetch helper
            def fetch_metric(namespace, metric_name, dimensions, period_seconds, start_delta):
                if cw is None:
                    return None, None
                try:
                    end = datetime.now(timezone.utc)
                    start = end - start_delta
                    params = {
                        'Namespace': namespace,
                        'MetricName': metric_name,
                        'StartTime': start,
                        'EndTime': end,
                        'Period': period_seconds,
                        'Statistics': ['Average'],
                    }
                    if dimensions:
                        params['Dimensions'] = dimensions
                    resp = cw.get_metric_statistics(**params)
                    dps = resp.get('Datapoints', [])
                    dps_sorted = sorted(dps, key=lambda x: x.get('Timestamp'))
                    if dps_sorted:
                        last = dps_sorted[-1]
                        return last.get('Average'), last.get('Timestamp')
                    return None, None
                except ClientError as e:
                    print(f"CloudWatch get_metric_statistics error for {metric_name}: {e}")
                    return None, None

            for name in tables:
                try:
                    desc = ddb.describe_table(TableName=name).get('Table', {})
                    status = desc.get('TableStatus')
                    items = desc.get('ItemCount')
                    size = desc.get('TableSizeBytes')
                    prov = desc.get('ProvisionedThroughput')
                    latest_stream = desc.get('LatestStreamArn')
                    print(f"  - {name} : status={status} items={items} size={size} bytes stream={latest_stream}")

                    if status != 'ACTIVE':
                        critical_tables.append((name, status))

                    # Check provisioned vs consumed if provisioned throughput present
                    if prov and 'ReadCapacityUnits' in prov:
                        rcap = prov.get('ReadCapacityUnits')
                        wcap = prov.get('WriteCapacityUnits')
                        # fetch average consumed read/write over last hour
                        r_avg, r_ts = fetch_metric('AWS/DynamoDB', 'ConsumedReadCapacityUnits', [{'Name': 'TableName', 'Value': name}], 300, timedelta(hours=1))
                        w_avg, w_ts = fetch_metric('AWS/DynamoDB', 'ConsumedWriteCapacityUnits', [{'Name': 'TableName', 'Value': name}], 300, timedelta(hours=1))
                        if r_avg is not None:
                            print(f"    Read consumed avg (1h): {r_avg:.2f} / provisioned {rcap}")
                            if r_avg >= rcap:
                                print(f"    CRITICAL: Read consumption >= provisioned for {name}")
                            elif r_avg >= 0.8 * rcap:
                                print(f"    WARNING: Read consumption nearing provisioned capacity for {name}")
                        if w_avg is not None:
                            print(f"    Write consumed avg (1h): {w_avg:.2f} / provisioned {wcap}")
                            if w_avg >= wcap:
                                print(f"    CRITICAL: Write consumption >= provisioned for {name}")
                            elif w_avg >= 0.8 * wcap:
                                print(f"    WARNING: Write consumption nearing provisioned capacity for {name}")

                    # PITR (continuous backups)
                    try:
                        p = ddb.describe_continuous_backups(TableName=name)
                        pitr = p.get('ContinuousBackupsDescription', {}).get('PointInTimeRecoveryDescription', {})
                        status_pitr = pitr.get('PointInTimeRecoveryStatus')
                        print(f"    PointInTimeRecovery: {status_pitr}")
                    except ClientError as e:
                        print(f"    describe_continuous_backups error for {name}: {e}")

                    # Backups: last successful backup
                    try:
                        b = ddb.list_backups(TableName=name, MaxResults=20)
                        backups = b.get('BackupSummaries', [])
                        if backups:
                            # find latest BackupCreationDateTime
                            latest = max(backups, key=lambda x: x.get('BackupCreationDateTime'))
                            btime = latest.get('BackupCreationDateTime')
                            print(f"    Last backup: {btime}")
                            if isinstance(btime, datetime):
                                age_hours = (datetime.now(timezone.utc) - btime).total_seconds() / 3600.0
                                if age_hours > backup_warn_hours:
                                    print(f"    WARNING: Last backup for {name} is {age_hours:.1f} hours old (> {backup_warn_hours}h)")
                        else:
                            print(f"    No backups found for {name}")
                    except ClientError as e:
                        print(f"    list_backups error for {name}: {e}")

                except ClientError as e:
                    print(f"describe_table error for {name}: {e}")

            if critical_tables:
                print("\nALERT: Tables not ACTIVE (critical):")
                for n, s in critical_tables:
                    print(f"  - {n} : {s}")
            else:
                print("All DynamoDB tables are ACTIVE.")

        except ClientError as e:
            print(f"DynamoDB.list_tables error: {e}")
    except (NoCredentialsError, PartialCredentialsError):
        print("ERROR: No credentials found for DynamoDB checks.")
    except Exception:
        print("Unexpected error in check_DynamoDB:")
        traceback.print_exc()

# Main flow: create a session and run checks.
def run_all_checks(profile: str, region: Optional[str], expected_region: Optional[str]):
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
    except (NoCredentialsError, PartialCredentialsError):
        print("ERROR: No credentials available for profile:", profile)
        return 1
    except Exception:
        print("ERROR: Unable to create boto3 session for profile:", profile)
        traceback.print_exc()
        return 1

    identity = check_identity(session)
    check_region(session, expected_region)

    # Use the session.region_name if region not explicitly provided
    effective_region = region or session.region_name

    check_s3(session)
    check_ec2(session, effective_region)
    check_lambda(session, effective_region)
    check_DynamoDB(session, effective_region)
    check_Cloudwatch(session, effective_region)
    check_CloudFormation(session, effective_region)

    print_header("Summary / Quick Actions")
    if identity:
        print("Health check completed. Recommendations:")
        print("- If you see running EC2 instances you don't expect, stop/terminate them from the console or EC2 manager script.")
        print("- If S3 buckets are public and you didn't create them, investigate immediately.")
        print("- If any AccessDenied messages appeared, attach the missing managed policy briefly and re-run this script.")
    else:
        print("Identity check failed. Re-check credentials/profile configuration and retry.")
    return 0

# ---------- CLI ----------

def parse_args():
    p = argparse.ArgumentParser(description="Safe AWS account health check (read-only).")
    p.add_argument("--profile", default="phase1", help="AWS CLI profile name to use (default: phase1)")
    p.add_argument("--region", default=None, help="Optional AWS region to target (overrides profile config)")
    p.add_argument("--expected-region", default="ap-south-1", help="Optional expected region for warning (default: ap-south-1)")
    return p.parse_args()

def main():
    args = parse_args()
    try:
        rc = run_all_checks(profile=args.profile, region=args.region, expected_region=args.expected_region)
        sys.exit(rc)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(2)

if __name__ == "__main__":
    main()