# app.py — FastAPI + Flatlib + Swiss Ephemeris (Render uyumlu)

import os
import swisseph as swe  # Swiss Ephemeris Python binding (pyswisseph)
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

# -----------------------------
# Swiss Ephemeris path ayarı
# -----------------------------
# Build sırasında ephemeris dosyaları "ephe/" klasörüne indiriliyor.
# (Render Environment'ta SE_EPHE_PATH=/opt/render/project/src/ephe)
EPHE_PATH = os.environ.get("SE_EPHE_PATH", os.path.join(os.getcwd(), "ephe"))
try:
    os.makedirs(EPHE_PATH, exist_ok=True)
except Exception:
    pass
swe.set_ephe_path(EPHE_PATH)

# -----------------------------
# Güvenlik (API Key)
# -----------------------------
SECRET = os.environ.get("SECRET", "CHANGE_ME")

# -----------------------------
# FastAPI & CORS
# -----------------------------
app = FastAPI(title="Natal API", version="1.0.0")

# Canlıya geçince origin'i sitenin domainiyle sınırla: ["https://seninsite.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Girdi şeması
# -----------------------------
class NatalIn(BaseModel):
    date: str           # "YYYY/MM/DD" ya da "YYYY-MM-DD" (normalize edeceğiz)
    time: str           # "HH:MM"
    tz: str = "+03:00"  # ör: "+03:00"
    lat: float
    lon: float

# -----------------------------
# Healthcheck
# -----------------------------
@app.get("/")
def health():
    return {"ok": True, "msg": "Natal API up", "ephe": EPHE_PATH}

# -----------------------------
# Ana uç nokta
# -----------------------------
@app.post("/natal")
async def natal(req: Request, data: NatalIn):
    # API KEY kontrolü
    key = req.headers.get("X-API-KEY")
    if key != SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Tarih/format normalizasyonu
    date_str = data.date.replace("-", "/").strip()
    time_str = data.time.strip()
    tz_str   = data.tz.strip()

    # Hesaplama
    try:
        dt  = Datetime(date_str, time_str, tz_str)
        pos = GeoPos(data.lat, data.lon)
        chart = Chart(dt, pos)
def pack(name: str):
    obj = chart.get(name)
    return {
        "sign": obj.sign,
        "lon": float(obj.lon),
    }

planets = {
    n: pack(n)
    for n in ["Sun","Moon","Mercury","Venus","Mars",
              "Jupiter","Saturn","Uranus","Neptune","Pluto"]
}
asc = chart.get("Asc")

return {
    "ok": True,
    "asc": {"sign": asc.sign, "lon": float(asc.lon)},
    "planets": planets
}

    except Exception as e:
        # Hataları logla ve anlamlı mesaj döndür
        print("Natal error:", repr(e))
        raise HTTPException(status_code=400, detail=f"Input error: {e}")


