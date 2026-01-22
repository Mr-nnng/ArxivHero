import type { StreamMessage, Paragraph } from '../interfaces'
import request from '../utils/request'
import { receiveStream } from '../utils/stream'


export const downloadSource = async (entry_id: string, onMessage: (msg: StreamMessage) => void) => {
    await receiveStream(`/content/source/${entry_id}`, onMessage, 'GET')
}

export const getParagraphs = async (entry_id: string): Promise<Paragraph[]> => {
    const res = await request.get<Paragraph[]>(`/content/${entry_id}`)
    return res.data
}

export const translateContent = async (entry_id: string, onMessage: (msg: StreamMessage) => void) => {
    await receiveStream(`/content/translate/${entry_id}`, onMessage, 'GET')
}