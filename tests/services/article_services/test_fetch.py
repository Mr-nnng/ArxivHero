from datetime import datetime

from arxiv_hero.services.article_services.fetcher import ArticleFetcher


def callback(state: str, data: dict | None = None, progress: float = 0.0):
    print("-" * 30)
    print(f"{state}: {progress*100:.2f}%")
    print("-" * 30)


def test_fetch_by_date():
    fetcher = ArticleFetcher()
    date = datetime(2025, 5, 1)
    articles = fetcher.fetch_and_translate(date=date, callback=callback)
    assert len(articles.articles) > 0


def test_fetch_by_entry_ids():
    fetcher = ArticleFetcher()
    entry_ids = ["2502.20730v1"]
    articles = fetcher.fetch_and_translate(entry_ids=entry_ids, callback=callback)
    assert len(articles.articles) > 0


if __name__ == "__main__":
    test_fetch_by_entry_ids()
