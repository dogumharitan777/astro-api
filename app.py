# app.py — FastAPI + Flatlib (Uranüs/Neptün/Plüton dahil)

import os
import swisseph as swe
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

app = FastAPI()

# Ephemeris klasörü (Render build'de ephe/ içine indiriliyor)
EPHE_PATH = os.path.join(os.getcwd(), "ephe")
try:
    os.makedirs(EPHE_PATH, exist_ok=True)
except Exception:
    pass
swe.set_ephe_path(EPHE_PATH)

# API anahtarı (Render Environment: SECRET=unknown007)
SECRET = os.environ.get("SECRET", "unknown007")

@app.get("/")
def home():
    return {"ok": True, "message": "Astro API çalışıyor", "ephe": EPHE_PATH}

@app.post("/natal")
async def natal(request: Request):
    try:
        body = await request.json()

        # API KEY kontrolü
        if request.headers.get("x-api-key") != SECRET:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        # Girdiler
        date = str(body["date"]).replace("-", "/").strip()  # YYYY/MM/DD
        time = str(body["time"]).strip()                    # HH:MM
        tz   = str(body["tz"]).strip()                      # +03:00
        lat  = float(body["lat"])
        lon  = float(body["lon"])

        # Tarih/konum
        dt  = Datetime(date, time, tz)
        pos = GeoPos(lat, lon)

        # >>> ÖNEMLİ: Dış gezegenleri de içeren ID listesi
        planet_ids = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.ASC
        ]

        # Chart'ı bu ID'lerle oluştur
        chart = Chart(dt, pos, IDs=planet_ids)

        # Güvenli paketleyici
        def pack(obj_name: str):
            try:
                obj = chart.get(obj_name)
                return {"sign": obj.sign, "lon": float(obj.lon)}
            except Exception:
                return None

        planets = {}
        for name in [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
        ]:
            info = pack(name)
            if info is not None:
                planets[name] = info

        asc_obj = chart.get(const.ASC)

        return {
            "ok": True,
            "asc": {"sign": asc_obj.sign, "lon": float(asc_obj.lon)},
            "planets": planets,
            "missing": [n for n in [
                const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
                const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
            ] if n not in planets]
        }

    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": f"Input error: {e}"})
