from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib import const
import swisseph as swe
import os

app = FastAPI()

# Ephemeris ayarı
EPHE_PATH = os.path.join(os.getcwd(), "ephe")
swe.set_ephe_path(EPHE_PATH)

# Basit anahtar kontrolü
API_KEY = os.environ.get("API_KEY", "unknown007")


@app.get("/")
def home():
    return {"ok": True, "message": "Astro API çalışıyor"}


@app.post("/natal")
async def natal(request: Request):
    try:
        # JSON body al
        body = await request.json()
        if request.headers.get("x-api-key") != API_KEY:
            return JSONResponse(status_code=403, content={"error": "invalid API key"})

        date = body["date"]  # YYYY/MM/DD
        time = body["time"]  # HH:MM
        tz = body["tz"]
        lat = body["lat"]
        lon = body["lon"]

        # Chart oluştur
        dt = Datetime(date, time, tz)
        chart = Chart(dt, (lat, lon))

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

        return {
            "ok": True,
            "asc": {"sign": asc.sign, "lon": float(asc.lon)},
            "planets": planets,
        }

    except Exception as e:
        # Burada artık SyntaxError olmaz çünkü except var ✅
        return JSONResponse(status_code=400, content={"detail": f"Input error: {str(e)}"})
