import type { SearchParams } from "../interfaces";

export function isValidSearchParams(params: SearchParams): boolean {
    const {
        category,
        keywords,
        fields,
        published_start,
        published_end,
        is_star,
    } = params;

    // 任一条件不为空即为合法
    const hasCondition = (
        !!category ||
        !!keywords ||
        (fields && fields.length > 0) ||
        !!published_start ||
        !!published_end ||
        is_star !== undefined
    );

    return hasCondition;
}