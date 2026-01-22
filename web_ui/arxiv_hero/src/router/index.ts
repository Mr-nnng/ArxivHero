import { createRouter, createWebHistory } from 'vue-router'
import Home from '../pages/Home.vue'
import Article from '../pages/Article.vue'
import Content from '../pages/Content.vue'
import Test from '../pages/Test.vue'

const routes = [
    { path: '/', component: Home },
    { path: '/articles', component: Article },
    { path: '/article/:entryId', component: Content },
    { path: '/test', component: Test },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

export default router
