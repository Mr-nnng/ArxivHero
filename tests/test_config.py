from arxiv_hero.config import get_config, Config
from arxiv_hero.config.protocol import (
    OpenAIConfig,
    MySQLConfig,
    ArxivConfig,
    TranslateConfig,
)


def test_get_config():

    config = get_config()

    # 检查返回对象是否为 Config 实例
    assert isinstance(config, Config)

    # 检查 openai 配置
    assert isinstance(config.openai, OpenAIConfig)

    # 检查 mysql 配置
    assert isinstance(config.mysql, MySQLConfig)

    # 检查 arxiv 配置
    assert isinstance(config.arxiv, ArxivConfig)

    # 检查 translate 配置
    assert isinstance(config.translate, TranslateConfig)

    # 检查时区
    assert isinstance(config.timezone, str)


if __name__ == "__main__":
    test_get_config()
