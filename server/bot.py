"""Japanese voice role-play tutor – Pipecat bot.

Pipeline: SmallWebRTC in → Deepgram STT (ja) → Claude → Cartesia TTS (ja) → out.

Run:  uv run bot.py      (serves POST /start + WebRTC signalling on :7860)
"""

import os

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.observers.user_bot_latency_observer import UserBotLatencyObserver
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.anthropic.llm import AnthropicLLMService
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.transcriptions.language import Language
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.workers.runner import WorkerRunner

from scenarios import (
    DEFAULT_LEVEL,
    DEFAULT_SCENARIO,
    LEVELS,
    SCENARIOS,
    build_system_prompt,
    opening_instruction,
)

load_dotenv(override=True)


def _session_config(runner_args: RunnerArguments) -> tuple[str, str]:
    body = runner_args.body if isinstance(runner_args.body, dict) else {}
    scenario = body.get("scenario", DEFAULT_SCENARIO)
    level = body.get("level", DEFAULT_LEVEL)
    if scenario not in SCENARIOS:
        scenario = DEFAULT_SCENARIO
    if level not in LEVELS:
        level = DEFAULT_LEVEL
    return scenario, level


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments) -> None:
    scenario, level = _session_config(runner_args)
    logger.info(f"Starting role-play: scenario={scenario} level={level}")

    stt = DeepgramSTTService(
        api_key=os.getenv("DEEPGRAM_API_KEY"),
        settings=DeepgramSTTService.Settings(model="nova-3", language=Language.JA),
    )

    llm = AnthropicLLMService(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        settings=AnthropicLLMService.Settings(
            model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5"),
            system_instruction=build_system_prompt(scenario, level),
            max_tokens=200,  # 2 short sentences; keeps the turn fast
        ),
    )

    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        settings=CartesiaTTSService.Settings(
            voice=os.environ["CARTESIA_VOICE_ID"],
            language=Language.JA,
        ),
    )

    context = LLMContext()
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
    )

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )

    # Latency: user stops speaking → bot's first audio, with per-stage breakdown.
    latency_observer = UserBotLatencyObserver()

    @latency_observer.event_handler("on_latency_measured")
    async def on_latency_measured(observer, latency_seconds: float):
        logger.info(f"⏱  E2E latency (user stop → bot audio): {latency_seconds * 1000:.0f} ms")

    @latency_observer.event_handler("on_latency_breakdown")
    async def on_latency_breakdown(observer, breakdown):
        for line in breakdown.turn_contribution_lines():
            logger.info(f"   {line}")

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
        observers=[latency_observer],
    )
    runner = WorkerRunner(handle_sigint=runner_args.handle_sigint)
    await runner.add_workers(worker)

    @worker.rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        context.add_message({"role": "developer", "content": opening_instruction(scenario)})
        await worker.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await runner.cancel()

    await runner.run()


async def bot(runner_args: RunnerArguments):
    transport_params = {
        "webrtc": lambda: TransportParams(audio_in_enabled=True, audio_out_enabled=True),
    }
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
