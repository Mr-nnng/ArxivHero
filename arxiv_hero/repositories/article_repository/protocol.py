from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Link(BaseModel):
    """
    文章的链接
    """

    href: str
    """链接的 href 属性"""
    title: Optional[str] = None
    """链接的标题"""
    rel: Optional[str] = None
    """Result 对象与链接的关系"""
    content_type: Optional[str] = None
    """链接的 HTTP 内容类型"""


class Author(BaseModel):
    name: str


class Article(BaseModel):
    entry_id: str
    updated: datetime
    published: datetime
    title: str
    authors: list[Author]
    summary: str
    comment: Optional[str] = None
    journal_ref: Optional[str] = None
    doi: Optional[str] = None
    primary_category: str
    categories: list[str]
    links: list[Link]
    pdf_url: str

    zh_title: Optional[str] = None
    zh_summary: Optional[str] = None

    is_star: bool = False


class DailyArticleCount(BaseModel):
    date: datetime
    count: int


class QueryResult(BaseModel):
    articles: list[Article]
    total_nums: int
