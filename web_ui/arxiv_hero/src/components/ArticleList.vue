<template>
    <n-layout-content style="min-height: 100vh; padding: 64px 16px;">
        <n-flex vertical justify="center" align="center" :style="articles.length <= 0 ? 'min-height: 80vh;' : ''">
            <template v-if="articles.length">
                <n-notification-provider>
                    <ArticleCard v-for="article in articles" :key="article.entry_id" :article="article" />
                </n-notification-provider>
            </template>
            <div v-else>
                <n-flex vertical justify="center" align="center" v-if="isSubmitting">
                    <n-text type="info"
                        style="font-weight: bold; margin-bottom: 15px; font-size: 18px; text-align: center;">
                        {{ message }}
                    </n-text>
                    <n-progress type="circle" :percentage="Number(progress.toFixed(1))" :height="50"
                        :stroke-width="8" />
                </n-flex>
                <n-empty v-if="!isSubmitting" description="暂无文章">
                    <template #extra>
                        <n-button size="small" :disabled="isSubmitting" @click="submitAddArticles">
                            添加当天文章
                        </n-button>
                    </template>
                </n-empty>
            </div>
        </n-flex>
    </n-layout-content>

    <n-back-top />

    <n-layout-footer bordered position="absolute" style="height: 64px; padding: 12px 24px;">
        <n-flex justify="center" align="center" style="height: 100%;">
            <n-pagination show-size-picker :page="searchParamsRef.page" :page-size="searchParamsRef.page_size"
                :page-sizes="[5, 10, 20, 30]" :page-count="Math.ceil(total / searchParams.page_size)"
                @update:page="handlePageChange" @update:page-size="handlePageSizeChange" />
        </n-flex>
    </n-layout-footer>
</template>

<script setup lang="ts">
import type { StreamMessage, QueryResult } from '../interfaces';
import { ref, toRef, watch } from 'vue'
import { isValidSearchParams } from '../utils/checker'
import type { Article, SearchParams } from '../interfaces'
import ArticleCard from './ArticleCard.vue'
import {
    useNotification, NBackTop, NEmpty, NButton, NLayoutContent,
    NLayoutFooter, NFlex, NPagination, NNotificationProvider,
    NProgress, NText
} from 'naive-ui'
import { queryArticles, addArticlesByDate } from '../services/article';

const props = defineProps<{
    searchParams: SearchParams,
    fromCalendar: boolean,
}>()
var searchParamsRef = toRef(props, 'searchParams')

// 起缓存作用，当searchParams被清空时，不影响切换页面
const publishedRange = [props.searchParams.published_start, props.searchParams.published_end]

const notification = useNotification()
const articles = ref<Article[]>([])
const total = ref(0)

const fetchArticles = async (searchParams: SearchParams, reset_page = true) => {
    if (reset_page) searchParams.page = 1
    if (!isValidSearchParams(searchParams)) {
        notification.create({
            title: '查询失败',
            content: '请至少输入一个查询条件',
            type: 'error',
            duration: 3000,
        })
        return
    }
    try {
        const res = await queryArticles(searchParams)
        articles.value = res.articles
        total.value = res.total_nums
        console.log('共计', total.value, '篇文章', '，获取到', res.articles.length, '篇文章')
    } catch (error) {
        console.error('获取文章失败:', error)
    }
}

const handlePageChange = (newPage: number) => {
    searchParamsRef.value.published_start = publishedRange[0]
    searchParamsRef.value.published_end = publishedRange[1]
    searchParamsRef.value.page = newPage
    fetchArticles(searchParamsRef.value, false)
}

const handlePageSizeChange = (newPageSize: number) => {
    searchParamsRef.value.published_start = publishedRange[0]
    searchParamsRef.value.published_end = publishedRange[1]
    searchParamsRef.value.page_size = newPageSize
    fetchArticles(searchParamsRef.value, true)
}

// Header.vue 会更新 props.searchParams
watch(
    () => props.searchParams,
    (newParams) => {
        fetchArticles(newParams, true)
    },
    { immediate: true }
)

const message = ref('')
const progress = ref(0)  // 处理进度
const isSubmitting = ref(false)

const submitAddArticles = async () => {
    if (publishedRange[0] == null) {
        notification.create({
            title: '添加失败',
            content: '日期无效，请重试',
            type: 'error',
            duration: 3000,
        })
        return
    }
    isSubmitting.value = true

    notification.create({
        title: '添加文章中',
        content: '请稍候...',
        type: 'info',
        duration: 3000,
    })

    const onMessage = (msg: StreamMessage) => {
        if (msg.code != 200) {
            console.error("ERROR:", msg.msg);
            notification.create({
                title: '添加失败',
                content: '添加文章失败，请重试\n错误: ' + msg.msg,
                type: 'error',
                duration: 3000,
            })
            return
        }
        if (msg.msg != null) {
            message.value = msg.msg
        }
        if (msg.progress != null) {
            progress.value = msg.progress * 100;
        }
        if (msg.data != null) {
            const result = msg.data as QueryResult;
            notification.create({
                title: '添加成功',
                content: `成功添加 ${result.total_nums} 篇文章`,
                type: 'success',
                duration: 3000,
            })
            articles.value = result.articles
            total.value = result.total_nums
        }
    }

    await addArticlesByDate(publishedRange[0], onMessage);
    isSubmitting.value = false
    message.value = ''
}
</script>