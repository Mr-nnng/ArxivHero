import os
from pydantic import BaseModel, model_validator
from typing import Optional

from arxiv_hero import logger


class OpenAIConfig(BaseModel):
    base_url: str = "https://api.openai.com/v1"
    api_key: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    max_retries: int = 3
    wait_time: int = 10


class MySQLConfig(BaseModel):
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: Optional[str] = None
    database: str = "arxiv_hero"


class SqliteConfig(BaseModel):
    path: str = ".db/arxiv_hero.db"

    @model_validator(mode="after")
    def create_db_dir(self) -> "SqliteConfig":
        if not os.path.exists(os.path.dirname(self.path)):
            logger.warning(f"数据库目录不存在，创建目录：{os.path.dirname(self.path)}")
            os.makedirs(os.path.dirname(self.path))
        return self


class ArxivConfig(BaseModel):
    categories: list[str]
    download_dir: str
    only_primary: bool = True

    @model_validator(mode="after")
    def create_download_dir(self) -> "ArxivConfig":
        if not os.path.exists(self.download_dir):
            logger.warning(f"下载文章的目录不存在，创建目录：{self.download_dir}")
            os.makedirs(self.download_dir)
        return self


class TranslateConfig(BaseModel):
    max_retries: int
    max_workers: int
