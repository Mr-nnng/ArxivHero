import { defineStore } from 'pinia'
import type { SearchParams } from '../interfaces'

export const useSearchStore = defineStore('search', {
    state: () => ({
        searchParams: {
            is_primary: false,
            page: 1,
            page_size: 5
        } as SearchParams,
        publishedRange: null as [number, number] | null,
        isStarString: 'all' as 'all' | 'true' | 'false',
        showCalendar: true,
        fromCalendar: false,

        // 搜索选项
        categoryOptions: [] as { label: string; value: string }[],
        fieldOptions: [] as { label: string; value: string }[],
        sortOptions: [] as { label: string; value: string }[],
    }),
    actions: {
        clear() {
            this.searchParams = {
                is_primary: false,
                page: 1,
                page_size: 5
            }
            this.publishedRange = null
            this.isStarString = 'all'
        }
    },
    persist: true
})
