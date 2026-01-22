<template>
    <div>
        <n-popover v-model:show="showPopover" trigger="click">
            <template #trigger>
                <n-button secondary type="primary" @click="showPopover = true">
                    + 添加文章
                </n-button>
            </template>
            <div style="padding: 5px; width: 300px; position: relative;">
                <div style="font-weight: bold; margin-bottom: 15px; font-size: 16px;">
                    {{ message }}
                </div>
                <div v-if="isSubmitting"
                    style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 10;">
                    <n-progress type="circle" :percentage="Number(progress.toFixed(1))" :height="50"
                        :stroke-width="8" />
                </div>
                <n-form label-placement="top" @submit.prevent="submitAddArticles" :disabled="isSubmitting"
                    :style="{ filter: isSubmitting ? 'grayscale(80%) opacity(0.1)' : 'none' }">
                    <n-form-item v-for="index in entryIds.length" :key="index" :label="`arxiv ID - ${index}`">
                        <n-input clearable v-model:value="entryIds[index - 1]" placeholder="请输入文章ID" />
                        <n-button ghost type="error" size="small" style="margin-left: 8px;"
                            @click="removeField(index - 1)" v-if="entryIds.length > 1">移除</n-button>
                    </n-form-item>
                    <div style="margin-bottom: 24px;">
                        <n-button text @click="addField" :disabled="entryIds.length >= 5 || isSubmitting">
                            + 添加项目
                        </n-button>
                    </div>
                    <n-divider />
                    <div style="margin: 24px 0;">
                        是否加入收藏：
                        <n-switch v-model:value="isStar" :disabled="isSubmitting">
                            <template #checked>是</template>
                            <template #unchecked>否</template>
                        </n-switch>
                    </div>

                    <n-grid :x-gap="12" :cols="2">
                        <n-grid-item>
                            <n-button block type="default" @click="showPopover = false">取消</n-button>
                        </n-grid-item>
                        <n-grid-item>
                            <n-button block type="primary" attr-type="submit" :disabled="isSubmitting">确认</n-button>
                        </n-grid-item>
                    </n-grid>
                </n-form>
            </div>
        </n-popover>
    </div>
</template>

<script setup lang="ts">
import type { StreamMessage, QueryResult } from '../interfaces';
import { ref } from 'vue'
import { useNotification } from 'naive-ui';
import {
    NPopover, NForm, NFormItem, NInput, NButton,
    NGrid, NGridItem, NSwitch, NDivider, NProgress
} from 'naive-ui'
import { addArticlesByEntryIds } from '../services/article';

const isSubmitting = ref(false) // 标识是否正在提交
const message = ref('添加文章')
const progress = ref(0)  // 处理进度

const showPopover = ref(false)
const entryIds = ref<string[]>([''])
const isStar = ref(true)

const addField = () => {
    if (entryIds.value.length < 5) entryIds.value.push('')
}
const removeField = (index: number) => {
    entryIds.value.splice(index, 1)
}

const notification = useNotification()
const submitAddArticles = async () => {
    isSubmitting.value = true
    showPopover.value = false
    const newEntryIds = entryIds.value.filter(id => id.trim().length > 0)
    if (newEntryIds.length === 0) {
        notification.create({
            title: '添加失败',
            content: '请至少输入一个有效的 arXiv 链接',
            type: 'error',
            duration: 3000,
        })
        isSubmitting.value = false
        return
    }
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
        }
    }
    const payload = {
        entry_ids: newEntryIds,
        star: isStar.value
    };

    await addArticlesByEntryIds(payload, onMessage);
    isSubmitting.value = false
    message.value = '添加文章'
}
</script>