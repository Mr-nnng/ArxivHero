<template>
    <n-layout-header bordered position="absolute" style="z-index: 1; padding: 14px 24px;">
        <!-- 返回主页按钮：绝对定位 -->
        <div v-if="showBackHome" style="position: absolute; left: 24px; top: 14px;">
            <n-button secondary type="primary" @click="backToHome">
                🡐 返回主页
            </n-button>
        </div>

        <n-grid :cols="3" :x-gap="12" :y-gap="0" item-responsive responsive="screen"
            style="display: flex; justify-content: center; align-items: center;">
            <n-grid-item span="3 s:2 m:1">
                <n-input-group>
                    <n-input v-model:value="searchStore.searchParams.keywords" placeholder="输入关键词搜索"
                        style="width: 400px;" clearable />
                    <n-button type="primary" @click="search">搜索</n-button>
                </n-input-group>
            </n-grid-item>
            <n-grid-item span="3 s:1 m:1" style="display: flex; justify-content: flex-start; padding-left: 12px;">
                <n-popover trigger="click" placement="bottom-start" :style="{ width: '320px' }" :show="showPopover"
                    @update:show="showPopover = $event">
                    <template #trigger>
                        <n-button secondary type="primary" tertiary @click="showPopover = true">
                            搜索设置
                        </n-button>
                    </template>
                    <div style="padding: 5px;">
                        <div style="font-weight: bold; margin-bottom: 15px; font-size: 16px;">搜索设置</div>
                        <n-form label-placement="top" @submit.prevent="search">
                            <n-form-item label="文章分类">
                                <n-select v-model:value="searchStore.searchParams.category"
                                    :options="[{ label: '全部', value: 'all' }].concat(searchStore.categoryOptions)"
                                    clearable placeholder="选择分类" />
                            </n-form-item>

                            <n-form-item label="是否为主分类">
                                <n-switch v-model:value="searchStore.searchParams.is_primary">
                                    <template #checked>主分类</template>
                                    <template #unchecked>非主分类</template>
                                </n-switch>
                            </n-form-item>

                            <n-form-item label="搜索关键词字段">
                                <n-select v-model:value="searchStore.searchParams.fields" multiple
                                    :options="searchStore.fieldOptions" placeholder="选择字段" clearable />
                            </n-form-item>

                            <n-form-item label="发布时间范围">
                                <n-date-picker v-model:value="searchStore.publishedRange" type="daterange" clearable
                                    style="width: 100%" placeholder="选择起止时间" />
                            </n-form-item>

                            <n-form-item label="是否收藏">
                                <n-select v-model:value="searchStore.isStarString" :options="[
                                    { label: '全部', value: 'all' },
                                    { label: '是', value: 'true' },
                                    { label: '否', value: 'false' }
                                ]" placeholder="是否收藏" />
                            </n-form-item>

                            <n-form-item label="排序字段">
                                <n-select v-model:value="searchStore.searchParams.sort_by"
                                    :options="searchStore.sortOptions" clearable placeholder="选择排序字段" />
                            </n-form-item>

                            <n-form-item label="正序/倒序">
                                <n-switch v-model:value="searchStore.searchParams.sort_asc">
                                    <template #checked>正序</template>
                                    <template #unchecked>倒序</template>
                                </n-switch>
                            </n-form-item>

                            <n-grid :x-gap="12" :cols="2">
                                <n-grid-item>
                                    <n-button block type="default" @click="clearSearch">清空</n-button>
                                </n-grid-item>
                                <n-grid-item>
                                    <n-button block type="primary" attr-type="submit">应用并搜索</n-button>
                                </n-grid-item>
                            </n-grid>

                        </n-form>
                    </div>
                </n-popover>
            </n-grid-item>
        </n-grid>

        <!-- 添加按钮：绝对定位在右侧 -->
        <div style="position: absolute; right: 24px; top: 14px;">
            <n-notification-provider>
                <AddArticle />
            </n-notification-provider>
        </div>
        <div style="position: absolute; right: 135px; top: 14px;">
            <n-notification-provider>
                <HistoryList />
            </n-notification-provider>
        </div>
    </n-layout-header>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AddArticle from './AddArticle.vue'
import HistoryList from './HistoryList.vue'
import { useSearchStore } from '../stores/useSearchStore'
import { getSearchOptions } from '../services/article';
import { buildSearchParams } from '../utils/tools';
import {
    NLayoutHeader, NInputGroup, NPopover, NInput, NGrid, NGridItem,
    NButton, NForm, NFormItem, NSelect, NSwitch, NDatePicker, NNotificationProvider
} from 'naive-ui'

defineProps({
    showBackHome: {
        type: Boolean,
        default: false
    }
})

const searchStore = useSearchStore()
const showPopover = ref(false);  // 控制搜索设置的显示与隐藏
const router = useRouter()

// 搜索操作
const search = () => {
    searchStore.searchParams = buildSearchParams(
        searchStore.searchParams,
        searchStore.publishedRange,
        searchStore.isStarString
    )
    console.log(searchStore.searchParams)
    showPopover.value = false
    searchStore.fromCalendar = false
    router.push('/articles') // 跳转到新页面
}

// 清空搜索
const clearSearch = () => {
    searchStore.clear()
}

// 加载搜索选项
const loadSearchOptions = async () => {
    try {
        const res = await getSearchOptions();
        searchStore.categoryOptions = res.categorys.map(cat => ({
            label: cat,
            value: cat
        }));
        searchStore.fieldOptions = res.query_fields.map(field => ({
            label: field.zh_field,
            value: field.field
        }));
        searchStore.sortOptions = res.sort_fields.map(field => ({
            label: field.zh_field,
            value: field.field
        }));
    } catch (e) {
        console.error('加载搜索选项失败:', e);
    }
};

// 返回主页
const backToHome = () => {
    router.push('/');
};

onMounted(() => {
    loadSearchOptions();
})
</script>

<style scoped></style>