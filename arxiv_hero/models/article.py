from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, Boolean

from arxiv_hero.models.base import BaseModel


class Article(BaseModel):
    __tablename__ = "article"

    id = Column(Integer, primary_key=True, autoincrement=True)

    entry_id = Column(String(255), nullable=False, unique=True)
    """文章 ID，形如 `https://arxiv.org/abs/{id}` 的 URL"""
    updated = Column(DateTime, nullable=False)
    """文章最后更新的时间"""
    published = Column(DateTime, nullable=False)
    """文章首次发表的时间"""
    title = Column(Text, nullable=False)
    """文章标题"""
    authors = Column(Text, nullable=False)
    """文章作者"""
    summary = Column(Text, nullable=False)
    """文章摘要"""
    comment = Column(Text, default="")
    """作者的备注，可能为空"""
    journal_ref = Column(Text, default="")
    """期刊引用，可能为空"""
    doi = Column(String(255), default="")
    """外部资源的 DOI，可能为空"""
    primary_category = Column(String(255), nullable=False)
    """
    文章的主要 arXiv 分类。见
    [arXiv: Category Taxonomy](https://arxiv.org/category_taxonomy)。
    """
    categories = Column(JSON, nullable=False)
    """
    文章的所有 arXiv 分类。见
    [arXiv: Category Taxonomy](https://arxiv.org/category_taxonomy)。
    """
    links = Column(Text, nullable=False)
    """文章的 URL，可能多于一个"""
    pdf_url = Column(Text, default="")
    """PDF 版本的 URL，如果存在"""

    zh_title = Column(Text, default="")
    """标题的中文翻译"""
    zh_summary = Column(Text, default="")
    """摘要的中文翻译"""

    is_star = Column(Boolean, default=False)
    """是否收藏"""
