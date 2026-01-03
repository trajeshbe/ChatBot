"""
Module Configuration API Routes

Provides REST endpoints for dynamic configuration management of Tier 2 and Tier 3 modules.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from uuid import UUID

from app.tier_1.infrastructure.database import get_db
from app.models.database_enhanced import User
from app.services.poc_config_service import poc_config_service
from app.schemas.module_config_schemas import (
    ModuleConfigurationCreate,
    ModuleConfigurationUpdate,
    ModuleConfigurationResponse,
    ModuleConfigurationListItem,
    UserOverrideCreate,
    UserOverrideResponse,
    ConfigVersionResponse,
    ConfigTemplateCreate,
    ConfigTemplateResponse,
    ConfigValidationResponse,
    MergedConfigResponse
)

# TODO: Implement get_current_user dependency once auth is set up
async def get_current_user(db: Session = Depends(get_db)) -> User:
    """Placeholder for authentication. Replace with actual implementation."""
    # For now, return a mock user
    # In production, this should validate JWT token and return actual user
    from uuid import uuid4
    class MockUser:
        id = uuid4()
        username = "admin"
        email = "admin@example.com"
        is_admin = True
    return MockUser()


router = APIRouter(prefix="/api/v1/module-config", tags=["Module Configuration"])


# ============================================================================
# Module Configuration Endpoints
# ============================================================================

@router.get("/modules", response_model=List[ModuleConfigurationListItem])
async def list_modules(
    module_type: Optional[str] = Query(None, description="Filter by module type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Show only active modules"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all available modules with basic information.

    **Query Parameters:**
    - module_type: Filter by 'tier2_domain_vertical' or 'tier3_customer_solution'
    - category: Filter by category (e.g., 'procurement', 'hr_talent')
    - active_only: Show only active modules (default: true)
    """
    modules = await poc_config_service.list_modules(
        db=db,
        module_type=module_type,
        category=category,
        active_only=active_only
    )
    return modules


