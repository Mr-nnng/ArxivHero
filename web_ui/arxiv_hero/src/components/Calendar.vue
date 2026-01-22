<template>
    <n-layout-content style="margin: 130px 170px 50px 170px;">
        <n-calendar v-model:value="currentDay" @panel-change="updatePanel" @update:value="updateDate">
            <template #default="{ year, month, date }">
                <div>
                    <n-text :type="articleCountMap[formatDate(year, month, date)] ? 'primary' : 'default'">
                        {{ year }} / {{ String(month).padStart(2, '0') }} / {{ String(date).padStart(2, '0') }}
                    </n-text>
                    <n-flex justify="center" v-if="articleCountMap[formatDate(year, month, date)]"
                        style="text-align: center;">
                        <n-text type="primary" style="font-size: x-large; margin-top: 5px; font-weight: bold;">
                            {{ articleCountMap[formatDate(year, month, date)] }}
                        </n-text>
                    </n-flex>
                </div>
            </template>
        </n-calendar>
    </n-layout-content>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import { useSearchStore } from '../stores/useSearchStore'
import { getArticleCounts } from '../services/article';
import { buildSearchParams } from '../utils/tools';
import { NLayoutContent, NFlex, NCalendar, NText } from 'naive-ui'

dayjs.extend(utc)
dayjs.extend(timezone)

const router = useRouter()
const searchStore = useSearchStore()
const currentDay = ref(dayjs().utc().valueOf()) // 返回 number 类型的时间戳

// 记录每日文章数（key为日期字符串：YYYY-MM-DD）
const articleCountMap = ref<Record<string, number>>({})

// 日期格式化为 YYYY-MM-DD
const formatDate = (year: number, month: number, date: number) => {
    return `${year}-${String(month).padStart(2, '0')}-${String(date).padStart(2, '0')}`
}

// 加载当前月份的文章数据
const loadArticleCounts = async (date: Date) => {
    try {
        articleCountMap.value = await getArticleCounts(date)
    } catch (e) {
        console.error('加载文章数据失败:', e)
    }
}


const updatePanel = (info: { year: number; month: number }) => {
    // 根据 year 和 month 加载相关数据
    const date = dayjs().year(info.year).month(info.month - 1).toDate() // month 是从 1 开始的，调整为 0 基索引
    loadArticleCounts(date)
}

const updateDate = (_: number, { year, month, date }: { year: number, month: number, date: number }) => {
    const startOfDay = dayjs().year(year).month(month - 1).date(date).startOf('day');
    const startOfNextDay = startOfDay.add(1, 'day');

    searchStore.publishedRange = [startOfDay.valueOf(), startOfNextDay.valueOf()];
    searchStore.searchParams = buildSearchParams(
        searchStore.searchParams,
        searchStore.publishedRange,
        searchStore.isStarString
    );
    searchStore.fromCalendar = true;
    router.push('/articles')
};

// 初始加载
onMounted(() => {
    loadArticleCounts(dayjs(currentDay.value).utc().toDate())
})

</script>

<style scoped></style>