"""Export router — generates downloadable conversation files."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, JSONResponse

from database import get_conversation_by_id

router = APIRouter(tags=["export"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_markdown(conv: dict) -> str:
    """Render a conversation dict as a Markdown document."""
    lines: list[str] = []
    lines.append(f"# {conv.get('title', 'Conversation')}")
    lines.append(f"\n> **Pipeline:** {conv.get('pipeline_mode', 'parallel')}  ")
    lines.append(f"> **Created:** {conv.get('created_at', '')}")
    lines.append("")

    for msg in conv.get("messages", []):
        role = msg.get("role", "user")

        if role == "user":
            lines.append("---")
            lines.append(f"\n## 🧑 User\n")
            lines.append(msg.get("content", ""))
            lines.append("")

        elif role == "assistant":
            # Specialist responses
            for sr in msg.get("specialist_responses", []):
                model = sr.get("model", "unknown")
                provider = sr.get("provider", "")
                lines.append("---")
                lines.append(f"\n### 🤖 {model} ({provider})\n")
                lines.append(sr.get("content", ""))
                lines.append("")
                lines.append(
                    f"> `{sr.get('tokens_per_sec', 0):.1f} tok/s` · "
                    f"`{sr.get('latency_ms', 0)} ms` · "
                    f"`{sr.get('token_count', 0)} tokens`"
                )
                lines.append("")

            # Chairman synthesis
            chairman_content = msg.get("content", "")
            if chairman_content:
                lines.append("---")
                lines.append("\n## 🏛️ Chairman Synthesis\n")
                lines.append(chairman_content)
                lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/conversations/{conversation_id}/export")
async def export_conversation(conversation_id: str, format: str = "markdown"):
    """
    Export a conversation as Markdown or JSON.

    Query params:
        format: ``"markdown"`` (default) or ``"json"``.
    """
    conv = await get_conversation_by_id(conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    safe_title = (conv.get("title") or "conversation")[:40].replace(" ", "_")

    if format == "json":
        return JSONResponse(
            content=conv,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{safe_title}.json"'
                ),
            },
        )

    # Default: markdown
    md = _build_markdown(conv)
    return Response(
        content=md,
        media_type="text/markdown",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{safe_title}.md"'
            ),
        },
    )
