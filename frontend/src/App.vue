<script setup>
import MarkdownIt from 'markdown-it'
import { computed, nextTick, ref } from 'vue'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
})

const input = ref('')
const loading = ref(false)
const error = ref('')
const summary = ref('')
const history = ref([])
const sources = ref([])
const messages = ref([
  {
    role: 'assistant',
    content: '你好，我是 **BookAgent**。可以问我书籍推荐、文学分析，也可以让我把回答转成语音。',
  },
])
const audioUrl = ref('')
const listRef = ref(null)

const canSend = computed(() => input.value.trim() && !loading.value)

function renderMarkdown(content) {
  return md.render(content || '')
}

async function scrollToBottom() {
  await nextTick()
  if (listRef.value) {
    listRef.value.scrollTop = listRef.value.scrollHeight
  }
}

function updateAssistantMessage(index, content) {
  messages.value[index] = {
    ...messages.value[index],
    content,
  }
}

function handleStreamEvent(eventData, assistantIndex) {
  if (eventData.type === 'sources') {
    sources.value = eventData.sources || []
    return
  }

  if (eventData.type === 'delta') {
    const current = messages.value[assistantIndex]?.content || ''
    updateAssistantMessage(assistantIndex, current + (eventData.content || ''))
    return
  }

  if (eventData.type === 'done') {
    summary.value = eventData.summary || ''
    history.value = eventData.history || []
    sources.value = eventData.sources || sources.value
    audioUrl.value = eventData.audioUrl ? `${eventData.audioUrl}?t=${Date.now()}` : ''
    return
  }

  if (eventData.type === 'error') {
    throw new Error(eventData.error || '流式响应失败')
  }
}

function parseSseBlock(block) {
  const dataLines = block
    .split('\n')
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.slice(5).trimStart())

  if (!dataLines.length) return null
  return JSON.parse(dataLines.join('\n'))
}

async function sendMessage() {
  const content = input.value.trim()
  if (!content || loading.value) return

  messages.value.push({ role: 'user', content })
  messages.value.push({ role: 'assistant', content: '' })
  const assistantIndex = messages.value.length - 1

  input.value = ''
  loading.value = true
  error.value = ''
  sources.value = []
  await scrollToBottom()

  try {
    const response = await fetch('/api/chat-stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: content }),
    })

    if (!response.ok || !response.body) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.error || '请求失败')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const blocks = buffer.split('\n\n')
      buffer = blocks.pop() || ''

      for (const block of blocks) {
        if (!block.trim()) continue
        const eventData = parseSseBlock(block)
        if (!eventData) continue
        handleStreamEvent(eventData, assistantIndex)
        await scrollToBottom()
      }
    }

    if (buffer.trim()) {
      const eventData = parseSseBlock(buffer)
      if (eventData) {
        handleStreamEvent(eventData, assistantIndex)
      }
    }
  } catch (err) {
    error.value = err.message || '服务连接失败'
    updateAssistantMessage(assistantIndex, '后端服务暂时不可用，请检查 Python API 是否已启动。')
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

async function resetChat() {
  error.value = ''
  await fetch('/api/reset', { method: 'POST' }).catch(() => {})
  summary.value = ''
  history.value = []
  sources.value = []
  audioUrl.value = ''
  messages.value = [
    {
      role: 'assistant',
      content: '记忆已清空，可以开始新的对话。',
    },
  ]
  await scrollToBottom()
}
</script>

<template>
  <main class="app-shell">
    <section class="chat-panel">
      <header class="topbar">
        <div>
          <h1>BookAgent</h1>
          <p>智能书籍问答助手</p>
        </div>
        <button class="ghost-button" type="button" @click="resetChat">清空</button>
      </header>

      <div ref="listRef" class="message-list">
        <article
          v-for="(message, index) in messages"
          :key="index"
          class="message"
          :class="message.role"
        >
          <span class="role">{{ message.role === 'user' ? '你' : '助手' }}</span>
          <div class="markdown-body" v-html="renderMarkdown(message.content || (loading ? '正在思考...' : ''))"></div>
        </article>
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <form class="composer" @submit.prevent="sendMessage">
        <textarea
          v-model="input"
          placeholder="请输入你的问题，例如：用要点总结《三体》的核心看点"
          rows="2"
          @keydown.enter.exact.prevent="sendMessage"
        />
        <button type="submit" :disabled="!canSend">
          {{ loading ? '发送中' : '发送' }}
        </button>
      </form>
    </section>

    <aside class="memory-panel">
      <section>
        <h2>记忆摘要</h2>
        <div class="summary markdown-body" v-html="renderMarkdown(summary || '达到记忆窗口后会自动生成摘要。')"></div>
      </section>

      <section>
        <h2>检索来源</h2>
        <ul class="sources">
          <li v-for="item in sources" :key="item.id">
            <div>
              <strong>片段 {{ item.id }}</strong>
              <span>{{ Number(item.score).toFixed(4) }}</span>
            </div>
            <div class="markdown-body source-text" v-html="renderMarkdown(item.text)"></div>
          </li>
        </ul>
        <p v-if="!sources.length" class="muted">提问后会显示匹配到的书籍资料。</p>
      </section>

      <section>
        <h2>最近对话</h2>
        <ul class="history">
          <li v-for="(item, index) in history" :key="index">
            <strong>{{ item.role }}</strong>
            <div class="markdown-body" v-html="renderMarkdown(item.content)"></div>
          </li>
        </ul>
        <p v-if="!history.length" class="muted">暂无历史。</p>
      </section>

      <section>
        <h2>语音输出</h2>
        <audio v-if="audioUrl" controls :src="audioUrl"></audio>
        <p v-else class="muted">当工具生成 output.mp3 后会显示播放器。</p>
      </section>
    </aside>
  </main>
</template>
