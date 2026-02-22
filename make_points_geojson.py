import json
import pandas as pd

INPUT_XLSX = "Спортшколы_2024_geocoded.xlsx"
SHEET = "Спортшколы 2024"
OUTPUT_GEOJSON = "schools_points.json"

def clean(v):
    # превращаем NaN/None в None (=> null в JSON)
    return None if pd.isna(v) else v

df = pd.read_excel(INPUT_XLSX, sheet_name=SHEET)

df = df[df["geo_found"] == True].copy()
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
df = df.dropna(subset=["lat", "lon"])

features = []
for _, r in df.iterrows():
    girls = r.get("Численность занимающихся футболом девочек")
    girls = 0 if pd.isna(girls) else int(girls)

    props = {
        "region": clean(r.get("Регион")),
        "city": clean(r.get("Город")),
        "name": clean(r.get("Название школы")),
        "address": clean(r.get("Адрес")),
        "girls_total": girls,
        "phone": clean(r.get("Телефон")),
        "email": clean(r.get("Email школы")),
        "geo_quality": clean(r.get("geo_quality")),
        "geo_kind": clean(r.get("geo_kind")),
    }

    features.append({
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [float(r["lon"]), float(r["lat"])]},
        "properties": props
    })

fc = {"type": "FeatureCollection", "features": features}

with open(OUTPUT_GEOJSON, "w", encoding="utf-8") as f:
    # allow_nan=False => если вдруг где-то остался NaN, скрипт упадет и мы это увидим
    json.dump(fc, f, ensure_ascii=False, allow_nan=False)

print("Saved:", OUTPUT_GEOJSON, "points:", len(features))
