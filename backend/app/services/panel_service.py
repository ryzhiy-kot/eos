"""Panel service — business logic for dashboard panels.

Uses the centralized database session from app.db.session.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.db.session import async_session
from app.models.panel import Panel
from app.services.mock_data import (
    mock_fx_rates,
    mock_interest_curves,
    mock_news,
    mock_pnl,
    mock_positions,
    mock_risk,
)

logger = get_logger(__name__)

BQ_FUNCTIONS: dict[str, callable] = {
    "pnl": mock_pnl,
    "risk": mock_risk,
    "fx_rates": mock_fx_rates,
    "curves": mock_interest_curves,
    "positions": mock_positions,
    "news": mock_news,
}


class PanelService:
    """Service for managing dashboard panels."""

    async def create_panel(
        self,
        user_id: UUID,
        artifact_id: str,
        name: str,
        bq_function: str,
        bq_params: Optional[dict] = None,
        refresh_interval: int = 0,
    ) -> Panel:
        """Create a new panel."""
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
            logger.info("Created panel %s for user %s", panel.id, user_id)
            return panel

    async def get_panels(self, user_id: UUID) -> list[Panel]:
        """Get all pinned panels for a user."""
        async with async_session() as session:
            result = await session.execute(
                select(Panel).where(Panel.user_id == user_id, Panel.is_pinned == True)
            )
            return list(result.scalars().all())

    async def get_panel(self, panel_id: UUID, user_id: UUID) -> Optional[Panel]:
        """Get a specific panel by ID."""
        async with async_session() as session:
            result = await session.execute(
                select(Panel).where(Panel.id == panel_id, Panel.user_id == user_id)
            )
            return result.scalar_one_or_none()

    async def refresh_panel(self, panel_id: UUID, user_id: UUID) -> dict:
        """Refresh panel data by re-executing its bq function."""
        panel = await self.get_panel(panel_id, user_id)
        if not panel:
            raise ValueError("Panel not found")

        func = BQ_FUNCTIONS.get(panel.bq_function)
        if not func:
            raise ValueError(f"Unknown function: {panel.bq_function}")

        return func(**panel.bq_params)

    async def delete_panel(self, panel_id: UUID, user_id: UUID) -> bool:
        """Delete a panel."""
        async with async_session() as session:
            result = await session.execute(
                delete(Panel).where(Panel.id == panel_id, Panel.user_id == user_id)
            )
            await session.commit()
            logger.info("Deleted panel %s", panel_id)
            return result.rowcount > 0

    async def update_panel(
        self,
        panel_id: UUID,
        user_id: UUID,
        name: Optional[str] = None,
        refresh_interval: Optional[int] = None,
    ) -> Optional[Panel]:
        """Update a panel's properties."""
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
            logger.info("Updated panel %s", panel_id)
            return panel


# Singleton for backward compatibility
_panel_service: Optional[PanelService] = None


def get_panel_service() -> PanelService:
    """Get or create a PanelService singleton."""
    global _panel_service
    if _panel_service is None:
        _panel_service = PanelService()
    return _panel_service


# Backward compatibility: module-level functions
async def create_panel(
    user_id: UUID,
    artifact_id: str,
    name: str,
    bq_function: str,
    bq_params: Optional[dict] = None,
    refresh_interval: int = 0,
) -> Panel:
    """Create a new panel (backward compatibility)."""
    return await get_panel_service().create_panel(
        user_id, artifact_id, name, bq_function, bq_params, refresh_interval
    )


async def get_panels(user_id: UUID) -> list[Panel]:
    """Get all pinned panels for a user (backward compatibility)."""
    return await get_panel_service().get_panels(user_id)


async def get_panel(panel_id: UUID, user_id: UUID) -> Optional[Panel]:
    """Get a specific panel by ID (backward compatibility)."""
    return await get_panel_service().get_panel(panel_id, user_id)


async def refresh_panel(panel_id: UUID, user_id: UUID) -> dict:
    """Refresh panel data (backward compatibility)."""
    return await get_panel_service().refresh_panel(panel_id, user_id)


async def delete_panel(panel_id: UUID, user_id: UUID) -> bool:
    """Delete a panel (backward compatibility)."""
    return await get_panel_service().delete_panel(panel_id, user_id)


async def update_panel(
    panel_id: UUID,
    user_id: UUID,
    name: Optional[str] = None,
    refresh_interval: Optional[int] = None,
) -> Optional[Panel]:
    """Update a panel (backward compatibility)."""
    return await get_panel_service().update_panel(panel_id, user_id, name, refresh_interval)