import re
import os
import string

import fitz  # PyMuPDF
import tarfile
import pypandoc
from PIL import Image

from arxiv_hero import logger
from arxiv_hero.services.content_services.protocol import (
    LatexMatched,
    LatexEnvMatched,
    LatexTitleMatched,
    FigMetaData,
    LatexFile,
)


def is_all_digits(s: str) -> bool:
    allowed_chars = string.digits + string.punctuation + string.whitespace
    return all(ch in allowed_chars for ch in s)


def save_text(text: str, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def load_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def load_latex(file_path: str):
    content = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("%"):
                continue
            content.append(line)
    return "".join(content)


def extract_tar_gz(file_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # 打开 tar.gz 文件
    with tarfile.open(file_path, "r:gz", encoding="utf-8") as tar:
        # 解压到指定目录
        tar.extractall(path=output_dir)


# 查找指定文件夹下指定格式的文件，并返回文件路径
def find_file(folder_path: str, file_format: str) -> str | None:
    for file in os.listdir(folder_path):
        if file.endswith(file_format):
            return os.path.join(folder_path, file)
    return None


def trans_latex_to_markdown(latex_text: str) -> str:
    md_text = pypandoc.convert_text(
        latex_text,
        "gfm",
        format="latex",
        extra_args=["--wrap=none"],
    )
    return md_text


def match_cite(text: str) -> list[LatexMatched]:
    # 扩展正则表达式，支持 cite、citet、citep、citeauthor、citeyear、parencite、textcite
    pattern = re.compile(r"\\(cite\w*|parencite|textcite)\s*{([^}]*)}")
    results = []
    all = pattern.finditer(text)
    for m in all:
        results.append(
            LatexMatched(
                type="cite",
                command=m.group(1),
                content=m.group(2),
                start=m.start(),
                end=m.end(),
            )
        )
    return results


def match_ref(text: str) -> list[LatexMatched]:
    # 支持 各种ref
    pattern = re.compile(r"\\(ref|cref|vref|pageref|eqref)\{([^\}]+)\}")
    results = []
    all = pattern.finditer(text)
    for m in all:
        results.append(
            LatexMatched(
                type="ref",
                command=m.group(1),
                content=m.group(2),
                start=m.start(),
                end=m.end(),
            )
        )
    return results


def match_title(text: str) -> list[LatexTitleMatched]:
    title_level_map = {
        "section": 1,
        "subsection": 2,
        "subsubsection": 3,
        "paragraph": 4,
        "subparagraph": 5,
    }
    title_counts = [0, 0, 0]  # h1, h2, h3
    pattern = pattern = re.compile(
        r"""
    (?P<command>\\
        (?:section|subsection|subsubsection|paragraph|subparagraph)
        \*?          # Optional star for unnumbered sections
    )
    (?:            # Optional short title in square brackets
        \[
        (?P<short>[^\]]+)
        \]
    )?
    \{             # Main title in curly braces
        (?P<title>[^}]+)
    \}
    (?:            # Optional label after the command, often on same line
        \s*
        \\label\{
            (?P<label>[^\}]+)
        \}
    )?
    """,
        re.VERBOSE,
    )
    matches = []
    for match in pattern.finditer(text):
        cmd = match.group("command").lstrip("\\").rstrip("*")
        title_level = title_level_map.get(cmd)
        if title_level == 1:
            title_counts = [title_counts[0] + 1, 0, 0]
            title_prefix = f"{title_counts[0]}. "
        elif title_level == 2:
            title_counts = [title_counts[0], title_counts[1] + 1, 0]
            title_prefix = f"{title_counts[0]}.{title_counts[1]} "
        elif title_level == 3:
            title_counts = [title_counts[0], title_counts[1], title_counts[2] + 1]
            title_prefix = f"{title_counts[0]}.{title_counts[1]}.{title_counts[2]} "
        else:
            title_prefix = ""
        matches.append(
            LatexTitleMatched(
                type="paragraph" if "paragraph" in cmd else "section",
                command=cmd,
                content=title_prefix + match.group("title"),
                label=match.group("label"),
                start=match.start(),
                end=match.end(),
                level=title_level_map.get(cmd),
                prefix=title_prefix,
            )
        )

    return matches


def match_caption(text: str) -> str | None:
    start = 0
    brace_level = 0
    range_start_idx = []
    if "\\caption{" in text:
        range_start_idx = text.find("\\caption{")
    elif "\\caption[" in text:
        range_start_idx = text.find("\\caption[")
    else:
        return
    range_start = range_start_idx
    for i in range(range_start, len(text)):
        if text[i] == "{":
            if brace_level == 0:
                start = i
            brace_level += 1
        elif text[i] == "}":
            brace_level -= 1
            if brace_level == 0:
                return text[start + 1 : i].strip()
    # caption_match = re.search(r"\\caption(?:\[.*?\])?\{(.*?)\}", text, re.DOTALL)
    # return caption_match.group(1) if caption_match else None


def match_label(text: str) -> str | None:
    label_match = re.search(r"\\label\{([^}]+)\}", text, re.DOTALL)
    return label_match.group(1) if label_match else None


def _re_index(env: LatexEnvMatched, offset: int = 0) -> None:
    # 当前节点处理
    env.start -= offset
    env.end -= offset

    # 遍历子节点，更新偏移量为当前节点原始 start
    for sub_env in env.sub_envs:
        _re_index(sub_env, offset=offset + env.start)


def match_environments(text: str) -> list[LatexEnvMatched]:
    env_order_map = {}
    # 同时捕获 \begin{env} 和 \end{env*}，env 里允许字母+数字+下划线，再可选一个 '*'
    pattern = re.compile(r"\\(begin|end)\{(\w+\*?)\}")
    results: list[LatexEnvMatched] = []
    match_stack: list[re.Match] = []
    sub_env_stack: list[list[LatexEnvMatched]] = []

    for m in pattern.finditer(text):
        kind, name = m.group(1), m.group(2)

        if kind == "begin":
            # 把 \begin{…} 的 match 对象压栈
            match_stack.append(m)
            sub_env_stack.append([])

        else:  # kind == "end"
            if not match_stack:
                # 多了一个没有对应的 begin，直接跳过
                continue

            top = match_stack.pop()
            sub_envs = sub_env_stack.pop()
            top_name = top.group(2)
            if top_name == name:
                # 栈顶 match 与当前 \end{…} 名称一致，则配对
                start_idx = top.start()
                end_idx = m.end()
                content = text[start_idx:end_idx]
                env_type = name.rstrip("*")
                if env_type not in env_order_map:
                    env_order_map[env_type] = 0
                env_order_map[env_type] += 1
                env = LatexEnvMatched(
                    type=env_type,
                    command=name,
                    content=content,
                    start=start_idx,
                    end=end_idx,
                    caption=match_caption(content),
                    label=match_label(content),
                    sub_envs=sub_envs,
                    order=env_order_map[env_type],
                )
                if match_stack:  # 如果栈不为空，说明是子环境
                    sub_env_stack[-1].append(env)
                else:
                    results.append(env)

    for env in results:
        _re_index(env)
    return results


def match_post_environments(text: str) -> list[LatexEnvMatched]:
    def parse_env_data(data_text: str) -> tuple[list[int], str, int]:
        for span in data_text.replace("【", "").split("】"):
            if span.startswith("index_path: "):
                index_path = [int(i) for i in span[12:].split(",")]
            elif span.startswith("type: "):
                type = span[6:]
            elif span.startswith("order: "):
                order = int(span[7:])
        return index_path, type, order

    pattern = re.compile(r"【-(START|END)_ENVIRONMENT-】")
    results: list[LatexEnvMatched] = []
    match_stack: list[re.Match] = []
    sub_env_stack: list[list[LatexEnvMatched]] = []

    for m in pattern.finditer(text):
        kind = m.group(1)
        if kind == "START":
            match_stack.append(m)
            sub_env_stack.append([])
        else:  # kind == "END"
            if not match_stack:
                continue

            top = match_stack.pop()
            sub_envs = sub_env_stack.pop()
            start_idx = top.start()
            end_idx = m.end()

            content = text[start_idx:end_idx]
            # 获取data_text，并去掉其中的 【-START_ENVIRONMENT-】
            data_text = content.split("\n", 1)[0][21:].strip()
            index_path, type, order = parse_env_data(data_text)

            env = LatexEnvMatched(
                type=type,
                command=type,
                content=content,
                start=start_idx,
                end=end_idx,
                sub_envs=sub_envs,
                order=order,
                meta_data={"index_path": index_path},
            )
            if match_stack:  # 如果栈不为空，说明是子环境
                sub_env_stack[-1].append(env)
            else:
                results.append(env)

    for env in results:
        _re_index(env)
    return results


def match_paragraph_environments(text: str) -> list[LatexEnvMatched]:
    pattern = re.compile(r"【-(START|END)_(FIGURE|TABLE|EQUATION|LATEX)-】")
    results: list[LatexEnvMatched] = []
    match_stack: list[re.Match] = []
    sub_env_stack: list[list[LatexEnvMatched]] = []
    type_map = {
        "FIGURE": "figure",
        "TABLE": "table",
        "EQUATION": "equation",
        "LATEX": "latex",
    }

    for m in pattern.finditer(text):
        kind, env_type = m.group(1), m.group(2)
        if kind == "START":
            match_stack.append(m)
            sub_env_stack.append([])
        else:  # kind == "END"
            if not match_stack:
                continue
            top = match_stack.pop()
            sub_envs = sub_env_stack.pop()
            env = LatexEnvMatched(
                type=type_map[env_type],
                command=env_type,
                content=text[top.end() : m.start()].strip(),
                start=top.start(),
                end=m.end(),
                sub_envs=sub_envs,
            )
            if match_stack:
                sub_env_stack[-1].append(env)
            else:
                results.append(env)
    for env in results:
        _re_index(env)
    return results


def parse_figure_block(latex_text: str) -> str:
    results: list[FigMetaData] = []

    # 1. 匹配 subfloat（subfig 包）
    subfloat_pattern = re.compile(
        r"\\subfloat\s*"
        r"\[\s*(?P<caption>.*?)\s*(?:\\label\{.*?\})?\s*\]\s*"  # [caption\label{...}]
        r"\{\s*\\includegraphics(?:\[[^\]]*\])?\{\s*(?P<path>[^}]+)\}\s*\}",
        re.DOTALL,
    )

    for match in subfloat_pattern.finditer(latex_text):
        caption = match.group("caption").strip()
        path = match.group("path").strip()
        results.append(FigMetaData(note=caption, path=path.lstrip("./").lstrip(".")))

    # 2. 匹配 subfigure 环境（subcaption 包）
    subfigure_env_pattern = re.compile(r"\\begin\{subfigure\}.*?\\end\{subfigure\}", re.DOTALL)
    for block in subfigure_env_pattern.findall(latex_text):
        # 本块中提取 includegraphics
        inc_match = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{\s*(?P<path>[^}]+)\}", block, re.DOTALL)
        cap_match = re.search(r"\\caption\{(?P<caption>.*?)\}", block, re.DOTALL)

        if inc_match:
            path = inc_match.group("path").strip()
        else:
            continue

        caption = cap_match.group("caption").strip() if cap_match else ""
        results.append(FigMetaData(note=caption, path=path.lstrip("./").lstrip(".")))

    # 3. 匹配 minipage + caption*（无编号子图）
    minipage_env_pattern = re.compile(r"\\begin\{minipage\}.*?\\end\{minipage\}", re.DOTALL)
    for block in minipage_env_pattern.findall(latex_text):
        inc_match = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{\s*(?P<path>[^}]+)\}", block, re.DOTALL)
        capstar_match = re.search(r"\\caption\*\{(?P<caption>.*?)\}", block, re.DOTALL)

        if inc_match:
            path = inc_match.group("path").strip()
        else:
            continue

        caption = capstar_match.group("caption").strip() if capstar_match else ""
        results.append(FigMetaData(note=caption, path=path.lstrip("./").lstrip(".")))

    # 4. 如果上面都没有匹配到，回退到单独 includegraphics
    if not results:
        include_pattern = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\{\s*(?P<path>[^}]+)\s*\}", re.DOTALL)
        for match in include_pattern.finditer(latex_text):
            path = match.group("path").strip()
            results.append(FigMetaData(path=path.lstrip("./").lstrip(".")))

    cache = []
    for item in results:
        cache.append(f"![]({item.path})\n\n{item.note}" if item.note else f"![]({item.path})")
    return "\n".join(cache)


