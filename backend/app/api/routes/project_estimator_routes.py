"""
Project Estimator API Routes

REST endpoints for the agentic project estimation workflow.
"""

import json
import logging
import os
import tempfile
from typing import List, Optional, Tuple
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

    # Optional: Model selection (from UI dropdown or Model Registry)
    model_id: Optional[str] = Form(None, description="LLM model to use (e.g., 'gpt-4', 'llama3.2-vision:11b')"),

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
        # 3. DETERMINE MODEL SELECTION
        # ====================================================================

        # If no model_id provided, use Model Registry to get recommended model
        if not model_id:
            try:
                from app.models.model_registry import get_model_registry
                registry = get_model_registry()
                recommended_model = registry.get_recommended_model()
                model_id = recommended_model.model_path if recommended_model else "gpt-4"
                logger.info(f"No model specified, using recommended: {model_id}")
            except Exception as e:
                logger.warning(f"Model Registry unavailable: {e}, defaulting to gpt-4")
                model_id = "gpt-4"
        else:
            logger.info(f"User selected model: {model_id}")

        # ====================================================================
        # 4. INITIALIZE WORKFLOW
        # ====================================================================

        # Initialize LLM service (no parameters needed)
        llm_service = LLMService()
        await llm_service.initialize()  # Initialize async clients

        # Initialize workflow
        workflow = ProjectEstimatorWorkflow(llm_service=llm_service, db=db)

        # ====================================================================
        # 5. BUILD INITIAL STATE
        # ====================================================================

        initial_state = {
            # User input
            "user_prompt": project_scope,
            "project_type": project_type,
            "scenario": scenario,
            "model_id": model_id,  # ← Add model selection to state

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
        # 6. EXECUTE WORKFLOW
        # ====================================================================

        logger.info(f"Starting agentic workflow execution with model: {model_id}...")

        final_state = await workflow.run(initial_state)

        logger.info(f"Workflow completed in {final_state['processing_time']:.2f}s")

        # ====================================================================
        # 5.5. SAVE WORKFLOW STATE (Phase 6)
        # ====================================================================

        # Extract timestamp from BRD filename to use as job_id
        brd_path = final_state.get("brd_path", "")
        if brd_path:
            # Extract timestamp from filename (e.g., BRD_20251126_123456.docx)
            import re
            match = re.search(r'BRD_(\d+)\.docx', os.path.basename(brd_path))
            if match:
                job_id = match.group(1)

                # Save workflow state to JSON file
                state_file_path = f"/app/uploads/project_estimator/state_{job_id}.json"
                try:
                    os.makedirs(os.path.dirname(state_file_path), exist_ok=True)
                    with open(state_file_path, 'w') as f:
                        json.dump(final_state, f, indent=2, default=str)
                    logger.info(f"Workflow state saved to {state_file_path}")
                except Exception as e:
                    logger.error(f"Failed to save workflow state: {str(e)}")

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

        # Convert file paths to download URLs
        brd_path = final_state.get("brd_path", "")
        excel_path = final_state.get("excel_path", "")

        brd_url = ""
        excel_url = ""

        if brd_path:
            filename = os.path.basename(brd_path)
            brd_url = f"/api/v1/project-estimator/download/{filename}"

        if excel_path:
            filename = os.path.basename(excel_path)
            excel_url = f"/api/v1/project-estimator/download/{filename}"

        response = {
            "success": True,
            "message": "Project estimation completed successfully",

            # Generated files (download URLs)
            "brd_url": brd_url,
            "excel_url": excel_url,

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
        llm_service = LLMService()
        await llm_service.initialize()

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


@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download generated files (BRD.docx or CostEstimate.xlsx).
    """
    from fastapi.responses import FileResponse
    import os

    # Security: only allow specific file patterns
    if not (filename.startswith("BRD_") or filename.startswith("CostEstimate_")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid filename"
        )

    # Look in persistent uploads directory
    file_path = f"/app/uploads/project_estimator/{filename}"

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Determine content type
    if filename.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif filename.endswith(".pptx"):
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    elif filename.endswith(".xlsx"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


# ============================================================================
# PHASE 6: EDA REPORT DOWNLOAD ENDPOINTS
# ============================================================================

@router.get("/{job_id}/eda-report")
async def get_eda_report_json(job_id: str):
    """
    Download EDA report as JSON.

    Returns the complete EDA report and recommended tech stack from a
    completed project estimation workflow.

    Args:
        job_id: The timestamp-based job ID (matches BRD/Excel filename timestamp)

    Returns:
        JSON containing:
        - eda_report: Full exploratory data analysis
        - recommended_tech_stack: AI/ML tools recommendations
        - consensus_analysis: Alignment validation from Agent 1.2
        - generated_at: Timestamp
    """
    import os
    import json

    try:
        # The job_id is the timestamp from the filename
        # Look for the corresponding state file
        state_file_path = f"/app/uploads/project_estimator/state_{job_id}.json"

        if not os.path.exists(state_file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"EDA report not found for job_id: {job_id}. Workflow state may not have been saved."
            )

        # Load workflow state
        with open(state_file_path, 'r') as f:
            workflow_state = json.load(f)

        # Extract EDA-related data
        complexity_analysis = workflow_state.get("complexity_analysis", {})
        eda_report = complexity_analysis.get("eda_report")
        recommended_tech_stack = complexity_analysis.get("recommended_tech_stack")
        consensus_analysis = workflow_state.get("consensus_analysis", {})

        if not eda_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No EDA report found in workflow state. Sample files may not have been uploaded."
            )

        response = {
            "job_id": job_id,
            "eda_report": eda_report,
            "recommended_tech_stack": recommended_tech_stack,
            "consensus_analysis": consensus_analysis,
            "generated_at": workflow_state.get("timestamp", ""),
            "project_type": workflow_state.get("project_type", ""),
            "metadata": {
                "total_files_analyzed": eda_report.get("total_files_analyzed", 0),
                "domain": eda_report.get("domain", "Unknown"),
                "overall_data_quality": eda_report.get("overall_data_quality", 0),
                "total_data_volume_mb": eda_report.get("total_data_volume_mb", 0)
            }
        }

        logger.info(f"EDA report retrieved for job_id: {job_id}")
        return response

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"EDA report not found for job_id: {job_id}"
        )
    except Exception as e:
        logger.error(f"Error retrieving EDA report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve EDA report: {str(e)}"
        )


@router.get("/{job_id}/eda-report/excel")
async def get_eda_report_excel(job_id: str):
    """
    Download EDA report as Excel file.

    Generates an Excel file with multiple sheets containing:
    - Sheet 1: Summary Metrics
    - Sheet 2: Detailed File Analysis
    - Sheet 3: Recommended Tech Stack
    - Sheet 4: Consensus Analysis (Agent 1.2)

    Args:
        job_id: The timestamp-based job ID

    Returns:
        Excel file download
    """
    import os
    import json
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill
    from fastapi.responses import FileResponse
    import tempfile

    try:
        # Load workflow state
        state_file_path = f"/app/uploads/project_estimator/state_{job_id}.json"

        if not os.path.exists(state_file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"EDA report not found for job_id: {job_id}"
            )

        with open(state_file_path, 'r') as f:
            workflow_state = json.load(f)

        complexity_analysis = workflow_state.get("complexity_analysis", {})
        eda_report = complexity_analysis.get("eda_report")
        recommended_tech_stack = complexity_analysis.get("recommended_tech_stack")
        consensus_analysis = workflow_state.get("consensus_analysis", {})

        if not eda_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No EDA report found in workflow state"
            )

        # Create Excel workbook
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Remove default sheet

        # Define styles
        header_font = Font(bold=True, size=12)
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")

        # ====================================================================
        # SHEET 1: Summary Metrics
        # ====================================================================
        ws1 = wb.create_sheet("Summary Metrics")

        ws1.append(["EDA Report - Summary Metrics"])
        ws1.append([])
        ws1.append(["Metric", "Value"])

        ws1.append(["Files Analyzed", eda_report.get("total_files_analyzed", 0)])
        ws1.append(["Domain Detected", eda_report.get("domain", "Unknown")])
        ws1.append(["Overall Data Quality", f"{eda_report.get('overall_data_quality', 0):.2%}"])
        ws1.append(["Total Data Volume (MB)", f"{eda_report.get('total_data_volume_mb', 0):.2f}"])
        ws1.append([])

        ws1.append(["Detected Data Types"])
        for data_type in eda_report.get("detected_data_types", []):
            ws1.append(["", data_type])

        ws1.append([])
        ws1.append(["Key Insights"])
        for insight in eda_report.get("insights", [])[:10]:
            ws1.append(["", insight])

        # Style header
        for cell in ws1[1]:
            cell.font = header_font

        # ====================================================================
        # SHEET 2: Detailed File Analysis
        # ====================================================================
        ws2 = wb.create_sheet("File Analysis")

        ws2.append(["Detailed File Analysis"])
        ws2.append([])

        files_analysis = eda_report.get("files_analysis", [])
        for i, file_data in enumerate(files_analysis, 1):
            ws2.append([f"File {i}: {file_data.get('file_type', 'Unknown').upper()}"])
            ws2.append(["File Size (MB)", f"{file_data.get('file_size_mb', 0):.2f}"])

            # File-type specific details
            if file_data.get("file_type") == "excel":
                ws2.append(["Sheets", file_data.get("sheets", 0)])
                ws2.append(["Total Rows", file_data.get("total_rows", 0)])
                ws2.append(["Total Columns", file_data.get("total_columns", 0)])
                ws2.append(["Data Quality", f"{file_data.get('overall_data_quality', 0):.2%}"])

            elif file_data.get("file_type") == "pdf":
                ws2.append(["Pages", file_data.get("total_pages", 0)])
                ws2.append(["Document Type", file_data.get("document_type", "Unknown")])

            elif file_data.get("file_type") == "image":
                ws2.append(["Format", file_data.get("image_format", "Unknown")])

            ws2.append([])

        # ====================================================================
        # SHEET 3: Recommended Tech Stack
        # ====================================================================
        ws3 = wb.create_sheet("Tech Stack")

        ws3.append(["Recommended AI/ML Tech Stack"])
        ws3.append([])

        if recommended_tech_stack:
            # Primary Tools
            ws3.append(["Primary Tools by Data Type"])
            ws3.append([])

            primary_tools = recommended_tech_stack.get("primary_tools", {})
            for data_type, tools_dict in primary_tools.items():
                ws3.append([f"Data Type: {data_type}"])
                for category, tools_list in tools_dict.items():
                    if isinstance(tools_list, list):
                        ws3.append([f"  {category}:"])
                        for tool in tools_list[:5]:  # Top 5
                            ws3.append(["", "", tool])
                ws3.append([])

            # ChatBot Tools
            ws3.append(["ChatBot Platform Capabilities"])
            ws3.append([])

            chatbot_tools = recommended_tech_stack.get("chatbot_tools", {})
            for category, tools_list in chatbot_tools.items():
                ws3.append([category])
                if isinstance(tools_list, list):
                    for tool in tools_list:
                        if isinstance(tool, dict):
                            ws3.append(["", tool.get("name", ""), tool.get("description", "")])
                        else:
                            ws3.append(["", tool])
                ws3.append([])

            # Use Cases
            ws3.append(["Recommended Use Cases"])
            ws3.append([])
            for use_case in recommended_tech_stack.get("use_cases", [])[:10]:
                ws3.append(["", use_case])

        # ====================================================================
        # SHEET 4: Consensus Analysis (Agent 1.2)
        # ====================================================================
        ws4 = wb.create_sheet("Consensus Analysis")

        ws4.append(["Consensus Analysis (Agent 1.2 - Debate Coordinator)"])
        ws4.append([])

        if consensus_analysis:
            ws4.append(["Metric", "Value"])
            ws4.append(["Alignment Score", f"{consensus_analysis.get('alignment_score', 0)}/100"])
            ws4.append(["Status", consensus_analysis.get("status", "UNKNOWN")])
            ws4.append(["Requires Clarification", consensus_analysis.get("requires_clarification", False)])
            ws4.append([])

            ws4.append(["Recommendation"])
            ws4.append([consensus_analysis.get("recommendation", "")])
            ws4.append([])

            issues = consensus_analysis.get("issues", [])
            if issues:
                ws4.append(["Identified Issues"])
                for issue in issues:
                    ws4.append(["", issue])
                ws4.append([])

            # Clarification (if second LLM call was triggered)
            clarification = consensus_analysis.get("clarification")
            if clarification:
                ws4.append(["Detailed Clarification (2nd LLM Call)"])
                ws4.append([])

                specific_actions = clarification.get("specific_actions", [])
                if specific_actions:
                    ws4.append(["Specific Actions"])
                    for action in specific_actions:
                        ws4.append(["", action])
                    ws4.append([])

                alt_approach = clarification.get("alternative_approach")
                if alt_approach:
                    ws4.append(["Alternative Approach"])
                    ws4.append([alt_approach])
        else:
            ws4.append(["No consensus analysis available"])

        # ====================================================================
        # SAVE AND RETURN
        # ====================================================================

        # Save to temp file
        temp_dir = tempfile.gettempdir()
        excel_filename = f"EDA_Report_{job_id}.xlsx"
        excel_path = os.path.join(temp_dir, excel_filename)

        wb.save(excel_path)

        logger.info(f"EDA Excel report generated: {excel_path}")

        return FileResponse(
            path=excel_path,
            filename=excel_filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"EDA report not found for job_id: {job_id}"
        )
    except Exception as e:
        logger.error(f"Error generating EDA Excel report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate EDA Excel report: {str(e)}"
        )
