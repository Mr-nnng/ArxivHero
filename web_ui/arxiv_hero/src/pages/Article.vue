<template>
    <n-layout position="absolute" :native-scrollbar="false">
        <Header :show-back-home="true" />
        <n-notification-provider>
            <ArticleList :search-params="searchStore.searchParams" :from-calendar="searchStore.fromCalendar" />
        </n-notification-provider>
    </n-layout>
</template>

<script setup lang="ts">
import Header from '../components/Header.vue'
import ArticleList from '../components/ArticleList.vue'
import { useSearchStore } from '../stores/useSearchStore'
import { NLayout, NNotificationProvider } from 'naive-ui'
const searchStore = useSearchStore()
</script>