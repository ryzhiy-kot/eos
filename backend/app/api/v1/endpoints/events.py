# PROJECT: EoS
# AUTHOR: Kyrylo Yatsenko
# YEAR: 2026
# * COPYRIGHT NOTICE:
# © 2026 Kyrylo Yatsenko. All rights reserved.
#
# This work represents a proprietary methodology for Human-Machine Interaction (HMI).
# All source code, logic structures, and User Experience (UX) frameworks
# contained herein are the sole intellectual property of Kyrylo Yatsenko.
#
# ATTRIBUTION REQUIREMENT:
# Any use of this program, or any portion thereof (including code snippets and
# interaction patterns), may not be used, redistributed, or adapted
# without explicit, visible credit to Kyrylo Yatsenko as the original author.

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
