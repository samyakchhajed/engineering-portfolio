# Headless Analytics in AWS Lambda (Lambda → S3)

## 1) What this teaches

* **Runtime‑Correctness Validation**: Confirming that heavy scientific libraries (pandas, NumPy, matplotlib, seaborn) can run reliably in a serverless environment.
* **Environment Alignment**: Recognizing that **OS + ABI + Python version** must match exactly; Linux is not a universal environment when native code is involved.
* **Build vs. Runtime Distinction**: Using Docker solely as a build-time tool to create Amazon Linux‑compatible artifacts, while Lambda remains the sole runtime compute.
* **Headless Constraints**: Adapting code to work without a GUI, display server, or persistent filesystem.
* **Dependency Discipline**: Understanding that in serverless, source compilation is a failure, not a fallback.

## 2) Goal

Validate that real-world data analysis workloads can execute inside AWS Lambda and produce persistent analytical artifacts (CSV, JSON, PNG) without servers or interactive environments.

## 3) Architecture / Flow

1. **Invocation**: Lambda is invoked manually via a test event.
2. **Generation**: Synthetic data is generated in-memory using pandas and NumPy.
3. **Analysis**: Headless statistical computation and visualization (matplotlib/seaborn) are performed.
4. **Local Write**: Resulting artifacts are saved to the ephemeral `/tmp` directory.
5. **Persistence**: Final artifacts are uploaded to an S3 bucket under a timestamped prefix.

## 4) AWS Services + Why they were used

* **AWS Lambda**: Provides the stateless, serverless compute environment for the analysis.
* **Amazon S3**: Acts as the permanent system of record for the analytical artifacts.
* **AWS Lambda Layers**: Used to manage and deliver heavy scientific dependencies separately from the function code.
* **Amazon CloudWatch Logs**: Used for execution monitoring and debugging environmental failures.

## 5) Recreation Guide

### Setup

* Ensure the local environment has **Docker Desktop** installed for building the layer.
* Create an **IAM Role** for the Lambda with `s3:PutObject` permissions for the target bucket and CloudWatch logging permissions.
* Initialize a directory structure: a top-level `python/` folder is required for Lambda layers.

### Execution

* **Build the Layer**:
1. Run the AWS Lambda Python 3.11 base image: `docker run -it --rm --entrypoint bash -v "%cd%":/build public.ecr.aws/lambda/python:3.11`.
2. Inside the container, install pinned, binary-only dependencies: `pip install "numpy==1.26.4" "pandas==1.5.3" "matplotlib==3.8.4" "seaborn==0.12.2" --only-binary=:all: -t python/`.
3. Zip the `python/` folder and exit the container.


* **Deploy**: Upload the zip as a Lambda Layer and attach it to your function.
* **Invoke**: Run a manual test event in the Lambda console.

### Verification (Proof checks)

* **Execution Success**: Lambda status returns "Success".
* **Artifact Presence**: Verify `data.csv`, `stats.json`, and `plot.png` exist in the S3 bucket under the `automated-analysis/` prefix.
* **Log Confirmation**: Check CloudWatch for successful headless rendering and S3 upload logs.

### Cleanup

* Delete the local `python/` directory and any temporary virtual environments used during failed attempts.
* Remove broken or old Lambda layers to prevent confusion.

## 6) IAM / Security notes

* **Least Privilege**: The Lambda execution role only requires `s3:PutObject` for the specific output prefix; no read permissions are needed if data is generated internally.
* **No Access Keys**: Permissions are handled entirely via IAM roles; no credentials should be in the code or environment variables.
* **Minimal Surface**: No inbound ports or SSH are required for execution.

## 7) Common errors & fixes

* **Error**: `ImportError` or `GLIBC_X.XX not found`.
* **Cause**: Dependencies built on Windows or generic Linux (Debian) are incompatible with the Amazon Linux runtime.
* **Fix**: Build the layer using the `public.ecr.aws/lambda/python` Docker image.


* **Error**: File system is read-only.
* **Cause**: Attempting to write files outside of the `/tmp` directory.
* **Fix**: Direct all file writes to `/tmp/`.


* **Error**: Matplotlib "no display" or backend error.
* **Cause**: Matplotlib attempting to use a GUI backend in a headless environment.
* **Fix**: Force a headless backend (e.g., `matplotlib.use('Agg')`).



## 8) Key commands / snippets 

### Build Pipeline: Environment Alignment (Windows to Amazon Linux)
```bat
:: 1. Navigate to project directory (No special characters in path)
D:
cd D:\Projects\AWS\Projects\PHASE_1-LAMBDA_EVENT_DRIVEN_CORE\Project_05_Headless_Analytics\Success

:: 2. Start Amazon Linux build container (Prevents Debian/GLIBC mismatch)
:: Note: Generic 'python:3.11' images use Debian; use the ECR image for Lambda ABI compatibility
docker run -it --rm --entrypoint bash -v "%cd%":/build public.ecr.aws/lambda/python:3.11

:: 3. Initialize layer structure inside container
cd /build
rm -rf python
mkdir python

:: 4. Install wheel-only dependencies (Source builds/compilation = failure)
pip install \
  "numpy==1.26.4" \
  "pandas==1.5.3" \
  "matplotlib==3.8.4" \
  "seaborn==0.12.2" \
  --only-binary=:all: \
  -t python/

:: 5. Package layer for deployment
yum install -y zip
zip -r analytics_layer.zip python
exit
```
## 9) Mini interview points

* **Why pin versions like NumPy 1.26.4?**: To ensure binary compatibility and avoid major version bumps (like NumPy 2.x) that might lag in wheel availability or change ABIs.
* **The Golden Rule of Lambda Analytics**: If the code needs a compiler or a display, Lambda is the wrong tool; if it only needs execution, Lambda is viable.
* **Why use --only-binary?**: In serverless, source compilation is a failure. Forcing wheels ensures dependencies are deployment-safe for environments without compiler toolchains.

## 10) Types of Linux (Debian vs Amazon Linux)

| Aspect | Debian | Amazon Linux |
| --- | --- | --- |
| **Purpose** | General-purpose distribution for servers, desktops, containers | Specifically maintained and optimized for AWS services |
| **GLIBC Version** | Uses versions newer or different from AWS Lambda | Uses glibc versions pinned specifically for AWS runtimes |
| **Optimization** | Broad hardware and software compatibility | Specialized for AWS service performance and security |
| **Compatibility** | Docker images like `python:3.11` are Debian-based; wheels may not run on Lambda | AWS Lambda runs on Amazon Linux; native libraries are guaranteed compatible |
