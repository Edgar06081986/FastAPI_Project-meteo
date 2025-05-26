# === database.py ===

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker  # Импорт для асинхронной работы с БД
from models import Base  # Импортируем базовый класс моделей

# Указываем путь к SQLite базе данных (файл database.db в текущей директории)
DATABASE_URL = "sqlite+aiosqlite:///./database.db"

# Создаем асинхронный движок для подключения к базе данных
engine = create_async_engine(DATABASE_URL, echo=False)

# Создаем фабрику сессий для работы с базой данных
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# Асинхронная функция для инициализации базы данных (создание таблиц)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # Создание всех таблиц, описанных в models.py
