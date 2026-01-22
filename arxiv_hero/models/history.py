from sqlalchemy import Column, String, Float, Integer

from arxiv_hero.models.base import BaseModel


class History(BaseModel):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(255), nullable=False, unique=True)
    progress = Column(Float, nullable=False)
