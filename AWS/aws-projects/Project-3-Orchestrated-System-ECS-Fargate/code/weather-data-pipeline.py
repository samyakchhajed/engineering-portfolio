import os
import logging
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import boto3
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from joblib import dump

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
OUTPUT_PREFIX = os.environ.get("OUTPUT_PREFIX", "batch/weather/")

CITIES_ENV = os.environ.get("CITIES")
CITIES_FILTER = [c.strip() for c in CITIES_ENV.split(",")] if CITIES_ENV else None

s3 = boto3.client("s3")

WORK_DIR = "/tmp/weather"
os.makedirs(WORK_DIR, exist_ok=True)

# -----------------------------
# Locations
# -----------------------------
DEFAULT_LOCATIONS = [
    {"city": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"city": "Delhi", "lat": 28.6139, "lon": 77.2090},
    {"city": "Chennai", "lat": 13.0827, "lon": 80.2707},
]

LOCATIONS = (
    [l for l in DEFAULT_LOCATIONS if l["city"] in CITIES_FILTER]
    if CITIES_FILTER else DEFAULT_LOCATIONS
)

# -----------------------------
# Fetch data
# -----------------------------
def fetch_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,relative_humidity_2m"
    )
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

# -----------------------------
# Pipeline
# -----------------------------
logging.info("Weather pipeline started")

dfs = []

for loc in LOCATIONS:
    logging.info(f"Fetching data for {loc['city']}")
    data = fetch_weather(loc["lat"], loc["lon"])

    df = pd.DataFrame({
        "time": data["hourly"]["time"],
        "temperature": data["hourly"]["temperature_2m"],
        "humidity": data["hourly"]["relative_humidity_2m"],
    })
    df["time"] = pd.to_datetime(df["time"])
    df["city"] = loc["city"]
    df["fetched_at"] = datetime.utcnow()

    dfs.append(df)

combined = pd.concat(dfs, ignore_index=True)
combined.drop_duplicates(subset=["time", "city"], inplace=True)

combined_file = f"{WORK_DIR}/all_weather_data.csv"
combined.to_csv(combined_file, index=False)

# -----------------------------
# Visualization
# -----------------------------
sns.set(style="whitegrid")

plt.figure(figsize=(10, 5))
sns.lineplot(data=combined, x="time", y="temperature", hue="city")
plt.xticks(rotation=45)
plt.tight_layout()
temp_plot = f"{WORK_DIR}/temperature_trends.png"
plt.savefig(temp_plot)
plt.close()

plt.figure(figsize=(10, 5))
sns.lineplot(data=combined, x="time", y="humidity", hue="city")
plt.xticks(rotation=45)
plt.tight_layout()
humidity_plot = f"{WORK_DIR}/humidity_trends.png"
plt.savefig(humidity_plot)
plt.close()

# -----------------------------
# Modeling
# -----------------------------
logging.info("Starting model training")

combined["hour"] = combined["time"].dt.hour
combined = pd.get_dummies(combined, columns=["city"], drop_first=True)

X = combined[[c for c in combined.columns if c.startswith("city_")] + ["humidity", "hour"]]
y = combined["temperature"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

model = LinearRegression()
model.fit(X_train_s, y_train)

cv_scores = cross_val_score(model, X_train_s, y_train, cv=5, scoring="r2")

y_pred = model.predict(X_test_s)

metrics = {
    "cv_scores": cv_scores.tolist(),
    "cv_mean": float(np.mean(cv_scores)),
    "mse": mean_squared_error(y_test, y_pred),
    "r2": r2_score(y_test, y_pred),
}

metrics_file = f"{WORK_DIR}/model_metrics.txt"
with open(metrics_file, "w") as f:
    for k, v in metrics.items():
        f.write(f"{k}: {v}\n")

model_file = f"{WORK_DIR}/weather_model.pkl"
dump(model, model_file)

# -----------------------------
# Upload artifacts
# -----------------------------
for file in [combined_file, temp_plot, humidity_plot, metrics_file, model_file]:
    key = f"{OUTPUT_PREFIX}{os.path.basename(file)}"
    s3.upload_file(file, OUTPUT_BUCKET, key)
    logging.info(f"Uploaded {key}")

logging.info("Weather pipeline completed successfully")
