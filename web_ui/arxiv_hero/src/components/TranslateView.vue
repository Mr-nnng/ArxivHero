<template>
    <n-progress v-if="progress < 1" type="line" :show-indicator="false" status="success" :percentage="progress * 100"
        :height=2 />
    <MarkdownRender :content="markdownText" />
</template>

<script setup lang="ts">
import type { StreamMessage, Paragraph } from "../interfaces";
import { ref, onMounted } from 'vue'
import { useNotification, NProgress } from 'naive-ui'
import { postProcessParagraph, replaceMarkdownText } from "../utils/tools";
import { translateContent } from "../services/content";
import MarkdownRender from './MarkdownRender.vue';


const { entryId } = defineProps({
    entryId: {
        type: String,
        required: true
    }
})

const baseUrl = import.meta.env.VITE_API_BASE_URL


const markdownText = ref('')

const isTranslating = ref(false)
const message = ref('')
const progress = ref(0)  // 翻译进度

const notification = useNotification()
const translate = () => {
    isTranslating.value = true
    const startTime = Date.now();
    const onMessage = (msg: StreamMessage) => {
        if (msg.code != 200) {
            console.error("ERROR:", msg.msg);
            notification.create({
                title: '翻译失败',
                content: '翻译文章失败，请重试\n错误: ' + msg.msg,
                type: 'error',
                duration: 3000,
            })
            return
        }
        if (msg.msg != null) {
            if (msg.msg == "[DONE]") {
                if (Date.now() - startTime > 2000) {
                    notification.create({
                        title: '翻译完成',
                        content: '成功翻译文章',
                        type: 'success',
                        duration: 3000,
                    })
                }
                return
            }
            message.value = msg.msg
        }
        if (msg.progress != null) {
            progress.value = msg.progress;
        }
        if (msg.data != null) {
            const chunk = msg.data as Paragraph;
            const figure_prefix = baseUrl + "/content/source/" + entryId + "/"
            const text = postProcessParagraph(chunk, "zh", figure_prefix)
            markdownText.value += replaceMarkdownText(text) + "\n\n";
        }
    }
    translateContent(entryId, onMessage)
    isTranslating.value = false
}

onMounted(() => {
    translate()
})
</script>

<style></style>