def get_env_by_index_path(envs: list[LatexEnvMatched], index_path: list[int]) -> LatexEnvMatched:
    env = envs[index_path[0]]
    for idx in index_path[1:]:
        env = env.sub_envs[idx]
    return env


def parse_table_block(table_env: LatexEnvMatched) -> str:
    tabular = None
    for sub_env in table_env.sub_envs:
        if sub_env.type in ("tabular", "tabularx"):
            tabular = sub_env
            break
    if not tabular:
        # raise ValueError("Table block does not contain tabular environment")
        logger.warning("Table block does not contain tabular environment")
        logger.debug(f"Table block content: {table_env.content}")
        return table_env.content

    if tabular.command == "tabular":
        table = trans_latex_to_markdown(tabular.content.replace("|", "\\|")).replace("\r\n", "\n").replace("\n\n", "\n")
        if not table.startswith("<div"):
            return table

    # 处理特殊的 tabular 以及 tabular* 和 tabularx
    body = ""
    for line in tabular.content.splitlines():
        if "\\begin" in line or "\\end" in line:
            continue
        body += line + "\n"
    num_columns = body.split("\\\\", 1)[0].count("&")
    tabular_content = "\\begin{tabular}" + "{l" + "c" * num_columns + "}\n" + body + "\\end{tabular}"
    table = trans_latex_to_markdown(tabular_content.replace("|", "\\|")).replace("\r\n", "\n").replace("\n\n", "\n")
    if table.startswith("<div"):
        return f"```latex\n{tabular.content}\n```"
    return table


