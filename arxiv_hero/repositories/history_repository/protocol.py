from pydantic import BaseModel
from datetime import datetime


class ReadHistory(BaseModel):
    entry_id: str
    title: str
    progress: float
    time_updated: datetime
