from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate


class WorkspaceService:
    @staticmethod
    async def get_workspaces(
        db: AsyncSession, is_archived: bool = False
    ) -> List[Workspace]:
        stmt = select(Workspace).where(Workspace.is_archived == is_archived)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_workspace(db: AsyncSession, workspace_id: str) -> Optional[Workspace]:
        stmt = select(Workspace).where(Workspace.id == workspace_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_workspace(
        db: AsyncSession, workspace_in: WorkspaceCreate
    ) -> Workspace:
        db_obj = Workspace(
            name=workspace_in.name,
            state=workspace_in.state,
            is_archived=workspace_in.is_archived,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def update_workspace(
        db: AsyncSession, workspace_id: str, workspace_in: WorkspaceUpdate
    ) -> Optional[Workspace]:
        db_obj = await WorkspaceService.get_workspace(db, workspace_id)
        if not db_obj:
            return None

        update_data = workspace_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    @staticmethod
    async def delete_workspace(db: AsyncSession, workspace_id: str) -> bool:
        db_obj = await WorkspaceService.get_workspace(db, workspace_id)
        if not db_obj:
            return False

        db_obj.is_archived = True
        await db.commit()
        return True

    @staticmethod
    async def archive_pane(
        db: AsyncSession,
        workspace_id: str,
        pane_data: dict,
        user_id: Optional[int] = None,
    ) -> bool:
        from app.models.archived_pane import ArchivedPane

        db_obj = ArchivedPane(
            workspace_id=workspace_id,
            user_id=user_id,
            pane_data=pane_data,
        )
        db.add(db_obj)
        await db.commit()
        return True
