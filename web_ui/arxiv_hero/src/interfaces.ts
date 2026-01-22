export interface Link {
    href: string;
    title?: string;
    rel?: string;
    content_type?: string;
}

export interface Author {
    name: string;
}

export interface Article {
    entry_id: string;
    updated: Date;
    published: Date;
    title: string;
    authors: Author[];
    summary: string;
    comment?: string;
    journal_ref?: string;
    doi?: string;
    primary_category: string;
    categories: string[];
    links: Link[];
    pdf_url: string;
    zh_title?: string;
    zh_summary?: string;
    is_star: boolean;
}

export interface SearchParams {
    category?: string;
    is_primary: boolean;
    keywords?: string;
    fields?: string[];
    published_start?: Date;
    published_end?: Date;
    is_star?: boolean;
    sort_by?: string;
    sort_asc?: boolean;
    page: number;
    page_size: number;
}

export interface Field {
    field: string;
    zh_field: string; // 字段的中文名称
}
export interface SearchOptions {
    categorys: string[];
    query_fields: Field[];
    sort_fields: Field[];
}

export interface StreamMessage {
    code: 200 | 400 | 500;
    msg?: string;
    data?: any; // 可以是字典或任意类型
    progress?: number;
}

export type QueryResult = {
    articles: Article[];
    total_nums: number;
}


// content
export interface RelativeStyle {
    left_percent: string;
    top_percent: string;
    width_percent: string;
    height_percent: string;
}

export interface Paragraph {
    type: string;
    order_idx?: number;
    text?: string;
    zh_text?: string;
    text_level?: number;
}

export interface DownloadMessage {
    message?: string;
    pdf_path?: string;
    source_dir?: string;
}

// history
export interface HistoryItem {
    entry_id: string;
    title: string;
    progress: number;
    time_updated: Date;
}