content_system_prompt = r"""\
请帮我翻译为中文

规则：
- 保证内容的原意的基础上，使其更易于理解，更符合中文的表达习惯
- 以markdown友好的格式输出，行内latex公式保留前后的`$`符号
- 在确保能正确渲染的基础上，尽可能保留原文的格式，如引用、html标签、代码块等

输入格式如下，"｛xxx｝"表示占位符：
<English>
｛原文｝
</English>

输出格式如下：
<Chinese>
｛翻译｝
</Chinese>

下面是示例：
<English>
For LLM decision-making problems [[1]], an LLM with profile $\widehat{p}$ receives a partially observable state $\widehat{o}_t$ and generates actions according to $\widehat{a}t = LLM{\widehat{p}}(\widehat{o}_t)$, where each input and output is represented as a sequence of tokens in text form. Given that chain-of-thought (CoT) reasoning [[3], [4]] will be frequently used in the following sections, we define the CoT output as:
</English>

<Chinese>
针对大语言模型（LLM）的决策问题[[1]]，一个具有参数配置$\widehat{p}$的LLM接收部分可观测状态$\widehat{o}_t$ ，并依据$\widehat{a}t = LLM{\widehat{p}}(\widehat{o}_t)$生成动作，其中每个输入输出均以文本形式的token序列表示。鉴于思维链（CoT）推理[[3], [4]]将在后续章节频繁使用，我们将思维链输出定义为：
</Chinese>

<English>
This section introduces the SIM-RAG framework, outlining its design in Section <a href="#sec:sim-rag-main">Section 3.1</a>. The overview of the SIM-RAG framework is illustrated in Figure <a href="#fig:overview">2</a>, following the information flow during the inference-time thinking process.
</English>

<Chinese>
本节将介绍SIM-RAG框架，其具体设计详见<a href="#sec:sim-rag-main">Section 3.1</a>。SIM-RAG框架的总体架构如图<a href="#fig:overview">2</a>所示，该图遵循了推理时思维过程中的信息流动方向。
</Chinese>
"""

title_system_prompt = """\
请帮我将论文标题翻译为中文

输入格式如下，"｛xxx｝"表示占位符：
<English>
｛原文｝
</English>

输出格式如下:
<Chinese>
｛翻译｝
</Chinese>

下面是示例：
<English>
Adaptive Layer-skipping in Pre-trained LLMs
</English>

<Chinese>
预训练大型语言模型中的自适应跳层机制
</Chinese>

<English>
Abstract
</English>

<Chinese>
摘要
</Chinese>

<English>
1. Introduction
</English>

<Chinese>
1. 简介
</Chinese>

<English>
2. Methods
</English>

<Chinese>
2. 方法
</Chinese>"""

markdown_systen_prompt = r"""\
将下面的内容翻译为中文

规则：
- 保证内容的原意的基础上，使其更易于理解，更符合中文的表达习惯
- 以markdown友好的格式输出，确保前端能够正常渲染

输入格式如下，"｛xxx｝"表示占位符：
<English>
｛原文｝
</English>

输出格式如下：
<Chinese>
｛翻译｝
</Chinese>

下面是示例：
<English>
<span id="CDM" class="label"></span>
![](CDM.eps)
**Figure 1**: Illustrative examples of (a) answer records of Yasser and Lisa: "?" denotes unanswered; (b) relation between exercises and knowledge concepts: gray denotes inactive; (c) interaction among knowledge concepts; (d) cognitive states.
</English>

<Chinese>
<span id="CDM" class="label"></span>
![](CDM.eps)
**图1**：示例说明：(a) Yasser和Lisa的答题记录："?"表示未作答；(b) 习题与知识点关联：灰色表示未激活；(c) 知识点间的相互作用；(d) 认知状态。
</Chinese>

<English>
</English>
```latex
\begin{algorithm}[htbp] \label{BubbleSortAlgorithm} 
	\caption{Bubble Sort Algorithm} 
	\LinesNumbered
	\KwIn{$\mathbf{A}$: An array of $n$ elements $[a_1, a_2, \ldots, a_n]$}
	\KwOut{$\mathbf{A}$: The sorted array in ascending order}
	
	$n$ $\leftarrow$ length of $\mathbf{A}$; \\
	$swapped$ $\leftarrow$ $\text{false}$; \\
	
	\Repeat{$swapped = \text{false}$}{
		$swapped$ $\leftarrow$ $\text{false}$; \\
		\For{$i$ $\leftarrow$ $1$ to $n-1$}{
			\If{$a_i > a_{i+1}$}{
				Swap $a_i$ and $a_{i+1}$; \\
				$swapped$ $\leftarrow$ $\text{true}$; \\
			}
		}
		$n$ $\leftarrow$ $n - 1$; \tcp*{The largest element is now in its final position}
	}
	Return $\mathbf{A}$;
\end{algorithm}
```
<Chinese>
**算法**: 冒泡排序

---

**输入**:
$\mathbf{A}$: 包含 $n$ 个元素的数组 $[a_1, a_2, \ldots, a_n]$

**输出**:
$\mathbf{A}$: 按升序排列的数组

1. $n \leftarrow \mathbf{A}$ 的长度;
2. $swapped \leftarrow \text{false}$;

重复执行以下步骤，直到 $swapped = \text{false}$：
   1. $swapped \leftarrow \text{false}$; 
   2. **对于** $i$ 从 $1$ 到 $n-1$：
      - **如果** $a_i > a_{i+1}$：
         - 交换 $a_i$ 和 $a_{i+1}$;
         - $swapped \leftarrow \text{true}$;
   3. $n \leftarrow n - 1$;（*此时最大元素已位于最终位置*）

**返回** $\mathbf{A}$; 

---
</Chinese>
"""

user_template = """\
<English>
{content}
</English>"""

assistant_template = """\
<Chinese>
{zh_content}
</Chinese>"""
