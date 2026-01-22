import type { StreamMessage } from "../interfaces";

/**
 * 接收并处理从后端流式返回的消息
 * @param endpoint 接口路径
 * @param onMessage 处理每一条消息的回调函数
 * @param method 请求方法，默认为 GET
 * @param data POST 请求体（仅在 method 为 POST 时有效）
 */
export async function receiveStream(
    endpoint: string,
    onMessage: (msg: StreamMessage) => void,
    method: "GET" | "POST" = "GET",
    data?: Record<string, any> // 或者 any 类型，看你数据格式
): Promise<void> {
    const baseUrl: string = import.meta.env.VITE_API_BASE_URL;
    const url = `${baseUrl}${endpoint}`;
    const fetchOptions: RequestInit = {
        method,
        headers: {
            "Content-Type": "application/json",
        },
    };
    if (method === "POST" && data) {
        fetchOptions.body = JSON.stringify(data);
    }
    const response = await fetch(url, fetchOptions);

    if (!response.body) {
        console.error("Response body is null");
        return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // 按双换行符分割
        let parts = buffer.split("\n\n");

        // 保留最后一部分（可能是不完整的一条）
        buffer = parts.pop() || "";

        for (const part of parts) {
            try {
                const msg: StreamMessage = JSON.parse(part);
                onMessage(msg);
            } catch (e) {
                console.warn("解析消息失败：", part, e);
            }
        }
    }

    // 处理最后残留的内容
    if (buffer.trim()) {
        try {
            const msg: StreamMessage = JSON.parse(buffer.trim());
            onMessage(msg);
        } catch (e) {
            console.warn("解析结尾消息失败：", buffer, e);
        }
    }
}