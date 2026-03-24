"""Chat router — runs the MoA pipeline and streams results as SSE."""

import json
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import (
    get_conversation_by_id,
    get_conversations,
    save_conversation,
    save_message,
    save_specialist_response,
)
from moa.chairman import ChairmanAggregator
from moa.pipeline import MoAPipeline
from providers.base import Specialist

router = APIRouter(tags=["chat"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class SpecialistConfig(BaseModel):
    model: str
    provider: str
    system_prompt: str = "You are a helpful assistant."
    temperature: float = 0.7
    max_tokens: int = 1024


class ChairmanConfig(BaseModel):
    model: str
    provider: str


class ChatRequest(BaseModel):
    query: str
    specialists: list[SpecialistConfig]
    chairman: ChairmanConfig
    pipeline_mode: str = "parallel"
    conversation_id: str | None = None  # None = create new conversation


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

def _sse(event: dict) -> str:
    """Format a dict as a single SSE data line."""
    return f"data: {json.dumps(event)}\n\n"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/chat")
async def chat(body: ChatRequest):
    """Run the MoA pipeline and stream results back as SSE events."""

    async def _generate():
        try:
            # 1. Convert request models to Specialist dataclasses
            specialists = [
                Specialist(
                    model=s.model,
                    provider=s.provider,
                    system_prompt=s.system_prompt,
                    temperature=s.temperature,
                    max_tokens=s.max_tokens,
                )
                for s in body.specialists
            ]

            # 2. Resolve conversation — resume or create
            if body.conversation_id:
                conv = await get_conversation_by_id(body.conversation_id)
                if conv is None:
                    raise ValueError(
                        f"Conversation '{body.conversation_id}' not found."
                    )
                conversation_id = body.conversation_id
                # Build history from stored messages (only role+content)
                history: list[dict[str, str]] = [
                    {"role": m["role"], "content": m["content"]}
                    for m in conv.get("messages", [])
                ]
            else:
                conversation_id = str(uuid4())
                history = []
                await save_conversation(
                    id=conversation_id,
                    title=body.query[:100],
                    pipeline_mode=body.pipeline_mode,
                )

            user_message_id = str(uuid4())
            await save_message(
                id=user_message_id,
                conversation_id=conversation_id,
                role="user",
                content=body.query,
            )

            # Emit the resolved conversation_id so the frontend can track it
            yield _sse({"type": "conversation_id", "conversation_id": conversation_id})

            # 3. Build per-token callback for specialist_token SSE events
            async def on_token(model: str, provider: str, token: str) -> None:
                pass  # yielded via the queue below

            # Use an asyncio.Queue to funnel tokens from concurrent specialist
            # coroutines into the single SSE generator coroutine.
            import asyncio
            token_queue: asyncio.Queue[dict | None] = asyncio.Queue()

            async def _on_token(model: str, provider: str, token: str) -> None:
                await token_queue.put(
                    {"type": "specialist_token", "model": model,
                     "provider": provider, "content": token}
                )

            # 4. Run pipeline (non-blocking) while draining the token queue
            pipeline = MoAPipeline()
            chairman_dict = {
                "model": body.chairman.model,
                "provider": body.chairman.provider,
            }

            pipeline_dispatch = {
                "parallel": pipeline.run_parallel,
                "serial": pipeline.run_serial,
                "debate": pipeline.run_debate,
            }
            run_fn = pipeline_dispatch.get(body.pipeline_mode, pipeline.run_parallel)

            # Kick off the pipeline as a task
            pipeline_task = asyncio.create_task(
                run_fn(
                    query=body.query,
                    specialists=specialists,
                    chairman_config=chairman_dict,
                    on_token=_on_token,
                    history=history if history else None,
                )
            )

            # Drain token queue until pipeline task completes
            while not pipeline_task.done():
                try:
                    event = await asyncio.wait_for(token_queue.get(), timeout=0.05)
                    if event is not None:
                        yield _sse(event)
                except asyncio.TimeoutError:
                    pass  # Check pipeline_task.done() again

            # Drain any remaining tokens that arrived just before task finished
            while not token_queue.empty():
                event = token_queue.get_nowait()
                if event is not None:
                    yield _sse(event)

            results = await pipeline_task

            # 5. Yield specialist_done with final stats for each specialist
            for r in results:
                yield _sse({
                    "type": "specialist_done",
                    "model": r.model,
                    "provider": r.provider,
                    "content": r.content,
                    "tokens_per_sec": r.tokens_per_sec,
                    "latency_ms": r.latency_ms,
                    "error": r.error,
                })

            # 6. Stream chairman aggregation
            yield _sse({"type": "chairman_start"})

            aggregator = ChairmanAggregator()
            chairman_chunks: list[str] = []

            async for chunk in aggregator.aggregate(
                query=body.query,
                results=results,
                chairman=chairman_dict,
            ):
                chairman_chunks.append(chunk)
                yield _sse({"type": "chairman_token", "content": chunk})

            yield _sse({"type": "chairman_done"})

            # 7. Persist assistant message + specialist responses
            assistant_message_id = str(uuid4())
            await save_message(
                id=assistant_message_id,
                conversation_id=conversation_id,
                role="assistant",
                content="".join(chairman_chunks),
            )

            for r in results:
                await save_specialist_response(
                    id=str(uuid4()),
                    message_id=assistant_message_id,
                    model=r.model,
                    provider=r.provider,
                    content=r.content,
                    tokens_per_sec=r.tokens_per_sec,
                    latency_ms=r.latency_ms,
                    token_count=r.token_count,
                )

        except Exception as exc:
            yield _sse({"type": "error", "message": str(exc)})

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations")
async def list_conversations():
    """Return all conversations ordered by most recently updated."""
    return await get_conversations()


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Return a single conversation with nested messages and specialist responses."""
    conversation = await get_conversation_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
