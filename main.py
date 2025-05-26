# === main.py ===

from fastapi import FastAPI, Request, Form, Response  # Импортируем необходимые классы из FastAPI
from fastapi.responses import HTMLResponse              # Для возврата HTML-шаблона как ответа
from fastapi.templating import Jinja2Templates          # Для подключения Jinja2 шаблонов (templates)
from fastapi.staticfiles import StaticFiles             # Для подключения статических файлов (например, CSS)
from sqlalchemy import select, func                     # Для составления SQL-запросов
from models import SearchHistory                        # Импорт модели истории поиска из models.py
from database import SessionLocal                       # Импорт фабрики сессий из database.py
import httpx, uuid, os                                  # Импорт библиотек: http-запросы, uuid, os для работы с файловой системой

# Создаем экземпляр приложения FastAPI
app = FastAPI()

# Указываем путь к директории шаблонов HTML
templates = Jinja2Templates(directory="templates")

# Если существует папка static, подключаем её для обслуживания CSS, JS и других файлов
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# === Эндпоинт главной страницы ===
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    last_city = request.cookies.get("last_city")  # Пытаемся получить из cookie последний введённый город
    return templates.TemplateResponse("weather.html", {  # Отдаём HTML-шаблон, передаём в него переменные
        "request": request,
        "last_city": last_city
    })


# === Эндпоинт POST /weather: получение погоды по городу ===
@app.post("/weather", response_class=HTMLResponse)
async def get_weather(request: Request, city: str = Form(...)):  # Получаем данные формы (название города)
    async with httpx.AsyncClient() as client:  # Создаем асинхронного клиента для HTTP-запросов
        # Получаем координаты города через API геокодинга
        geo_resp = await client.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1")
        geo_data = geo_resp.json()  # Преобразуем ответ в JSON

        if not geo_data.get("results"):  # Если город не найден — выводим сообщение об ошибке
            return templates.TemplateResponse("weather.html", {
                "request": request,
                "weather": {"error": "Город не найден"},
                "city": city
            })

        # Получаем координаты первого результата
        coords = geo_data["results"][0]
        lat, lon = coords["latitude"], coords["longitude"]

        # Запрашиваем прогноз погоды на ближайшее время, включая текущую погоду и прогноз на 3 дня
        weather_resp = await client.get(
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current_weather=true"
            f"&daily=temperature_2m_max,temperature_2m_min"
            f"&timezone=auto"
        )
        weather = weather_resp.json()  # Ответ от OpenMeteo преобразуем в JSON

    # Работа с cookie: если нет user_id, создаем новый UUID для пользователя
    user_id = request.cookies.get("user_id")
    if not user_id:
        user_id = str(uuid.uuid4())

    # Сохраняем поиск в базу данных
    async with SessionLocal() as session:
        session.add(SearchHistory(user_id=user_id, city=city))  # Создаём новую запись
        await session.commit()  # Сохраняем изменения

    # Отправляем HTML-шаблон пользователю
    response = templates.TemplateResponse("weather.html", {
        "request": request,
        "weather": weather,
        "city": city
    })

    # Устанавливаем cookies с последним городом и идентификатором пользователя
    response.set_cookie("last_city", city, max_age=60 * 60 * 24 * 30)  # Хранится 30 дней
    response.set_cookie("user_id", user_id, max_age=60 * 60 * 24 * 365)  # Хранится 1 год
    return response


# === Эндпоинт автодополнения названия города ===
@app.get("/autocomplete")
async def autocomplete(q: str):  # Получаем параметр запроса "q"
    async with httpx.AsyncClient() as client:
        res = await client.get(f"https://geocoding-api.open-meteo.com/v1/search?name={q}&count=5")
        data = res.json()
        suggestions = [item["name"] for item in data.get("results", [])]  # Формируем список подсказок
        return {"suggestions": suggestions}  # Возвращаем словарь с подсказками


# === Эндпоинт статистики: сколько раз искали каждый город ===
@app.get("/stats")
async def stats():
    async with SessionLocal() as session:
        # Группируем записи по названию города и считаем количество
        stmt = select(SearchHistory.city, func.count().label("count")).group_by(SearchHistory.city)
        result = await session.execute(stmt)
        return {city: count for city, count in result.all()}  # Формируем словарь: {"Москва": 3, "Киев": 2}

