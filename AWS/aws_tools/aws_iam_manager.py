import boto3
from botocore.exceptions import ProfileNotFound, NoCredentialsError, ClientError
import sys
from datetime import datetime

# =========================
# CONFIGURATION (EXPLICIT)
# =========================
AWS_PROFILE = "phase1"


def print_header():
    print("=" * 70)
    print("IAM MANAGER — READ-ONLY INSPECTOR")
    print(f"AWS Profile : {AWS_PROFILE}")
    print("Mode        : READ-ONLY (No changes possible)")
    print("=" * 70)


def create_iam_client():
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        return session.client("iam")
    except ProfileNotFound:
        print("ERROR: AWS profile not found.")
        sys.exit(1)
    except NoCredentialsError:
        print("ERROR: AWS credentials not available.")
        sys.exit(1)


# -------------------------
# IAM USERS
# -------------------------
def list_iam_users(iam):
    try:
        return iam.list_users().get("Users", [])
    except ClientError as e:
        print(f"ERROR: Unable to list IAM users: {e}")
        sys.exit(1)


def user_has_console_access(iam, username):
    try:
        iam.get_login_profile(UserName=username)
        return True
    except iam.exceptions.NoSuchEntityException:
        return False


def count_access_keys(iam, username):
    try:
        keys = iam.list_access_keys(UserName=username)
        return len(keys.get("AccessKeyMetadata", []))
    except ClientError:
        return 0


def count_user_policies(iam, username):
    try:
        attached = iam.list_attached_user_policies(UserName=username)
        inline = iam.list_user_policies(UserName=username)
        return (
            len(attached.get("AttachedPolicies", [])) +
            len(inline.get("PolicyNames", []))
        )
    except ClientError:
        return 0


# -------------------------
# IAM ROLES
# -------------------------
def list_iam_roles(iam):
    try:
        return iam.list_roles().get("Roles", [])
    except ClientError as e:
        print(f"ERROR: Unable to list IAM roles: {e}")
        sys.exit(1)


def extract_trusted_services(role):
    services = []
    policy = role.get("AssumeRolePolicyDocument", {})
    for stmt in policy.get("Statement", []):
        principal = stmt.get("Principal", {})
        service = principal.get("Service")
        if isinstance(service, list):
            services.extend(service)
        elif isinstance(service, str):
            services.append(service)
    return ", ".join(services) if services else "N/A"


# -------------------------
# IAM POLICIES
# -------------------------
def list_customer_policies(iam):
    try:
        return iam.list_policies(Scope="Local").get("Policies", [])
    except ClientError as e:
        print(f"ERROR: Unable to list IAM policies: {e}")
        sys.exit(1)


# -------------------------
# MAIN
# -------------------------
def main():
    print_header()
    iam = create_iam_client()

    # USERS
    users = list_iam_users(iam)
    print("\nIAM USERS")
    print("-" * 70)
    print(f"{'User':<20} {'Console':<10} {'Keys':<5} {'Policies':<8} {'Created'}")
    for u in users:
        name = u["UserName"]
        created = u["CreateDate"].strftime("%Y-%m-%d")
        console = "Yes" if user_has_console_access(iam, name) else "No"
        keys = count_access_keys(iam, name)
        policies = count_user_policies(iam, name)

        print(f"{name:<20} {console:<10} {keys:<5} {policies:<8} {created}")

    # ROLES
    roles = list_iam_roles(iam)
    print("\nIAM ROLES")
    print("-" * 70)
    print(f"{'Role':<30} {'Trusted Service(s)':<30} {'Created'}")
    for r in roles:
        name = r["RoleName"]
        created = r["CreateDate"].strftime("%Y-%m-%d")
        trusted = extract_trusted_services(r)
        print(f"{name:<30} {trusted:<30} {created}")

    # POLICIES
    policies = list_customer_policies(iam)
    orphan_policies = [p for p in policies if p["AttachmentCount"] == 0]

    print("\nCUSTOMER-MANAGED POLICIES")
    print("-" * 70)
    print(f"{'Policy Name':<30} {'Attachments':<12} {'Created'}")
    for p in policies:
        name = p["PolicyName"]
        created = p["CreateDate"].strftime("%Y-%m-%d")
        attachments = p["AttachmentCount"]
        print(f"{name:<30} {attachments:<12} {created}")

    # ORPHANS
    print("\nORPHAN POLICIES (0 ATTACHMENTS)")
    print("-" * 70)
    if orphan_policies:
        for p in orphan_policies:
            print(f"- {p['PolicyName']}")
    else:
        print("None found.")

    print("\nIAM inspection complete. No changes were performed.")


if __name__ == "__main__":
    main()
