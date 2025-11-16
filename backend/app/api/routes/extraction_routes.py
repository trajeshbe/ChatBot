"""
Extraction Workflow API Routes

Provides API endpoints for the Phase 3 LangGraph extraction workflow.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import uuid
import logging

from app.services.webscraper.workflows import ExtractionWorkflow, extract_data_from_urls

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/extraction", tags=["Data Extraction"])

# In-memory job storage (replace with database in production)
jobs_store: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# Request/Response Models
# ============================================================================

class ExtractionJobRequest(BaseModel):
    """Request to create an extraction job"""
    urls: List[str] = Field(..., min_items=1, max_items=100, description="URLs to scrape")
    template_id: Optional[str] = Field(None, description="Template ID for structured extraction")
    output_format: Literal['excel', 'csv', 'json', 'xml', 'parquet'] = Field('excel', description="Output format")
    delivery_method: Literal['download', 'email', 'webhook', 'storage'] = Field('download', description="Delivery method")
    delivery_config: Optional[Dict[str, Any]] = Field(None, description="Delivery configuration")
    scrape_config: Optional[Dict[str, Any]] = Field(None, description="Scraping configuration")
    session_id: Optional[str] = Field(None, description="Session ID for document association")


class ExtractionJobResponse(BaseModel):
    """Response with job details"""
    job_id: str
    status: str
    created_at: datetime
    urls_count: int
    output_format: str
    delivery_method: str


class ExtractionJobStatusResponse(BaseModel):
    """Detailed job status"""
    job_id: str
    status: str
    current_step: str
    progress_percentage: float
    urls_total: int
    urls_processed: int
    successful_scrapes: int
    failed_scrapes: int
    records_extracted: int
    quality_score: float
    output_file_path: Optional[str]
    delivery_success: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]
    total_duration_seconds: Optional[float]


class ExtractionJobResultResponse(BaseModel):
    """Job result with download link"""
    job_id: str
    status: str
    output_file_path: Optional[str]
    output_file_size: Optional[int]
    records_extracted: int
    quality_score: float
    download_url: Optional[str]


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/jobs", response_model=ExtractionJobResponse)
async def create_extraction_job(
    request: ExtractionJobRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new extraction job

    This endpoint creates a new data extraction job that will:
    1. Scrape the provided URLs in parallel
    2. Extract structured data (if template provided)
    3. Process and validate the data
    4. Generate output in the requested format
    5. Deliver via the specified method

    Example:
    ```json
    {
        "urls": [
            "https://example.com/page1",
            "https://example.com/page2"
        ],
        "output_format": "excel",
        "delivery_method": "download",
        "scrape_config": {
            "compliance_level": "balanced",
            "max_concurrent_requests": 5
        }
    }
    ```
    """
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())

        # Store initial job info
        jobs_store[job_id] = {
            'job_id': job_id,
            'status': 'pending',
            'created_at': datetime.utcnow(),
            'urls_count': len(request.urls),
            'output_format': request.output_format,
            'delivery_method': request.delivery_method,
            'current_step': 'pending',
            'progress_percentage': 0.0
        }

        # Run workflow in background
        background_tasks.add_task(
            run_extraction_workflow,
            job_id=job_id,
            urls=request.urls,
            template_id=request.template_id,
            output_format=request.output_format,
            delivery_method=request.delivery_method,
            delivery_config=request.delivery_config or {},
            scrape_config=request.scrape_config or {},
            session_id=request.session_id
        )

        logger.info(f"Created extraction job {job_id} for {len(request.urls)} URLs")

        return ExtractionJobResponse(
            job_id=job_id,
            status='pending',
            created_at=jobs_store[job_id]['created_at'],
            urls_count=len(request.urls),
            output_format=request.output_format,
            delivery_method=request.delivery_method
        )

    except Exception as e:
        logger.error(f"Error creating extraction job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=ExtractionJobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get job status and progress

    Returns detailed information about the job including:
    - Current status and step
    - Progress percentage
    - URLs processed
    - Records extracted
    - Quality score
    - Errors and warnings
    """
    try:
        if job_id not in jobs_store:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        job = jobs_store[job_id]

        return ExtractionJobStatusResponse(
            job_id=job['job_id'],
            status=job.get('status', 'unknown'),
            current_step=job.get('current_step', 'unknown'),
            progress_percentage=job.get('progress_percentage', 0.0),
            urls_total=job.get('urls_count', 0),
            urls_processed=job.get('successful_scrapes', 0) + job.get('failed_scrapes', 0),
            successful_scrapes=job.get('successful_scrapes', 0),
            failed_scrapes=job.get('failed_scrapes', 0),
            records_extracted=job.get('records_extracted', 0),
            quality_score=job.get('quality_score', 0.0),
            output_file_path=job.get('output_file_path'),
            delivery_success=job.get('delivery_success', False),
            errors=job.get('errors', []),
            warnings=job.get('warnings', []),
            started_at=job.get('started_at', job['created_at']),
            completed_at=job.get('completed_at'),
            total_duration_seconds=job.get('total_duration_seconds')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/result", response_model=ExtractionJobResultResponse)
async def get_job_result(job_id: str):
    """
    Get job result with download link

    Returns the final result of the extraction job including
    the output file path and download URL.
    """
    try:
        if job_id not in jobs_store:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        job = jobs_store[job_id]

        if job.get('status') not in ['completed', 'completed_with_errors']:
            raise HTTPException(
                status_code=400,
                detail=f"Job is not completed yet. Current status: {job.get('status')}"
            )

        download_url = None
        if job.get('output_file_path'):
            # In production, this would be a signed URL or proper download endpoint
            download_url = f"/api/v1/extraction/jobs/{job_id}/download"

        return ExtractionJobResultResponse(
            job_id=job['job_id'],
            status=job.get('status', 'unknown'),
            output_file_path=job.get('output_file_path'),
            output_file_size=job.get('output_file_size'),
            records_extracted=job.get('records_extracted', 0),
            quality_score=job.get('quality_score', 0.0),
            download_url=download_url
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job result: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/download")
async def download_job_result(job_id: str):
    """
    Download the extraction result file

    Returns the generated output file for download.
    """
    try:
        if job_id not in jobs_store:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        job = jobs_store[job_id]

        if not job.get('output_file_path'):
            raise HTTPException(status_code=404, detail="Output file not found")

        from fastapi.responses import FileResponse
        import os

        file_path = job['output_file_path']

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Output file not found on disk")

        # Get filename and media type
        filename = os.path.basename(file_path)

        # Determine media type based on extension
        media_types = {
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.parquet': 'application/octet-stream'
        }

        ext = os.path.splitext(filename)[1].lower()
        media_type = media_types.get(ext, 'application/octet-stream')

        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job and its results

    Removes the job from storage and deletes the output file.
    """
    try:
        if job_id not in jobs_store:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        job = jobs_store[job_id]

        # Delete output file if exists
        if job.get('output_file_path'):
            import os
            try:
                if os.path.exists(job['output_file_path']):
                    os.remove(job['output_file_path'])
            except Exception as e:
                logger.warning(f"Could not delete output file: {str(e)}")

        # Remove from store
        del jobs_store[job_id]

        logger.info(f"Deleted job {job_id}")

        return {"message": f"Job {job_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[ExtractionJobResponse])
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 100
):
    """
    List all extraction jobs

    Optionally filter by status and limit results.
    """
    try:
        jobs = list(jobs_store.values())

        # Filter by status if provided
        if status:
            jobs = [j for j in jobs if j.get('status') == status]

        # Sort by created_at descending
        jobs.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)

        # Limit results
        jobs = jobs[:limit]

        return [
            ExtractionJobResponse(
                job_id=job['job_id'],
                status=job.get('status', 'unknown'),
                created_at=job.get('created_at', datetime.utcnow()),
                urls_count=job.get('urls_count', 0),
                output_format=job.get('output_format', 'unknown'),
                delivery_method=job.get('delivery_method', 'unknown')
            )
            for job in jobs
        ]

    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Background Task
