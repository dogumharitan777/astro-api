# app.py — FastAPI + Flatlib (tüm gezegenler + sağlam ASC)

import os
import swisseph as swe
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

app = FastAPI()

# Ephemeris klasörü
EPHE_PATH = os.path.join(os.getcwd(), "ephe")
os.makedirs(EPHE_PATH, exist_ok=True)
swe.set_ephe_path(EPHE_PATH)

# Basit API anahtarı
SECRET = os.environ.get("SECRET", "unknown007")

@app.get("/")
def home():
    return {"ok": True, "message": "Astro API çalışıyor", "ephe": EPHE_PATH}

@app.post("/natal")
async def natal(request: Request):
    try:
        body = await request.json()

        # API key
        if request.headers.get("x-api-key") != SECRET:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        # Girdiler
        date = str(body["date"]).replace("-", "/").strip()  # YYYY/MM/DD
        time = str(body["time"]).strip()                    # HH:MM
        tz   = str(body["tz"]).strip()                      # +03:00
        lat  = float(body["lat"])
        lon  = float(body["lon"])

        # Zaman/konum
        dt  = Datetime(date, time, tz)
        pos = GeoPos(lat, lon)

        # Dış gezegenleri ve ASC'yi de hesapla
        planet_ids = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
        ]

        # Ev sistemi: Placidus (ASC hesaplaması için önemli)
        chart = Chart(dt, pos, IDs=planet_ids, hsys=const.HOUSES_PLACIDUS)

        # Gezegenleri güvenli paketle
        def pack(name: str):
            try:
                obj = chart.get(name)
                return {"sign": obj.sign, "lon": float(obj.lon)}
            except Exception:
                return None

        planets = {}
        for name in planet_ids:
            info = pack(name)
            if info is not None:
                planets[name] = info

        # ASC'yi houses üzerinden al (chart.get('Asc') yerine)
        try:
            asc_obj = chart.houses.asc
            asc_payload = {"sign": asc_obj.sign, "lon": float(asc_obj.lon)}
        except Exception:
            asc_payload = None  # nadiren ev hesaplayamazsa

        # Hangi gezegenler eksik?
        missing = [n for n in planet_ids if n not in planets]

        return {
            "ok": True,
            "asc": asc_payload,
            "planets": planets,
            "missing": missing
        }

    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": f"Input error: {e}"})
