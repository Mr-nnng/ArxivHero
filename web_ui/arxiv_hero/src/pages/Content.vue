<template>
    <n-notification-provider>
        <ContentViewer :entryId="entryId" />
    </n-notification-provider>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { NNotificationProvider } from 'naive-ui'
import ContentViewer from '../components/ContentViewer.vue'

const route = useRoute()
const entryId = route.params.entryId as string

</script>