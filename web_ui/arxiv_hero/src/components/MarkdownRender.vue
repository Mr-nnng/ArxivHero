<template>
    <div class="markdown-body">
        <div v-html="htmlContent"></div>
    </div>
</template>

<script setup lang="ts">
import { ref, watchEffect, onMounted } from 'vue';
import { renderMarkdown } from '../utils/markdownRender';

interface Props {
    content: string;
}

const props = defineProps<Props>();

const htmlContent = ref('');

// 声明全局 KaTeX 渲染函数
declare global {
    interface Window {
        renderMathInElement?: (element: HTMLElement, options?: any) => void;
    }
}

const renderMath = () => {
    if (window.renderMathInElement) {
        const container = document.querySelector('.markdown-body');
        if (container) {
            // 添加类型断言解决 HTMLElement 类型问题
            window.renderMathInElement(container as HTMLElement, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '$', right: '$', display: false },
                    { left: '\\(', right: '\\)', display: false },
                    { left: '\\[', right: '\\]', display: true }
                ],
                throwOnError: false
            });
        }
    }
};

onMounted(() => {
    // 先加载 katex 主库
    const katexScript = document.createElement('script');
    katexScript.src = '/lib/katex/katex.min.js';
    katexScript.integrity = 'sha384-cMkvdD8LoxVzGF/RPUKAcvmm49FQ0oxwDF3BGKtDXcEc+T1b2N+teh/OJfpU0jr6';
    katexScript.crossOrigin = 'anonymous';
    katexScript.onload = () => {
        // 再加载 auto-render 插件
        const renderScript = document.createElement('script');
        renderScript.src = '/lib/katex/auto-render.min.js';
        renderScript.integrity = 'sha384-+VBxd3r6XgURycqtZ117nYw44OOcIax56Z4dCRWbxyPt0Koah1uHoK0o4+/RRE05';
        renderScript.crossOrigin = 'anonymous';
        renderScript.onload = renderMath;
        document.head.appendChild(renderScript);
    };
    document.head.appendChild(katexScript);
});

watchEffect(() => {
    htmlContent.value = renderMarkdown(props.content);

    // 延迟渲染确保 DOM 更新完成
    setTimeout(renderMath, 100);
});
</script>


<style scoped>
/* 基础样式 */
.markdown-body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #cecac3;
    max-width: 100%;
    overflow: auto;
    padding: 16px;
    border: 1px solid #363b41;
    background-color: #2c3032;
}
</style>

<style>
/* 全局 Markdown 样式 */
@import 'github-markdown-css/github-markdown.css';
@import 'katex/dist/katex.min.css';

/* LaTeX 公式增强 */
.katex {
    font-size: 1.1em !important;
    padding: 0.2em 0;
}

.katex-display {
    margin: 1em 0;
    overflow: auto hidden;
}

/* 引用链接样式 */
.markdown-body a[href^="#"] {
    color: #0969da;
    padding: 0 4px;
    margin: 0 2px;
    background-color: rgba(9, 105, 218, 0.1);
    border-radius: 4px;
    text-decoration: none;
    font-weight: 500;
}

.markdown-body a[href^="#"]:hover {
    background-color: rgba(9, 105, 218, 0.2);
    text-decoration: underline;
}

/* 代码块增强 */
.markdown-body pre {
    border-radius: 8px;
    padding: 16px;
    overflow: auto;
    background: #242424 !important;
    border: 1px solid #e1e4e8;
    margin: 1em 0;
}

/* 表格样式 */
.markdown-body table {
    display: table;
    width: 100%;
    border-collapse: collapse;
    margin: 1.5em 0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.markdown-body th {
    background-color: #242424;
    font-weight: 600;
}

.markdown-body td,
.markdown-body th {
    padding: 0.75em 1em;
    border: 1px solid #dfe2e5;
}

/* 数学块特殊处理 */
[data-math] {
    overflow-x: auto;
    overflow-y: hidden;
}

/* 响应式调整 */
@media (max-width: 768px) {
    .markdown-body {
        font-size: 15px;
    }

    .katex {
        font-size: 1em !important;
    }
}
</style>