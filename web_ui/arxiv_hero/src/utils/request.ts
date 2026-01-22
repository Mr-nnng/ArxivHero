import axios from 'axios'

const service = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    timeout: 30000
})

export default service
