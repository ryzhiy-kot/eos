import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json

router = APIRouter()


async def event_generator(request: Request):
    while True:
        if await request.is_disconnected():
            break

        # Simple heartbeat
        payload = json.dumps(
            {"type": "heartbeat", "timestamp": asyncio.get_event_loop().time()}
        )
        yield f"data: {payload}\n\n"
        await asyncio.sleep(10)


@router.get("/stream", tags=["events"])
async def stream_events(request: Request):
    return StreamingResponse(event_generator(request), media_type="text/event-stream")
