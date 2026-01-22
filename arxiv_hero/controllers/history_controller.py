from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, Query, Body

from arxiv_hero.repositories.history_repository import HistoryRepository
from arxiv_hero.repositories.history_repository.protocol import ReadHistory


class HistoryUpdate(BaseModel):
    progress: float = Field(..., ge=0.0, le=1.0, description="进度")


router = APIRouter(
    prefix="/history",
    tags=["History"],
)
repository = HistoryRepository()


@router.get("/{entry_id}", summary="获取历史记录")
def get_read_history(entry_id: str) -> ReadHistory:
    history = repository.get_history(entry_id)
    if not history:
        raise HTTPException(status_code=404, detail="History not found")
    return history


@router.get("", summary="获取最新历史记录")
def get_latest_histories(
    start: int = Query(0, ge=0, description="起始位置"),
    nums: int = Query(10, ge=0, description="数量"),
) -> list[ReadHistory]:
    return repository.get_latest_histories(start, nums)


@router.post("/{entry_id}", summary="添加或更新历史记录")
def add_history(
    entry_id: str,
    history_update: HistoryUpdate,
) -> bool:
    return repository.add_history(entry_id, history_update.progress)


@router.delete("/{entry_id}", summary="删除历史记录")
def delete_history(entry_id: str) -> bool:
    return repository.remove_history(entry_id)
