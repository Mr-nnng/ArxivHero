from arxiv_hero.controllers.article_controller import router as article_router
from arxiv_hero.controllers.content_controller import router as content_router
from arxiv_hero.controllers.history_controller import router as history_router

__all__ = [
    "article_router",
    "content_router",
    "history_router",
]
