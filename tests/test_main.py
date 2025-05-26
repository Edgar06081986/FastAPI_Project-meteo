# === tests/test_main.py ===

import pytest  # Импортируем pytest для написания тестов
from httpx import AsyncClient  # HTTP-клиент для асинхронного тестирования FastAPI
from main import app  # Импортируем FastAPI-приложение из main.py


# Тест на корневую страницу (GET /)
@pytest.mark.asyncio  # Помечаем тест как асинхронный
async def test_homepage():
    async with AsyncClient(app=app, base_url="http://test") as ac:  # Создаем тестового клиента
        response = await ac.get("/")  # Отправляем GET-запрос на корень сайта
        assert response.status_code == 200  # Проверяем, что ответ успешный
        assert "Прогноз погоды" in response.text  # Убеждаемся, что на странице есть нужный текст


# Тест на получение прогноза по городу (POST /weather)
@pytest.mark.asyncio
async def test_weather_forecast():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/weather", data={"city": "Москва"})  # Отправляем город через форму
        assert response.status_code == 200
        assert "Погода в городе Москва" in response.text or "Температура" in response.text


# Тест на автодополнение (GET /autocomplete?q=...)
@pytest.mark.asyncio
async def test_autocomplete():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/autocomplete?q=Лон")  # Пример: ввод "Лон" для Лондон
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data  # Проверяем, что в ответе есть ключ suggestions
        assert any("Лондон" in s for s in data["suggestions"]) or len(data["suggestions"]) > 0  # Есть хотя бы одна подсказка


# Тест на API статистики (GET /stats)
@pytest.mark.asyncio
async def test_stats():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/stats")  # Запрос к API статистики
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)  # Убеждаемся, что возвращается словарь
        # Словарь может быть пустым, если ещё никто не искал
