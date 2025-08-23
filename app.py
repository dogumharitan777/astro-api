# app.py — FastAPI + Flatlib + Swiss Ephemeris
# - Tüm gezegenler: Flatlib ile
# - ASC (Yükselen): Swiss Ephemeris ile DOĞRUDAN (null riski yok)

import os
from datetime import datetime, timedelta
import swisseph as swe
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

app = FastAPI()

# Ephemeris klasörü (Render build komutuyla ephe/ içine dosyalar indiriliyor)
EPHE_PATH = os.path.join(os.getcwd(), "ephe")
os.makedirs(EPHE_PATH, exist_ok=True)
swe.set_ephe_path(EPHE_PATH)

# Basit API anahtarı (Render → Environment: SECRET=unknown007)
SECRET = os.environ.get("SECRET", "unknown007")


@app.get("/")
def home():
    return {"ok": True, "message": "Astro API çalışıyor", "ephe": EPHE_PATH}


def _parse_tz_to_offset_hours(tz_str: str) -> float:
    """'+03:00' -> 3.0, '-05:30' -> -5.5"""
    tz = tz_str.strip()
    sign = 1 if tz[0] == '+' else -1
    hh, mm = tz[1:].split(':')
    return sign * (int(hh) + int(mm) / 60.0)


def _asc_with_swe(date_str: str, time_str: str, tz_str: str, lat: float, lon: float):
    """Swiss Ephemeris ile Ascendant (yükselen) lon + sign hesapla."""
    # date_str: 'YYYY/MM/DD' (normalize ediyoruz)
    y, m, d = [int(x) for x in date_str.replace('-', '/').split('/')]
    hh, mi = [int(x) for x in time_str.split(':')]

    # Yerel zamanı UTC'ye çevir
    tz_offset = _parse_tz_to_offset_hours(tz_str)  # saat cinsinden
    local_dt = datetime(y, m, d, hh, mi)
    utc_dt = local_dt - timedelta(hours=tz_offset)

    # Julian day (UT)
    hour_float = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    jd_ut = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour_float)

    # Placidus ev sistemi ('P'): cusps, ascmc
    # ascmc[0] = ASC, ascmc[1] = MC, (bkz. pyswisseph docs)
    cusps, ascmc = swe.houses(jd_ut, lat, lon, b'P')
    asc_lon = float(ascmc[0]) % 360.0

    # Burç adı
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    sign_idx = int(asc_lon // 30) % 12
    asc_sign = signs[sign_idx]
    return {"sign": asc_sign, "lon": asc_lon}


@app.post("/natal")
async def natal(request: Request):
    try:
        body = await request.json()

        # API key kontrolü
        if request.headers.get("x-api-key") != SECRET:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        # Girdiler
        date = str(body["date"]).replace("-", "/").strip()  # YYYY/MM/DD
        time = str(body["time"]).strip()                    # HH:MM
        tz   = str(body["tz"]).strip()                      # +03:00
        lat  = float(body["lat"])
        lon  = float(body["lon"])

        # Chart (gezegenler için)
        dt  = Datetime(date, time, tz)
        pos = GeoPos(lat, lon)
        planet_ids = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
        ]
        chart = Chart(dt, pos, IDs=planet_ids)

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

        # ASC'yi Swiss Ephemeris ile kesin olarak hesapla
        asc_payload = _asc_with_swe(date, time, tz, lat, lon)

        return {
            "ok": True,
            "asc": asc_payload,
            "planets": planets,
            "missing": [n for n in planet_ids if n not in planets]
        }

    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": f"Input error: {e}"})