# ============================================================================

async def run_extraction_workflow(
    job_id: str,
    urls: List[str],
    template_id: Optional[str],
    output_format: str,
    delivery_method: str,
    delivery_config: Dict[str, Any],
    scrape_config: Dict[str, Any],
    session_id: Optional[str]
):
    """
    Run the extraction workflow in the background

    This function is executed as a background task and updates
    the job status in the jobs_store.
    """
    try:
        logger.info(f"Starting extraction workflow for job {job_id}")

        # Update status
        jobs_store[job_id]['status'] = 'running'
        jobs_store[job_id]['started_at'] = datetime.utcnow()

        # Run workflow
        workflow = ExtractionWorkflow()

        result = await workflow.run(
            job_id=job_id,
            urls=urls,
            template_id=template_id,
            scrape_config=scrape_config,
            output_format=output_format,
            delivery_method=delivery_method,
            delivery_config=delivery_config,
            session_id=session_id
        )

        # Update job with result
        jobs_store[job_id].update({
            'status': result['workflow_status'],
            'current_step': result['current_step'],
            'progress_percentage': result['progress_percentage'],
            'successful_scrapes': result['successful_scrapes'],
            'failed_scrapes': result['failed_scrapes'],
            'records_extracted': result['records_extracted'],
            'quality_score': result['quality_score'],
            'output_file_path': result.get('output_file_path'),
            'output_file_size': result.get('output_file_size'),
            'delivery_success': result.get('delivery_success', False),
            'errors': result.get('errors', []),
            'warnings': result.get('warnings', []),
            'completed_at': result.get('completed_at'),
            'total_duration_seconds': result.get('total_duration_seconds')
        })

        logger.info(
            f"Extraction workflow completed for job {job_id}: "
            f"status={result['workflow_status']}, records={result['records_extracted']}"
        )

    except Exception as e:
        logger.error(f"Error in extraction workflow for job {job_id}: {str(e)}", exc_info=True)

        # Update job with error
        jobs_store[job_id].update({
            'status': 'failed',
            'errors': [{
                'step': 'workflow_execution',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }],
            'completed_at': datetime.utcnow()
        })
