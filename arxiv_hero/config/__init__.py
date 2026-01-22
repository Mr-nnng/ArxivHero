import os
import toml
from typing import Optional

from arxiv_hero.config.protocol import (
    OpenAIConfig,
    MySQLConfig,
    ArxivConfig,
    TranslateConfig,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Config:
    def __init__(self):
        config_path = os.path.join(BASE_DIR, "config.toml")
        with open(config_path, "r", encoding="utf-8") as f:
            settings = toml.load(f)

        self.openai = OpenAIConfig(**settings["openai"])
        self.mysql = MySQLConfig(**settings["mysql"])
        self.arxiv = ArxivConfig(
            categories=settings["arxiv"]["categories"],
            only_primary=settings["arxiv"]["only_primary"],
            download_dir=os.path.abspath(
                os.path.join(BASE_DIR, settings["arxiv"]["download_dir"])
            ),
        )
        self.translate = TranslateConfig(**settings["translate"])
        self.timezone: str = settings["timezone"]["timezone"]

    def __str__(self):
        return f"Configs(openai={self.openai}, mysql={self.mysql}, arxiv={self.arxiv}, translate={self.translate}, timezone='{self.timezone}')"


# 单例实例（懒加载）
_config_instance: Optional[Config] = None


def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


__all__ = [
    "get_config",
    "Config",
    "OpenAIConfig",
    "MySQLConfig",
    "ArxivConfig",
    "TranslateConfig",
]
