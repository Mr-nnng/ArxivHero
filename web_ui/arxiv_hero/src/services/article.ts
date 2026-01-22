import type { SearchOptions, SearchParams, QueryResult, StreamMessage } from '../interfaces'
import qs from 'qs';
import dayjs from 'dayjs'
import request from '../utils/request'
import { receiveStream } from '../utils/stream'

export const getSearchOptions = async (): Promise<SearchOptions> => {
    const res = await request.get<SearchOptions>('/articles/query/option');
    return res.data
}

export const getArticleCounts = async (date: Date): Promise<Record<string, number>> => {
    const isoDate = dayjs(date).utc().toISOString()

    const res = await request.get('/articles/count', {
        params: { date: isoDate }
    })
    const map: Record<string, number> = {}
    for (const item of res.data) {
        const dateStr = dayjs(item.date).format('YYYY-MM-DD') // 接口返回的是 UTC 时间
        map[dateStr] = item.count
    }
    return map
}

export const queryArticles = async (searchParams: SearchParams): Promise<QueryResult> => {
    const res = await request.get('/articles/query', {
        params: {
            ...searchParams,
        },
        paramsSerializer: params => {
            return qs.stringify(params, { arrayFormat: 'repeat' })
        }
    })
    return res.data
}

export const addArticlesByEntryIds = async (payload: { entry_ids: string[], star: boolean }, onMessage: (msg: StreamMessage) => void) => {
    await receiveStream('/articles/create', onMessage, 'POST', payload)
}

export const addArticlesByDate = async (date: Date, onMessage: (msg: StreamMessage) => void) => {
    const isoDate = dayjs(date).utc().toISOString()
    await receiveStream('/articles/create', onMessage, 'POST', { date: isoDate })
}