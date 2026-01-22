import os
import time
from typing import Callable

import arxiv

from arxiv_hero.config import get_config
from arxiv_hero.repositories.article_repository import ArticleRepository
from arxiv_hero.repositories.content_repository import ContentRepository
from arxiv_hero.repositories.content_repository.protocol import LatexPagagraph
from arxiv_hero.services.content_services.latex_parser import LatexParser
from arxiv_hero.services.content_services.translator import Translator
from arxiv_hero.services.content_services import utils


class ContentProcessor:
    def __init__(self):
        self.config = get_config().arxiv
        self.repository = ContentRepository()
        self.article_repository = ArticleRepository()
        self.translator = Translator()

    def download_pdf(self, article_id: str) -> str:
        download_dir = os.path.join(self.config.download_dir, article_id)
        download_path = os.path.join(download_dir, f"{article_id}.pdf")
        if os.path.isfile(download_path):
            return download_path

        os.makedirs(download_dir, exist_ok=True)
        paper = next(
            arxiv.Client(delay_seconds=600).results(arxiv.Search(id_list=[article_id]))
        )
        download_path = paper.download_pdf(
            dirpath=download_dir,
            filename=f"{article_id}.pdf",
            download_domain="arxiv.org",
        )
        return download_path

    def download_source_and_extract(self, article_id: str) -> str:
        download_dir = os.path.join(self.config.download_dir, article_id)
        source_dir = os.path.join(download_dir, "source")
        if os.path.isfile(os.path.join(download_dir, f"{article_id}.tar.gz")):
            return source_dir

        os.makedirs(source_dir, exist_ok=True)
        paper = next(
            arxiv.Client(delay_seconds=600).results(arxiv.Search(id_list=[article_id]))
        )
        download_path = paper.download_source(
            dirpath=download_dir,
            filename=f"{article_id}.tar.gz",
        )
        utils.extract_tar_gz(download_path, source_dir)
        return source_dir

    def post_process_paragraphs(
        self, entry_id: str, paragraphs: list[LatexPagagraph]
    ) -> None:
        for paragraph in paragraphs:
            if paragraph.type == "figure":
                figure_path_list = utils.extract_figure_path(paragraph.text)
                for figure_path in figure_path_list:
                    if figure_path.endswith((".pdf", ".eps", ".bmp")):
                        basename, ext = figure_path.rsplit(".", 1)
                        utils.trans_figure_to_png(
                            os.path.join(
                                self.config.download_dir,
                                entry_id,
                                "source",
                                figure_path,
                            )
                        )
                        paragraph.text = paragraph.text.replace(
                            figure_path, f"{basename}.png"
                        )

    def translate_paragraph(
        self,
        paragraph: LatexPagagraph,
        history: list[list[str]] = None,
    ) -> tuple[LatexPagagraph, bool]:
        history = history or []
        if paragraph.zh_text is not None:
            return paragraph, False

        if utils.is_all_digits(paragraph.text):
            return paragraph, False

        if paragraph.type == "text":
            if "<div" in paragraph.text or "<span" in paragraph.text:
                return paragraph, False
            zh_text = self.translator.translate_content(paragraph.text, history)
            paragraph.zh_text = zh_text
            return paragraph, True
        if paragraph.type == "title":
            zh_text = self.translator.translate_title(paragraph.text)
            paragraph.zh_text = zh_text
            return paragraph, True
        if paragraph.type in ("table", "figure", "latex"):
            zh_text = self.translator.translate_markdown(paragraph.text)
            paragraph.zh_text = zh_text
            return paragraph, True
        if paragraph.type in (
            "equation",
            "post_content",
            "reference",
            "article_name",
            "abstract",
        ):
            return paragraph, False

    def parse(self, entry_id: str) -> list[LatexPagagraph]:
        article = self.article_repository.get_article_by_entry_id(entry_id)
        if not article:
            raise Exception(f"【{entry_id}】不存在")

        pagagraphs = self.repository.get_pagagraphs(entry_id=entry_id)
        if not pagagraphs:
            # 0. 下载PDF和源文件
            self.download_pdf(entry_id)
            source_dir = self.download_source_and_extract(entry_id)

            # 1. 解析 Latex
            pagagraphs = LatexParser().parse(source_dir)

            # 2. 后处理
            self.post_process_paragraphs(entry_id, pagagraphs)

            # 3. 入库
            self.repository.create_content(entry_id, pagagraphs, is_translated=True)

        pagagraphs = [
            LatexPagagraph(
                type="article_name",
                text=article.title,
                zh_text=article.zh_title,
            ),
            LatexPagagraph(
                type="abstract",
                text=article.summary.replace("\n", " "),
                zh_text=article.zh_summary,
            ),
        ] + pagagraphs

        md_path = os.path.join(
            self.config.download_dir, entry_id, "source", f"{entry_id}_en.md"
        )
        if not os.path.isfile(md_path):
            utils.save_text(
                "\n\n".join([p.to_markdown(lang="en") for p in pagagraphs]),
                md_path,
            )

        return pagagraphs

    def translate(
        self,
        entry_id: str,
        callback: Callable[[str, dict, float], None] = None,
    ) -> list[LatexPagagraph]:
        article = self.article_repository.get_article_by_entry_id(entry_id)
        if not article or not article.zh_summary:
            raise Exception(f"【{entry_id}】没有中文摘要")

        if callback:
            callback(f"【{entry_id}】开始翻译，正在解析文档... ", None, 0)

        start_time = time.time()  # 开始计时

        # 1. 解析文档
        pagagraphs = self.parse(entry_id)

        if callback:
            callback(
                f"解析文档完成，用时{time.time() - start_time:.2f}s ",
                None,
                0.2,
            )

        history = [article.summary.replace("\n", " "), article.zh_summary]

        # 2. 翻译
        for i, pagagraph in enumerate(pagagraphs):
            pagagraph, is_translated = self.translate_paragraph(pagagraph, history)
            # 3. 填充翻译
            if is_translated:
                self.repository.update_zh_field(
                    entry_id, pagagraph.order_idx, {"zh_text": pagagraph.zh_text}
                )
            pagagraph.order_idx = i
            if callback:
                callback(
                    f"翻译中... {i+1}/{len(pagagraphs)}" if is_translated else None,
                    pagagraph.model_dump(),
                    0.2 + 0.8 * ((i + 1) / len(pagagraphs)),
                )

        if callback:
            callback(
                f"【{entry_id}】翻译完成，共用时{time.time() - start_time:.2f}s ",
                None,
                1,
            )

        md_path = os.path.join(
            self.config.download_dir, entry_id, "source", f"{entry_id}_zh.md"
        )
        if not os.path.isfile(md_path):
            utils.save_text(
                "\n\n".join([p.to_markdown(lang="zh") for p in pagagraphs]),
                md_path,
            )

        return pagagraphs


if __name__ == "__main__":
    processor = ContentProcessor()
    entry_id = "2504.21370v1"

    def callback(msg, item, progress):
        print("-" * 50)
        print(msg)
        print(f"data: {item}")
        print(f"progress: {progress}")
        print("-" * 50)

    pagagraphs = processor.translate(entry_id, callback)
    with open(r"D:\code\arxiv_hero\tmp\article.md", "w", encoding="utf-8") as f:
        for pagagraph in pagagraphs:
            f.write(pagagraph.to_markdown(lang="zh") + "\n\n")
