# Secure VPC Blueprint

## 1) What this teaches
- Proving traffic flow and isolation in practice.
- The fundamental cloud networking question: "Who can talk to whom, from where, and why?"
- Public vs. private distinction is a routing decision, not a subnet label.
- Security Groups represent identity-based access, not just IP-based location.
- Bastions reduce the blast radius by centralizing trust as a controlled entry point.
- Defense in depth: Security is enforced by layers (Routing, SGs, and Identity) aligning together.

## 2) Goal
Design and prove a VPC architecture where only one component is internet-facing, while all workload resources remain completely private and isolated.

## 3) Architecture / Flow
1. Internet Gateway enables traffic to the VPC boundary.
2. Public Route Table directs 0.0.0.0/0 traffic to the Internet Gateway.
3. Public Subnet hosts a Bastion EC2 acting as the entry point.
4. Main Route Table (Private) has no route to the Internet Gateway.
5. Private Subnet hosts a Private EC2 with no public IP or direct external reachability.
6. SSH Flow: Laptop -> Bastion (via Public IP) -> Private EC2 (via Private IP).

## 4) AWS Services + Why they were used
- **VPC:** To create an isolated private network boundary (10.0.0.0/16).
- **Subnets:** To explicitly separate internet-facing spaces (Public) from protected workloads (Private).
- **Internet Gateway (IGW):** To provide the VPC with a gateway for internet reachability.
- **Route Tables:** To control reachability; the mechanism that actually determines if a subnet is public or private.
- **Security Groups:** Layered firewalling; the Bastion SG restricts entry to a specific user IP, while the Private SG trusts only the identity of the Bastion SG.
- **EC2 Instances:** A Bastion for controlled access and a Private EC2 to represent a protected backend workload.

## 5) Recreation Guide
### Setup
- Create a custom VPC (10.0.0.0/16).
- Create a Public Subnet (10.0.1.0/24) and a Private Subnet (10.0.2.0/24) in the same AZ.
- Create and attach an Internet Gateway (IGW) to the VPC.
- Create a Public Route Table with a route (0.0.0.0/0 -> IGW) and associate it with the Public Subnet.

### Execution
- Create a Bastion Security Group allowing SSH (22) from "My IP" only.
- Create a Private Security Group allowing SSH (22) from the Bastion Security Group only.
- Launch the Bastion EC2 in the Public Subnet with a Public IP and the Bastion SG.
- Launch the Private EC2 in the Private Subnet with NO Public IP and the Private SG.
- Fix local SSH key permissions on Windows (icacls) or Linux (chmod).

### Verification (Proof checks)
- Attempt direct SSH from Laptop to Private EC2 (Result: Fail).
- SSH from Laptop to Bastion EC2 (Result: Success).
- Copy the key to the Bastion, set permissions (chmod 400), and SSH from Bastion to Private EC2 (Result: Success).

### Cleanup
- Remove the SSH key from the Bastion EC2.
- Delete the key from the local machine.
- Terminate the Bastion and Private EC2 instances.

## 6) IAM / Security notes
- Routing controls reachability, while Security Groups control permission; both must align for access.
- SG-to-SG rules trust identity; if the Bastion's IP changes, access to the Private EC2 does not break.
- Private subnets provide defense in depth; even if an SG is misconfigured, the lack of a public IP and IGW route prevents exposure.

## 7) Common errors & fixes
- **Error:** Laptop cannot SSH directly to Private EC2.
  **Cause:** Working as designed (no public IP/route/SG trust).
  **Fix:** None needed; use the Bastion.
- **Error:** "Permission denied" when SSHing from Bastion to Private EC2.
  **Cause:** Identity issue (missing or incorrect SSH key on the Bastion).
  **Fix:** Ensure the private key is present on the Bastion and has 400 permissions.
- **Error:** "UNPROTECTED PRIVATE KEY FILE" (Windows).
  **Cause:** Broad default file permissions.
  **Fix:** Use `icacls` commands to remove inheritance and grant exclusive read access.

## 8) Key commands / snippets

### Local Machine Verification (Windows CMD)

```cmd
:: 1. Fix SSH key permissions (Strict requirement for Windows)
icacls C:\aws_keys\week7-key.pem /inheritance:r
icacls C:\aws_keys\week7-key.pem /grant %username%:R

:: 2. Connect to the Bastion (Public entry point)
ssh -i C:\aws_keys\week7-key.pem ec2-user@<BASTION_PUBLIC_IP>

:: 3. Copy the key to the Bastion (Temporary, for internal hop verification)
scp -i C:\aws_keys\week7-key.pem C:\aws_keys\week7-key.pem ec2-user@<BASTION_PUBLIC_IP>:/home/ec2-user/

```

### Bastion Host Operations (Linux)

```bash
# 1. Restrict key permissions inside the Bastion
chmod 400 week7-key.pem

# 2. Secure internal hop to the Private EC2
ssh -i week7-key.pem ec2-user@<PRIVATE_EC2_PRIVATE_IP>

```

### Security Hygiene & Cleanup

```bash
# 1. Remove the identity file from the Bastion after use
rm week7-key.pem

# 2. Terminate sessions
exit

```

## 9) Mini interview points

* **Public vs. Private Subnets:** A subnet is only "public" if its route table points to an Internet Gateway; the name is just a label.
* **Bastion vs. Direct Access:** Direct access to workloads increases the attack surface; a bastion centralizes access into a single, auditable entry point.
* **Why trust a Security Group instead of an IP?** Trusting an SG identity is scalable and prevents breaks if instance IPs change.
* **Network Reachability vs. Permission:** Routing determines if a packet can reach a destination; Security Groups determine if that packet is allowed in.
