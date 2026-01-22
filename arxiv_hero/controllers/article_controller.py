from pydantic import BaseModel
from datetime import datetime, timedelta
import calendar

from fastapi import APIRouter, Request, Depends
from fastapi import Query, Body, HTTPException
from fastapi.responses import StreamingResponse

from arxiv_hero import logger
from arxiv_hero.config import get_config
from arxiv_hero.services import ArticleFetcher
from arxiv_hero.services.task_manager import TaskManager
from arxiv_hero.repositories.article_repository.protocol import (
    QueryResult,
    DailyArticleCount,
)

config = get_config()
fetcher = ArticleFetcher()
router = APIRouter(
    prefix="/articles",
    tags=["Article"],
)


class Field(BaseModel):
    field: str
    zh_field: str


class QueryOptions(BaseModel):
    categorys: list[str]
    query_fields: list[Field]
    sort_fields: list[Field]


def get_task_manager(request: Request) -> TaskManager:
    return request.app.state.task_manager


def callback(msg: str, data: dict, progress: float):
    if msg:
        logger.debug(
            (
                "\n---------------------------------------------------------------------"
                f"\n{msg}: {progress*100:.2f}%"
                "\n---------------------------------------------------------------------"
            )
        )


@router.get("/count", summary="文章数量统计")
def get_article_counts(
    date: datetime = Query(
        default_factory=lambda: datetime.now(),
        description="查询日期所在月份的每日文章数，默认为当前日期",
    )
) -> list[DailyArticleCount]:
    # 当月第一天的 0:00
    month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # 获取当月的天数
    last_day = calendar.monthrange(date.year, date.month)[1]
    # 当月最后一天的 23:59:59
    month_end = date.replace(
        day=last_day, hour=23, minute=59, second=59, microsecond=999999
    )

    result = fetcher.respository.get_daily_article_counts(
        start_date=month_start,
        end_date=month_end,
    )
    return result


@router.post(
    "/create",
    summary="添加文章",
    description="批量添加文章，date和entry_ids二选一，优先级为date>entry_ids，两者不能同时为空",
)
def create_articles(
    date: datetime = Body(None, description="文章发布日期"),
    entry_ids: list[str] = Body(None, description="文章的 entry_id 列表"),
    star: bool = Body(False, description="是否收藏，默认为 False"),
    task_manager: TaskManager = Depends(get_task_manager),
):
    if not date and not entry_ids:
        raise HTTPException(
            status_code=400, detail="date or entry_ids must be provided"
        )
    task_id = (
        "create_articles_by_date_" + date.strftime("%Y-%m-%d")
        if date
        else "create_articles_by_entry_ids_" + str(sorted(entry_ids))
    )

    def create_and_update_star(callback):
        # 1. 联网获取文章和翻译
        result = (
            fetcher.fetch_and_translate(date=date, callback=callback)
            if date
            else fetcher.fetch_and_translate(entry_ids=entry_ids, callback=callback)
        )
        # 2. 更新收藏
        if star:
            fetcher.respository.bulk_update_star(
                entry_ids=[article.entry_id for article in result.articles],
                is_star=star,
            )
        # 3. 当根据 entry_ids 添加文章时，无需再次查询
        if entry_ids:
            return result

        # 4. 根据日期添加文章时，只返回第一页的文章
        published_start = datetime(date.year, date.month, date.day)
        return fetcher.respository.query_articles_advanced(
            published_start=published_start,
            published_end=published_start + timedelta(days=1),
            page=1,
            page_size=5,
        )

    task = task_manager.get_task(task_id) or task_manager.create_task(
        create_and_update_star, kwargs={"callback": callback}, task_id=task_id
    )
    generator = task_manager.get_task_generator(task.task_id)
    return StreamingResponse(generator(), media_type="text/event-stream")


@router.get("/query/option", summary="检索选项")
def get_query_options() -> QueryOptions:
    return QueryOptions(
        categorys=config.arxiv.categories,
        query_fields=[
            Field(field=field, zh_field=zh_field)
            for field, zh_field, in zip(
                fetcher.respository.queryable_fields,
                fetcher.respository.zh_queryable_fields,
            )
        ],
        sort_fields=[
            Field(field=field, zh_field=zh_field)
            for field, zh_field, in zip(
                fetcher.respository.sortable_fields,
                fetcher.respository.zh_sortable_fields,
            )
        ],
    )


@router.get("/query", summary="文章检索")
def query_articles(
    category: str = Query(None, description="文章的分类，例如 cs.AI等"),
    is_primary: bool = Query(False, description="是否主分类，默认认为 False"),
    keywords: str = Query(None, description="关键词，默认认为 None"),
    fields: list[str] = Query(None, description="关键词查询字段，默认认为 None"),
    published_start: datetime = Query(
        None, description="published 起始时间，默认认为 None"
    ),
    published_end: datetime = Query(
        None, description="published 结束时间，默认认为 None"
    ),
    is_star: bool = Query(None, description="是否收藏，默认认为 None"),
    sort_by: str = Query(None, description="排序字段，则默认为 None"),
    sort_asc: bool = Query(
        None, description="是否为正序，默认为 None，表示逆序(从大到小/从晚到早)"
    ),
    page: int = Query(1, description="页码，默认认为 1"),
    page_size: int = Query(10, description="每页数量，默认认为 10"),
) -> QueryResult:
    if not (
        category or keywords or fields or published_start or published_end or is_star
    ):
        raise HTTPException(400, detail="请至少输入一个查询条件")

    return fetcher.respository.query_articles_advanced(
        category=category,
        is_primary=is_primary,
        keywords=keywords,
        fields=fields,
        published_start=published_start,
        published_end=published_end,
        is_star=is_star,
        sort_by=sort_by,
        sort_order="asc" if sort_asc else "desc",
        page=page,
        page_size=page_size,
    )


@router.put("/star", summary="收藏文章")
def star_article(
    entry_id: str = Query(..., description="文章的 entry_id"),
    star: bool = Query(True, description="是否收藏，True 为收藏，False 为取消收藏"),
) -> bool:
    try:
        result = fetcher.respository.update_star(entry_id, star)
        return result
    except Exception as e:
        raise HTTPException(500, detail=str(e))
