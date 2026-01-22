import time
from typing import Iterator

import openai
from openai import OpenAI
from openai.types.chat import ChatCompletionChunk

from arxiv_hero import logger
from arxiv_hero.config import get_config

openai_cfg = get_config().openai

# 客户端
client = OpenAI(base_url=openai_cfg.base_url, api_key=openai_cfg.api_key)


def chat(
    prompt: str = None,
    messages: list[dict] = None,
    max_tokens: int = None,
    stop: list[str] = None,
) -> str:
    global client

    if not prompt and not messages:
        raise ValueError("prompt or messages must be provided")

    if prompt:
        messages = [{"role": "user", "content": prompt}]

    for _ in range(openai_cfg.max_retries):
        try:
            response = client.chat.completions.create(
                messages=messages,
                model=openai_cfg.model,
                temperature=0.7,
                max_tokens=max_tokens,
                stop=stop,
                # extra_body={"enable_thinking": False},
            )

            return response.choices[0].message.content

        except openai.RateLimitError as e:
            logger.warning(
                f"Rate limit error: {e}. Waiting for {openai_cfg.wait_time} seconds and Retrying..."
            )
            time.sleep(openai_cfg.wait_time)

    raise openai.RateLimitError("Rate limit exceeded")


def stream_chat(
    prompt: str = None,
    messages: list[dict[str, str]] = None,
    max_tokens: int = None,
    stop: list[str] = None,
) -> Iterator[str]:
    global client

    if not prompt and not messages:
        raise ValueError("prompt or messages must be provided")

    if prompt:
        messages = [{"role": "user", "content": prompt}]

    response: Iterator[ChatCompletionChunk] = client.chat.completions.create(
        stream=True,
        messages=messages,
        model=openai_cfg.model,
        temperature=0.7,
        max_tokens=max_tokens,
        stop=stop,
        # extra_body={"enable_thinking": False},
    )

    for chunk in response:
        content = chunk.choices[0].delta.content
        if content is not None:
            yield content
