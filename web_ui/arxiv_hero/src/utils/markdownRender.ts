import type Token from 'markdown-it/lib/token.mjs';
import type Renderer from 'markdown-it/lib/renderer.mjs';
import MarkdownIt from 'markdown-it';
import mk from '@traptitech/markdown-it-katex';
import hljs from 'highlight.js';
import type { PluginWithOptions } from 'markdown-it';

const md = new MarkdownIt({
    html: true,
    linkify: true,
    typographer: true,
    highlight: (str: string, lang: string) => {
        if (lang && hljs.getLanguage(lang)) {
            try {
                return hljs.highlight(str, { language: lang }).value;
            } catch (__) { }
        }
        return '';
    }
});

md.use(mk as PluginWithOptions, {
    throwOnError: false,
    errorColor: '#cc0000',
    katexOptions: {
        strict: false, // 禁用严格模式，允许 Unicode 字符
    },
});

// 自定义引用渲染修复 (添加类型声明)
md.renderer.rules.link_open = (
    tokens: Token[],
    idx: number,
    options: any,
    env: any,
    self: Renderer
) => {
    const token = tokens[idx];

    // 确保 attrs 存在
    if (token.attrs) {
        const hrefIndex = token.attrIndex('href');

        if (hrefIndex >= 0) {
            const href = token.attrs[hrefIndex][1];
            // 处理 [[1]] 类型的引用
            if (typeof href === 'string' && href.startsWith('[') && href.endsWith(']')) {
                token.attrs[hrefIndex][1] = `#${href.slice(1, -1)}`;
            }
        }
    }
    env = env || {};

    return self.renderToken(tokens, idx, options);
};

export const renderMarkdown = (content: string): string => {
    return md.render(content);
};