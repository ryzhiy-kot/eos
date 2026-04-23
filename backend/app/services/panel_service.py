import asyncio
import uuid


from sqlalchemy import delete, select

from app.services.namespace_registry import NamespaceRegistry
from app.services.session_service import Panel, async_session


async def create_panel(
    user_id: str,
    artifact_id: str,
    name: str,
    bq_function: str,
    bq_params: dict | None = None,
    refresh_interval: int = 0,
) -> Panel:
    async with async_session() as session:
        panel = Panel(
            user_id=user_id,
            artifact_id=artifact_id,
            name=name,
            bq_function=bq_function,
            bq_params=bq_params or {},
            refresh_interval=refresh_interval,
        )
        session.add(panel)
        await session.commit()
        await session.refresh(panel)
        return panel


async def get_panels(user_id: str) -> list[Panel]:
    async with async_session() as session:
        result = await session.execute(
            select(Panel).where(Panel.user_id == user_id, Panel.is_pinned == True)
        )
        return list(result.scalars().all())


async def get_panel(panel_id: str, user_id: str) -> Panel | None:
    async with async_session() as session:
        result = await session.execute(
            select(Panel).where(Panel.id == panel_id, Panel.user_id == user_id)
        )
        return result.scalar_one_or_none()


async def refresh_panel(panel_id: str, user_id: str) -> dict:
    panel = await get_panel(panel_id, user_id)
    if not panel:
        raise ValueError("Panel not found")

    func_info = NamespaceRegistry.get_function("bq", panel.bq_function)
    if not func_info:
        raise ValueError(f"Unknown function: {panel.bq_function}")

    return func_info.func(**panel.bq_params)


async def stream_panel(websocket, panel_id: str, user_id: str):
    """Stream panel data updates via WebSocket."""
    panel = await get_panel(panel_id, user_id)
    if not panel:
        await websocket.send_json({"error": "Panel not found"})
        return

    func_info = NamespaceRegistry.get_function("bq", panel.bq_function)
    if not func_info:
        await websocket.send_json({"error": f"Unknown function: {panel.bq_function}"})
        return

    try:
        while True:
            data = func_info.func(**panel.bq_params)
            await websocket.send_json({
                "type": "panel_update",
                "panel_id": str(panel_id),
                "data": data,
            })
            await asyncio.sleep(panel.refresh_interval)
    except Exception as e:
        await websocket.send_json({"error": str(e)})


async def delete_panel(panel_id: str, user_id: str) -> bool:
    async with async_session() as session:
        result = await session.execute(
            delete(Panel).where(Panel.id == panel_id, Panel.user_id == user_id)
        )
        await session.commit()
        return result.rowcount > 0


async def update_panel(
    panel_id: str,
    user_id: str,
    name: str | None = None,
    refresh_interval: int | None = None,
) -> Panel | None:
    async with async_session() as session:
        result = await session.execute(
            select(Panel).where(Panel.id == panel_id, Panel.user_id == user_id)
        )
        panel = result.scalar_one_or_none()
        if not panel:
            return None

        if name is not None:
            panel.name = name
        if refresh_interval is not None:
            panel.refresh_interval = refresh_interval

        await session.commit()
        await session.refresh(panel)
        return panel
