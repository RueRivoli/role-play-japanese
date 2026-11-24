<script setup lang="ts">
import { computed, nextTick, ref, shallowRef } from 'vue'
import { PipecatClient, type TransportState } from '@pipecat-ai/client-js'
import { SmallWebRTCTransport } from '@pipecat-ai/small-webrtc-transport'
import { LEVELS, SCENARIOS, type Level, type ScenarioId } from './scenarios'

type Line = { who: 'user' | 'bot'; text: string; final: boolean }

const scenario = ref<ScenarioId>('cafe')
const level = ref<Level>('N5')
const state = ref<TransportState>('disconnected')
const error = ref<string | null>(null)
const lines = ref<Line[]>([])
const userSpeaking = ref(false)
const botSpeaking = ref(false)

const client = shallowRef<PipecatClient | null>(null)
const audioEl = ref<HTMLAudioElement | null>(null)
const logEl = ref<HTMLElement | null>(null)

const active = computed(() => !['disconnected', 'error'].includes(state.value))
const ready = computed(() => state.value === 'ready')
const currentScenario = computed(() => SCENARIOS.find((s) => s.id === scenario.value)!)

function scrollDown() {
  nextTick(() => logEl.value?.scrollTo({ top: logEl.value.scrollHeight, behavior: 'smooth' }))
}

// Interim user transcripts replace the last non-final user line.
function pushUser(text: string, final: boolean) {
  const last = lines.value.at(-1)
  if (last?.who === 'user' && !last.final) {
    last.text = text
    last.final = final
  } else {
    lines.value.push({ who: 'user', text, final })
  }
  scrollDown()
}

// Bot text streams in chunks; append to the current bot line until the bot stops speaking.
function pushBot(text: string) {
  const last = lines.value.at(-1)
  if (last?.who === 'bot' && !last.final) last.text += text
  else lines.value.push({ who: 'bot', text, final: false })
  scrollDown()
}

function closeBotLine() {
  const last = lines.value.at(-1)
  if (last?.who === 'bot') last.final = true
}

async function start() {
  error.value = null
  lines.value = []
  const pc = new PipecatClient({
    transport: new SmallWebRTCTransport(),
    enableMic: true,
    enableCam: false,
    callbacks: {
      onTransportStateChanged: (s) => (state.value = s),
      onError: (msg) => (error.value = JSON.stringify(msg.data)),
      onUserStartedSpeaking: () => (userSpeaking.value = true),
      onUserStoppedSpeaking: () => (userSpeaking.value = false),
      onBotStartedSpeaking: () => (botSpeaking.value = true),
      onBotStoppedSpeaking: () => {
        botSpeaking.value = false
        closeBotLine()
      },
      onUserTranscript: (d) => d.text.trim() && pushUser(d.text, d.final),
      onBotOutput: (d) => {
        // Only show text that will be spoken, at sentence granularity
        if (d.will_be_spoken === false) return
        if (d.output_type && d.output_type !== 'sentence') return
        pushBot(d.text)
      },
      onTrackStarted: (track, participant) => {
        if (participant?.local || track.kind !== 'audio' || !audioEl.value) return
        audioEl.value.srcObject = new MediaStream([track])
        audioEl.value.play().catch(() => {})
      },
    },
  })
  client.value = pc
  try {
    await pc.startBotAndConnect({
      endpoint: '/start',
      requestData: {
        transport: 'webrtc',
        body: { scenario: scenario.value, level: level.value },
      },
    })
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
    await stop()
  }
}

async function stop() {
  await client.value?.disconnect()
  client.value = null
  userSpeaking.value = false
  botSpeaking.value = false
}
</script>

<template>
  <main class="app">
    <header>
      <h1>HiKana <span>ロールプレイ</span></h1>
      <p class="sub">Entraîne-toi à parler japonais en situation réelle.</p>
    </header>

    <section v-if="!active" class="setup">
      <h2>Choisis une situation</h2>
      <div class="cards">
        <button
          v-for="s in SCENARIOS"
          :key="s.id"
          class="card"
          :class="{ selected: scenario === s.id }"
          @click="scenario = s.id"
        >
          <span class="emoji">{{ s.emoji }}</span>
          <strong>{{ s.title }}</strong>
          <span class="jp">{{ s.jp }}</span>
          <small>{{ s.desc }}</small>
        </button>
      </div>

      <h2>Ton niveau</h2>
      <div class="levels">
        <button
          v-for="l in LEVELS"
          :key="l"
          class="pill"
          :class="{ selected: level === l }"
          @click="level = l"
        >
          JLPT {{ l }}
        </button>
      </div>

      <button class="primary" @click="start">Commencer la conversation</button>
      <p class="hint">Autorise le micro, puis parle normalement. Tu peux couper la parole au personnage.</p>
    </section>

    <section v-else class="session">
      <div class="status">
        <span class="badge">{{ currentScenario.emoji }} {{ currentScenario.title }} · {{ level }}</span>
        <span class="dot" :class="{ on: ready }" />
        <span v-if="!ready">Connexion…</span>
        <span v-else-if="userSpeaking">Tu parles…</span>
        <span v-else-if="botSpeaking">Le personnage parle…</span>
        <span v-else>À toi !</span>
      </div>

      <div ref="logEl" class="log">
        <div v-for="(l, i) in lines" :key="i" class="line" :class="[l.who, { interim: !l.final && l.who === 'user' }]">
          {{ l.text }}
        </div>
        <p v-if="ready && !lines.length" class="hint">Le personnage va te saluer…</p>
      </div>

      <div class="mic" :class="{ speaking: userSpeaking }">🎙️</div>
      <button class="secondary" @click="stop">Terminer</button>
    </section>

    <p v-if="error" class="error">Erreur : {{ error }}</p>
    <audio ref="audioEl" autoplay />
  </main>
</template>
