<template>
    <div>
        <n-button v-if="showButton" strong type="primary"
            style="position: fixed; top: 10px; left: 20px; min-width: 101px; z-index: 10;" @click="goBack">
            🡐 返回
        </n-button>
        <n-button v-if="showButton && isDownloaded" strong
            style="position: fixed; top: 10px; left: 140px; min-width: 126px; z-index: 10;" type="primary"
            @click="showMarkdown = !showMarkdown; showPdf = !showPdf">
            {{ showMarkdown ? "显示PDF" : "显示Markdown" }}
        </n-button>
    </div>

    <n-grid :cols="2" x-gap="10" style="width: max-content;">
        <!-- 原内容 -->
        <n-grid-item>
            <n-scrollbar trigger="hover" style="height: 100vh;">
                <n-back-top :right="width + 60" />
                <n-progress v-if="progress < 1" type="line" :show-indicator="false" status="success"
                    :percentage="progress * 100" :height=2 />
                <div v-if="isDownloaded || showPdf">
                    <div v-if="isDownloaded && showMarkdown" :style="{ maxWidth: width + 'px' }">
                        <MarkdownRender :content="markdownText" />
                    </div>
                    <VuePdfEmbed v-if="showPdf" annotation-layer text-layer :source="pdfSource" :width="width"
                        :scale="1.5" />
                </div>
                <n-card v-else style="height: 99.5vh;" :style="{ maxWidth: width + 'px' }">
                    <n-skeleton text :repeat="6" />
                    <n-divider />
                    <n-skeleton text :repeat="6" />
                </n-card>

            </n-scrollbar>
        </n-grid-item>

        <!-- 翻译后内容 -->
        <n-grid-item>
            <n-scrollbar trigger="hover" style="height: 100vh;">
                <n-back-top :right="55" />
                <div v-if="isDownloaded" :style="{ maxWidth: width + 'px' }">
                    <TranslateView :entry-id="entryId" />
                </div>
                <n-card v-else style="height: 99.5vh;" :style="{ maxWidth: width + 'px' }">
                    <n-skeleton text :repeat="6" :width="width" />
                    <n-divider />
                    <n-skeleton text :repeat="6" :width="width" />
                </n-card>
            </n-scrollbar>
        </n-grid-item>
    </n-grid>
</template>

<script setup lang="ts">
import type { Paragraph, StreamMessage, DownloadMessage } from '../interfaces';
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import VuePdfEmbed from 'vue-pdf-embed'
import { useNotification } from 'naive-ui'
import { NButton, NGrid, NGridItem, NScrollbar, NProgress, NCard, NSkeleton, NDivider, NBackTop } from 'naive-ui'
import { postProcessParagraph, replaceMarkdownText } from "../utils/tools";
import { downloadSource, getParagraphs } from '../services/content';
import { addOrUpdateHistory } from '../services/history';
import MarkdownRender from './MarkdownRender.vue';
import TranslateView from './TranslateView.vue'


// 引入 pdf 样式
import 'vue-pdf-embed/dist/styles/annotationLayer.css'
import 'vue-pdf-embed/dist/styles/textLayer.css'

const { entryId } = defineProps({
    entryId: {
        type: String,
        required: true
    }
})

const baseUrl = import.meta.env.VITE_API_BASE_URL

const width = (window.innerWidth * 0.985) / 2

const showMarkdown = ref(false)
const showPdf = ref(false)
const showButton = ref(false)
const isDownloaded = ref(false)
const pdfSource = ref('')
const progress = ref(0) // 下载进度
const message = ref('')
const markdownText = ref('')

const notification = useNotification()
const startDownload = () => {
    const downloadStartTime = Date.now();
    const onMessage = (msg: StreamMessage) => {
        if (msg.code != 200) {
            console.error("ERROR:", msg.msg);
            notification.create({
                title: '下载失败',
                content: '下载资源失败，请重试\n错误: ' + msg.msg,
                type: 'error',
                duration: 3000,
            })
        }
        if (msg.msg != null) {
            if (msg.msg == "[DONE]") {
                if (Date.now() - downloadStartTime > 2000) {
                    notification.create({
                        title: '下载完成',
                        content: '下载资源完成',
                        type: 'success',
                        duration: 3000,
                    })
                }
            }
            else {
                message.value = msg.msg
            }
        }
        if (msg.progress != null) {
            progress.value = msg.progress;
        }
        if (msg.data != null) {
            const chunk = msg.data as DownloadMessage;
            if (chunk.pdf_path != null) {
                pdfSource.value = `${baseUrl}/content/pdf/${entryId}.pdf`
                showPdf.value = true
            }
            if (chunk.message != null && chunk.message == "success") {
                progress.value = 1
                isDownloaded.value = true
            }
        }
    }
    downloadSource(entryId, onMessage)
}

const getMarkdownContent = async () => {
    if (markdownText.value.length > 0) {
        return
    }
    if (!showMarkdown.value) {
        notification.create({
            title: "正在下载资源",
            content: "正在下载资源，请稍候...",
            type: "info",
            duration: 3000,
        })
        return
    }
    try {
        const paragraphs = await getParagraphs(entryId);
        if (paragraphs.length == 0) {
            notification.create({
                title: "获取原文失败",
                content: "获取原文失败，请重试",
                type: "error",
                duration: 3000,
            })
            return
        }
        const figure_prefix = baseUrl + "/content/source/" + entryId + "/";
        paragraphs.forEach((paragraph: Paragraph) => {
            const text = postProcessParagraph(paragraph, "en", figure_prefix);
            markdownText.value += replaceMarkdownText(text) + "\n\n";
        })
    }
    catch (error) {
        console.error("获取原文失败:", error);
        notification.create({
            title: "获取原文失败",
            content: "获取原文失败，请重试\n错误: " + error,
            type: "error",
            duration: 3000,
        })
    }
}

function onMouseMove(event: MouseEvent) {
    const y = event.clientY // 鼠标相对于视口顶部的Y坐标
    const viewportHeight = window.innerHeight
    showButton.value = y <= viewportHeight / 5
}

const router = useRouter()

const goBack = () => {
    router.back()
}

watch(showMarkdown, () => {
    if (showMarkdown.value) {
        getMarkdownContent()
    }
})


onBeforeUnmount(() => {
    window.removeEventListener('mousemove', onMouseMove)
})

onMounted(() => {
    addOrUpdateHistory(entryId, 0)
    startDownload()
    window.addEventListener('mousemove', onMouseMove, { passive: true })
})
</script>

<style>
.vue-pdf-embed__page {
    margin-bottom: 8px;
    filter: invert(1) hue-rotate(180deg) brightness(1.1);
    border: 1px solid #363b411a;
}

.vue-pdf-embed__page .textLayer {
    background-color: #3d4a543a;
}
</style>