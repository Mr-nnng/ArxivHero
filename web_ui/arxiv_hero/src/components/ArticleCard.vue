<template>
    <n-space item-style="padding: 4px">
        <n-grid :cols="2" :x-gap="8" align="stretch">
            <n-gi style="height: 100%">
                <n-card :title="article.title" class="article-card" style="height: 100%">
                    <template #header-extra>
                        <n-tag v-if="article.primary_category" type="info">
                            {{ article.primary_category }}
                        </n-tag>
                    </template>

                    {{ formatAuthors(article.authors) }}
                    <br /><br />
                    {{ article.summary }}

                    <template #footer>
                        发布日期：{{ formattedDate(article.published) }}
                        <br />
                        下载地址:
                        <n-a :href="article.links[0].href" target="_blank">
                            {{ article.links[0].href }}
                        </n-a>
                    </template>
                </n-card>
            </n-gi>

            <n-gi style="height: 100%">
                <n-card :title="article.zh_title" class="article-card" style="height: 100%">
                    <template #header-extra>
                        <n-rate clearable :count="1" :default-value="article.is_star ? 1 : 0"
                            @update:value="handleStarChange" />
                        &nbsp; &nbsp;
                        <n-tag v-if="article.primary_category" type="info">
                            {{ article.primary_category }}
                        </n-tag>
                    </template>

                    {{ formatAuthors(article.authors) }}
                    <br /><br />
                    {{ article.zh_summary }}
                    <template #footer>
                        <div
                            style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                            <div>
                                发布日期：{{ formattedDate(article.published) }}
                                <br />
                                下载地址:
                                <n-a :href="article.links[0].href" target="_blank">
                                    {{ article.links[0].href }}
                                </n-a>
                            </div>
                            <div style="margin-top: 10px; margin-right: 20px;">
                                <n-button secondary type="primary" @click="handleRead(article.entry_id)">
                                    开始阅读
                                </n-button>
                            </div>
                        </div>
                    </template>
                </n-card>
            </n-gi>
        </n-grid>
    </n-space>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { useRouter } from 'vue-router'
import request from '../utils/request';
import type { Article, Author } from '../interfaces';
import { useNotification, NSpace, NCard, NButton, NRate, NTag, NGrid, NGi, NA } from 'naive-ui'


const { article } = defineProps<{ article: Article }>();
const router = useRouter()
const notification = useNotification()

const formatAuthors = (authors: Author[]) => {
    return authors.map((author) => author.name)?.join(', ') || 'N/A';
};

const formattedDate = (date: Date) => dayjs(date).format('YYYY-MM-DD');

const handleStarChange = async (value: number) => {
    const star = value === 1
    try {
        await request.put('/articles/star', null, {
            params: {
                entry_id: article.entry_id,
                star: star
            }
        })
        article.is_star = star;
        notification.create({
            title: '更新收藏状态',
            content: star ? '收藏成功' : '取消收藏成功',
            duration: 1500,
            type: 'info'
        })

    } catch (error) {
        console.error('更新收藏状态失败: ', error)
    }
}

const handleRead = (entry_id: string) => {
    router.push(`/article/${entry_id}`)
}
</script>