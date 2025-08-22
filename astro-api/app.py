import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

SECRET = os.environ.get("SECRET", "CHANGE_ME")  # Render > Environment ile vereceğiz

app = FastAPI()

# CORS: WP sitenden çağırabilmek için domainini buraya ekleyebilirsin
origins = ["*"]  # güvenlik için canlıda "*" yerine sitenin domainini yaz
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

class NatalIn(BaseModel):
    date: str   # "1999-07-21"
    time: str   # "14:30"
    tz: str = "+03:00"
    lat: float
    lon: float

@app.get("/")
def health():
    return {"ok": True, "msg": "Natal API up"}

@app.post("/natal")
async def natal(req: Request, data: NatalIn):
    # Basit shared-secret kontrolü
    key = req.headers.get("X-API-KEY")
    if key != SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    dt  = Datetime(data.date, data.time, data.tz)
    pos = GeoPos(data.lat, data.lon)
    chart = Chart(dt, pos)

    def pack(name):
        obj = chart.get(name)
        return {"sign": obj.sign, "house": obj.house, "lon": float(obj.lon)}

    planet_names = ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto"]
    planets = {n: pack(n) for n in planet_names}
    asc = chart.get("Asc")

    return {
        "ok": True,
        "asc": {"sign": asc.sign, "lon": float(asc.lon)},
        "planets": planets
    }
