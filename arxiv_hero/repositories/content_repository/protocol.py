from typing import Literal, Optional

from pydantic import BaseModel


class LatexPagagraph(BaseModel):
    type: Literal[
        "article_name",  # 文章名
        "abstract",
        "title",
        "text",
        "figure",
        "table",
        "equation",
        "latex",
        "post_content",
        "reference",  # 参考文献
    ]
    order_idx: Optional[int] = None

    text: Optional[str] = None
    zh_text: Optional[str] = None
    text_level: Optional[int] = None  # 只对 title 有效

    def to_markdown(self, lang: Literal["en", "zh"] = "en"):
        text = self.text if lang == "en" else (self.zh_text or self.text)
        if self.type in ("equation", "post_content", "reference"):
            return self.text
        elif self.type == "title":
            return f"{'#' * self.text_level} {text}"
        elif self.type == "article_name":
            return "<h1><center>" + text + "</center></h1>"
        elif self.type == "abstract":
            return "# Abstract:\n\n" + text
        else:
            return text
