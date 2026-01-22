import threading
import uuid
import traceback
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Literal, Optional, Iterator, Callable

from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.job import Job

from arxiv_hero import logger


class TaskStatus(Enum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class TaskMessage(BaseModel):
    code: Literal[200, 400, 500] = 200
    msg: Optional[str] = None
    data: Optional[dict | Any] = None
    progress: Optional[float] = None


class Task:
    def __init__(self, task_id: str, func: Callable, args: tuple, kwargs: dict):
        args = args or ()
        kwargs = kwargs or {}

        self.task_id = task_id
        self._func = func
        self._args = args
        self._callback: Optional[Callable[[str, dict, float], None]] = kwargs.pop(
            "callback", None
        )
        self._kwargs = kwargs

        self._status = TaskStatus.WAITING
        self._progress: float = 0.0  # 执行进度

        self.history: list[TaskMessage] = []  # 存储执行过程中的信息
        self.result: Optional[dict | Any] = None
        self.condition = threading.Condition()  # 用于线程间通知

    def __add_message(self, message: TaskMessage) -> None:
        with self.condition:
            self.history.append(message)
            self.condition.notify_all()

    def __update_status(self, status: TaskStatus) -> None:
        if not isinstance(status, TaskStatus):
            raise ValueError("Invalid status type")
        with self.condition:
            self._status = status
            self.condition.notify_all()

    def __update_progress(self, progress: float) -> None:
        if not 0 <= progress <= 1:
            logger.warning(f"非法进度：{progress}")
            return
        with self.condition:
            self._progress = progress
            self.condition.notify_all()

    def _run(self) -> None:
        def _callback(msg: str = None, data: dict = None, progress: float = None):
            self._callback(msg, data, progress)
            self.__add_message(TaskMessage(msg=msg, data=data, progress=progress))
            if progress is not None:
                self.__update_progress(progress)

        args = self._args
        kwargs = (
            (self._kwargs)
            if (self._callback is None)
            else {**self._kwargs, "callback": _callback}
        )

        self.__update_progress(0)
        self.__update_status(TaskStatus.RUNNING)
        try:
            result = self._func(*args, **kwargs)
            self.__update_progress(1)
            self.set_result(result)
            self.__add_message(TaskMessage(msg="[DONE]", data=result, progress=1))
            self.__update_status(TaskStatus.COMPLETED)
        except Exception as e:
            logger.warning(
                f"\n执行任务 {self.task_id} 失败：{str(e)}\n{traceback.format_exc()}"
            )
            self.__add_message(TaskMessage(code=500, msg=str(e)))
            self.__update_status(TaskStatus.ERROR)

    def cancel(self) -> None:
        self.__update_status(TaskStatus.CANCELLED)

    def get_status(self) -> TaskStatus:
        with self.condition:
            return self._status

    def get_progress(self) -> float:
        with self.condition:
            return self._progress

    def get_result(self) -> dict | Any:
        with self.condition:
            return self.result

    def set_result(self, result: dict | Any):
        with self.condition:
            self.result = result


class TaskManager:
    def __init__(self, max_workers: int = 5, clean_interval: int = 360):
        self.tasks: dict[str, Task] = {}
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._shutdown = False

        # 初始化 apscheduler
        self.scheduler = BackgroundScheduler(daemon=True)
        self.scheduler.start()

        # 注册定期清理任务
        self.scheduler.add_job(
            self.clean_completed_tasks,
            trigger=IntervalTrigger(seconds=clean_interval),
            id="clean_completed_tasks",
            replace_existing=True,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown(wait=True)

    def clean_completed_tasks(self):
        """
        删除状态为 COMPLETED、CANCELLED 或 ERROR 的任务。
        """
        with self.lock:
            to_delete = [
                task_id
                for task_id, task in self.tasks.items()
                if task.get_status()
                in {TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.ERROR}
            ]
            for task_id in to_delete:
                self.tasks.pop(task_id, None)
            if to_delete:
                logger.info(f"已清理完成/取消/错误任务: {to_delete}")

    def shutdown(self, wait: bool = True) -> None:
        """
        关闭线程池并防止进一步提交任务。

        Args:
            wait: 是否等待已提交的任务完成
        """
        with self.lock:
            if not self._shutdown:
                self._shutdown = True
                self.scheduler.shutdown(wait=False)
                self.executor.shutdown(wait=wait)
                logger.info("任务管理器已关闭，线程池已释放。")

    def create_task(
        self,
        func: Callable,
        args: tuple = None,
        kwargs: dict = None,
        task_id: str = None,
    ) -> Task:
        if self._shutdown:
            raise RuntimeError("任务管理器已关闭，无法创建新任务。")

        task_id = task_id or str(uuid.uuid4())
        with self.lock:
            if task_id not in self.tasks:
                self.tasks[task_id] = Task(task_id, func=func, args=args, kwargs=kwargs)
            return self.tasks[task_id]

    def get_task(self, task_id: str) -> Optional[Task]:
        with self.lock:
            return self.tasks.get(task_id)

    def delete_task(self, task_id: str) -> None:
        with self.lock:
            task = self.tasks.pop(task_id, None)
            if task:
                task.cancel()

    def run_task(self, task_id: str) -> None:
        if self._shutdown:
            logger.warning("任务管理器已关闭，无法执行任务。")
            return

        task = self.get_task(task_id)
        if task is None:
            logger.warning(f"任务 {task_id} 不存在")
            return

        if task.get_status() == TaskStatus.RUNNING:
            logger.warning(f"任务 {task_id} 正在执行中")
            return

        logger.info(f"开始异步执行任务 {task_id}")
        self.executor.submit(task._run)

    def get_task_generator(self, task_id: str) -> Callable[..., Iterator[str]]:
        task = self.get_task(task_id)
        if task is None:
            logger.warning(f"任务 {task_id} 不存在")
            return

        if task.get_status() == TaskStatus.WAITING:
            self.run_task(task_id)

        def task_generator():
            sent_index = 0
            while True:
                messages_to_send = []
                with task.condition:
                    while (
                        len(task.history) <= sent_index
                        and task.get_status() == TaskStatus.RUNNING
                    ):
                        task.condition.wait()
                    while sent_index < len(task.history):
                        messages_to_send.append(
                            task.history[sent_index].model_dump_json()
                        )
                        sent_index += 1

                # 🚀 在锁之外 yield，避免连接断开干扰锁
                for msg in messages_to_send:
                    yield msg + "\n\n"

                if task.get_status() in {
                    TaskStatus.COMPLETED,
                    TaskStatus.CANCELLED,
                    TaskStatus.ERROR,
                }:
                    for msg in task.history[sent_index:]:
                        yield msg.model_dump_json() + "\n\n"

                    break

            self.delete_task(task_id)  # 执行完成，删除任务

        return task_generator

    def get_task_result(self, task_id: str) -> dict | Any:
        task = self.get_task(task_id)
        if task is None:
            logger.warning(f"任务 {task_id} 不存在")
            return None

        if task.get_status() == TaskStatus.WAITING:
            self.run_task(task_id)

        while True:
            with task.condition:
                while task.get_status() == TaskStatus.RUNNING:
                    task.condition.wait()
            if task.get_status() in {
                TaskStatus.COMPLETED,
                TaskStatus.CANCELLED,
                TaskStatus.ERROR,
            }:
                return task.get_result()


class ScheduleTaskManager(TaskManager):
    def __init__(self, max_workers: int = 5):
        super().__init__(max_workers)

        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.scheduled_jobs: dict[str, Job] = {}

    def shutdown(self, wait: bool = True) -> None:
        with self.lock:
            if not self._shutdown:
                self._shutdown = True
                self.executor.shutdown(wait=wait)
                self.scheduler.shutdown(wait=wait)  # 停止定时器
                logger.info("任务管理器已关闭，线程池和调度器已释放。")

    def create_task(
        self,
        func: Callable,
        args: tuple = None,
        kwargs: dict = None,
        trigger_type: Literal["interval", "cron"] = "interval",
        trigger_args: dict = None,
        task_id: str = None,
    ) -> Task:
        """
        定时调度一个任务。

        Args:
            func: 要执行的函数
            args: 传入的参数
            kwargs: 传入的关键字参数
            trigger_type: "interval" 或 "cron"
            trigger_args: APScheduler 的 trigger 配置，如 {"seconds": 10}
            task_id: 任务 ID

        Returns:
            Task: 调度器中的任务
        """
        if self._shutdown:
            raise RuntimeError("任务管理器已关闭，无法调度任务。")

        trigger_args = trigger_args or {}

        task_id = task_id or str(uuid.uuid4())

        task = super().create_task(func, args, kwargs, task_id=task_id)

        def scheduled_func(task_id=task.task_id, self_ref=self):
            super(ScheduleTaskManager, self_ref).run_task(task_id)

        trigger_cls = IntervalTrigger if trigger_type == "interval" else CronTrigger
        with self.lock:
            if task_id not in self.scheduled_jobs:
                job = self.scheduler.add_job(
                    scheduled_func,
                    trigger=trigger_cls(**trigger_args),
                    id=task_id,
                    replace_existing=True,
                )
                self.scheduled_jobs[task_id] = job
        return task

    def delete_task(self, task_id: str) -> None:
        super().delete_task(task_id)
        with self.lock:
            job = self.scheduled_jobs.pop(task_id, None)
            if job:
                job.remove()
