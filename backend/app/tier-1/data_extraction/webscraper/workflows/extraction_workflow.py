"""
LangGraph Data Extraction Workflow

This module defines the main data extraction workflow using LangGraph.
The workflow orchestrates parallel scraping, data extraction, consolidation,
processing, and delivery in a DAG-based flow.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from .workflow_state import WorkflowState, create_initial_state
from .workflow_nodes import ExtractionWorkflowNodes
from .workflow_tools import ProgressTracker, MetricsCollector

logger = logging.getLogger(__name__)


class ExtractionWorkflow:
    """
    Main data extraction workflow orchestrator using LangGraph

    This workflow implements a DAG-based extraction pipeline:
    1. Parse template
    2. Plan extraction
    3. Scrape sources (parallel)
    4. Extract data
    5. Consolidate data
    6. Transform data
    7. Clean data
    8. Deduplicate data
    9. Validate data
    10. Generate output
    11. Deliver results
    12. Finalize
    """

    def __init__(self):
        """Initialize the extraction workflow"""
        self.graph = self._build_workflow_graph()
        self.compiled_graph = self.graph.compile()

    def _build_workflow_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow DAG

        Returns:
            Configured StateGraph
        """
        # Create workflow graph with WorkflowState
        workflow = StateGraph(WorkflowState)

        # Add nodes to the graph
        workflow.add_node("parse_template", ExtractionWorkflowNodes.parse_template_node)
        workflow.add_node("plan_extraction", ExtractionWorkflowNodes.plan_extraction_node)
        workflow.add_node("scrape_sources", ExtractionWorkflowNodes.scrape_sources_node)
        workflow.add_node("extract_data", ExtractionWorkflowNodes.extract_data_node)
        workflow.add_node("consolidate", ExtractionWorkflowNodes.consolidate_node)
        workflow.add_node("transform", ExtractionWorkflowNodes.transform_node)
        workflow.add_node("clean", ExtractionWorkflowNodes.clean_node)
        workflow.add_node("deduplicate", ExtractionWorkflowNodes.deduplicate_node)
        workflow.add_node("validate", ExtractionWorkflowNodes.validate_node)
        workflow.add_node("generate_output", ExtractionWorkflowNodes.generate_output_node)
        workflow.add_node("deliver", ExtractionWorkflowNodes.deliver_node)
        workflow.add_node("finalize", ExtractionWorkflowNodes.finalize_node)

        # Define the workflow flow (DAG)
        workflow.set_entry_point("parse_template")

        # Sequential flow
        workflow.add_edge("parse_template", "plan_extraction")
        workflow.add_edge("plan_extraction", "scrape_sources")
        workflow.add_edge("scrape_sources", "extract_data")
        workflow.add_edge("extract_data", "consolidate")
        workflow.add_edge("consolidate", "transform")
        workflow.add_edge("transform", "clean")
        workflow.add_edge("clean", "deduplicate")
        workflow.add_edge("deduplicate", "validate")
        workflow.add_edge("validate", "generate_output")
        workflow.add_edge("generate_output", "deliver")
        workflow.add_edge("deliver", "finalize")

        # End after finalize
        workflow.add_edge("finalize", END)

        logger.info("Extraction workflow graph built successfully")
        return workflow

    async def run(
        self,
        job_id: str,
        urls: List[str],
        template_id: Optional[str] = None,
        scrape_config: Optional[Dict[str, Any]] = None,
        output_format: str = "excel",
        delivery_method: str = "download",
        delivery_config: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> WorkflowState:
        """
        Execute the extraction workflow

        Args:
            job_id: Unique job identifier
            urls: List of URLs to scrape
            template_id: Optional template ID for structured extraction
            scrape_config: Optional scraping configuration
            output_format: Output format (excel, csv, json, xml, parquet)
            delivery_method: Delivery method (download, email, webhook, s3, database)
            delivery_config: Delivery configuration
            session_id: Optional session ID

        Returns:
            Final workflow state with results
        """
        logger.info(
            f"Starting extraction workflow for job {job_id} with {len(urls)} URLs"
        )

        try:
            # Create initial state
            initial_state = create_initial_state(
                job_id=job_id,
                urls=urls,
                template_id=template_id,
                scrape_config=scrape_config,
                output_format=output_format,
                delivery_method=delivery_method,
                delivery_config=delivery_config,
                session_id=session_id
            )

            # Run the workflow
            start_time = MetricsCollector.start_timer()

            # Execute workflow using LangGraph
            config = RunnableConfig(
                recursion_limit=50,
                configurable={"job_id": job_id}
            )

            # Run the compiled graph
            final_state = await self.compiled_graph.ainvoke(
                initial_state,
                config=config
            )

            # Calculate total duration
            total_duration = MetricsCollector.end_timer(start_time)
            final_state['total_duration_seconds'] = total_duration

            logger.info(
                f"Workflow completed for job {job_id}: "
                f"status={final_state['workflow_status']}, "
                f"duration={total_duration:.2f}s, "
                f"records={final_state['records_extracted']}"
            )

            return final_state

        except Exception as e:
            logger.error(f"Workflow failed for job {job_id}: {str(e)}", exc_info=True)

            # Return error state
            error_state = create_initial_state(
                job_id=job_id,
                urls=urls,
                template_id=template_id,
                output_format=output_format,
                delivery_method=delivery_method
            )
            error_state['workflow_status'] = 'failed'
            error_state['errors'].append({
                'step': 'workflow_execution',
                'error': str(e),
                'timestamp': datetime.utcnow()
            })
            error_state['completed_at'] = datetime.utcnow()

            return error_state

    async def run_with_callbacks(
        self,
        job_id: str,
        urls: List[str],
        template_id: Optional[str] = None,
        scrape_config: Optional[Dict[str, Any]] = None,
        output_format: str = "excel",
        delivery_method: str = "download",
        delivery_config: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        progress_callback: Optional[callable] = None,
        error_callback: Optional[callable] = None
    ) -> WorkflowState:
        """
        Execute workflow with progress and error callbacks

        Args:
            job_id: Unique job identifier
            urls: List of URLs to scrape
            template_id: Optional template ID
            scrape_config: Scraping configuration
            output_format: Output format
            delivery_method: Delivery method
            delivery_config: Delivery configuration
            session_id: Optional session ID
            progress_callback: Optional callback for progress updates
            error_callback: Optional callback for error notifications

        Returns:
            Final workflow state
        """
        # TODO: Implement callback mechanism
        # For now, just run the workflow normally
        return await self.run(
            job_id=job_id,
            urls=urls,
            template_id=template_id,
            scrape_config=scrape_config,
            output_format=output_format,
            delivery_method=delivery_method,
            delivery_config=delivery_config,
            session_id=session_id
        )

    def get_workflow_visualization(self) -> str:
        """
        Get a visual representation of the workflow DAG

        Returns:
            Mermaid diagram string
        """
        mermaid = """
        graph TD
            A[Start] --> B[Parse Template]
            B --> C[Plan Extraction]
            C --> D[Scrape Sources - PARALLEL]
            D --> E[Extract Data]
            E --> F[Consolidate Data]
            F --> G[Transform Data]
            G --> H[Clean Data]
            H --> I[Deduplicate Data]
            I --> J[Validate Data]
            J --> K[Generate Output]
            K --> L[Deliver Results]
            L --> M[Finalize]
            M --> N[End]

            style D fill:#90EE90
            style K fill:#FFD700
            style L fill:#87CEEB
        """
        return mermaid


# Convenience function for simple workflow execution
async def extract_data_from_urls(
    urls: List[str],
    job_id: Optional[str] = None,
    template_id: Optional[str] = None,
    output_format: str = "excel",
    delivery_method: str = "download",
    scrape_config: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
) -> WorkflowState:
    """
    Convenience function to extract data from URLs

    Args:
        urls: List of URLs to scrape
        job_id: Optional job ID (auto-generated if not provided)
        template_id: Optional template ID for structured extraction
        output_format: Output format (excel, csv, json, xml, parquet)
        delivery_method: Delivery method (download, email, webhook, s3)
        scrape_config: Optional scraping configuration
        session_id: Optional session ID

    Returns:
        Workflow state with results
    """
    import uuid

    if job_id is None:
        job_id = str(uuid.uuid4())

    workflow = ExtractionWorkflow()

    result = await workflow.run(
        job_id=job_id,
        urls=urls,
        template_id=template_id,
        scrape_config=scrape_config or {},
        output_format=output_format,
        delivery_method=delivery_method,
        session_id=session_id
    )

    return result


# Export main classes
__all__ = [
    'ExtractionWorkflow',
    'extract_data_from_urls'
]
