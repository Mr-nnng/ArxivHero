from sqlalchemy import Column, String, Text, Integer, Boolean

from arxiv_hero.models.base import BaseModel


class Content(BaseModel):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(255), nullable=False)

    type = Column(String(255), nullable=False)
    order_idx = Column(Integer, nullable=False)
    is_translated = Column(Boolean, default=False, nullable=False)

    text = Column(Text, nullable=True)
    zh_text = Column(Text, nullable=True)
    text_level = Column(Integer, nullable=True)
