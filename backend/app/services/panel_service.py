import uuid
from typing import Optional

from sqlalchemy import delete, select

from app.db.session import async_session
from app.models.panel import Panel
from app.services.context_injector import (
    mock_fx_rates,
    mock_interest_curves,
    mock_news,
    mock_pnl,
    mock_positions,
    mock_risk,
)

BQ_FUNCTIONS = {
    "pnl": mock_pnl,
    "risk": mock_risk,
    "fx_rates": mock_fx_rates,
    "curves": mock_interest_curves,
    "positions": mock_positions,
    "news": mock_news,
}


async def create_panel(
    user_id: uuid.UUID,
    artifact_id: str,
    name: str,
    bq_function: str,
    bq_params: Optional[dict] = None,
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


async def get_panels(user_id: uuid.UUID) -> list[Panel]:
    async with async_session() as session:
        result = await session.execute(
            select(Panel).where(Panel.user_id == user_id, Panel.is_pinned == True)
        )
        return list(result.scalars().all())


async def get_panel(panel_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Panel]:
    async with async_session() as session:
        result = await session.execute(
            select(Panel).where(Panel.id == panel_id, Panel.user_id == user_id)
        )
        return result.scalar_one_or_none()


async def refresh_panel(panel_id: uuid.UUID, user_id: uuid.UUID) -> dict:
    panel = await get_panel(panel_id, user_id)
    if not panel:
        raise ValueError("Panel not found")

    func = BQ_FUNCTIONS.get(panel.bq_function)
    if not func:
        raise ValueError(f"Unknown function: {panel.bq_function}")

    return func(**panel.bq_params)


async def delete_panel(panel_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    async with async_session() as session:
        result = await session.execute(
            delete(Panel).where(Panel.id == panel_id, Panel.user_id == user_id)
        )
        await session.commit()
        return result.rowcount > 0


async def update_panel(
    panel_id: uuid.UUID,
    user_id: uuid.UUID,
    name: Optional[str] = None,
    refresh_interval: Optional[int] = None,
) -> Optional[Panel]:
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
