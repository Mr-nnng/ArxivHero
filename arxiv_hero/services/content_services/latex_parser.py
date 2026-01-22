import re
import os
import bibtexparser
from urllib.parse import quote_plus
from pathlib import Path
from typing import Optional

from arxiv_hero import logger
from arxiv_hero.repositories.content_repository.protocol import LatexPagagraph
from arxiv_hero.services.content_services.protocol import (
    LatexMatched,
    LatexEnvMatched,
    LatexTitleMatched,
    LatexFile,
)
from arxiv_hero.services.content_services import utils

RESERVE_ENV_TYPE = (
    "itemize",
    "enumerate",
    "titlepage",
    "description",
    "quote",
    "verse",
    "center",
    "flushleft",
    "flushright",
    "centering",
    "raggedright",
    "raggedleft",
    "minipage",
    "keywords",
    "cases",
    "AIbox",
    "compactitem",
)

FONT_ENV_TYPE = (
    "tiny",
    "scriptsize",
    "footnotesize",
    "small",
    "normalsize",
    "large",
    "Large",
    "LARGE",
    "huge",
    "Huge",
)

SKIP_ENV_TYPE = (
    "title",
    "author",
    "abstract",
)


class LatexFiller:
    def __init__(self, source_dir: str) -> None:
        self.source_dir = source_dir
        self.include_pattern = re.compile(r"\\(?:input|include)\{([^}]+)\}")
        self.latex_files = self.get_latex_files()

        if os.path.isfile(os.path.join(source_dir, "__main_full__.tex")):
            self.flatten = lambda: os.path.join(source_dir, "__main_full__.tex")
        elif len(self.latex_files) == 1:
            self.flatten = lambda: str(self.latex_files[0])
        else:
            self.latex_map = self.build_latex_map()
            self.root_file = self.build_latex_graph()

    def get_latex_files(self) -> list[Path]:
        latex_files = []
        for root, _, files in os.walk(self.source_dir):
            for name in files:
                if name.endswith(".tex"):
                    latex_files.append(Path(os.path.join(root, name)).absolute())
        return latex_files

    def get_included_files(self, content: str) -> list[str]:
        return self.include_pattern.findall(content)

    def build_latex_map(self) -> dict[Path, LatexFile]:
        # k:文件路径 v:文件信息
        latex_map: dict[Path, LatexFile] = {
            file_path: LatexFile(path=file_path) for file_path in self.latex_files
        }
        return latex_map

    def build_latex_graph(self) -> LatexFile:
        for file_path, file in self.latex_map.items():
            content = utils.load_latex(file_path)
            included_files_path = self.get_included_files(content)
            included_files = []
            for path in included_files_path:
                path = os.path.join(self.source_dir, path)
                if not path.endswith(".tex"):
                    path = path + ".tex"
                path = Path(path).absolute()
                included_files.append(self.latex_map[path])
                self.latex_map[path].parent_file = file
            file.included_files = included_files
            file.content = content

        return utils.get_root_file(file)

    def _flatten(self, file: Optional[LatexFile] = None, visited=None) -> str:
        file = file or self.root_file
        if visited is None:
            visited = set()
        path_str = str(file.path.resolve())
        if path_str in visited:
            return ""
        visited.add(path_str)
        content = file.content or ""

        def repl(match: re.Match) -> str:
            fname = match.group(1)
            tex_name = fname if fname.endswith(".tex") else fname + ".tex"
            next_path = (Path(self.source_dir) / tex_name).resolve()
            child = self.latex_map.get(next_path)
            if child:
                return self._flatten(child, visited)
            else:
                logger.warning(f"\nincluded file not found: {next_path}")
                return ""

        return self.include_pattern.sub(repl, content)

    def flatten(self) -> str:
        full_content = self._flatten()
        save_path = os.path.join(self.source_dir, "__main_full__.tex")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(full_content)
        return save_path


