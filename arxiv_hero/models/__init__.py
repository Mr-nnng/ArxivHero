from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from arxiv_hero.config import get_config
from arxiv_hero.models.base import Base
from arxiv_hero.models.article import Article
from arxiv_hero.models.content import Content
from arxiv_hero.models.history import History

db_config = get_config().mysql

# 使用 mysqlclient 驱动
engine = create_engine(
    f"mysql+mysqldb://{db_config.user}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database}"
)

# 创建表
Base.metadata.create_all(engine)

DBSession = sessionmaker(bind=engine)

__all__ = [
    "DBSession",
    "Article",
    "Content",
    "History",
]
