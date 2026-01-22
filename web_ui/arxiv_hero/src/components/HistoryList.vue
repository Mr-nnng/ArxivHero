<template>
    <div>
        <n-popover trigger="click">
            <template #trigger>
                <n-button secondary type="primary" @click="getHistoryList">
                    🕗 阅读记录
                </n-button>
            </template>
            <n-infinite-scroll style="max-height: 700px; padding: 0px; width: 550px; position: relative;"
                @load="addHistories">
                <n-table :single-line="false">
                    <thead>
                        <tr>
                            <th>标题</th>
                            <th style="width: 150px;">时间</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="item in historyList" :key="item.entry_id">
                            <td>
                                <n-a @click="handleRead(item.entry_id)" target="_blank">
                                    {{ item.title }}
                                </n-a>
                            </td>
                            <td>
                                <n-time :time="item.time_updated" />
                            </td>
                        </tr>
                    </tbody>
                </n-table>
                <br>
                <div v-if="loading" class="text">
                    加载中...
                </div>
                <div v-if="noMore" class="text">
                    没有更多了 🤪
                </div>
            </n-infinite-scroll>
        </n-popover>
    </div>
</template>

<script setup lang="ts">
import type { HistoryItem } from '../interfaces';
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NPopover, NButton, NTable, NA, NTime, NInfiniteScroll } from 'naive-ui';
import { getLastHistories } from '../services/history';

const historyList = ref<HistoryItem[]>([])
const loading = ref(false)
const noMore = ref(false)
const router = useRouter()

const getHistoryList = async () => {
    loading.value = true
    noMore.value = false
    const histories = await getLastHistories(0, 5)
    if (histories.length < 5) { noMore.value = true }
    historyList.value = histories
    loading.value = false
}

const addHistories = async () => {
    if (noMore.value) { return }
    loading.value = true
    noMore.value = false
    const histories = await getLastHistories(historyList.value.length, 5)
    if (histories.length < 5) { noMore.value = true }
    historyList.value.push(...histories)
    loading.value = false
}

const handleRead = (entry_id: string) => {
    router.push(`/article/${entry_id}`)
}

onMounted(() => {
    getHistoryList()
})
</script>

<style scoped>
.text {
    text-align: center;
}
</style>