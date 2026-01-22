from arxiv_hero.utils.chat_utils import chat, stream_chat


def test_chat():
    response = chat("介绍一下 ChatGPT")
    print(response)

    assert isinstance(response, str)
    assert len(response) > 0


if __name__ == "__main__":
    test_chat()
