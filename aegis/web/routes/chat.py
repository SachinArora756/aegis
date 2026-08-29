"""Ask Aegis — RAG-powered security chatbot routes."""

import asyncio
import json
import uuid

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from aegis.web.app import templates, is_demo_mode

router = APIRouter()


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse(request, "chat.html", {
        "demo_mode": is_demo_mode(),
        "active_page": "chat",
    })


@router.post("/api/chat/message")
async def api_chat_message(request: Request):
    body = await request.json()
    question = body.get("question", "").strip()
    session_id = body.get("session_id") or str(uuid.uuid4())

    if not question:
        return {"error": "No question provided", "session_id": session_id}

    if is_demo_mode():
        from aegis.rag.chat import DemoChatEngine
        engine = DemoChatEngine()
        result = await engine.answer(question)
        return {
            "answer": result.answer,
            "sources": result.sources,
            "session_id": session_id,
        }

    return {
        "answer": "Production mode requires ANTHROPIC_API_KEY and VOYAGE_API_KEY to be configured.",
        "sources": [],
        "session_id": session_id,
    }


@router.websocket("/api/chat/stream")
async def ws_chat_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        raw = await websocket.receive_text()
        data = json.loads(raw)
        question = data.get("question", "").strip()
        fast = data.get("fast", False)

        if not question:
            await websocket.send_json({"type": "error", "text": "No question provided"})
            await websocket.send_json({"type": "done"})
            await websocket.close()
            return

        if is_demo_mode():
            from aegis.rag.chat import DemoChatEngine
            engine = DemoChatEngine()
            async for event in engine.stream_answer(question):
                await websocket.send_json(event)
        else:
            msg = "Production mode requires ANTHROPIC_API_KEY and VOYAGE_API_KEY."
            for char in msg:
                await websocket.send_json({"type": "token", "text": char})
                await asyncio.sleep(0.02)

        await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "text": str(e)})
            await websocket.send_json({"type": "done"})
        except Exception:
            pass
