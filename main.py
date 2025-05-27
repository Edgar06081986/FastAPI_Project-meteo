from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func
from models import SearchHistory
from database import SessionLocal
import httpx, uuid, os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Подключаем статику (если будет CSS)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    last_city = request.cookies.get("last_city")
    return templates.TemplateResponse("weather.html", {
        "request": request,
        "last_city": last_city
    })

@app.post("/weather", response_class=HTMLResponse)
async def get_weather(request: Request, city: str = Form(...)):
    async with httpx.AsyncClient() as client:
        geo_resp = await client.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1")
        geo_data = geo_resp.json()
        if not geo_data.get("results"):
            return templates.TemplateResponse("weather.html", {
                "request": request,
                "weather": {"error": "Город не найден"},
                "city": city
            })

        coords = geo_data["results"][0]
        lat, lon = coords["latitude"], coords["longitude"]

        weather_resp = await client.get(
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current_weather=true"
            f"&daily=temperature_2m_max,temperature_2m_min"
            f"&timezone=auto"
        )
        weather = weather_resp.json()

    user_id = request.cookies.get("user_id")
    if not user_id:
        user_id = str(uuid.uuid4())

    async with SessionLocal() as session:
        session.add(SearchHistory(user_id=user_id, city=city))
        await session.commit()

    response = templates.TemplateResponse("weather.html", {
        "request": request,
        "weather": weather,
        "city": city
    })
    response.set_cookie("last_city", city, max_age=60 * 60 * 24 * 30)
    response.set_cookie("user_id", user_id, max_age=60 * 60 * 24 * 365)
    return response

@app.get("/autocomplete")
async def autocomplete(q: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"https://geocoding-api.open-meteo.com/v1/search?name={q}&count=5")
        data = res.json()
        suggestions = [item["name"] for item in data.get("results", [])]
        return {"suggestions": suggestions}

@app.get("/stats")
async def stats():
    async with SessionLocal() as session:
        stmt = select(SearchHistory.city, func.count().label("count")).group_by(SearchHistory.city)
        result = await session.execute(stmt)
        return {city: count for city, count in result.all()}
