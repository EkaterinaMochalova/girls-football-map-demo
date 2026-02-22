import json
import pandas as pd
import numpy as np

INPUT_XLSX = "Спортшколы_2024_geocoded.xlsx"
SHEET = "Спортшколы 2024"
OUTPUT_GEOJSON = "schools_points.geojson"

df = pd.read_excel(INPUT_XLSX, sheet_name=SHEET)

# Берём только строки с найденными координатами
df = df[df["geo_found"] == True].copy()

# Приводим координаты к числам
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
df = df.dropna(subset=["lat", "lon"])

features = []

for _, r in df.iterrows():

    girls = r.get("Численность занимающихся футболом девочек")
    if pd.isna(girls):
        girls = 0
    else:
        girls = int(girls)

    props = {
        "region": r.get("Регион"),
        "city": r.get("Город"),
        "name": r.get("Название школы"),
        "address": r.get("Адрес"),
        "girls_total": girls,
        "phone": r.get("Телефон"),
        "email": r.get("Email школы"),
        "geo_quality": r.get("geo_quality"),
        "geo_kind": r.get("geo_kind"),
    }

    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [float(r["lon"]), float(r["lat"])]
        },
        "properties": props
    }

    features.append(feature)

fc = {
    "type": "FeatureCollection",
    "features": features
}

with open(OUTPUT_GEOJSON, "w", encoding="utf-8") as f:
    json.dump(fc, f, ensure_ascii=False)

print("Saved:", OUTPUT_GEOJSON)
print("Points:", len(features))