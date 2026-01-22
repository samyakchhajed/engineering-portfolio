import boto3
from botocore.exceptions import ProfileNotFound, NoCredentialsError, ClientError
from datetime import datetime
import sys

# =========================
# CONFIGURATION (EXPLICIT)
# =========================
AWS_PROFILE = "phase1"
AWS_REGION = "ap-south-1"  # change only if you intentionally want a different region


def print_header(mode):
    print("=" * 70)
    print(f"EC2 MANAGER — {mode}")
    print(f"AWS Profile : {AWS_PROFILE}")
    print(f"AWS Region  : {AWS_REGION}")
    print("=" * 70)


def create_ec2_client():
    try:
        session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
        return session.client("ec2")
    except ProfileNotFound:
        print("ERROR: AWS profile not found.")
        sys.exit(1)
    except NoCredentialsError:
        print("ERROR: AWS credentials not available.")
        sys.exit(1)


def get_instance_name(tags):
    if not tags:
        return "N/A"
    for tag in tags:
        if tag.get("Key") == "Name":
            return tag.get("Value", "N/A")
    return "N/A"


def fetch_all_instances(ec2_client):
    try:
        response = ec2_client.describe_instances()
        instances = []
        for res in response["Reservations"]:
            for inst in res["Instances"]:
                instances.append(inst)
        return instances
    except ClientError as e:
        print(f"ERROR: Unable to fetch EC2 data: {e}")
        sys.exit(1)


def normalize_instance(obj):
    """Normalize either a reservation dict (with 'Instances') or a single instance dict.

    - If given a reservation dict, returns a list of instance_data dicts.
    - If given a single instance dict, returns a single instance_data dict.
    """
    def _to_data(instance):
        return {
            "InstanceId": instance.get("InstanceId"),
            "Name": get_instance_name(instance.get("Tags")),
            "State": instance.get("State", {}).get("Name"),
            "Type": instance.get("InstanceType"),
            "PublicIP": instance.get("PublicIpAddress", "None"),
            "PrivateIP": instance.get("PrivateIpAddress", "None"),
            "AZ": instance.get("Placement", {}).get("AvailabilityZone"),
            "LaunchTime": instance.get("LaunchTime")
        }

    # reservation-like object
    if isinstance(obj, dict) and "Instances" in obj:
        instances = []
        for inst in obj.get("Instances", []):
            instances.append(_to_data(inst))
        return instances

    # single instance dict
    if isinstance(obj, dict):
        return _to_data(obj)

    # fallback: return empty list
    return []


def display_instances(instances):
    if not instances:
        print("No EC2 instances found.")
        return

    print(
        f"{'Instance ID':<20} {'Name':<20} {'State':<10} "
        f"{'Type':<12} {'Public IP':<15} {'AZ':<12} {'Launch Time'}"
    )
    print("-" * 120)

    running_count = 0
    stopped_count = 0

    for inst in instances:
        launch_time = inst["LaunchTime"]
        if isinstance(launch_time, datetime):
            launch_time = launch_time.strftime("%Y-%m-%d %H:%M:%S")

        print(
            f"{inst['InstanceId']:<20} {inst['Name']:<20} {inst['State']:<10} "
            f"{inst['Type']:<12} {inst['PublicIP']:<15} {inst['AZ']:<12} {launch_time}"
        )

        if inst["State"] == "running":
            running_count += 1
        elif inst["State"] == "stopped":
            stopped_count += 1

    print("-" * 120)
    print(f"Total instances : {len(instances)}",  f"Running : {running_count}", f"Stopped : {stopped_count}")


def confirm_action(instance, action):
    print("\nACTION CONFIRMATION")
    print("-" * 40)
    print(f"Instance ID : {instance['InstanceId']}")
    print(f"Name        : {instance['Name']}")
    print(f"Current     : {instance['State']}")
    print(f"Requested   : {action.upper()}")
    print("-" * 40)
    choice = input("Type YES to continue: ")
    return choice == "YES"


def confirm_termination(instance):
    print("\n!!! TERMINATION WARNING !!!")
    print("=" * 50)
    print("YOU ARE ABOUT TO TERMINATE AN EC2 INSTANCE")
    print("THIS ACTION IS IRREVERSIBLE")
    print("=" * 50)
    print(f"Instance ID : {instance['InstanceId']}")
    print(f"Name        : {instance['Name']}")
    print(f"State       : {instance['State']}")
    print(f"Type        : {instance['Type']}")
    print(f"AZ          : {instance['AZ']}")
    print(f"Launch Time : {instance['LaunchTime']}")
    print("=" * 50)

    typed = input(
        f"Type TERMINATE {instance['InstanceId']} to confirm: "
    )

    return typed == f"TERMINATE {instance['InstanceId']}"


def perform_action(ec2_client, instance, action):
    try:
        if action == "start":
            ec2_client.start_instances(InstanceIds=[instance["InstanceId"]])
        elif action == "stop":
            ec2_client.stop_instances(InstanceIds=[instance["InstanceId"]])
        elif action == "reboot":
            ec2_client.reboot_instances(InstanceIds=[instance["InstanceId"]])
        elif action == "terminate":
            ec2_client.terminate_instances(InstanceIds=[instance["InstanceId"]])
    except ClientError as e:
        print(f"ERROR: Failed to {action} instance: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) == 1:
        print_header("PHASE A — READ-ONLY")
        ec2 = create_ec2_client()
        raw_instances = fetch_all_instances(ec2)
        instances = [normalize_instance(i) for i in raw_instances]
        display_instances(instances)
        print("\nRead-only inspection complete.")
        return

    if len(sys.argv) != 3:
        print("Usage:")
        print("  python aws_ec2_manager.py")
        print("  python D:\Projects\_tools\aws_tools\aws_ec2_manager.py <start|stop|reboot|terminate> <instance-id>")
        sys.exit(1)

    action = sys.argv[1]
    instance_id = sys.argv[2]

    if action not in ["start", "stop", "reboot", "terminate"]:
        print("ERROR: Invalid action. Allowed: start, stop, reboot, terminate.")
        sys.exit(1)

    phase = "PHASE C" if action == "terminate" else "PHASE B"
    print_header(f"{phase} — {action.upper()}")

    ec2 = create_ec2_client()
    raw_instances = fetch_all_instances(ec2)

    target = None
    for inst in raw_instances:
        if inst["InstanceId"] == instance_id:
            target = normalize_instance(inst)
            break

    if not target:
        print("ERROR: Instance ID not found.")
        sys.exit(1)

    if action == "start" and target["State"] != "stopped":
        print("ERROR: Instance is not in stopped state.")
        sys.exit(1)

    if action == "stop" and target["State"] != "running":
        print("ERROR: Instance is not in running state.")
        sys.exit(1)

    if action == "terminate":
        if confirm_termination(target):
            perform_action(ec2, target, action)
            print("\nTERMINATION initiated successfully.")
        else:
            print("\nTermination cancelled. No action taken.")
    else:
        if confirm_action(target, action):
            perform_action(ec2, target, action)
            print(f"\nAction '{action}' initiated successfully.")
        else:
            print("\nAction cancelled by user.")


if __name__ == "__main__":
    main()
