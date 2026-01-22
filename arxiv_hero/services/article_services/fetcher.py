from typing import Callable
from datetime import datetime, timedelta

import arxiv

from arxiv_hero import logger
from arxiv_hero.config import get_config
from arxiv_hero.repositories.article_repository.protocol import (
    Article,
    Author,
    Link,
    QueryResult,
)
from arxiv_hero.repositories.article_repository import ArticleRepository
from arxiv_hero.services.article_services.translator import Translator


class ArticleFetcher:
    config = get_config().arxiv

    def __init__(self):
        self.translator = Translator()
        self.respository = ArticleRepository()

        self.client = arxiv.Client(delay_seconds=15)

    def _convert_result_to_pydantic(self, article: arxiv.Result) -> Article:
        return Article(
            entry_id=article.entry_id.rsplit("/", 1)[-1],
            updated=article.updated,
            published=article.published,
            title=article.title,
            authors=[Author(name=author.name) for author in article.authors],
            summary=article.summary.replace("\n", " "),
            comment=article.comment,
            journal_ref=article.journal_ref,
            doi=article.doi,
            primary_category=article.primary_category,
            categories=article.categories,
            links=[
                Link(
                    href=link.href,
                    title=link.title,
                    rel=link.rel,
                    content_type=link.content_type,
                )
                for link in article.links
            ],
            pdf_url=article.pdf_url,
        )

    def fetch_articles_by_category(
        self,
        category: str,
        date: datetime = None,
    ) -> QueryResult:
        """
        获取指定类别的文章

        Args:
            category: 类别
            date: 搜索的日期，默认为None，表示当天时间

        Returns:
            QueryResult: 查询结果，包括文章列表和总数
        """
        date = date or datetime.now()
        date_str = date.strftime("%Y%m%d") + "0000"  # YYYYMMDDTTTT
        next_date_str = (date + timedelta(days=1)).strftime("%Y%m%d") + "0000"

        search = arxiv.Search(
            query=f"cat:{category} AND submittedDate:[{date_str} TO {next_date_str}]",
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )
        results = self.client.results(search)
        aritcles = [self._convert_result_to_pydantic(article) for article in results]
        if self.config.only_primary:  # 只获取主要类别
            aritcles = [
                article for article in aritcles if article.primary_category == category
            ]
        return QueryResult(articles=aritcles, total_nums=len(aritcles))

    def fetch_articles_by_entry_ids(
        self,
        entry_ids: list[str],
    ) -> QueryResult:
        """
        获取指定ID的文章，但是不根据类别进行过滤(即`only_primary`参数不生效)

        Args:
            entry_ids: 文章ID列表

        Returns:
            QueryResult: 查询结果，包括文章列表和总数
        """
        results = self.client.results(arxiv.Search(id_list=entry_ids))
        aritcles = [self._convert_result_to_pydantic(article) for article in results]
        return QueryResult(articles=aritcles, total_nums=len(aritcles))

    def fetch_and_translate(
        self,
        *,
        date: datetime = None,
        entry_ids: list[str] = None,
        callback: Callable[[str, dict, float], None] = None,
    ) -> QueryResult:
        """
        获取并翻译文章的标题和摘要

        Args:
            date: 搜索的日期，默认为None
            entry_ids: 文章ID列表，默认为None
            callback: 进度回调函数，输入参数依次为：描述信息、数据和进度百分比

        Returns:
            QueryResult: 翻译后的文章列表和总数
        """
        trans_fail_nums = 0  # 翻译失败的文章数

        if not date and not entry_ids:
            raise ValueError("date or entry_ids must be provided")

        # 联网获取文章
        if callback:
            callback(
                f" 联网获取中... ",
                None,
                0,
            )

        query_articles = []
        if date:
            for category in self.config.categories:
                query_articles.extend(
                    self.fetch_articles_by_category(category, date).articles
                )
        else:
            query_articles = self.fetch_articles_by_entry_ids(entry_ids).articles

        if callback:
            callback(
                f" 已获取{len(query_articles)}篇文章，翻译中... ",
                None,
                0.2,
            )

        # 去除已在数据库中的文章
        exist_entry_ids = set(
            [
                article.entry_id
                for article in self.respository.get_articles_by_entry_ids(
                    [article.entry_id for article in query_articles]
                )
            ]
        )

        articles = [
            article
            for article in query_articles
            if article.entry_id not in exist_entry_ids
        ]

        # 分组翻译
        max_workers = self.translator.config.max_workers
        article_groups = [
            articles[i : i + max_workers] for i in range(0, len(articles), max_workers)
        ]
        for i, article_group in enumerate(article_groups):
            zh_titles = self.translator.batch_translate_titles(
                [article.title for article in article_group]
            )
            zh_abstracts = self.translator.batch_translate_abstracts(
                [article.summary for article in article_group]
            )
            for article, zh_title, zh_abstract in zip(
                article_group, zh_titles, zh_abstracts
            ):
                article.zh_title = zh_title
                article.zh_summary = zh_abstract
                if not zh_title or not zh_abstract:
                    trans_fail_nums += 1

            # 批量保存
            self.respository.create_articles(article_group)
            if callback and i < len(article_groups) - 1:
                callback(
                    f" 第 {i+1} / {len(article_groups)} 组翻译完成，正在翻译下一组... ",
                    None,
                    (0.2 + ((i + 1) / len(article_groups)) * 0.8)
                    / len(self.config.categories),
                )  # 翻译完成，group的进度从1开始

        # 更新进度
        if callback:
            callback(
                f"获取和翻译完成，共{len(articles)}篇，失败{trans_fail_nums}篇",
                None,
                1,
            )

        # 日志
        logger.info(
            (
                "\n---------------------------------------------------------------------"
                f"\n检索日期：{date.strftime('%Y-%m-%d') if date else datetime.now().strftime('%Y-%m-%d')}"
                f"\n文章列表：{entry_ids}"
                f"\n检索参数：{self.config.model_dump()}"
                f"\n检索文章数量：{len(query_articles)}"
                f"\n翻译文章数量：{len(articles)}"
                f"\n翻译失败数量：{trans_fail_nums}"
                "\n---------------------------------------------------------------------"
            )
        )

        # 从数据库获取所有文章
        articles = self.respository.get_articles_by_entry_ids(
            [article.entry_id for article in query_articles]
        )
        return QueryResult(articles=articles, total_nums=len(articles))
