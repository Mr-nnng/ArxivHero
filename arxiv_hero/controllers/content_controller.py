import os

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse

from arxiv_hero import logger
from arxiv_hero.services import ContentProcessor
from arxiv_hero.services.task_manager import TaskManager


processor = ContentProcessor()
router = APIRouter(
    prefix="/content",
    tags=["Content"],
)


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


@router.get("/pdf/{entry_id}.pdf", summary="下载PDF文件")
def get_pdf(entry_id: str):
    pdf_path = processor.download_pdf(entry_id)
    return FileResponse(pdf_path, media_type="application/pdf")


@router.get("/source/{entry_id}/{filepath:path}", summary="下载源文件，主要是图片")
def get_source(entry_id: str, filepath: str):
    SUPPORTED_EXTS = {".png", ".jpg", ".jpeg"}
    filename, ext = os.path.splitext(filepath)
    if ext not in SUPPORTED_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext}")
    source_dir = processor.download_source_and_extract(entry_id)
    file_path = os.path.join(source_dir, filepath)
    if not os.path.exists(file_path):
        logger.warning(f"文件不存在：{file_path}")
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/octet-stream")


@router.get("/source/{entry_id}", summary="下载源文件")
def download_source(
    entry_id: str, task_manager: TaskManager = Depends(get_task_manager)
):
    def _download(entry_id, callback):
        callback("开始下载PDF文件", None, 0)
        pdf_path = processor.download_pdf(entry_id)
        callback("PDF文件下载完成，开始下载源文件", {"pdf_path": pdf_path}, 0.3)
        source_dir = processor.download_source_and_extract(entry_id)
        callback("源文件下载完成，开始解析", {"source_dir": source_dir}, 0.7)
        processor.parse(entry_id)
        callback("解析完成", None, 1)
        return {"message": "success"}

    task_id = f"download_source_{entry_id}"
    task = task_manager.get_task(task_id) or task_manager.create_task(
        _download,
        args=(entry_id,),
        kwargs={"callback": callback},
        task_id=task_id,
    )
    generator = task_manager.get_task_generator(task.task_id)
    return StreamingResponse(generator(), media_type="text/event-stream")


@router.get("/{entry_id}", summary="获取文章内容")
def get_content(entry_id: str):
    return processor.parse(entry_id)


@router.get("/translate/{entry_id}", summary="翻译文章")
def translate_content(
    entry_id: str,
    task_manager: TaskManager = Depends(get_task_manager),
):
    task_id = f"translate_content_{entry_id}"
    task = task_manager.get_task(task_id) or task_manager.create_task(
        processor.translate,
        args=(entry_id,),
        kwargs={"callback": callback},
        task_id=task_id,
    )
    generator = task_manager.get_task_generator(task.task_id)
    return StreamingResponse(generator(), media_type="text/event-stream")


@router.delete("/{entry_id}", summary="删除文章内容")
def delete_content(entry_id: str) -> bool:
    return processor.repository.remove_content_by_entry_id(entry_id)
