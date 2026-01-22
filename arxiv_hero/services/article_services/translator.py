import re

from arxiv_hero import logger
from arxiv_hero.config import get_config
from arxiv_hero.utils.chat_utils import chat
from arxiv_hero.utils.parallel_utils import parallel_func
from arxiv_hero.services.article_services.prompts import (
    title_system_prompt,
    abstract_system_prompt,
    user_template,
)


class Translator(object):
    config = get_config().translate

    @staticmethod
    def _match_zh_translated(text: str) -> str | None:
        match = re.search(r"<Chinese>(.*?)</Chinese>", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def translate_title(
        self, title: str, max_retries: int = config.max_retries
    ) -> str | None:
        retries = 0

        while retries < max_retries:
            response = chat(
                messages=[
                    {"role": "system", "content": title_system_prompt},
                    {"role": "user", "content": user_template.format(content=title)},
                ]
            )
            zh_title = self._match_zh_translated(response)
            if zh_title:
                return zh_title.strip()

            logger.warning(
                f"\n-------\n没有匹配到中文翻译结果：\n输入：{title}\n输出：{response}\n-------"
            )
            retries += 1

        return None

    def translate_abstract(
        self, abstract: str, max_retries: int = config.max_retries
    ) -> str | None:
        retries = 0

        while retries < max_retries:
            response = chat(
                messages=[
                    {"role": "system", "content": abstract_system_prompt},
                    {"role": "user", "content": user_template.format(content=abstract)},
                ]
            )
            zh_abstract = self._match_zh_translated(response)
            if zh_abstract:
                return zh_abstract.strip()

            logger.warning(
                f"\n-------\n没有匹配到中文翻译结果：\n输入：{abstract}\n输出：{response}\n-------"
            )
            retries += 1

        return None

    def batch_translate_titles(
        self,
        titles: list[str],
        max_workers: int = config.max_workers,
    ) -> list[str | None]:
        """并行翻译多个标题"""
        return parallel_func(
            self.translate_title,
            [(title,) for title in titles],
            max_workers=max_workers,
        )

    def batch_translate_abstracts(
        self,
        abstracts: list[str],
        max_workers: int = config.max_workers,
    ) -> list[str | None]:
        """并行翻译多个摘要"""
        return parallel_func(
            self.translate_abstract,
            [(abstract,) for abstract in abstracts],
            max_workers=max_workers,
        )
