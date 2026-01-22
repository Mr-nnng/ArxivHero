from typing import Optional, Literal
from pydantic import BaseModel
from pathlib import Path


class LatexMatched(BaseModel):
    type: str
    command: str
    content: str
    start: int
    end: int
    order: Optional[int] = None


class LatexTitleMatched(LatexMatched):
    level: Optional[int] = None
    label: Optional[str] = None
    prefix: Optional[str] = None


class FigMetaData(BaseModel):
    note: Optional[str] = None
    path: Optional[str] = None


class LatexEnvMatched(LatexMatched):
    caption: Optional[str] = None
    label: Optional[str] = None
    sub_envs: Optional[list["LatexEnvMatched"]] = None
    meta_data: Optional[dict] = None


class LatexFile(BaseModel):
    path: Path
    content: Optional[str] = None
    included_files: Optional[list["LatexFile"]] = None
    parent_file: Optional["LatexFile"] = None
