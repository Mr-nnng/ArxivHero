import type { SearchParams, RelativeStyle, Paragraph } from '../interfaces';
import dayjs from "dayjs";

export const toUTCDate = (d?: Date): Date | undefined => {
    if (!d) return undefined;
    return dayjs.utc()
        .year(d.getFullYear())
        .month(d.getMonth())       // 注意：JavaScript 中月份是从 0 开始的
        .date(d.getDate())
        .hour(d.getHours())
        .minute(d.getMinutes())
        .second(d.getSeconds())
        .millisecond(d.getMilliseconds())
        .toDate();
};

export const buildSearchParams = (
    searchParams: SearchParams,
    publishedRange: [number, number] | null,
    isStarString: 'all' | 'true' | 'false'
): SearchParams => {
    const start = publishedRange?.[0]
        ? (() => {
            const date = toUTCDate(new Date(publishedRange?.[0]));
            return date;
        })()
        : undefined;

    const end = publishedRange?.[1]
        ? (() => {
            const date = toUTCDate(new Date(publishedRange?.[1]));
            return date;
        })()
        : undefined;

    return {
        category: searchParams.category === 'all' ? undefined : (searchParams.category || undefined),
        is_primary: searchParams.is_primary,
        keywords: searchParams.keywords || undefined,
        fields: (searchParams.fields && searchParams.fields.length > 0) ? searchParams.fields : undefined,
        published_start: start,
        published_end: end,
        is_star: isStarString === 'all' ? undefined : isStarString === 'true',
        sort_by: searchParams.sort_by || undefined,
        sort_asc: searchParams.sort_asc || undefined,
        page: searchParams.page,
        page_size: searchParams.page_size,
    };
};

export const convertBboxToRelativePosition = (
    bbox: number[], // 四个元素，依次为：左上角 x；左上角 y；右下角 x；右下角 y
    page_size: number[], // 两个元素，依次为：宽度和高度
): RelativeStyle => {
    const [x0, y0, x1, y1] = bbox;
    const [width, height] = page_size;

    const box_width = x1 - x0;
    const box_height = y1 - y0;

    const left = x0 / width * 100;
    const top = y0 / height * 100;
    const widthPercent = box_width / width * 100;
    const heightPercent = box_height / height * 100;

    return {
        left_percent: `${left.toFixed(2)}%`,
        top_percent: `${top.toFixed(2)}%`,
        width_percent: `${widthPercent.toFixed(2)}%`,
        height_percent: `${heightPercent.toFixed(2)}%`,
    };
}

export const addPrefixToImageLinks = (input: string, prefix: string): string => {
    return input.replace(/!\[\]\(([^)]+)\)/g, (_match, path) => {
        return `![](${prefix}${path})`;
    });
}

export const postProcessParagraph = (paragraph: Paragraph, lang: string, figure_prefix?: string): string => {
    let text = (lang == "zh" ? (paragraph.zh_text || paragraph.text) : paragraph.text) || '';

    if (lang == "zh") {
        // 给 span 的 id 加 zh 前缀
        text = text.replace(/<span\s+([^>]*?)id="([^"]+)"([^>]*)>/g, (_match, preAttr, id, postAttr) => {
            return `<span ${preAttr}id="zh_${id}"${postAttr}>`;
        });

        // 给 a 的 href 中以 # 开头的引用加 zh 前缀
        text = text.replace(/<a\s+([^>]*?)href="#([^"]+)"([^>]*)>/g, (_match, preAttr, href, postAttr) => {
            return `<a ${preAttr}href="#zh_${href}"${postAttr}>`;
        });
    }
    if (paragraph.type == 'title') {
        text = '#'.repeat((paragraph.text_level || 4) + 1) + ' ' + text
    }
    else if (paragraph.type == 'figure') {
        text = addPrefixToImageLinks(text, figure_prefix || '')
    }
    else if (paragraph.type == 'article_name') {
        text = `# <center>${text}</center>`
    }
    else if (paragraph.type == 'abstract') {
        text = (lang == "zh" ? "**摘要**: " : "**Abstract**: ") + text
    }
    return text
}

export const replaceMarkdownText = (text: string): string => {
    // 替换反斜杠（注意：正则中的反斜杠需要双重转义）
    // var text = text.replace(/\\/g, '\\\\');
    // 替换 ```（使用字符串字面量）
    // var text = text.replace(/```/g, '\\`\\`\\`');
    return text
        .replace(/\u2013/g, '-') // 替换 en dash
        .replace(/\u2014/g, '-') // 替换 em dash（—）也可以顺便处理
}