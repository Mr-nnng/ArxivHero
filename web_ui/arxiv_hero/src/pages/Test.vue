<script setup lang="ts">
import { ref } from 'vue';
import MarkdownRender from '../components/MarkdownRender.vue';

const markdownContent = ref(`
# 完整的 Markdown 渲染解决方案

## LaTeX 公式支持

### 行内公式示例
数据集合表示为：$\\mathcal{D} = \\{r_1, \\dots, r_n\\}$，其中 $n$ 是样本数量。

### 块级公式示例
$$
\\tau_j =
\\begin{cases}
\\text{numerical} & \\text{if } c_j \\text{ contains quantitative values with high cardinality}, \\\\
\\text{temporal} & \\text{if } c_j \\text{ conforms to known date/time formats}, \\\\
\\text{categorical} & \\text{otherwise}.
\\end{cases}
$$


矩阵公式示例：
$$
A = \\begin{pmatrix}
a_{11} & a_{12} & \\cdots & a_{1n} \\\\
a_{21} & a_{22} & \\cdots & a_{2n} \\\\
\\vdots & \\vdots & \\ddots & \\vdots \\\\
a_{m1} & a_{m2} & \\cdots & a_{mn}
\\end{pmatrix}
$$

## 引用支持

如文献 [\\[1\\]][1] 所述，以及另一篇研究 [\\[2\\]][2] 提出的方法。

[1]: https://arxiv.org/abs/2001.00001 "重要参考文献"
[2]: https://arxiv.org/abs/2002.00002

## 代码块示例

\`\`\`typescript
interface User {
  id: number;
  name: string;
  email: string;
}

function getUser(id: number): Promise<User> {
  return fetch(\`/api/users/\${id}\`).then(res => res.json());
}
\`\`\`

\`\`\`latex
\\begin{verbatim}
{
  "steps": [
    "Filter data to include only Measures fields: 'deaths', 'New cases'",
    "Group data by WHO Region dimension",
    "Calculate sum of 'deaths' and 'New cases' for each WHO Region"
  ],
  "fields_used": ["deaths", "New cases", "WHO Region"],
  "description": "This analysis compares the total deaths and new cases for each WHO region."
}
\\end{verbatim}
\`\`\`

## 表格支持

| 特征类型       | 描述                          | 示例         |
|----------------|-------------------------------|--------------|
| Numerical      | 连续数值数据                  | 身高、体重   |
| Temporal       | 时间相关数据                  | 日期、时间戳 |
| Categorical    | 分类数据                      | 性别、国家   |

## 复杂公式组合

$$
f(x) = \\int_{-\\infty}^\\infty \\hat f(\\xi)\\,e^{2 \\pi i \\xi x} \\,d\\xi
$$

结合文本：当 $x = 0$ 时，函数值 $f(0) = \\frac{1}{2\\pi} \\int \\hat f(\\xi) d\\xi$。

## 图片支持

![示例图](http://127.0.0.1:4587/content/source/test/doa.eps)

`);

// 实际应用中可以从 API 获取内容
// const fetchContent = async () => {
//   const response = await fetch('/api/markdown-content');
//   markdownContent.value = await response.text();
// }
</script>

<template>
  <div class="container">
    <MarkdownRender :content="markdownContent" />
  </div>
</template>

<style scoped>
.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}
</style>