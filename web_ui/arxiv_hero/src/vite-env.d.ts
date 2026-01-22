/// <reference types="vite/client" />

declare module '*.vue' {
    import { ComponentOptions } from 'vue'
    const componentOptions: ComponentOptions
    export default componentOptions
}

export { }

declare global {
    interface Window {
        MathJax: {
            typesetPromise: () => Promise<void>;
        };
    }
}