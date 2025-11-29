"""
Simple modules endpoint - workaround for RBAC table conflicts
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db

router = APIRouter(
    prefix="/api/v1/modules",
    tags=["Modules"],
)


@router.get("/user/{user_id}")
async def get_user_modules(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get modules accessible to a user based on their role assignments.

    Simplified version that directly queries the database.
    """
    try:
        # Query to get accessible modules for a user
        query = text("""
        SELECT DISTINCT
            m.id,
            m.name,
            m.code,
            m.description,
            m.icon,
            m.route,
            m.display_order,
            m.is_active
        FROM modules m
        JOIN role_module_permissions rmp ON rmp.module_id = m.id
        JOIN user_roles ur ON ur.role_id = rmp.role_id
        WHERE ur.user_id = :user_id
          AND rmp.can_read = TRUE
          AND m.is_active = TRUE
          AND ur.is_active = TRUE
        ORDER BY m.display_order
        """)

        result = await db.execute(query, {"user_id": str(user_id)})
        rows = result.fetchall()

        modules = []
        for row in rows:
            modules.append({
                "id": str(row[0]),
                "name": row[1],
                "code": row[2],
                "description": row[3],
                "icon": row[4],
                "route": row[5],
                "display_order": row[6],
                "is_active": row[7],
            })

        return modules

    except Exception as e:
        print(f"Error getting user modules: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting modules: {str(e)}")
