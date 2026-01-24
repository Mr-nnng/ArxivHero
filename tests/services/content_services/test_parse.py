from arxiv_hero.services import ContentProcessor


def test_process():
    processor = ContentProcessor()
    entry_id = "2601.05187v1"
    processor.parse(entry_id)


if __name__ == "__main__":
    test_process()
