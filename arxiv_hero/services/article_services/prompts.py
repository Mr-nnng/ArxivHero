abstract_system_prompt = r"""\
请帮我翻译为中文

规则：
- 保证内容的原意的基础上，使其更易于理解，更符合中文的表达习惯
- 翻译专业术语时，第一次出现时要在括号里面写上英文原文

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
Various layer-skipping methods have been proposed to accelerate token generation in large language models (LLMs). However, they have overlooked a fundamental question: How do computational demands vary across the generation of different tokens? In this work, we introduce FlexiDepth, a method that dynamically adjusts the number of Transformer layers used in text generation. By incorporating a plug-in router and adapter, FlexiDepth enables adaptive layer-skipping in LLMs without modifying their original parameters. Introducing FlexiDepth to Llama-3-8B model achieves layer skipping of 8 layers out of 32, and meanwhile maintains the full 100\% benchmark performance. Experimental results with FlexiDepth demonstrate that computational demands in LLMs significantly vary based on token type. Specifically, generating repetitive tokens or fixed phrases requires fewer layers, whereas producing tokens involving computation or high uncertainty requires more layers. Interestingly, this adaptive allocation pattern aligns with human intuition. To advance research in this area, we open sourced FlexiDepth and a dataset documenting FlexiDepth's layer allocation patterns for future exploration.
</English>

<Chinese>
为了加速大型语言模型（Large Language Models, LLMs）在生成文本时的处理速度，已有多种跳层（layer-skipping）方法被提出。然而，这些方法忽略了一个根本性的问题：在生成不同的词元（tokens）时，计算需求是否存在差异？本研究提出了一种名为 FlexiDepth 的方法，该方法能够在文本生成过程中动态调整所使用的 Transformer 层数。通过引入可插拔的路由器（router）和适配器（adapter），FlexiDepth 实现了在不修改 LLM 原始参数的前提下进行自适应跳层。将 FlexiDepth 应用于 Llama-3-8B 模型时，可在总共 32 层中跳过 8 层，同时保持基准测试性能的 100%。实验结果表明，LLMs 在生成不同类型的词元时，其计算需求存在显著差异。具体而言，生成重复词元或固定短语所需的层数较少，而生成涉及复杂计算或高度不确定性的词元则需要更多层。值得注意的是，这种自适应资源分配模式与人类的直觉高度一致。为促进该领域的进一步研究，我们开源了 FlexiDepth 方法以及记录其跳层分配模式的数据集，供未来探索使用。
</Chinese>"""

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
</Chinese>"""

user_template = """\
<English> 
{content}
</English>"""