class LatexParser:

    def _init_global_cachers(self) -> None:
        self.cites_map: dict[str, int] = {}
        self.cites: list[LatexMatched] = []
        self.refs_map: dict[str, tuple[str, int | str]] = {}  # k:名称 v:(类型,编号)
        self.refs: list[LatexMatched] = []
        self.titles: list[LatexTitleMatched] = []
        self.environments: list[LatexEnvMatched] = []
        self.env_paragraphs: list[LatexPagagraph] = []

    def _load_latex(self, source_dir: str) -> str:
        latex_path = LatexFiller(source_dir).flatten()
        with open(latex_path, "r", encoding="utf-8") as f:
            latex_cache = []
            for line in f:
                if line.startswith("%"):
                    continue
                latex_cache.append(line)
            latex_text = "".join(latex_cache)

        # 匹配 \begin{document} 到 \end{document} 之间的内容
        pattern = r"\\begin\{document\}(.*?)\\end\{document\}"
        pre_match = re.search(pattern, latex_text, re.DOTALL)
        if pre_match:
            latex_text = pre_match.group(1)
        latex_text = (
            "【-START_OF_DOCUMENT-】\n\n" + latex_text + "\n\n【-END_OF_DOCUMENT-】"
        )
        return latex_text

    def _parse_bib(self, bib_path: str) -> tuple[LatexPagagraph, LatexPagagraph]:
        with open(bib_path, encoding="utf-8") as f:
            bib_database = bibtexparser.load(f)
        reference_map = {}
        reference_text_map = {}
        for entry in bib_database.entries:
            entry_id = entry.get("ID")
            order = self.cites_map.get(entry_id) if entry_id else None
            if not order:
                continue
            author = entry.get("author", "Unknown Author").replace("\n", " ")
            year = entry.get("year", "n.d.")
            journal = entry.get("journal", "").replace("\n", " ")
            booktitle = entry.get("booktitle", "").replace("\n", " ")
            publisher = entry.get("publisher", "").replace("\n", " ")
            title = entry.get("title", "Untitled").replace("\n", " ")
            href_title = utils.extract_href_title(title)
            title = href_title["text"]
            doi = (
                href_title.get("url")
                or entry.get("doi", "")
                or ("https://www.bing.com/search?q=" + quote_plus(title))
            )
            if not doi.startswith("http"):
                doi = "https://doi.org/" + doi
            # 处理作者只保留第一作者
            first_author = author.split(" and ")[0].split(",")[0]

            # 构造 markdown 引用部分
            citation = f"{first_author} et al., {title}, {journal or booktitle or publisher}, {year}"
            markdown_ref = f'[{order}]: {doi} "{citation}"'
            reference_map[order] = markdown_ref
            markdown_ref_text = f"[\\[{order}\\] {citation}][{order}]"
            reference_text_map[order] = markdown_ref_text

        references = []
        for _, ref in sorted(reference_map.items(), key=lambda x: x[0]):
            references.append(ref)
        references_text = []
        for _, ref_text in sorted(reference_text_map.items(), key=lambda x: x[0]):
            references_text.append(ref_text)

        return (
            LatexPagagraph(type="reference", text="\n\n".join(references)),
            LatexPagagraph(type="reference", text="\n\n".join(references_text)),
        )

    def _replace_environments(
        self, text: str, envs: list[LatexEnvMatched], idx_path: list[int] = None
    ) -> str:
        if not envs:
            return text
        idx_path = idx_path or []
        text_len = len(text)
        for idx, env in enumerate(envs):
            if env.label and env.label not in self.refs_map:
                self.refs_map[env.label] = (env.type, env.order)

            if env.type in ("aligned", "array"):
                continue
            if env.type in ("table", "figure", "wrapfigure"):
                main_text = ""
            elif env.type in ("equation"):
                main_text = text[env.start - text_len : env.end - text_len]
            else:
                main_text = self._replace_environments(
                    text[env.start - text_len : env.end - text_len],
                    env.sub_envs,
                    idx_path + [idx],
                )

            env_text = (
                main_text
                if env.type in RESERVE_ENV_TYPE or env.type in FONT_ENV_TYPE
                else (
                    f"\n【-START_ENVIRONMENT-】【index_path: {",".join([str(i) for i in idx_path+[idx]])}】【type: {env.type}】【order: {env.order}】\n\n"
                    + main_text
                    + "\n\n【-END_ENVIRONMENT-】\n"
                )
            )
            text = text[: env.start - text_len] + env_text + text[env.end - text_len :]

        return text

    def _replace_post_environments(self, text: str, envs: list[LatexEnvMatched]) -> str:
        if not envs:
            return text
        text_len = len(text)
        for env in envs:
            _env = utils.get_env_by_index_path(
                self.environments, env.meta_data["index_path"]
            )
            if env.type in ("figure", "wrapfigure"):
                figure_body = utils.parse_figure_block(_env.content)
                main_text = (
                    figure_body
                    + f"\n\n**Figure {_env.order}**: {utils.trans_latex_to_markdown(_env.caption)}"
                )
                env_text = (
                    "\n【-START_FIGURE-】\n【-LABEL-】\n"
                    + main_text
                    + "\n【-END_FIGURE-】\n"
                )
            elif env.type == "table":
                table_body = utils.parse_table_block(_env)
                main_text = (
                    f"**Table {_env.order}**: {utils.trans_latex_to_markdown(_env.caption)}\n\n"
                    + table_body
                )
                env_text = (
                    "\n【-START_TABLE-】\n【-LABEL-】\n"
                    + main_text
                    + "\n【-END_TABLE-】\n"
                )
            elif env.type == "equation":
                main_text = env.content.split("】\n", 1)[-1].split(
                    "【-END_ENVIRONMENT-】", 1
                )[0]
                main_text = main_text.replace(
                    "\n【-MATH_ORDER-】", f"   ({_env.order})"
                ).replace("【-MATH_ORDER-】", f"   ({_env.order})")
                env_text = (
                    "\n【-START_EQUATION-】\n【-LABEL-】\n"
                    + main_text
                    + "\n【-END_EQUATION-】\n"
                )
            elif env.type == "algorithm":
                main_text = f"```latex\n{_env.content}\n```"
                env_text = (
                    "\n【-START_LATEX-】\n【-LABEL-】\n"
                    + main_text
                    + "\n【-END_LATEX-】\n"
                )
            elif env.type in SKIP_ENV_TYPE:
                env_text = ""
            else:
                if env.sub_envs:
                    env_text = self._replace_post_environments(
                        text[env.start - text_len : env.end - text_len],
                        env.sub_envs,
                    )
                else:
                    main_text = f"```latex\n{_env.content}\n```"
                    env_text = (
                        "\n【-START_LATEX-】\n【-LABEL-】\n"
                        + main_text
                        + "\n【-END_LATEX-】\n"
                    )

            if _env.label:
                env_text = env_text.replace("【-LABEL-】", f"【LABEL_{_env.label}】")
            else:
                env_text = env_text.replace("【-LABEL-】", "")

            text = text[: env.start - text_len] + env_text + text[env.end - text_len :]

        return text

    def _replace_paragraph_environments(
        self, text: str, envs: list[LatexEnvMatched], is_top: bool = False
    ) -> str:
        if not envs:
            return text
        text_len = len(text)
        for env in envs:
            if env.sub_envs:
                env_text = self._replace_paragraph_environments(
                    text[env.start - text_len : env.end - text_len],
                    env.sub_envs,
                )
                env_text = env_text[
                    len(f"【-START_{env.command}-】") : -len(f"【-END_{env.command}-】")
                ]
            else:
                env_text = ""

            if is_top:
                text = (
                    text[: env.start - text_len]
                    + f"【ENVIRONMENT】【index: {len(self.env_paragraphs)}】"
                    + text[env.end - text_len :]
                )
                self.env_paragraphs.append(
                    LatexPagagraph(
                        type=env.type,
                        text=env_text or env.content,
                    )
                )
            else:
                text = (
                    text[: env.start - text_len]
                    + (env_text or env.content)
                    + text[env.end - text_len :]
                )

        return text

    def pre_process(self, text: str) -> str:

        # 将 \cal X 替换为 \mathcal{X}
        text = re.sub(r"\\cal\s+([A-Za-z])", r"\\mathcal{\1}", text)

        # 替换 cite
        self.cites = utils.match_cite(text)
        text_len = len(text)
        for cite in self.cites:
            items = [item.strip() for item in cite.content.split(",")]
            for item in items:
                if item not in self.cites_map:
                    self.cites_map[item] = len(self.cites_map) + 1
            cite_text = str([self.cites_map[item] for item in items])
            text = (
                text[: cite.start - text_len] + cite_text + text[cite.end - text_len :]
            )

        # 替换 title
        self.titles = utils.match_title(text)
        text_len = len(text)
        for title in self.titles:
            title_text = f"\\{title.command}" + "{" + title.content + "}"
            if title.label:
                title_text += f"\n\n【LABEL_{title.label}】\n\n"
                self.refs_map[title.label] = (title.type, title.prefix)
            text = (
                text[: title.start - text_len]
                + title_text
                + text[title.end - text_len :]
            )

        # 替换 environment
        self.environments = utils.match_environments(text)
        text = self._replace_environments(text, self.environments)

        # 替换 ref
        self.refs = utils.match_ref(text)
        text_len = len(text)
        for ref in self.refs:
            ref_text_cache = []
            for item in ref.content.split(","):
                if item not in self.refs_map:
                    continue
                ref_type, ref_order = self.refs_map[item]
                ref_note = (
                    ref_order
                    if ref_type in ("table", "figure", "wrapfigure")
                    else ref_type.capitalize() + " " + str(ref_order)
                )
                ref_text_cache.append(f"【REF_{item}_{ref_note}】")
            text = (
                text[: ref.start - text_len]
                + " ".join(ref_text_cache)
                + text[ref.end - text_len :]
            )

        # 替换 label
        text = re.sub(r"\\label\{(.*?)\}", r"【LABEL_\1】", text)

        return text

    def post_process(self, text: str, is_replace_cite: bool = True) -> str:
        def remove_backticks_in_dollar(match: re.Match):
            content = match.group(1)
            # 去除 content 中的反引号（`）
            cleaned = content.replace("`", "")
            return f"${cleaned}$"

        def remove_label_in_math_blocks(match: re.Match):
            content = match.group(1)
            # 去除其中的【LABEL_XXX】标签
            cleaned = re.sub(r"【LABEL_[^】]+】\s*", "", content)
            cleaned = cleaned.replace("\\hfill", "").replace("\\vfill", "")
            return f"$$\n{cleaned}　　【-MATH_ORDER-】\n$$"

        def replace_ref(match: re.Match):
            content = match.group(1)
            label, note = content.rsplit("_", 1)
            note = note.strip().rstrip(".")
            return r'<a href="#' + label + r'">' + note + r"</a>"

        def replace_cite(match):
            content = match.group(1)
            numbers = [num.strip() for num in content.split(",")]
            if len(numbers) == 1:
                return f"[[{numbers[0]}]]"
            else:
                return "[" + ", ".join(f"[{num}]" for num in numbers) + "]"

        def replace_multiline_equation(match):
            # 匹配换行公式
            content = match.group(1).replace("【-MATH_ORDER-】", "").strip()
            content = (
                "\n【-START_EQUATION-】\n"
                + f"$$\n{content}\n$$"
                + "\n【-END_EQUATION-】\n"
            )
            return content

        text = text.replace("$$", "$ $").replace("\r", "")
        # 使用正则表达式去掉含有 ```math 的行前面的空格
        text = re.sub(r"^\s*(``` math)", r"\1", text, flags=re.MULTILINE)
        text = re.sub(
            r"``` math\n(.*?)```", remove_label_in_math_blocks, text, flags=re.DOTALL
        )  # 去除 math 块中的 label
        text = re.sub(
            r'<div\s+class="adjustwidth">.*?</div>', "", text, flags=re.DOTALL
        )  # 去除 adjustwidth

        # 替换 env
        post_envs = utils.match_post_environments(text)
        text = self._replace_post_environments(text, post_envs)

        text = re.sub(
            r"\$(.*?)\$", remove_backticks_in_dollar, text
        )  # 匹配 ` 包裹的 LaTeX 行内公式（即 $`...`$）
        text = re.sub(
            r"【LABEL_([^】]+)】", r'<span id="\1"></span>', text
        )  # 替换 label
        text = re.sub(r"【REF_([^】]+)】", replace_ref, text)  # 替换 ref

        # 再次替换 env
        paragraph_envs = utils.match_paragraph_environments(text)
        text = self._replace_paragraph_environments(text, paragraph_envs, is_top=True)

        # 替换换行公式
        text = re.sub(
            r"\$\$(.*?)\$\$", replace_multiline_equation, text, flags=re.DOTALL
        )
        multiline_equation_envs = utils.match_paragraph_environments(text)
        text = self._replace_paragraph_environments(
            text, multiline_equation_envs, is_top=True
        )

        # 替换 cite
        # 匹配 \[ ... \] 中的内容
        text = re.sub(r"\\\[(\d+(?:\s*,\s*\d+)*)\\\]", replace_cite, text)

        text = text.replace("【-MATH_ORDER-】", "")
        return text

    def build_latex_paragraphs(self, text: str) -> list[LatexPagagraph]:
        result = []

        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith(("【-END_ENVIRONMENT-】")):
                continue
            if line.startswith("【-START_ENVIRONMENT-】"):
                logger.warning(f"\n未处理的环境：{line}")
                continue
            if line.startswith("【ENVIRONMENT】"):
                index = int(line[13:].split("】")[0].replace("【index: ", ""))
                result.append(self.env_paragraphs[index])
            elif line.startswith("#"):
                symbol, title = line.split(" ", 1)
                result.append(
                    LatexPagagraph(
                        type="title",
                        text=title,
                        text_level=symbol.count("#"),
                    )
                )
            else:
                result.append(LatexPagagraph(type="text", text=line))
        return result

    def parse(self, source_dir: str) -> list[LatexPagagraph]:
        self._init_global_cachers()

        latex_text = self._load_latex(source_dir)
        latex_text = self.pre_process(latex_text)
        md_text = utils.trans_latex_to_markdown(latex_text)

        bib_path = utils.find_file(source_dir, ".bib")
        md_text = self.post_process(md_text, True if bib_path else False)

        post_content = md_text[md_text.rfind("【-END_OF_DOCUMENT-】") + 19 :].strip()
        doc_match = re.search(
            r"【-START_OF_DOCUMENT-】(.*?)【-END_OF_DOCUMENT-】", md_text, re.DOTALL
        )
        if doc_match:
            md_text = doc_match.group(1)

        # 只保留第一章及之后的内容
        start_idxs = []
        if "# 1. " in md_text:
            start_idxs.append(md_text.find("# 1. "))
        if "【ENVIRONMENT】" in md_text:
            start_idxs.append(md_text.find("【ENVIRONMENT】"))
        if start_idxs:
            md_text = md_text[min(start_idxs) :]

        latex_paragraphs = self.build_latex_paragraphs(md_text)
        if post_content:
            latex_paragraphs.append(
                LatexPagagraph(
                    type="post_content",
                    text=post_content.replace(r"<span", "\n\n" + r"<span"),
                )
            )

        if bib_path:
            refs, refs_text = self._parse_bib(bib_path)
            latex_paragraphs.insert(0, refs)
            latex_paragraphs.append(refs_text)

        for i, paragraph in enumerate(latex_paragraphs):
            paragraph.order_idx = i

        return latex_paragraphs


if __name__ == "__main__":
    latex_parser = LatexParser()
    latex_paragraphs = latex_parser.parse(
        r"D:\code\arxiv_hero\.data\articles\2504.21318v1\source",
    )

    md_text = "\n\n".join([p.to_markdown() for p in latex_paragraphs])

    utils.save_text(
        md_text, r"D:\code\arxiv_hero\.data\articles\2504.21318v1\source\md_text.md"
    )