def extract_href_title(title_str):
    r"""
    提取 \href{url}{text} 格式中的 url 和 text。
    """
    match = re.search(r"\\href\{([^}]+)\}\{([^}]+)\}", title_str)
    if match:
        url, text = match.groups()
        return {"url": url, "text": text}
    else:
        return {"url": None, "text": title_str}


def extract_figure_path(text: str) -> list[str]:
    pattern = r"!\[[^\]]*\]\(([^)]+)\)"
    matches = re.findall(pattern, text)
    return [match.split(" ", 1)[0] for match in matches]


def trans_figure_to_png(fig_path: str) -> str:
    basename, ext = os.path.splitext(fig_path)
    save_path = basename + ".png"
    if os.path.isfile(save_path):
        return save_path
    if ext == ".pdf":
        page = fitz.open(fig_path).load_page(0)
        page.get_pixmap(dpi=300).save(save_path)
        return save_path
    if ext in (".eps", ".bmp"):
        Image.open(fig_path).save(save_path, "PNG")
        return save_path
    return fig_path


def get_root_file(file: LatexFile) -> LatexFile:
    """递归查找并返回LatexFile树中的根文件"""
    # 如果当前文件没有被其他文件包含，则它就是根文件
    if file.parent_file is None:
        return file
    # 否则递归查找其父文件的根
    return get_root_file(file.parent_file)
