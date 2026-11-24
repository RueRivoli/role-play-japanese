import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Proxy the Pipecat dev runner (uv run bot.py → :7860)
const BOT = 'http://localhost:7860'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/start': BOT,
      '/sessions': BOT,
      '/api/offer': BOT,
    },
  },
})
