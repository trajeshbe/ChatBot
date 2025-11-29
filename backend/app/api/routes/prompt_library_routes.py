"""
Prompt Library and Output Templates API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.models.prompt_library import PromptLibrary, PromptRating, OutputTemplate, PromptUsageLog
from app.models.database_enhanced import User, Project
from app.models.rbac import Department
from app.schemas.prompt_schemas import (
    PromptCreate,
    PromptUpdate,
    PromptResponse,
    PromptListResponse,
    PromptRatingCreate,
    PromptRatingResponse,
    PromptUsageCreate,
    OutputTemplateCreate,
    OutputTemplateUpdate,
    OutputTemplateResponse,
    OutputTemplateListResponse,
)
from app.api.routes.auth import get_current_user, get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["prompt-library"])


# ============================================================================
# PROMPT LIBRARY ENDPOINTS
# ============================================================================

@router.get("/prompts", response_model=PromptListResponse)
async def list_prompts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    prompt_type: Optional[str] = None,
    category: Optional[str] = None,
    module: Optional[str] = None,
    is_public: Optional[bool] = None,
    project_id: Optional[UUID] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(created_at|usage_count|average_rating|name)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    List prompts with filtering and pagination.

    - Filters: prompt_type, category, module, is_public, project_id, search
    - Sorting: created_at, usage_count, average_rating, name
    - Returns public prompts and user's own prompts
    """
    try:
        # Build filter conditions
        filters = []

        if prompt_type:
            filters.append(PromptLibrary.prompt_type == prompt_type)
        if category:
            filters.append(PromptLibrary.category == category)
        if module:
            filters.append(PromptLibrary.module == module)
        if project_id:
            filters.append(PromptLibrary.project_id == project_id)

        # Public prompts or user's own prompts
        if current_user:
            visibility_filter = or_(
                PromptLibrary.is_public == True,
                PromptLibrary.created_by == current_user.id
            )
        else:
            visibility_filter = PromptLibrary.is_public == True

        if is_public is not None:
            filters.append(PromptLibrary.is_public == is_public)

        filters.append(visibility_filter)

        # Search in name and description
        if search:
            search_filter = or_(
                PromptLibrary.name.ilike(f"%{search}%"),
                PromptLibrary.description.ilike(f"%{search}%")
            )
            filters.append(search_filter)

        # Count total
        count_query = select(func.count(PromptLibrary.id)).where(and_(*filters))
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Build query with sorting
        query = select(PromptLibrary).where(and_(*filters))

        # Apply sorting
        sort_column = getattr(PromptLibrary, sort_by)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Load with relationships
        query = query.options(
            selectinload(PromptLibrary.creator),
            selectinload(PromptLibrary.project),
            selectinload(PromptLibrary.department)
        )

        result = await db.execute(query)
        prompts = result.scalars().all()

        # Convert to response with additional info
        prompt_responses = []
        for prompt in prompts:
            prompt_dict = {
                **prompt.__dict__,
                "creator_username": prompt.creator.username if prompt.creator else None,
                "project_name": prompt.project.name if prompt.project else None,
                "department_name": prompt.department.name if prompt.department else None
            }
            prompt_responses.append(PromptResponse(**prompt_dict))

        return PromptListResponse(
            prompts=prompt_responses,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error listing prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: UUID,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific prompt by ID"""
    try:
        query = select(PromptLibrary).where(PromptLibrary.id == prompt_id).options(
            selectinload(PromptLibrary.creator),
            selectinload(PromptLibrary.project),
            selectinload(PromptLibrary.department)
        )
        result = await db.execute(query)
        prompt = result.scalar_one_or_none()

        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        # Check access - must be public or owned by user
        if not prompt.is_public and (not current_user or prompt.created_by != current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")

        prompt_dict = {
            **prompt.__dict__,
            "creator_username": prompt.creator.username if prompt.creator else None,
            "project_name": prompt.project.name if prompt.project else None,
            "department_name": prompt.department.name if prompt.department else None
        }

        return PromptResponse(**prompt_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts", response_model=PromptResponse)
async def create_prompt(
    prompt: PromptCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new prompt"""
    try:
        # Create new prompt
        new_prompt = PromptLibrary(
            **prompt.model_dump(),
            created_by=current_user.id,
            department_id=current_user.department_id
        )

        db.add(new_prompt)
        await db.commit()
        await db.refresh(new_prompt)

        # Load relationships
        query = select(PromptLibrary).where(PromptLibrary.id == new_prompt.id).options(
            selectinload(PromptLibrary.creator),
            selectinload(PromptLibrary.project),
            selectinload(PromptLibrary.department)
        )
        result = await db.execute(query)
        created_prompt = result.scalar_one()

        prompt_dict = {
            **created_prompt.__dict__,
            "creator_username": created_prompt.creator.username if created_prompt.creator else None,
            "project_name": created_prompt.project.name if created_prompt.project else None,
            "department_name": created_prompt.department.name if created_prompt.department else None
        }

        logger.info(f"Created prompt: {new_prompt.id} by user {current_user.username}")
        return PromptResponse(**prompt_dict)

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/prompts/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: UUID,
    prompt_update: PromptUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a prompt (only owner can update)"""
    try:
        # Get existing prompt
        result = await db.execute(
            select(PromptLibrary).where(PromptLibrary.id == prompt_id)
        )
        existing_prompt = result.scalar_one_or_none()

        if not existing_prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        # Check ownership
        if existing_prompt.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Only the creator can update this prompt")

        # Update fields
        update_data = prompt_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_prompt, field, value)

        await db.commit()
        await db.refresh(existing_prompt)

        # Load relationships
        query = select(PromptLibrary).where(PromptLibrary.id == existing_prompt.id).options(
            selectinload(PromptLibrary.creator),
            selectinload(PromptLibrary.project),
            selectinload(PromptLibrary.department)
        )
        result = await db.execute(query)
        updated_prompt = result.scalar_one()

        prompt_dict = {
            **updated_prompt.__dict__,
            "creator_username": updated_prompt.creator.username if updated_prompt.creator else None,
            "project_name": updated_prompt.project.name if updated_prompt.project else None,
            "department_name": updated_prompt.department.name if updated_prompt.department else None
        }

        logger.info(f"Updated prompt: {prompt_id} by user {current_user.username}")
        return PromptResponse(**prompt_dict)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/prompts/{prompt_id}")
async def delete_prompt(
    prompt_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a prompt (only owner can delete)"""
    try:
        # Get existing prompt
        result = await db.execute(
            select(PromptLibrary).where(PromptLibrary.id == prompt_id)
        )
        existing_prompt = result.scalar_one_or_none()

        if not existing_prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        # Check ownership
        if existing_prompt.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Only the creator can delete this prompt")

        await db.delete(existing_prompt)
        await db.commit()

        logger.info(f"Deleted prompt: {prompt_id} by user {current_user.username}")
        return {"success": True, "message": "Prompt deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts/{prompt_id}/rate", response_model=PromptRatingResponse)
async def rate_prompt(
    prompt_id: UUID,
    rating_data: PromptRatingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Rate a prompt (1-5 stars)"""
    try:
        # Check if prompt exists
        prompt_result = await db.execute(
            select(PromptLibrary).where(PromptLibrary.id == prompt_id)
        )
        prompt = prompt_result.scalar_one_or_none()

        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        # Check if user already rated
        existing_rating_result = await db.execute(
            select(PromptRating).where(
                and_(
                    PromptRating.prompt_id == prompt_id,
                    PromptRating.user_id == current_user.id
                )
            )
        )
        existing_rating = existing_rating_result.scalar_one_or_none()

        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating_data.rating
            existing_rating.feedback = rating_data.feedback
            rating = existing_rating
        else:
            # Create new rating
            rating = PromptRating(
                prompt_id=prompt_id,
                user_id=current_user.id,
                rating=rating_data.rating,
                feedback=rating_data.feedback
            )
            db.add(rating)

        await db.commit()

        # Recalculate average rating
        ratings_result = await db.execute(
            select(func.avg(PromptRating.rating), func.count(PromptRating.id)).where(
                PromptRating.prompt_id == prompt_id
            )
        )
        avg_rating, total_ratings = ratings_result.first()

        # Update prompt
        prompt.average_rating = float(avg_rating or 0.0)
        prompt.total_ratings = total_ratings or 0
        await db.commit()

        await db.refresh(rating)

        logger.info(f"User {current_user.username} rated prompt {prompt_id}: {rating_data.rating}/5")
        return PromptRatingResponse(**rating.__dict__)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error rating prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts/{prompt_id}/use")
async def log_prompt_usage(
    prompt_id: UUID,
    usage_data: PromptUsageCreate,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Log prompt usage for analytics"""
    try:
        # Check if prompt exists
        prompt_result = await db.execute(
            select(PromptLibrary).where(PromptLibrary.id == prompt_id)
        )
        prompt = prompt_result.scalar_one_or_none()

        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")

        # Create usage log
        usage_log = PromptUsageLog(
            prompt_id=prompt_id,
            user_id=current_user.id if current_user else None,
            **usage_data.model_dump()
        )
        db.add(usage_log)

        # Increment usage count and update last_used_at
        prompt.usage_count += 1
        prompt.last_used_at = func.now()

        await db.commit()

        logger.info(f"Logged usage for prompt {prompt_id}")
        return {"success": True, "message": "Usage logged successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error logging prompt usage {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# OUTPUT TEMPLATES ENDPOINTS
# ============================================================================

@router.get("/templates", response_model=OutputTemplateListResponse)
async def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    template_type: Optional[str] = None,
    is_public: Optional[bool] = None,
    project_id: Optional[UUID] = None,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List output templates with filtering"""
    try:
        filters = []

        if template_type:
            filters.append(OutputTemplate.template_type == template_type)
        if project_id:
            filters.append(OutputTemplate.project_id == project_id)

        # Public templates or user's own templates
        if current_user:
            visibility_filter = or_(
                OutputTemplate.is_public == True,
                OutputTemplate.created_by == current_user.id
            )
        else:
            visibility_filter = OutputTemplate.is_public == True

        if is_public is not None:
            filters.append(OutputTemplate.is_public == is_public)

        filters.append(visibility_filter)

        # Count total
        count_query = select(func.count(OutputTemplate.id)).where(and_(*filters))
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Build query
        query = select(OutputTemplate).where(and_(*filters))
        query = query.order_by(OutputTemplate.created_at.desc())

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Load relationships
        query = query.options(
            selectinload(OutputTemplate.creator),
            selectinload(OutputTemplate.project),
            selectinload(OutputTemplate.department)
        )

        result = await db.execute(query)
        templates = result.scalars().all()

        # Convert to response
        template_responses = []
        for template in templates:
            template_dict = {
                **template.__dict__,
                "creator_username": template.creator.username if template.creator else None,
                "project_name": template.project.name if template.project else None,
                "department_name": template.department.name if template.department else None
            }
            template_responses.append(OutputTemplateResponse(**template_dict))

        return OutputTemplateListResponse(
            templates=template_responses,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}", response_model=OutputTemplateResponse)
async def get_template(
    template_id: UUID,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific output template"""
    try:
        query = select(OutputTemplate).where(OutputTemplate.id == template_id).options(
            selectinload(OutputTemplate.creator),
            selectinload(OutputTemplate.project),
            selectinload(OutputTemplate.department)
        )
        result = await db.execute(query)
        template = result.scalar_one_or_none()

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Check access
        if not template.is_public and (not current_user or template.created_by != current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")

        template_dict = {
            **template.__dict__,
            "creator_username": template.creator.username if template.creator else None,
            "project_name": template.project.name if template.project else None,
            "department_name": template.department.name if template.department else None
        }

        return OutputTemplateResponse(**template_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates", response_model=OutputTemplateResponse)
async def create_template(
    template: OutputTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new output template"""
    try:
        new_template = OutputTemplate(
            **template.model_dump(),
            created_by=current_user.id,
            department_id=current_user.department_id
        )

        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)

        # Load relationships
        query = select(OutputTemplate).where(OutputTemplate.id == new_template.id).options(
            selectinload(OutputTemplate.creator),
            selectinload(OutputTemplate.project),
            selectinload(OutputTemplate.department)
        )
        result = await db.execute(query)
        created_template = result.scalar_one()

        template_dict = {
            **created_template.__dict__,
            "creator_username": created_template.creator.username if created_template.creator else None,
            "project_name": created_template.project.name if created_template.project else None,
            "department_name": created_template.department.name if created_template.department else None
        }

        logger.info(f"Created template: {new_template.id} by user {current_user.username}")
        return OutputTemplateResponse(**template_dict)

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/templates/{template_id}", response_model=OutputTemplateResponse)
async def update_template(
    template_id: UUID,
    template_update: OutputTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an output template"""
    try:
        result = await db.execute(
            select(OutputTemplate).where(OutputTemplate.id == template_id)
        )
        existing_template = result.scalar_one_or_none()

        if not existing_template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Check ownership
        if existing_template.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Only the creator can update this template")

        # Update fields
        update_data = template_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_template, field, value)

        await db.commit()
        await db.refresh(existing_template)

        # Load relationships
        query = select(OutputTemplate).where(OutputTemplate.id == existing_template.id).options(
            selectinload(OutputTemplate.creator),
            selectinload(OutputTemplate.project),
            selectinload(OutputTemplate.department)
        )
        result = await db.execute(query)
        updated_template = result.scalar_one()

        template_dict = {
            **updated_template.__dict__,
            "creator_username": updated_template.creator.username if updated_template.creator else None,
            "project_name": updated_template.project.name if updated_template.project else None,
            "department_name": updated_template.department.name if updated_template.department else None
        }

        logger.info(f"Updated template: {template_id} by user {current_user.username}")
        return OutputTemplateResponse(**template_dict)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an output template"""
    try:
        result = await db.execute(
            select(OutputTemplate).where(OutputTemplate.id == template_id)
        )
        existing_template = result.scalar_one_or_none()

        if not existing_template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Check ownership
        if existing_template.created_by != current_user.id:
            raise HTTPException(status_code=403, detail="Only the creator can delete this template")

        await db.delete(existing_template)
        await db.commit()

        logger.info(f"Deleted template: {template_id} by user {current_user.username}")
        return {"success": True, "message": "Template deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
