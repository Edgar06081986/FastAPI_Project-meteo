from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column  
from sqlalchemy import String  

# Создаем базовый класс для всех моделей
class Base(DeclarativeBase):
    pass  


class SearchHistory(Base):
    __tablename__ = "search_history"  

    id: Mapped[int] = mapped_column(primary_key=True)  
    user_id: Mapped[str] = mapped_column(String)        
    city: Mapped[str] = mapped_column(String)