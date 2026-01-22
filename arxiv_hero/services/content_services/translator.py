import re

from arxiv_hero import logger
from arxiv_hero.config import get_config
from arxiv_hero.utils.chat_utils import chat
from arxiv_hero.services.content_services.prompts import (
    title_system_prompt,
    content_system_prompt,
    markdown_systen_prompt,
    assistant_template,
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
        self,
        title: str,
        max_retries: int = config.max_retries,
    ) -> str | None:
        retries = 0

        while retries < max_retries:
            response = chat(
                messages=[
                    {
                        "role": "system",
                        "content": title_system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_template.format(content=title),
                    },
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

    def translate_content(
        self,
        content: str,
        history: list[list[str]] = None,
        max_retries: int = config.max_retries,
    ) -> str | None:
        retries = 0

        messages = [{"role": "system", "content": content_system_prompt}]
        for item in history or []:
            messages.extend(
                [
                    {
                        "role": "user",
                        "content": user_template.format(content=item[0]),
                    },
                    {
                        "role": "assistant",
                        "content": assistant_template.format(zh_content=item[1]),
                    },
                ]
            )
        messages.append(
            {"role": "user", "content": user_template.format(content=content)}
        )

        while retries < max_retries:
            response = chat(messages=messages)
            zh_content = self._match_zh_translated(response)
            if zh_content:
                return zh_content.strip()

            logger.warning(
                f"\n-------\n没有匹配到中文翻译结果：\n输入：\ncontent={content}\nhistory={history}\n\n输出：\n{response}\n-------"
            )
            retries += 1

        return None

    def translate_markdown(
        self,
        content: str,
        history: list[list[str]] = None,
        max_retries: int = config.max_retries,
    ) -> str | None:
        retries = 0

        messages = [{"role": "system", "content": markdown_systen_prompt}]
        for item in history or []:
            messages.extend(
                [
                    {
                        "role": "user",
                        "content": user_template.format(content=item[0]),
                    },
                    {
                        "role": "assistant",
                        "content": assistant_template.format(zh_content=item[1]),
                    },
                ]
            )
        messages.append(
            {"role": "user", "content": user_template.format(content=content)}
        )

        while retries < max_retries:
            response = chat(messages=messages)
            zh_content = self._match_zh_translated(response)
            if zh_content:
                return zh_content.strip()

            logger.warning(
                f"\n-------\n没有匹配到中文翻译结果：\n输入：\ncontent={content}\nhistory={history}\n\n输出：\n{response}\n-------"
            )
            retries += 1

        return None
