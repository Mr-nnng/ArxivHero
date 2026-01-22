import type { HistoryItem } from '../interfaces'
import qs from 'qs';
import request from '../utils/request'

export const getHistory = async (entry_id: string): Promise<HistoryItem> => {
    const res = await request.get<HistoryItem>(`/history/${entry_id}`);
    return {
        ...res.data,
        time_updated: new Date(res.data.time_updated)
    };
};


export const getLastHistories = async (start: number, nums: number): Promise<HistoryItem[]> => {
    const res = await request.get<HistoryItem[]>(`/history`, {
        params: {
            start,
            nums
        },
        paramsSerializer: params => {
            return qs.stringify(params, { arrayFormat: 'repeat' })
        }
    })
    // 手动转换时间字段
    return res.data.map(item => ({
        ...item,
        time_updated: new Date(item.time_updated)
    }))
}

export const addOrUpdateHistory = async (entry_id: string, progress: number): Promise<boolean> => {
    const res = await request.post(`/history/${entry_id}`, { "progress": progress })
    return res.data
}

export const deleteHistory = async (entry_id: string): Promise<boolean> => {
    const res = await request.delete(`/history/${entry_id}`)
    return res.data
}