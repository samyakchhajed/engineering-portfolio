import os
import logging
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import boto3
from scipy import integrate, optimize, signal

# -----------------------------
# Logging (CloudWatch)
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# -----------------------------
# Env vars
# -----------------------------
OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]
OUTPUT_PREFIX = os.environ.get("OUTPUT_PREFIX", "batch/computation/")

s3 = boto3.client("s3")

# -----------------------------
# Computation
# -----------------------------
logging.info("Starting scientific computation task")

np.random.seed(42)
x = np.linspace(0, 10, 500)
y_true = np.sin(x)
noise = np.random.normal(0, 0.5, size=len(x))
y_noisy = y_true + noise

# -----------------------------
# Plot 1: Noisy vs True Signal
# -----------------------------
plt.figure(figsize=(10, 5))
sns.lineplot(x=x, y=y_noisy, label="Noisy Signal")
sns.lineplot(x=x, y=y_true, label="True Signal")
plt.title("Noisy Sine Wave Simulation")
plt.legend()
plot1 = "noisy_vs_true_signal.png"
plt.savefig(plot1)
plt.close()

# -----------------------------
# Peak Detection
# -----------------------------
peaks, _ = signal.find_peaks(y_noisy, height=0)

plt.figure(figsize=(10, 5))
plt.plot(x, y_noisy, label="Noisy Signal")
plt.plot(x[peaks], y_noisy[peaks], "ro", label="Peaks")
plt.title("Peak Detection")
plt.legend()
plot2 = "peak_detection.png"
plt.savefig(plot2)
plt.close()

# -----------------------------
# Curve Fitting
# -----------------------------
def sine_func(x, A, B, C):
    return A * np.sin(B * x + C)

params, _ = optimize.curve_fit(sine_func, x, y_noisy, p0=[1, 1, 0])
A, B, C = params

y_fit = sine_func(x, A, B, C)

plt.figure(figsize=(10, 5))
plt.plot(x, y_noisy, label="Noisy Signal", alpha=0.6)
plt.plot(x, y_true, "r--", label="True Signal")
plt.plot(x, y_fit, "g", label=f"Fitted Curve")
plt.title("Curve Fitting Result")
plt.legend()
plot3 = "curve_fitting.png"
plt.savefig(plot3)
plt.close()

# -----------------------------
# Integration Result
# -----------------------------
area, _ = integrate.quad(lambda t: sine_func(t, A, B, C), 0, 10)

result_file = "integration_result.txt"
with open(result_file, "w") as f:
    f.write(f"Area under fitted sine curve [0,10]: {area:.6f}\n")

logging.info("Integration completed successfully")

# -----------------------------
# Upload artifacts to S3
# -----------------------------
for file in [plot1, plot2, plot3, result_file]:
    s3.upload_file(
        file,
        OUTPUT_BUCKET,
        f"{OUTPUT_PREFIX}{file}"
    )
    logging.info(f"Uploaded {file} to s3://{OUTPUT_BUCKET}/{OUTPUT_PREFIX}")

logging.info("Scientific computation task finished successfully")
