from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from arxiv_hero.controllers import (
    article_router,
    content_router,
    history_router,
)
from arxiv_hero.services.task_manager import TaskManager
from arxiv_hero.services import ArticleFetcher

fetcher = ArticleFetcher()
task_manager = TaskManager()


def schedule_fetch_articles():
    last_publish_date = fetcher.respository.get_last_publish_date()
    if last_publish_date.tzinfo is None:
        last_publish_date = last_publish_date.replace(tzinfo=timezone.utc)

    next_date = last_publish_date + timedelta(days=1)
    now_date = datetime.now(tz=timezone.utc)

    while next_date <= now_date:
        fetcher.fetch_and_translate(date=next_date)
        next_date += timedelta(days=1)  # 执行抓取后，日期加一天


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.task_manager = task_manager
    yield
    task_manager.shutdown()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或指定你的前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["DOCS"], summary="文档首页")
def doc_index():
    # 重定向到 /docs 页面
    return RedirectResponse(url="/docs")


app.include_router(article_router)
app.include_router(content_router)
app.include_router(history_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=4587)
