from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
import os

app = FastAPI()

# Güvenlik için basit API Key
SECRET = os.environ.get("API_KEY", "unknown007")

@app.get("/")
def home():
    return {"msg": "Astro API is running!"}

@app.post("/natal")
async def natal(request: Request):
    try:
        body = await request.json()

        # Basit API Key kontrolü
        if request.headers.get("x-api-key") != SECRET:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        # Input verilerini al
        date = str(body["date"]).replace("-", "/").strip()
        time = str(body["time"]).strip()
        tz   = str(body["tz"]).strip()
        lat  = float(body["lat"])
        lon  = float(body["lon"])

        # Chart oluştur
        dt  = Datetime(date, time, tz)
        pos = GeoPos(lat, lon)
        chart = Chart(dt, pos)

        # Güvenli erişim
        def pack(name: str):
            try:
                obj = chart.get(name)
                return {"sign": obj.sign, "lon": float(obj.lon)}
            except Exception:
                return None

        # Gezegen listesi
        planet_names = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
        ]

        planets = {}
        for n in planet_names:
            info = pack(n)
            if info is not None:
                planets[n] = info

        # ASC al
        asc = chart.get(const.ASC)

        return {
            "ok": True,
            "asc": {"sign": asc.sign, "lon": float(asc.lon)},
            "planets": planets,
            "missing": [p for p in planet_names if p not in planets]  # Debug için
        }

    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": f"Input error: {e}"})
