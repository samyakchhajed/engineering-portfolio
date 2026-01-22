# EC2 CLI Deployment Playbook

## 1) What this teaches
- Cloud servers are remote Linux machines, not magical entities.
- The local laptop serves as a control terminal while execution occurs on AWS.
- Environments are not identical; Linux requires specific attention to permissions, case sensitivity, and file paths.
- The AWS Console is for high-level design and visibility, while the CLI is for direct execution and control.
- Managing resources by stopping them is as critical as starting them to control costs.

## 2) Goal
Deploy and run an interactive Python Tic-Tac-Toe game on an AWS EC2 Linux server using CLI access and SSH.

## 3) Architecture / Flow
1. Local Setup: Configure an EC2 key pair and restrict Windows file permissions.
2. Instance Provisioning: Launch an Amazon Linux EC2 instance with a Security Group allowing only SSH.
3. Connectivity: Establish an SSH tunnel from the laptop to the EC2 instance.
4. Environment Prep: Install necessary dependencies like pip and set up a Python virtual environment.
5. Deployment: Transfer the Python script from the local machine to EC2 via SCP.
6. Execution: Run the code on the cloud server and interact via the local terminal.

## 4) AWS Services + Why they were used
- **EC2 (Elastic Compute Cloud):** Used as the remote Linux server to host and run the Python project.
- **EC2 Key Pair:** Provides the identity file (.pem) required for secure SSH and SCP authentication.
- **Security Groups:** Acts as a firewall to allow SSH access while minimizing the attack surface by blocking all other ports.

## 5) Recreation Guide
### Setup
- Create an EC2 key pair in the AWS Console and download the `.pem` file.
- Store the key at `C:\aws-keys\tictactoe-key.pem`.
- Fix Windows SSH permissions using `icacls tictactoe-key.pem /inheritance:r` followed by `icacls tictactoe-key.pem /grant %username%:R`.

### Execution
- Launch a `t2.micro` instance with Amazon Linux and name it `tictactoe-ec2`.
- Set Security Group to allow SSH (port 22) from "My IP" only.
- Connect via SSH: `ssh -i C:\aws-keys\tictactoe-key.pem ec2-user@<PUBLIC_IPV4>`.
- Install pip (not preinstalled): `sudo yum install -y python3-pip`.
- Create project directory and virtual environment: `mkdir tictactoe && cd tictactoe && python3 -m venv venv`.
- Activate environment: `source venv/bin/activate`.
- Upload file from local machine: `scp -i C:\aws-keys\tictactoe-key.pem Tic-tac-toe.py ec2-user@<PUBLIC_IPV4>:/home/ec2-user/tictactoe/`.
- Run the script: `python Tic-tac-toe.py`.

### Verification (Proof checks)
- Confirm Python is active on EC2 with `python3 --version`.
- Use `ls` inside the `tictactoe` directory to ensure `Tic-tac-toe.py` and `venv` are present.
- Verify that the game interacts with laptop `input()` commands over the SSH stream.

### Cleanup
- Stop the Python program using `Ctrl + C`.
- Exit the virtual environment and SSH session with `deactivate` then `exit`.
- Stop the instance in the AWS Console to preserve the setup without incurring compute costs.

## 6) IAM / Security notes
- Private key files must have restricted permissions (readable only by the owner) or SSH will reject the connection.
- Limiting Security Group sources to "My IP only" prevents unauthorized access from the public internet.

## 7) Common errors & fixes
- **Error:** “UNPROTECTED PRIVATE KEY FILE”
  **Cause:** Windows provides broad default file permissions; SSH requires exclusive access.
  **Fix:** Use `icacls` to remove inheritance and grant specific read access to the user.
- **Error:** Program fails to find file.
  **Cause:** Linux is case-sensitive (e.g., `Tic-tac-toe.py` vs `tictactoe.py`).
  **Fix:** Use the exact case-sensitive filename in all commands.

## 8) Key commands / snippets
```cmd
:: Windows SSH Key Permission Fix
icacls tictactoe-key.pem /inheritance:r
icacls tictactoe-key.pem /grant %username%:R

:: SSH Connection
ssh -i C:\aws-keys\tictactoe-key.pem ec2-user@<PUBLIC_IPV4>

:: Environment Setup
sudo yum install -y python3-pip
python3 -m venv venv
source venv/bin/activate

:: Uploading via SCP
cd /d <path-to-project-folder>
scp -i C:\aws-keys\tictactoe-key.pem Tic-tac-toe.py ec2-user@<PUBLIC_IPV4>:/home/ec2-user/tictactoe/

```

## 9) Mini interview points

* **Stopping vs. Terminating:** Stopping preserves the EBS volume and instance configuration for a quick restart; terminating deletes the resource entirely.
* **Virtual Environments on EC2:** Using a `venv` mirrors professional server hygiene and keeps the system Python installation clean.
* **Interactive Cloud execution:** SSH allows streaming input/output so that local interaction controls remote cloud compute.
