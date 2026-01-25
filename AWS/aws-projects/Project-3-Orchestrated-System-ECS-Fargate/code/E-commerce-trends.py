import os
import logging
import random
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import boto3
from io import StringIO

# -----------------------------
# Logging (CloudWatch via stdout)
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# -----------------------------
# Env vars
# -----------------------------
INPUT_BUCKET = os.environ["INPUT_BUCKET"]
INPUT_PREFIX = os.environ.get("INPUT_PREFIX", "")
OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]
OUTPUT_PREFIX = os.environ.get("OUTPUT_PREFIX", "batch/ecommerce/")

s3 = boto3.client("s3")

# -----------------------------
# Generate synthetic data
# -----------------------------
logging.info("Generating synthetic e-commerce data")

date_range = pd.date_range(start="2025-01-01", end="2025-03-01")

products = {
    "Product": ["Laptop", "Smartphone", "Tablet", "Headphones", "Smartwatch",
                "Camera", "Printer", "Monitor", "Keyboard", "Gaming Console",
                "PS5", "Xbox"],
    "Price": [50000, 20000, 30000, 1500, 3000, 25000, 20000, 4000, 1500, 5000, 45000, 40000]
}

products_df = pd.DataFrame(products)

num_orders = 500

df = pd.DataFrame({
    "OrderID": [f"ORD{i+1:04d}" for i in range(num_orders)],
    "CustomerID": [f"CU{i+1:04d}" for i in range(num_orders)],
    "Product": [random.choice(products_df["Product"]) for _ in range(num_orders)],
    "OrderDate": [random.choice(date_range) for _ in range(num_orders)],
    "ShippingTime": [random.randint(1, 7) for _ in range(num_orders)],
    "Quantity": [random.randint(1, 5) for _ in range(num_orders)],
})

df = df.merge(products_df, on="Product", how="left")
df["Revenue"] = df["Quantity"] * df["Price"]

# -----------------------------
# Analysis
# -----------------------------
logging.info("Running revenue analysis")

revenue_by_product = df.groupby("Product")["Revenue"].sum()

plt.figure(figsize=(10, 6))
sns.barplot(x=revenue_by_product.index, y=revenue_by_product.values)
plt.xticks(rotation=45)
plt.title("Revenue by Product")
plt.tight_layout()

plot_file = "revenue_by_product.png"
plt.savefig(plot_file)

csv_file = "sales_data.csv"
df.to_csv(csv_file, index=False)

# -----------------------------
# Upload artifacts to S3
# -----------------------------
logging.info("Uploading artifacts to S3")

for file in [csv_file, plot_file]:
    s3.upload_file(
        file,
        OUTPUT_BUCKET,
        f"{OUTPUT_PREFIX}{file}"
    )

logging.info("E-commerce analysis completed successfully")