@router.get("/modules/{module_name}", response_model=MergedConfigResponse)
async def get_module_config(
    module_name: str,
    user_id: Optional[str] = Query(None, description="User ID for personalized config"),
    include_overrides: bool = Query(True, description="Include user overrides"),
    include_metadata: bool = Query(False, description="Include resolution metadata"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete configuration for a module with 3-level resolution:
    1. Global defaults
    2. Module-specific configuration
    3. User-specific overrides (if user_id provided)

    **Returns:** Merged configuration with optional metadata about overrides.
    """
    try:
        effective_user_id = user_id or str(current_user.id)

        if include_metadata:
            result = await poc_config_service.get_config_with_metadata(
                db=db,
                module_name=module_name,
                user_id=effective_user_id if include_overrides else None
            )
            return MergedConfigResponse(
                module_name=module_name,
                config=result["config"],
                has_user_overrides=result["has_user_overrides"],
                override_fields=result["override_fields"],
                resolution_order=result["resolution_order"]
            )
        else:
            config = await poc_config_service.get_config(
                db=db,
                module_name=module_name,
                user_id=effective_user_id if include_overrides else None,
                include_overrides=include_overrides
            )
            return MergedConfigResponse(
                module_name=module_name,
                config=config,
                has_user_overrides=False,
                override_fields=[],
                resolution_order=["global_defaults", "module_config"]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


@router.post("/modules", response_model=ModuleConfigurationResponse)
async def create_module_config(
    config_create: ModuleConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new module configuration.

    **Requires:** Admin privileges (not enforced yet)
    """
    try:
        module_config = await poc_config_service.create_module_config(
            db=db,
            module_name=config_create.module_name,
            display_name=config_create.display_name,
            module_type=config_create.module_type,
            config=config_create.config.dict(exclude_none=True),
            description=config_create.description,
            category=config_create.category,
            created_by=current_user.id
        )
        return module_config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create configuration: {str(e)}")


@router.put("/modules/{module_name}", response_model=Dict[str, Any])
async def update_module_config(
    module_name: str,
    config_update: ModuleConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update module configuration (creates new version).

    **Requires:** Admin privileges (not enforced yet)

    **Note:** This creates a new version and preserves full history.
    """
    try:
        updated_config = await poc_config_service.update_module_config(
            db=db,
            module_name=module_name,
            updates=config_update.updates,
            changed_by=current_user.id,
            change_reason=config_update.change_reason
        )
        return {
            "module_name": module_name,
            "config": updated_config,
            "message": "Configuration updated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


# ============================================================================
# User Overrides Endpoints
# ============================================================================

@router.post("/modules/{module_name}/overrides", response_model=Dict[str, Any])
async def set_user_override(
    module_name: str,
    override_create: UserOverrideCreate,
    user_id: Optional[str] = Query(None, description="User ID (defaults to current user)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set user-specific configuration overrides.

    **Use Cases:**
    - A/B testing different prompts
    - Personalized parameters
    - Customer-specific tuning
    """
    try:
        effective_user_id = UUID(user_id) if user_id else current_user.id

        # Only allow users to override their own config (unless admin)
        if str(effective_user_id) != str(current_user.id) and not getattr(current_user, 'is_admin', False):
            raise HTTPException(
                status_code=403,
                detail="You can only modify your own configuration overrides"
            )

        overrides = await poc_config_service.set_user_override(
            db=db,
            module_name=module_name,
            user_id=effective_user_id,
            overrides=override_create.overrides,
            variant_name=override_create.variant_name,
            experiment_id=override_create.experiment_id
        )

        return {
            "module_name": module_name,
            "user_id": str(effective_user_id),
            "overrides": overrides,
            "message": "User overrides set successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set overrides: {str(e)}")


@router.delete("/modules/{module_name}/overrides", response_model=Dict[str, str])
async def clear_user_override(
    module_name: str,
    user_id: Optional[str] = Query(None, description="User ID (defaults to current user)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clear user-specific overrides (revert to module defaults).
    """
    try:
        effective_user_id = UUID(user_id) if user_id else current_user.id

        # Only allow users to clear their own overrides (unless admin)
        if str(effective_user_id) != str(current_user.id) and not getattr(current_user, 'is_admin', False):
            raise HTTPException(
                status_code=403,
                detail="You can only clear your own configuration overrides"
            )

        success = await poc_config_service.clear_user_override(
            db=db,
            module_name=module_name,
            user_id=effective_user_id
        )

        if success:
            return {
                "status": "success",
                "message": f"User overrides cleared for module '{module_name}'"
            }
        else:
            return {
                "status": "not_found",
                "message": "No overrides found to clear"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear overrides: {str(e)}")


# ============================================================================
# Version Management Endpoints
# ============================================================================

@router.get("/modules/{module_name}/versions", response_model=List[Dict[str, Any]])
async def get_config_versions(
    module_name: str,
    limit: int = Query(10, ge=1, le=100, description="Number of versions to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get version history for module configuration.

    **Returns:** List of versions (newest first) with change metadata.
    """
    try:
        versions = await poc_config_service.get_versions(
            db=db,
            module_name=module_name,
            limit=limit
        )
        return versions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get versions: {str(e)}")


@router.post("/modules/{module_name}/versions/{version}/restore", response_model=Dict[str, Any])
async def restore_version(
    module_name: str,
    version: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Restore a previous configuration version.

    **Requires:** Admin privileges (not enforced yet)

    **Note:** Creates a new version with the restored configuration.
    """
    try:
        restored_config = await poc_config_service.restore_version(
            db=db,
            module_name=module_name,
            version=version,
            changed_by=current_user.id
        )
        return {
            "module_name": module_name,
            "restored_from_version": version,
            "config": restored_config,
            "message": f"Configuration restored from version {version}"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore version: {str(e)}")


# ============================================================================
# Template Management Endpoints
# ============================================================================

@router.get("/templates", response_model=List[Dict[str, Any]])
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    module_type: Optional[str] = Query(None, description="Filter by module type"),
    public_only: bool = Query(True, description="Show only public templates"),
    db: Session = Depends(get_db)
):
    """
    List available configuration templates.

    **Use Cases:**
    - Quick setup for new modules
    - Industry best practices
    - Pre-configured common scenarios
    """
    try:
        templates = await poc_config_service.list_templates(
            db=db,
            category=category,
            module_type=module_type,
            public_only=public_only
        )
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")


@router.post("/modules/{module_name}/from-template", response_model=ModuleConfigurationResponse)
async def create_from_template(
    module_name: str,
    template_name: str = Query(..., description="Name of the template to use"),
    overrides: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new module configuration from a template.

    **Requires:** Admin privileges (not enforced yet)

    **Optional:** Provide overrides to customize the template.
    """
    try:
        module_config = await poc_config_service.create_from_template(
            db=db,
            module_name=module_name,
            template_name=template_name,
            overrides=overrides,
            created_by=current_user.id
        )
        return module_config
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create from template: {str(e)}")


# ============================================================================
# Validation Endpoints
# ============================================================================

@router.post("/modules/{module_name}/validate", response_model=ConfigValidationResponse)
async def validate_config(
    module_name: str,
    config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Validate configuration against schema without saving.

    **Use Cases:**
    - Pre-validation before saving
    - Testing configuration changes
    - UI validation feedback
    """
    try:
        is_valid, errors = await poc_config_service.validate_config(
            db=db,
            module_name=module_name,
            config=config
        )
        return ConfigValidationResponse(
            valid=is_valid,
            errors=errors,
            warnings=[]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


# ============================================================================
# Utility Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "module-configuration",
        "version": "1.0.0"
    }


@router.get("/categories")
async def list_categories(db: Session = Depends(get_db)):
    """List all available module categories"""
    # This could be enhanced to query from database
    return {
        "tier2_categories": [
            "procurement",
            "hr_talent",
            "agriculture",
            "analytics",
            "construction",
            "document_intelligence",
            "ecommerce",
            "industry_verticals",
            "maritime",
            "marketing",
            "advanced_capabilities"
        ],
        "tier3_categories": [
            "education",
            "mining",
            "automotive",
            "insurance",
            "construction_monitoring"
        ]
    }


@router.get("/module-types")
async def list_module_types():
    """List available module types"""
    return {
        "module_types": [
            {
                "value": "tier2_domain_vertical",
                "label": "Tier 2 - Domain Vertical",
                "description": "General-purpose industry vertical modules"
            },
            {
                "value": "tier3_customer_solution",
                "label": "Tier 3 - Customer Solution",
                "description": "Customer-specific POC implementations"
            }
        ]
    }
