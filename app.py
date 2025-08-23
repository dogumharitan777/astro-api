# app.py — FastAPI + Flatlib + Swiss Ephemeris (Render uyumlu ve stabil)

import os
import swisseph as swe
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

app = FastAPI()

# Ephemeris yolu (Render build'de ephe/ içine indiriyoruz)
EPHE_PATH = os.path.join(os.getcwd(), "ephe")
try:
    os.makedirs(EPHE_PATH, exist_ok=True)
except Exception:
    pass
swe.set_ephe_path(EPHE_PATH)

# API anahtarı (Render → Environment: SECRET=unknown007)
SECRET = os.environ.get("SECRET", "unknown007")


@app.get("/")
def home():
    return {"ok": True, "message": "Astro API çalışıyor", "ephe": EPHE_PATH}


@app.post("/natal")
async def natal(request: Request):
    try:
        body = await request.json()

        # API key kontrolü (header ismi X-API-KEY)
        if request.headers.get("x-api-key") != SECRET:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        # Girdiler
        date = str(body["date"]).replace("-", "/").strip()  # 1999-07-21 -> 1999/07/21
        time = str(body["time"]).strip()                    # HH:MM
        tz   = str(body["tz"]).strip()                      # +03:00
        lat  = float(body["lat"])
        lon  = float(body["lon"])

        # Chart oluştur
        dt  = Datetime(date, time, tz)
        pos = GeoPos(lat, lon)          # << ÖNEMLİ: GeoPos kullan!
        chart = Chart(dt, pos)

        def pack(name: str):
            obj = chart.get(name)
            return {"sign": obj.sign, "lon": float(obj.lon)}

        planets = {
            n: pack(n)
            for n in [
                const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
                const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
            ]
        }
        asc = chart.get(const.ASC)

        return {"ok": True,
                "asc": {"sign": asc.sign, "lon": float(asc.lon)},
                "planets": planets}

    except Exception as e:
        # Anlamlı hata döndür
        return JSONResponse(status_code=400, content={"detail": f"Input error: {e}"})
