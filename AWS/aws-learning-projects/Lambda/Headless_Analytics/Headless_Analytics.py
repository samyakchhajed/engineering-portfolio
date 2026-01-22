import json, os
from datetime import datetime
import boto3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless backend
import matplotlib.pyplot as plt
import seaborn as sns


def lambda_handler(event, context):
    # ---------- 1. Create run identifier ----------
    run_id = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")

    # ---------- 2. Generate synthetic data ----------
    rows = 200
    data = {
        "timestamp": pd.date_range(start="2025-01-01", periods=rows, freq="H"),
        "category": np.random.choice(["A", "B", "C"], size=rows),
        "value": np.random.normal(loc=50, scale=10, size=rows),
    }

    df = pd.DataFrame(data)

    # ---------- 3. Compute statistics ----------
    stats = {
        "count": int(df["value"].count()),
        "mean": float(df["value"].mean()),
        "median": float(df["value"].median()),
        "std": float(df["value"].std()),
        "min": float(df["value"].min()),
        "max": float(df["value"].max()),
    }

    # ---------- 4. File paths (Lambda-safe) ----------
    csv_path = "/tmp/data.csv"
    plot_path = "/tmp/plot.png"
    json_path = "/tmp/stats.json"

    # ---------- 5. Save CSV ----------
    df.to_csv(csv_path, index=False)

    # ---------- 6. Create headless plot ----------
    plt.figure(figsize=(8, 4))
    sns.histplot(df["value"], bins=30, kde=True)
    plt.title("Value Distribution")
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close("all")

    # ---------- 7. Save stats JSON ----------
    with open(json_path, "w") as f:
        json.dump(stats, f, indent=2)

    # ---------- 8. Upload to S3 ----------
    s3 = boto3.client("s3")

    bucket_name = "all-project-bucket-general-use"
    base_key = f"automated-analysis/run_id={run_id}"

    s3.upload_file(csv_path, bucket_name, f"{base_key}/data.csv")
    s3.upload_file(plot_path, bucket_name, f"{base_key}/plot.png")
    s3.upload_file(json_path, bucket_name, f"{base_key}/stats.json")

    return {
        "status": "success",
        "run_id": run_id,
        "artifacts": [
            "data.csv",
            "plot.png",
            "stats.json"
        ]
    }
