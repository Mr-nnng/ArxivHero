import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Literal

import sqlalchemy
from sqlalchemy.sql import func
from sqlalchemy import desc

from arxiv_hero.models import DBSession
from arxiv_hero.models.article import Article as ArticleModel
from arxiv_hero.repositories.article_repository.protocol import (
    Article,
    DailyArticleCount,
    QueryResult,
)


class ArticleRepository:
    queryable_fields = ["title", "authors", "summary", "zh_title", "zh_summary"]
    zh_queryable_fields = ["标题", "作者", "摘要", "中文标题", "中文摘要"]
    sortable_fields = ["time_updated", "published"]
    zh_sortable_fields = ["修改时间", "发布时间"]

    @staticmethod
    def _convert_orm_to_pydantic(article_mdl: ArticleModel) -> Article:
        return Article(
            entry_id=article_mdl.entry_id,
            updated=article_mdl.updated,
            published=article_mdl.published,
            title=article_mdl.title,
            authors=json.loads(article_mdl.authors),
            summary=article_mdl.summary,
            comment=article_mdl.comment,
            journal_ref=article_mdl.journal_ref,
            doi=article_mdl.doi,
            primary_category=article_mdl.primary_category,
            categories=article_mdl.categories,
            links=json.loads(article_mdl.links),
            pdf_url=article_mdl.pdf_url,
            zh_title=article_mdl.zh_title,
            zh_summary=article_mdl.zh_summary,
            is_star=article_mdl.is_star,
        )

    @staticmethod
    def _convert_pydantic_to_orm(article: Article) -> ArticleModel:
        return ArticleModel(
            entry_id=article.entry_id,
            updated=article.updated,
            published=article.published,
            title=article.title,
            authors=json.dumps(
                [i.model_dump() for i in article.authors], ensure_ascii=False
            ),
            summary=article.summary,
            comment=article.comment,
            journal_ref=article.journal_ref,
            doi=article.doi,
            primary_category=article.primary_category,
            categories=article.categories,
            links=json.dumps(
                [i.model_dump() for i in article.links], ensure_ascii=False
            ),
            pdf_url=article.pdf_url,
            zh_title=article.zh_title,
            zh_summary=article.zh_summary,
            is_star=article.is_star,
        )

    def get_article_by_entry_id(self, entry_id: str) -> Article:
        """
        根据 entry_id 查询文章

        Args:
            entry_id (str): 文章的 entry_id

        Returns:
            Article: 文章
        """
        with DBSession() as session:
            article_mdl = (
                session.query(ArticleModel)
                .filter(ArticleModel.entry_id == entry_id)
                .first()
            )
            return self._convert_orm_to_pydantic(article_mdl) if article_mdl else None

    def get_articles_by_entry_ids(self, entry_ids: list[str]) -> list[Article]:
        """
        根据 entry_id 列表查询文章列表

        Args:
            entry_ids (List[str]): 文章的 entry_id 列表

        Returns:
            List[Article]: 匹配的文章列表
        """
        if not entry_ids:
            return []

        with DBSession() as session:
            article_mdls = (
                session.query(ArticleModel)
                .filter(ArticleModel.entry_id.in_(entry_ids))
                .all()
            )
            return [
                self._convert_orm_to_pydantic(article_mdl)
                for article_mdl in article_mdls
            ]

    def get_daily_article_counts(
        self,
        start_date: datetime,
        end_date: datetime = None,
    ) -> list[DailyArticleCount]:
        """
        统计指定时间范围内每天的文章数量

        Args:
            start_date (datetime): 起始日期
            end_date (datetime): 结束日期，默认为None，表示当前时间

        Returns:
            List[DailyArticleCount]: 每天的文章数量统计，例如：
                [
                    {"date": "2025-04-01", "count": 12},
                    {"date": "2025-04-02", "count": 8},
                    ...
                ]
        """
        end_date = end_date or datetime.now()
        with DBSession() as session:
            results = (
                session.query(
                    func.date(ArticleModel.published).label("date_"),
                    func.count().label("count_"),
                )
                .filter(ArticleModel.published >= start_date)
                .filter(ArticleModel.published <= end_date)
                .group_by(func.date(ArticleModel.published))
                .order_by(func.date(ArticleModel.published))
                .all()
            )

            return [
                DailyArticleCount(date=row.date_, count=row.count_) for row in results
            ]

    def get_last_publish_date(self) -> datetime:
        with DBSession() as session:
            last_publish_date = (
                session.query(ArticleModel.published)
                .order_by(ArticleModel.published.desc())
                .first()
            )
            if last_publish_date:
                return last_publish_date[0]
            return datetime.now(tz=timezone.utc) - timedelta(days=1)

    def query_articles_advanced(
        self,
        category: Optional[str] = None,
        is_primary: bool = False,
        keywords: Optional[str] = None,
        fields: Optional[list[str]] = None,
        published_start: Optional[datetime] = None,
        published_end: Optional[datetime] = None,
        is_star: Optional[bool] = None,
        sort_by: Optional[str] = None,
        sort_order: Literal["asc", "desc"] = None,
        page: int = 1,
        page_size: int = 5,
    ) -> QueryResult:
        """
        综合条件查询文章

        Args:
            category (Optional[str]): 分类，默认认为 None
            is_primary (bool): 是否主分类，默认认为 False
            keywords (Optional[str]): 关键词，默认认为 None
            fields (Optional[list[str]]): 关键词查询字段，默认认为 None
            published_start (Optional[datetime]): published 起始时间，默认认为 None
            published_end (Optional[datetime]): published 结束时间，默认认为 None
            is_star (Optional[bool]): 是否收藏，默认认为 None
            page (int): 页码，默认认为 1
            page_size (int): 每页数量，默认认为 5

        Returns:
            QueryResult: 查询到的文章列表和符合条件的文章总数量
        """
        offset = (page - 1) * page_size
        fields = fields or self.queryable_fields

        with DBSession() as session:
            query = session.query(ArticleModel)

            # 1. 分类筛选
            if category:
                if is_primary:
                    query = query.filter(ArticleModel.primary_category == category)
                else:
                    query = query.filter(ArticleModel.categories.contains(category))

            # 2. 关键词模糊搜索
            if keywords:
                pattern = f"%{keywords}%"
                keyword_conditions = [
                    getattr(ArticleModel, field).ilike(pattern)
                    for field in fields
                    if field in self.queryable_fields
                ]
                if keyword_conditions:
                    query = query.filter(sqlalchemy.or_(*keyword_conditions))

            # 3. published 时间范围
            if published_start:
                query = query.filter(ArticleModel.published >= published_start)
            if published_end:
                query = query.filter(ArticleModel.published <= published_end)

            # 5. 收藏状态
            if is_star is not None:
                query = query.filter(ArticleModel.is_star == is_star)

            # 排序
            if sort_by and sort_by in self.sortable_fields:
                if sort_order == "desc":
                    query = query.order_by(desc(getattr(ArticleModel, sort_by)))
                query = query.order_by(getattr(ArticleModel, sort_by))

            # 结果分页 + 总数统计
            total_nums = query.count()
            articles_mdl = query.offset(offset).limit(page_size).all()
            articles = [
                self._convert_orm_to_pydantic(article)
                for article in articles_mdl
                if article
            ]

            return QueryResult(articles=articles, total_nums=total_nums)

    def remove_article_by_entry_id(self, entry_id: str) -> bool:
        """
        根据 entry_id 删除文章

        Args:
            entry_id (str): 文章的 entry_id

        Returns:
            bool: 是否删除成功
        """

        with DBSession() as session:
            article_mdl = (
                session.query(ArticleModel)
                .filter(ArticleModel.entry_id == entry_id)
                .first()
            )
            if article_mdl:
                session.delete(article_mdl)
                session.commit()
                return True
        return False

    def update_zh_title(self, entry_id: str, zh_title: str) -> bool:
        with DBSession() as session:
            article_mdl = (
                session.query(ArticleModel)
                .filter(ArticleModel.entry_id == entry_id)
                .first()
            )
            if article_mdl:
                article_mdl.zh_title = zh_title
                session.commit()
                return True
        return False

    def update_zh_summary(self, entry_id: str, zh_summary: str) -> bool:
        with DBSession() as session:
            article_mdl = (
                session.query(ArticleModel)
                .filter(ArticleModel.entry_id == entry_id)
                .first()
            )
            if article_mdl:
                article_mdl.zh_summary = zh_summary
                session.commit()
                return True
        return False

    def update_star(self, entry_id: str, is_star: bool) -> bool:
        with DBSession() as session:
            article_mdl = (
                session.query(ArticleModel)
                .filter(ArticleModel.entry_id == entry_id)
                .first()
            )
            if article_mdl:
                article_mdl.is_star = is_star
                session.commit()
                return True
        return False

    def bulk_update_star(self, entry_ids: list[str], is_star: bool) -> bool:
        with DBSession() as session:
            article_mdls = (
                session.query(ArticleModel)
                .filter(ArticleModel.entry_id.in_(entry_ids))
                .all()
            )
            session.bulk_update_mappings(
                ArticleModel, [{"id": i.id, "is_star": is_star} for i in article_mdls]
            )
            session.commit()
            return True

    def create_article(self, article: Article) -> bool:
        with DBSession() as session:
            article_mdl = self._convert_pydantic_to_orm(article)
            session.add(article_mdl)
            session.commit()
            return True

    def create_articles(self, articles: list[Article]) -> bool:
        with DBSession() as session:
            session.bulk_save_objects(
                [self._convert_pydantic_to_orm(article) for article in articles]
            )
            session.commit()
            return True
