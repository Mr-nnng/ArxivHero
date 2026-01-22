from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base
import pytz

from arxiv_hero.config import get_config

Base = declarative_base()

# 时区
tz = pytz.timezone(get_config().timezone)


class BaseModel(Base):
    __abstract__ = True  # 声明为抽象基类，不会创建对应的表

    time_created = Column(
        DateTime(timezone=True),
        doc="创建时间",
        default=lambda: datetime.now(tz),
        nullable=False,
    )

    time_updated = Column(
        DateTime(timezone=True),
        doc="更新时间",
        default=lambda: datetime.now(tz),
        onupdate=lambda: datetime.now(tz),
        nullable=False,
    )
