"""
Project Estimator API Routes

REST endpoints for the agentic project estimation workflow.
"""

import json
import logging
import os
import tempfile
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.llm_service import LLMService
from app.agents.project_estimator.workflow import ProjectEstimatorWorkflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/project-estimator", tags=["project-estimator"])


# ============================================================================
# Helper Functions
# ============================================================================

async def save_uploaded_file(upload_file: UploadFile, category: str) -> str:
    """
    Save an uploaded file to a temporary directory.

    Args:
        upload_file: The uploaded file
        category: File category (brd, cost, sample)

    Returns:
        Path to saved file
    """
    # Create temp directory if needed
    temp_dir = os.path.join(tempfile.gettempdir(), "project_estimator", category)
    os.makedirs(temp_dir, exist_ok=True)

    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{upload_file.filename}"
    file_path = os.path.join(temp_dir, filename)

    # Save file
    with open(file_path, "wb") as f:
        content = await upload_file.read()
        f.write(content)

    logger.info(f"Saved {category} file: {file_path}")
    return file_path


def validate_project_type(project_type: str) -> str:
    """Validate project type parameter."""
    valid_types = ["POC", "Staff Augmentation", "Full Service"]
    if project_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project_type. Must be one of: {valid_types}"
        )
    return project_type


def validate_scenario(scenario: str) -> str:
    """Validate scenario parameter."""
    valid_scenarios = ["baseline", "conservative", "aggressive"]
    if scenario not in valid_scenarios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario. Must be one of: {valid_scenarios}"
        )
    return scenario


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/generate-agentic")
async def generate_agentic_estimate(
    # Required: Project description
    project_scope: str = Form(..., description="Project description/prompt"),

    # Required: Project configuration
    project_type: str = Form(..., description="POC, Staff Augmentation, or Full Service"),
    scenario: str = Form(..., description="baseline, conservative, or aggressive"),

    # Required: Rate configuration (JSON string)
    rate_config: str = Form(..., description="JSON object with rate categories and values"),

    # Optional: Overhead configuration
    overhead_config: Optional[str] = Form(None, description="JSON object with overhead percentages"),

    # Optional: File uploads (examples and samples)
    brd_files: List[UploadFile] = File([], description="BRD example files (.pptx, .pdf)"),
    cost_files: List[UploadFile] = File([], description="Cost estimate example files (.xlsx, .csv)"),
    sample_files: List[UploadFile] = File([], description="Sample data files (.json, .csv, .xlsx)"),

    # Database session
    db: Session = Depends(get_db)
):
    """
    Generate project estimation using 6-agent agentic workflow.

    This endpoint accepts:
    - Project description and configuration
    - UI rate configuration (user-controlled rates)
    - Optional example files (BRDs, cost estimates, sample data) to guide LLM

    The workflow executes 6 specialized agents:
    1. Analyst - analyzes examples and extracts requirements
    2. Team Planner - identifies engineering teams
    3. Task Generator - generates project-specific tasks
    4. Workflow Agent - creates execution phases and timeline
    5. Rate Assignment - maps tasks to rate categories
    6. Document Generator - creates BRD.pptx and Excel outputs

    Returns:
    - Generated BRD.pptx download URL
    - Generated CostEstimate.xlsx download URL
    - Workflow summary (phases, milestones, total cost)
    """
    start_time = datetime.utcnow()

    try:
        # ====================================================================
        # 1. VALIDATE INPUT
        # ====================================================================

        logger.info(f"Project Estimator request: {project_scope[:100]}...")

        # Validate project type and scenario
        project_type = validate_project_type(project_type)
        scenario = validate_scenario(scenario)

        # Parse rate configuration
        try:
            rate_config_dict = json.loads(rate_config)
            if not isinstance(rate_config_dict, dict):
                raise ValueError("rate_config must be a JSON object")
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid rate_config JSON: {str(e)}"
            )

        # Parse overhead configuration (optional)
        overhead_config_dict = {}
        if overhead_config:
            try:
                overhead_config_dict = json.loads(overhead_config)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid overhead_config JSON: {str(e)}"
                )

        # ====================================================================
        # 2. SAVE UPLOADED FILES
        # ====================================================================

        logger.info(f"Saving uploaded files: {len(brd_files)} BRDs, {len(cost_files)} costs, {len(sample_files)} samples")

        # Save BRD example files
        brd_file_paths = []
        for brd_file in brd_files:
            if brd_file.filename:
                path = await save_uploaded_file(brd_file, "brd")
                brd_file_paths.append(path)

        # Save cost estimate example files
        cost_file_paths = []
        for cost_file in cost_files:
            if cost_file.filename:
                path = await save_uploaded_file(cost_file, "cost")
                cost_file_paths.append(path)

        # Save sample data files
        sample_file_paths = []
        for sample_file in sample_files:
            if sample_file.filename:
                path = await save_uploaded_file(sample_file, "sample")
                sample_file_paths.append(path)

        logger.info(f"Files saved: {len(brd_file_paths)} BRDs, {len(cost_file_paths)} costs, {len(sample_file_paths)} samples")

        # ====================================================================
        # 3. INITIALIZE WORKFLOW
        # ====================================================================

        # Initialize LLM service
        llm_service = LLMService(db)

        # Initialize workflow
        workflow = ProjectEstimatorWorkflow(llm_service=llm_service, db=db)

        # ====================================================================
        # 4. BUILD INITIAL STATE
        # ====================================================================

        initial_state = {
            # User input
            "user_prompt": project_scope,
            "project_type": project_type,
            "scenario": scenario,

            # Uploaded files
            "uploaded_brd_files": brd_file_paths,
            "uploaded_cost_files": cost_file_paths,
            "uploaded_sample_data": sample_file_paths,

            # Rate configuration from UI
            "rate_config": rate_config_dict,
            "overhead_config": overhead_config_dict or {"overhead_percentage": 0.15},

            # Initialize empty fields
            "brd_examples_summary": "",
            "cost_examples_summary": "",
            "sample_data_complexity": "",
            "requirements": {},
            "team_plan": {},
            "tasks_by_team": {},
            "project_workflow": {},
            "costs_by_team": {},
            "brd_path": "",
            "excel_path": "",
            "errors": [],
            "processing_time": 0.0,
            "timestamp": start_time.isoformat()
        }

        # ====================================================================
        # 5. EXECUTE WORKFLOW
        # ====================================================================

        logger.info("Starting agentic workflow execution...")

        final_state = await workflow.run(initial_state)

        logger.info(f"Workflow completed in {final_state['processing_time']:.2f}s")

        # ====================================================================
        # 6. CHECK FOR ERRORS
        # ====================================================================

        if final_state.get("errors"):
            logger.error(f"Workflow errors: {final_state['errors']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": "Workflow completed with errors",
                    "errors": final_state["errors"]
                }
            )

        # ====================================================================
        # 7. PREPARE RESPONSE
        # ====================================================================

        # Extract workflow summary
        workflow_summary = final_state.get("project_workflow", {}).get("workflow", {})
        costs_summary = final_state.get("costs_by_team", {}).get("summary", {})

        response = {
            "success": True,
            "message": "Project estimation completed successfully",

            # Generated files
            "brd_url": final_state.get("brd_path", ""),
            "excel_url": final_state.get("excel_path", ""),

            # Summary
            "summary": {
                "project_type": project_type,
                "scenario": scenario,
                "total_cost": costs_summary.get("total_cost", 0),
                "total_hours": costs_summary.get("total_hours", 0),
                "team_count": costs_summary.get("team_count", 0),
                "total_duration_weeks": workflow_summary.get("total_duration_weeks", 0),
                "phases": len(workflow_summary.get("phases", [])),
                "milestones": len(workflow_summary.get("milestones", []))
            },

            # Workflow details
            "workflow": {
                "phases": workflow_summary.get("phases", []),
                "milestones": workflow_summary.get("milestones", [])
            },

            # Teams
            "teams": [
                {
                    "team_name": team["team_name"],
                    "total_cost": team["total_cost"],
                    "total_hours": team["total_hours"]
                }
                for team_name, team in final_state.get("costs_by_team", {}).items()
                if team_name != "summary"
            ],

            # Metadata
            "metadata": {
                "processing_time_seconds": final_state.get("processing_time", 0),
                "timestamp": final_state.get("timestamp", ""),
                "examples_used": {
                    "brd_files": len(brd_file_paths),
                    "cost_files": len(cost_file_paths),
                    "sample_files": len(sample_file_paths)
                }
            }
        }

        logger.info(f"Response prepared: ${costs_summary.get('total_cost', 0):.2f}, {workflow_summary.get('total_duration_weeks', 0)} weeks")

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Project estimation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Project estimation failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for project estimator service.
    """
    return {
        "status": "healthy",
        "service": "project-estimator",
        "agents": 6,
        "workflow": "LangGraph",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/config/project-types")
async def get_project_types():
    """
    Get available project types.
    """
    return {
        "project_types": [
            {
                "value": "POC",
                "label": "Proof of Concept",
                "description": "Quick MVP to validate feasibility (4-8 weeks)"
            },
            {
                "value": "Staff Augmentation",
                "label": "Staff Augmentation",
                "description": "Specific resources/skills for client's project"
            },
            {
                "value": "Full Service",
                "label": "Full Service",
                "description": "Complete end-to-end solution with ongoing support (8-16 weeks)"
            }
        ]
    }


@router.get("/config/scenarios")
async def get_scenarios():
    """
    Get available estimation scenarios.
    """
    return {
        "scenarios": [
            {
                "value": "baseline",
                "label": "Baseline",
                "description": "Standard rates and realistic timelines"
            },
            {
                "value": "conservative",
                "label": "Conservative",
                "description": "Higher rates, buffer time for uncertainties"
            },
            {
                "value": "aggressive",
                "label": "Aggressive",
                "description": "Lower rates, optimistic timelines"
            }
        ]
    }


@router.get("/config/rate-categories")
async def get_rate_categories():
    """
    Get available rate categories with descriptions.
    """
    return {
        "rate_categories": [
            {
                "key": "planning_rate",
                "label": "Planning & Design",
                "description": "Architecture, planning, technical design",
                "typical_range": "$25-40/hour"
            },
            {
                "key": "development_rate",
                "label": "Development",
                "description": "Core software development tasks",
                "typical_range": "$30-50/hour"
            },
            {
                "key": "scraping_development_rate",
                "label": "Scraping Development",
                "description": "Web scraping specific development",
                "typical_range": "$30-45/hour"
            },
            {
                "key": "testing_rate",
                "label": "Testing & QA",
                "description": "Quality assurance and testing",
                "typical_range": "$20-35/hour"
            },
            {
                "key": "devops_rate",
                "label": "DevOps & Infrastructure",
                "description": "Infrastructure, deployment, CI/CD",
                "typical_range": "$35-55/hour"
            },
            {
                "key": "data_engineering_rate",
                "label": "Data Engineering",
                "description": "ETL, data pipelines, databases",
                "typical_range": "$35-50/hour"
            },
            {
                "key": "ml_engineering_rate",
                "label": "ML Engineering",
                "description": "AI/ML model development and deployment",
                "typical_range": "$40-60/hour"
            }
        ]
    }


@router.get("/workflow/visualization")
async def get_workflow_visualization(db: Session = Depends(get_db)):
    """
    Get LangGraph workflow visualization with Mermaid diagram.
    
    Returns:
        - Mermaid diagram for visualization
        - Agent metadata and descriptions
        - Workflow execution flow information
    """
    try:
        # Initialize services
        llm_service = LLMService(db)
        
        # Create workflow instance
        workflow = ProjectEstimatorWorkflow(llm_service=llm_service, db=db)
        
        # Get visualization data
        viz_data = workflow.get_graph_visualization()
        
        return {
            "success": True,
            "visualization": viz_data,
            "usage": {
                "mermaid_live_editor": "https://mermaid.live/",
                "instructions": "Copy the mermaid_diagram to Mermaid Live Editor to visualize"
            }
        }
        
    except Exception as e:
        logger.error(f"Workflow visualization failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Visualization failed: {str(e)}"
        )
