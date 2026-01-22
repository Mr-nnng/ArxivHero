<template>
    <n-layout position="absolute" :native-scrollbar="false">
        <!-- 顶部搜索区域 -->
        <Header />
        <!-- 日历区域 -->
        <Calendar />
        <n-layout-footer bordered position="absolute" style="height: 64px; padding: 12px 24px;">
            <n-flex justify="center" align="center" style="height: 100%;">
                Arxiv Hero · Made with Vue3 + NaiveUI
            </n-flex>
        </n-layout-footer>
    </n-layout>
</template>

<script setup lang="ts">
import Header from '../components/Header.vue';
import Calendar from '../components/Calendar.vue';
import { NLayout, NLayoutFooter, NFlex } from 'naive-ui'
</script>
