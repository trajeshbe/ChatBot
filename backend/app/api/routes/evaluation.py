"""
API Routes for RAG Evaluation System

Endpoints for:
- Configuring evaluation settings (toggleable metrics)
- Running evaluations on demand
- Retrieving evaluation results and analytics
- Managing human feedback
- Viewing evaluation benchmarks
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as sql_text, select, func
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.services.evaluation_service import evaluation_service, EvaluationMethod, EvaluationConfig as ServiceEvaluationConfig
from app.models.database_enhanced import EvaluationConfig, EvaluationResult, HumanFeedback, EvaluationMetricsBenchmark

router = APIRouter(prefix="/api/v1/evaluation", tags=["evaluation"])


# Pydantic Schemas
class EvaluationConfigCreate(BaseModel):
    """Configuration for evaluation methods"""
    session_id: Optional[str] = None

    # Toggle switches
    enable_ragas: bool = False
    enable_llm_as_judge: bool = False
    enable_deepeval: bool = False
    enable_semantic_similarity: bool = False
    enable_bertscore: bool = False
    enable_citation_accuracy: bool = True
    enable_toxicity: bool = True
    enable_bias_detection: bool = True
    enable_hallucination: bool = True
    enable_answer_relevancy: bool = True
    enable_context_precision: bool = False
    enable_context_recall: bool = False
    enable_faithfulness: bool = True

    # Configuration parameters
    llm_judge_model: str = "gpt-4-turbo-preview"
    use_cache: bool = True
    async_evaluation: bool = True
    batch_size: int = 10
    min_score_threshold: float = 0.7
    cache_ttl_seconds: int = 3600

    # Auto-evaluation
    auto_evaluate: bool = False
    evaluation_sampling_rate: float = 1.0


class EvaluationConfigResponse(BaseModel):
    """Response model for evaluation configuration"""
    id: str
    session_id: Optional[str]
    enabled_methods: List[str]
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvaluationRequest(BaseModel):
    """Request to evaluate a RAG response"""
    query: str
    response: str
    context_chunks: List[Dict[str, Any]]
    ground_truth: Optional[str] = None
    session_id: Optional[str] = None
    use_stored_config: bool = True


class EvaluationResultResponse(BaseModel):
    """Response model for evaluation results"""
    id: Optional[str] = None
    overall_score: float
    scores: Dict[str, Any]
    evaluation_time_ms: float
    enabled_methods: List[str]
    metadata: Dict[str, Any]
    errors: List[Dict[str, str]] = []
    created_at: Optional[datetime] = None


class HumanFeedbackCreate(BaseModel):
    """Human feedback on a response"""
    session_id: Optional[str] = None
    message_id: Optional[str] = None
    evaluation_id: Optional[str] = None

    rating: Optional[int] = Field(None, ge=1, le=5)
    thumbs_up: Optional[bool] = None
    feedback_text: Optional[str] = None

    accuracy_rating: Optional[int] = Field(None, ge=1, le=5)
    helpfulness_rating: Optional[int] = Field(None, ge=1, le=5)
    clarity_rating: Optional[int] = Field(None, ge=1, le=5)

    has_hallucination: bool = False
    has_bias: bool = False
    has_toxicity: bool = False
    is_irrelevant: bool = False

    feedback_type: str = "inline"


class HumanFeedbackResponse(BaseModel):
    """Response model for human feedback"""
    id: str
    rating: Optional[int]
    thumbs_up: Optional[bool]
    feedback_text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationAnalytics(BaseModel):
    """Analytics for evaluation results"""
    total_evaluations: int
    avg_overall_score: float
    avg_scores_by_method: Dict[str, float]
    score_distribution: Dict[str, int]
    common_issues: Dict[str, int]
    time_series: List[Dict[str, Any]]


# API Endpoints

@router.post("/config", response_model=EvaluationConfigResponse)
async def create_evaluation_config(
    config: EvaluationConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create or update evaluation configuration for a session

    Configure which evaluation metrics are enabled and their parameters.
    """
    try:
        # Check if config exists for this session
        if config.session_id:
            query = select(EvaluationConfig).where(
                EvaluationConfig.session_id == config.session_id
            )
            result = await db.execute(query)
            existing_config = result.scalar_one_or_none()

            if existing_config:
                # Update existing config
                for key, value in config.model_dump().items():
                    if key != "session_id" and hasattr(existing_config, key):
                        setattr(existing_config, key, value)
                existing_config.updated_at = datetime.utcnow()
                await db.commit()
                await db.refresh(existing_config)

                eval_config = existing_config
            else:
                # Create new config
                eval_config = EvaluationConfig(**config.model_dump())
                db.add(eval_config)
                await db.commit()
                await db.refresh(eval_config)
        else:
            # Create new config
            eval_config = EvaluationConfig(**config.model_dump())
            db.add(eval_config)
            await db.commit()
            await db.refresh(eval_config)

        # Get enabled methods
        enabled_methods = []
        for method in EvaluationMethod:
            field_name = f"enable_{method.value}"
            if hasattr(eval_config, field_name) and getattr(eval_config, field_name):
                enabled_methods.append(method.value)

        return EvaluationConfigResponse(
            id=str(eval_config.id),
            session_id=str(eval_config.session_id) if eval_config.session_id else None,
            enabled_methods=enabled_methods,
            config=config.model_dump(),
            created_at=eval_config.created_at,
            updated_at=eval_config.updated_at
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create config: {str(e)}")


@router.get("/config/{session_id}", response_model=EvaluationConfigResponse)
async def get_evaluation_config(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get evaluation configuration for a session"""
    try:
        query = select(EvaluationConfig).where(
            EvaluationConfig.session_id == session_id
        )
        result = await db.execute(query)
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")

        # Get enabled methods
        enabled_methods = []
        for method in EvaluationMethod:
            field_name = f"enable_{method.value}"
            if hasattr(config, field_name) and getattr(config, field_name):
                enabled_methods.append(method.value)

        return EvaluationConfigResponse(
            id=str(config.id),
            session_id=str(config.session_id) if config.session_id else None,
            enabled_methods=enabled_methods,
            config={
                "llm_judge_model": config.llm_judge_model,
                "use_cache": config.use_cache,
                "async_evaluation": config.async_evaluation,
                "auto_evaluate": config.auto_evaluate
            },
            created_at=config.created_at,
            updated_at=config.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@router.post("/evaluate", response_model=EvaluationResultResponse)
async def evaluate_response(
    request: EvaluationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluate a RAG response using configured metrics

    Runs all enabled evaluation methods and returns comprehensive scores.
    """
    try:
        # Get evaluation config if session_id provided
        service_config = None
        if request.use_stored_config and request.session_id:
            query = select(EvaluationConfig).where(
                EvaluationConfig.session_id == request.session_id
            )
            result = await db.execute(query)
            config = result.scalar_one_or_none()

            if config:
                # Build enabled methods list
                enabled_methods = []
                for method in EvaluationMethod:
                    field_name = f"enable_{method.value}"
                    if hasattr(config, field_name) and getattr(config, field_name):
                        enabled_methods.append(method)

                service_config = ServiceEvaluationConfig(
                    enabled_methods=enabled_methods,
                    use_cache=config.use_cache,
                    async_evaluation=config.async_evaluation,
                    batch_size=config.batch_size,
                    llm_judge_model=config.llm_judge_model,
                    cache_ttl_seconds=config.cache_ttl_seconds,
                    min_score_threshold=config.min_score_threshold
                )

        # Run evaluation
        result = await evaluation_service.evaluate_response(
            query=request.query,
            response=request.response,
            context_chunks=request.context_chunks,
            ground_truth=request.ground_truth,
            config=service_config,
            db=db
        )

        return EvaluationResultResponse(
            overall_score=result.get('overall_score', 0.0),
            scores=result.get('evaluations', {}),
            evaluation_time_ms=result.get('metadata', {}).get('evaluation_time_ms', 0),
            enabled_methods=result.get('metadata', {}).get('enabled_methods', []),
            metadata=result.get('metadata', {}),
            errors=result.get('errors', [])
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get("/results", response_model=List[EvaluationResultResponse])
async def get_evaluation_results(
    session_id: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get evaluation results with optional filtering

    Filter by session, score threshold, and pagination.
    """
    try:
        query = select(EvaluationResult)

        if session_id:
            query = query.where(EvaluationResult.session_id == session_id)

        if min_score is not None:
            query = query.where(EvaluationResult.overall_score >= min_score)

        query = query.order_by(EvaluationResult.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        results = result.scalars().all()

        return [
            EvaluationResultResponse(
                id=str(r.id),
                overall_score=r.overall_score or 0.0,
                scores=r.scores or {},
                evaluation_time_ms=r.evaluation_time_ms or 0,
                enabled_methods=r.enabled_methods or [],
                metadata=r.metadata or {},
                errors=r.errors or [],
                created_at=r.created_at
            )
            for r in results
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@router.get("/analytics", response_model=EvaluationAnalytics)
async def get_evaluation_analytics(
    session_id: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get evaluation analytics and insights

    Returns aggregated metrics, trends, and common issues.
    """
    try:
        # Build base query
        date_threshold = datetime.utcnow() - timedelta(days=days)
        base_query = select(EvaluationResult).where(
            EvaluationResult.created_at >= date_threshold
        )

        if session_id:
            base_query = base_query.where(EvaluationResult.session_id == session_id)

        # Get all results
        result = await db.execute(base_query)
        results = result.scalars().all()

        if not results:
            return EvaluationAnalytics(
                total_evaluations=0,
                avg_overall_score=0.0,
                avg_scores_by_method={},
                score_distribution={},
                common_issues={},
                time_series=[]
            )

        # Calculate analytics
        total = len(results)
        avg_score = sum(r.overall_score or 0 for r in results) / total

        # Average scores by method
        method_scores = {}
        method_counts = {}

        for r in results:
            scores_dict = r.scores or {}
            for method, method_data in scores_dict.items():
                if isinstance(method_data, dict) and 'scores' in method_data:
                    for score_name, score_value in method_data['scores'].items():
                        if isinstance(score_value, (int, float)) and score_value is not None:
                            key = f"{method}.{score_name}"
                            method_scores[key] = method_scores.get(key, 0) + score_value
                            method_counts[key] = method_counts.get(key, 0) + 1

        avg_scores_by_method = {
            method: method_scores[method] / method_counts[method]
            for method in method_scores
            if method_counts[method] > 0
        }

        # Score distribution
        score_distribution = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0
        }

        for r in results:
            score = r.overall_score or 0
            if score < 0.2:
                score_distribution["0.0-0.2"] += 1
            elif score < 0.4:
                score_distribution["0.2-0.4"] += 1
            elif score < 0.6:
                score_distribution["0.4-0.6"] += 1
            elif score < 0.8:
                score_distribution["0.6-0.8"] += 1
            else:
                score_distribution["0.8-1.0"] += 1

        # Common issues
        common_issues = {
            "hallucination": 0,
            "low_relevancy": 0,
            "bias": 0,
            "toxicity": 0
        }

        for r in results:
            scores_dict = r.scores or {}
            for method, method_data in scores_dict.items():
                if isinstance(method_data, dict) and 'scores' in method_data:
                    scores = method_data['scores']
                    if 'hallucination_score' in scores and scores['hallucination_score'] > 0.3:
                        common_issues["hallucination"] += 1
                    if 'relevancy' in scores and scores['relevancy'] < 0.5:
                        common_issues["low_relevancy"] += 1
                    if 'bias_score' in scores and scores['bias_score'] > 0.2:
                        common_issues["bias"] += 1
                    if 'toxicity' in scores and scores['toxicity'] > 0.2:
                        common_issues["toxicity"] += 1

        # Time series (daily aggregates)
        time_series = []
        results_by_date = {}
        for r in results:
            date_key = r.created_at.date().isoformat()
            if date_key not in results_by_date:
                results_by_date[date_key] = []
            results_by_date[date_key].append(r)

        for date_key in sorted(results_by_date.keys()):
            day_results = results_by_date[date_key]
            avg_day_score = sum(r.overall_score or 0 for r in day_results) / len(day_results)
            time_series.append({
                "date": date_key,
                "avg_score": avg_day_score,
                "count": len(day_results)
            })

        return EvaluationAnalytics(
            total_evaluations=total,
            avg_overall_score=avg_score,
            avg_scores_by_method=avg_scores_by_method,
            score_distribution=score_distribution,
            common_issues=common_issues,
            time_series=time_series
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.post("/feedback", response_model=HumanFeedbackResponse)
async def submit_human_feedback(
    feedback: HumanFeedbackCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit human feedback on a RAG response

    Allows users to provide ratings, thumbs up/down, and detailed feedback.
    """
    try:
        feedback_obj = HumanFeedback(**feedback.model_dump())
        db.add(feedback_obj)
        await db.commit()
        await db.refresh(feedback_obj)

        return HumanFeedbackResponse(
            id=str(feedback_obj.id),
            rating=feedback_obj.rating,
            thumbs_up=feedback_obj.thumbs_up,
            feedback_text=feedback_obj.feedback_text,
            created_at=feedback_obj.created_at
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")


@router.get("/feedback", response_model=List[HumanFeedbackResponse])
async def get_human_feedback(
    session_id: Optional[str] = None,
    evaluation_id: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get human feedback with optional filtering"""
    try:
        query = select(HumanFeedback)

        if session_id:
            query = query.where(HumanFeedback.session_id == session_id)

        if evaluation_id:
            query = query.where(HumanFeedback.evaluation_id == evaluation_id)

        query = query.order_by(HumanFeedback.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        feedbacks = result.scalars().all()

        return [
            HumanFeedbackResponse(
                id=str(f.id),
                rating=f.rating,
                thumbs_up=f.thumbs_up,
                feedback_text=f.feedback_text,
                created_at=f.created_at
            )
            for f in feedbacks
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")


@router.get("/methods", response_model=List[Dict[str, str]])
async def get_available_methods():
    """
    Get list of available evaluation methods

    Returns all supported evaluation methods with descriptions.
    """
    methods = [
        {
            "id": EvaluationMethod.RAGAS.value,
            "name": "RAGAS",
            "description": "Comprehensive RAG evaluation framework (Answer Relevancy, Faithfulness, Context Precision/Recall)",
            "category": "framework",
            "requires_external_lib": True
        },
        {
            "id": EvaluationMethod.LLM_AS_JUDGE.value,
            "name": "LLM-as-a-Judge",
            "description": "Use GPT-4/Claude to evaluate response quality across multiple criteria",
            "category": "llm",
            "requires_external_lib": False
        },
        {
            "id": EvaluationMethod.DEEPEVAL.value,
            "name": "DeepEval",
            "description": "Modern evaluation framework with hallucination detection and contextual metrics",
            "category": "framework",
            "requires_external_lib": True
        },
        {
            "id": EvaluationMethod.SEMANTIC_SIMILARITY.value,
            "name": "Semantic Similarity",
            "description": "Compare response to ground truth using embedding similarity",
            "category": "metric",
            "requires_external_lib": False
        },
        {
            "id": EvaluationMethod.BERTSCORE.value,
            "name": "BERTScore",
            "description": "Semantic text similarity using BERT embeddings",
            "category": "metric",
            "requires_external_lib": True
        },
        {
            "id": EvaluationMethod.CITATION_ACCURACY.value,
            "name": "Citation Accuracy",
            "description": "Evaluate source attribution and grounding in context",
            "category": "metric",
            "requires_external_lib": False
        },
        {
            "id": EvaluationMethod.TOXICITY.value,
            "name": "Toxicity Detection",
            "description": "Detect harmful, offensive, or toxic content",
            "category": "safety",
            "requires_external_lib": False
        },
        {
            "id": EvaluationMethod.BIAS_DETECTION.value,
            "name": "Bias Detection",
            "description": "Identify potential biases in responses",
            "category": "safety",
            "requires_external_lib": False
        },
        {
            "id": EvaluationMethod.HALLUCINATION.value,
            "name": "Hallucination Detection",
            "description": "Detect unsupported claims not grounded in context",
            "category": "safety",
            "requires_external_lib": False
        },
        {
            "id": EvaluationMethod.ANSWER_RELEVANCY.value,
            "name": "Answer Relevancy",
            "description": "Measure how relevant the answer is to the query",
            "category": "metric",
            "requires_external_lib": False
        },
        {
            "id": EvaluationMethod.CONTEXT_PRECISION.value,
            "name": "Context Precision",
            "description": "Measure precision of retrieved context chunks",
            "category": "retrieval",
            "requires_external_lib": False
        },
        {
            "id": EvaluationMethod.CONTEXT_RECALL.value,
            "name": "Context Recall",
            "description": "Measure recall of retrieved context chunks",
            "category": "retrieval",
            "requires_external_lib": False
        },
        {
            "id": EvaluationMethod.FAITHFULNESS.value,
            "name": "Faithfulness",
            "description": "Measure how well the answer is grounded in the context",
            "category": "metric",
            "requires_external_lib": False
        }
    ]

    return methods
