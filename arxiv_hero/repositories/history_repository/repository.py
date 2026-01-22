import pytz
from datetime import datetime

from arxiv_hero.config import get_config
from arxiv_hero.models import DBSession
from arxiv_hero.models.article import Article as ArticleModel
from arxiv_hero.models.history import History as HistoryModel
from arxiv_hero.repositories.history_repository.protocol import ReadHistory


class HistoryRepository:

    def get_history(self, entry_id: str) -> ReadHistory | None:
        with DBSession() as session:
            stmt = (
                (
                    session.query(
                        HistoryModel.entry_id,
                        ArticleModel.zh_title,
                        HistoryModel.progress,
                        HistoryModel.time_updated,
                    ).join(ArticleModel, HistoryModel.entry_id == ArticleModel.entry_id)
                )
                .filter(HistoryModel.entry_id == entry_id)
                .first()
            )
            return (
                ReadHistory(
                    entry_id=stmt.entry_id,
                    title=stmt.zh_title,
                    progress=stmt.progress,
                    time_updated=stmt.time_updated,
                )
                if stmt
                else None
            )

    def get_latest_histories(
        self, offset: int = 0, limit: int = 10
    ) -> list[ReadHistory]:
        with DBSession() as session:
            stmt = (
                (
                    session.query(
                        HistoryModel.entry_id,
                        ArticleModel.zh_title,
                        HistoryModel.progress,
                        HistoryModel.time_updated,
                    ).join(ArticleModel, HistoryModel.entry_id == ArticleModel.entry_id)
                )
                .order_by(HistoryModel.time_updated.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [
                ReadHistory(
                    entry_id=stmt.entry_id,
                    title=stmt.zh_title,
                    progress=stmt.progress,
                    time_updated=stmt.time_updated,
                )
                for stmt in stmt
            ]

    def add_history(self, entry_id: str, progress: float) -> bool:
        with DBSession() as session:
            history = (
                session.query(HistoryModel)
                .filter(HistoryModel.entry_id == entry_id)
                .first()
            )
            if history:
                history.progress = progress
                history.time_updated = datetime.now(
                    pytz.timezone(get_config().timezone)
                )
            else:
                history = HistoryModel(entry_id=entry_id, progress=progress)
                session.add(history)
            session.commit()
            return True

    def remove_history(self, entry_id: str) -> bool:
        with DBSession() as session:
            m = (
                session.query(HistoryModel)
                .filter(HistoryModel.entry_id == entry_id)
                .delete()
            )
            if not m:
                return False
            session.commit()
            return True
