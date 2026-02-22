import os
YANDEX_API_KEY = os.getenv("YANDEX_GEOCODER_KEY")
if not YANDEX_API_KEY:
    raise RuntimeError("Set env var YANDEX_GEOCODER_KEY")
import time
import hashlib
import pandas as pd
import requests

INPUT_XLSX = "Спортшколы_2024_prepared_for_geocoding.xlsx"
SHEET = "Спортшколы 2024"
OUTPUT_XLSX = "Спортшколы_2024_geocoded.xlsx"

YANDEX_API_KEY = "15725671-4736-4f60-bfa7-8fef9ebd24cb"
BASE_URL = "https://geocode-maps.yandex.ru/v1/"
SLEEP_SEC = 0.25  # бережно к API

def yandex_geocode(query: str) -> dict:
    params = {
        "apikey": YANDEX_API_KEY,
        "geocode": query,
        "format": "json",
        "results": 1,
        "lang": "ru_RU",
    }
    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def parse_first_point(data: dict):
    try:
        feature = data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        pos = feature["Point"]["pos"]  # "lon lat"
        lon, lat = map(float, pos.split())
        meta = feature.get("metaDataProperty", {}).get("GeocoderMetaData", {})
        precision = meta.get("precision")  # exact/number/street/other...
        kind = meta.get("kind")            # house/street/locality...
        text = meta.get("text")
        return True, lat, lon, precision, kind, text
    except Exception:
        return False, None, None, None, None, None

def key(q: str) -> str:
    return hashlib.md5(q.encode("utf-8")).hexdigest()

df = pd.read_excel(INPUT_XLSX, sheet_name=SHEET)

# работаем только с тем, что можно геокодировать
df["geo_request"] = df["geo_request"].astype(str).str.strip()
queries = df["geo_request"].dropna().unique().tolist()

cache = {}

for q in queries:
    k = key(q)
    if k in cache:
        continue
    try:
        data = yandex_geocode(q)
        ok, lat, lon, precision, kind, text = parse_first_point(data)
        cache[k] = dict(
            geo_found=ok,
            lat=lat,
            lon=lon,
            geo_quality=precision,
            geo_kind=kind,
            geo_text=text,
        )
    except Exception:
        cache[k] = dict(
            geo_found=False, lat=None, lon=None,
            geo_quality=None, geo_kind=None, geo_text=None
        )
    time.sleep(SLEEP_SEC)

def pick(q, field):
    return cache.get(key(q), {}).get(field)

for c in ["geo_found","lat","lon","geo_quality","geo_kind","geo_text"]:
    df[c] = df["geo_request"].apply(lambda x, cc=c: pick(x, cc))

with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as w:
    df.to_excel(w, sheet_name=SHEET, index=False)

print("Saved:", OUTPUT_XLSX)
print("Found:", int(df["geo_found"].sum()), "of", len(df))
