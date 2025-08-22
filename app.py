# app.py  —  TAM ve DOĞRU SÜRÜM

import os
import swisseph as swe  # <<--- ÖNEMLİ: önce import et
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

# Swiss Ephemeris yolunu kur (hem env hem de local fallback)
EPHE_PATH = os.environ.get("SE_EPHE_PATH", os.path.join(os.getcwd(), "ephe"))
try:
    os.makedirs(EPHE_PATH, exist_ok=True)
except Exception:
    pass
swe.set_ephe_path(EPHE_PATH)  # <<--- HATA BURADAYDI: swe import edilmeden çağrılıyordu

SECRET = os.environ.get("SECRET", "CHANGE_ME")

app = FastAPI()

# Canlıya geçince domainini yaz: ["https://seninsite.com"]
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

class NatalIn(BaseModel):
    date: str
    time: str
    tz: str = "+03:00"
    lat: float
    lon: float

@app.get("/")
def health():
    return {"ok": True, "msg": "Natal API up"}

@app.post("/natal")
async def natal(req: Request, data: NatalIn):
    key = req.headers.get("X-API-KEY")
    if key != SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    dt  = Datetime(data.date, data.time, data.tz)
    pos = GeoPos(data.lat, data.lon)
    chart = Chart(dt, pos)

    def pack(name):
        obj = chart.get(name)
        return {"sign": obj.sign, "house": obj.house, "lon": float(obj.lon)}

    planets = {n: pack(n) for n in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto"]}
    asc = chart.get("Asc")
    return {"ok": True, "asc": {"sign": asc.sign, "lon": float(asc.lon)}, "planets": planets}
