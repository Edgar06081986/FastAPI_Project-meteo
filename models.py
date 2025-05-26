# === models.py ===

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column  # Импортируем базовые классы ORM из SQLAlchemy
from sqlalchemy import String  # Импортируем тип String для столбца

# Создаем базовый класс для всех моделей
class Base(DeclarativeBase):
    pass  # Здесь ничего не нужно — это просто базовый класс для наследования


# Модель для хранения истории поиска
class SearchHistory(Base):
    __tablename__ = "search_history"  # Название таблицы в базе данных

    id: Mapped[int] = mapped_column(primary_key=True)  # Уникальный ID записи, автоматически увеличивается
    user_id: Mapped[str] = mapped_column(String)       # Уникальный идентификатор пользователя (из cookie)
    city: Mapped[str] = mapped_column(String)          # Название города, которое искал пользователь
