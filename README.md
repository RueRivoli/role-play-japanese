# HiKana – Japanese voice role-play tutor (demo)

Browser (Vue) ⇄ WebRTC ⇄ Pipecat bot: Silero VAD → Deepgram STT (ja) → Claude Haiku 5.5 → Cartesia TTS (ja).

## Setup

```bash
# server (Python 3.12, uv)
cd server
cp .env.example .env    # fill in DEEPGRAM / ANTHROPIC / CARTESIA keys + a Japanese Cartesia voice ID
uv sync
uv run bot.py -t webrtc # http://localhost:7860

# client (in another terminal)
cd client
npm install
npm run dev             # http://localhost:5173 (proxies /start and /sessions to :7860)
```

## Where things live

- `server/scenarios.py`: scenarios (café, hotel, konbini), JLPT levels and the system prompt (2 short sentences max, no romaji, recasting).
- `server/bot.py`: the pipeline. Barge-in works through VAD, which interrupts the TTS as soon as the user speaks.
- `client/src/App.vue`: choosing a scenario and level, the live transcript, and bot audio playback.

## Latency

Each turn logs:

```
⏱  E2E latency (user stop → bot audio): 812 ms
   <per-stage breakdown: VAD, STT, LLM TTFB, TTS TTFB…>
```

To add a scenario, add it in `server/scenarios.py` and in `client/src/scenarios.ts`, using the same `id`.
