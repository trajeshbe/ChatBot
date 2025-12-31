"""
Enterprise RAG Evaluation Service

Supports state-of-the-art evaluation methods:
- RAGAS (Retrieval-Augmented Generation Assessment)
- LLM-as-a-Judge (GPT-4/Claude evaluators)
- DeepEval framework
- Custom semantic metrics
- Human feedback integration

Features:
- Configurable evaluation toggles
- Async/parallel execution
- Result caching
- Performance metrics
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import logging
import asyncio
import time
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as sql_text

logger = logging.getLogger(__name__)


class EvaluationMethod(str, Enum):
    """Available evaluation methods"""
    RAGAS = "ragas"
    LLM_AS_JUDGE = "llm_as_judge"
    DEEPEVAL = "deepeval"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    BERTSCORE = "bertscore"
    CITATION_ACCURACY = "citation_accuracy"
    TOXICITY = "toxicity"
    BIAS_DETECTION = "bias_detection"
    HALLUCINATION = "hallucination"
    ANSWER_RELEVANCY = "answer_relevancy"
    CONTEXT_PRECISION = "context_precision"
    CONTEXT_RECALL = "context_recall"
    FAITHFULNESS = "faithfulness"


class EvaluationConfig:
    """Configuration for evaluation methods"""

    def __init__(
        self,
        enabled_methods: List[EvaluationMethod] = None,
        use_cache: bool = True,
        async_evaluation: bool = True,
        batch_size: int = 10,
        llm_judge_model: str = "gpt-4-turbo-preview",
        cache_ttl_seconds: int = 3600,
        min_score_threshold: float = 0.7
    ):
        self.enabled_methods = enabled_methods or [
            EvaluationMethod.ANSWER_RELEVANCY,
            EvaluationMethod.FAITHFULNESS,
            EvaluationMethod.CITATION_ACCURACY
        ]
        self.use_cache = use_cache
        self.async_evaluation = async_evaluation
        self.batch_size = batch_size
        self.llm_judge_model = llm_judge_model
        self.cache_ttl_seconds = cache_ttl_seconds
        self.min_score_threshold = min_score_threshold


class EvaluationService:
    """Enterprise RAG Evaluation Service"""

    def __init__(self):
        self.config = EvaluationConfig()
        self._evaluation_cache = {}

    async def evaluate_response(
        self,
        query: str,
        response: str,
        context_chunks: List[Dict],
        ground_truth: Optional[str] = None,
        config: Optional[EvaluationConfig] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive evaluation of RAG response

        Args:
            query: User query
            response: Generated response
            context_chunks: Retrieved context chunks
            ground_truth: Optional ground truth answer for comparison
            config: Evaluation configuration
            db: Database session

        Returns:
            Dictionary with evaluation scores and metrics
        """
        start_time = time.time()
        config = config or self.config

        # Check cache first
        if config.use_cache:
            cache_key = self._get_cache_key(query, response, context_chunks)
            cached_result = await self._check_cache(cache_key, db)
            if cached_result:
                logger.info(f"Evaluation cache hit for query: {query[:50]}...")
                return cached_result

        # Collect evaluation tasks
        evaluation_tasks = []

        for method in config.enabled_methods:
            if method == EvaluationMethod.RAGAS:
                evaluation_tasks.append(
                    self._evaluate_ragas(query, response, context_chunks, ground_truth)
                )
            elif method == EvaluationMethod.LLM_AS_JUDGE:
                evaluation_tasks.append(
                    self._evaluate_llm_as_judge(query, response, context_chunks, config)
                )
            elif method == EvaluationMethod.DEEPEVAL:
                evaluation_tasks.append(
                    self._evaluate_deepeval(query, response, context_chunks)
                )
            elif method == EvaluationMethod.SEMANTIC_SIMILARITY:
                evaluation_tasks.append(
                    self._evaluate_semantic_similarity(response, ground_truth)
                )
            elif method == EvaluationMethod.BERTSCORE:
                evaluation_tasks.append(
                    self._evaluate_bertscore(response, ground_truth)
                )
            elif method == EvaluationMethod.CITATION_ACCURACY:
                evaluation_tasks.append(
                    self._evaluate_citation_accuracy(response, context_chunks)
                )
            elif method == EvaluationMethod.TOXICITY:
                evaluation_tasks.append(
                    self._evaluate_toxicity(response)
                )
            elif method == EvaluationMethod.BIAS_DETECTION:
                evaluation_tasks.append(
                    self._evaluate_bias(response)
                )
            elif method == EvaluationMethod.HALLUCINATION:
                evaluation_tasks.append(
                    self._evaluate_hallucination(response, context_chunks)
                )
            elif method == EvaluationMethod.ANSWER_RELEVANCY:
                evaluation_tasks.append(
                    self._evaluate_answer_relevancy(query, response)
                )
            elif method == EvaluationMethod.CONTEXT_PRECISION:
                evaluation_tasks.append(
                    self._evaluate_context_precision(query, context_chunks)
                )
            elif method == EvaluationMethod.CONTEXT_RECALL:
                evaluation_tasks.append(
                    self._evaluate_context_recall(context_chunks, ground_truth)
                )
            elif method == EvaluationMethod.FAITHFULNESS:
                evaluation_tasks.append(
                    self._evaluate_faithfulness(response, context_chunks)
                )

        # Execute evaluations (async or sequential)
        if config.async_evaluation and len(evaluation_tasks) > 1:
            evaluation_results = await asyncio.gather(*evaluation_tasks, return_exceptions=True)
        else:
            evaluation_results = []
            for task in evaluation_tasks:
                try:
                    result = await task
                    evaluation_results.append(result)
                except Exception as e:
                    evaluation_results.append(e)

        # Aggregate results
        aggregated_results = self._aggregate_results(evaluation_results, config.enabled_methods)

        # Add metadata
        aggregated_results['metadata'] = {
            'query': query[:200],
            'num_contexts': len(context_chunks),
            'response_length': len(response),
            'evaluation_time_ms': (time.time() - start_time) * 1000,
            'enabled_methods': [m.value for m in config.enabled_methods],
            'timestamp': datetime.utcnow().isoformat()
        }

        # Calculate overall score
        aggregated_results['overall_score'] = self._calculate_overall_score(aggregated_results)

        # Cache result
        if config.use_cache and db:
            await self._cache_result(cache_key, aggregated_results, config.cache_ttl_seconds, db)

        # Store in database
        if db:
            await self._store_evaluation(query, response, aggregated_results, db)

        return aggregated_results

    async def _evaluate_ragas(
        self,
        query: str,
        response: str,
        context_chunks: List[Dict],
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        RAGAS (Retrieval-Augmented Generation Assessment) evaluation

        Metrics:
        - Answer Relevancy: How relevant is the answer to the query
        - Faithfulness: Is the answer grounded in the context
        - Context Relevancy: Are the contexts relevant to the query
        - Context Precision: Precision of retrieved contexts
        - Context Recall: Recall of retrieved contexts
        """
        try:
            # Import RAGAS (optional dependency)
            try:
                from ragas import evaluate
                from ragas.metrics import (
                    answer_relevancy,
                    faithfulness,
                    context_precision,
                    context_recall,
                    context_relevancy
                )
                from datasets import Dataset
            except ImportError:
                logger.warning("RAGAS not installed. Install with: pip install ragas")
                return {
                    'method': 'ragas',
                    'error': 'RAGAS not installed',
                    'scores': {}
                }

            # Prepare data for RAGAS
            contexts = [chunk.get('content', '') for chunk in context_chunks]

            data = {
                'question': [query],
                'answer': [response],
                'contexts': [contexts]
            }

            if ground_truth:
                data['ground_truth'] = [ground_truth]

            dataset = Dataset.from_dict(data)

            # Select metrics based on available data
            metrics = [answer_relevancy, faithfulness, context_relevancy]

            if ground_truth:
                metrics.extend([context_precision, context_recall])

            # Run evaluation
            result = evaluate(dataset, metrics=metrics)

            return {
                'method': 'ragas',
                'scores': {
                    'answer_relevancy': result.get('answer_relevancy', 0),
                    'faithfulness': result.get('faithfulness', 0),
                    'context_relevancy': result.get('context_relevancy', 0),
                    'context_precision': result.get('context_precision', 0) if ground_truth else None,
                    'context_recall': result.get('context_recall', 0) if ground_truth else None
                }
            }

        except Exception as e:
            logger.error(f"RAGAS evaluation error: {e}")
            return {
                'method': 'ragas',
                'error': str(e),
                'scores': {}
            }

    async def _evaluate_llm_as_judge(
        self,
        query: str,
        response: str,
        context_chunks: List[Dict],
        config: EvaluationConfig
    ) -> Dict[str, Any]:
        """
        LLM-as-a-Judge evaluation using GPT-4/Claude

        Evaluates:
        - Accuracy: Is the answer accurate?
        - Completeness: Does it fully answer the question?
        - Clarity: Is the answer clear and well-structured?
        - Helpfulness: Is the answer helpful to the user?
        """
        try:
            from app.services.llm_service import llm_service

            contexts_text = "\n\n".join([
                f"Context {i+1}: {chunk.get('content', '')[:500]}"
                for i, chunk in enumerate(context_chunks[:3])
            ])

            judge_prompt = f"""You are an expert evaluator for RAG (Retrieval-Augmented Generation) systems.

Evaluate the following answer on a scale of 0-10 for each criterion:

**Query:** {query}

**Retrieved Contexts:**
{contexts_text}

**Generated Answer:**
{response}

**Evaluation Criteria:**
1. **Accuracy** (0-10): Is the answer factually correct based on the contexts?
2. **Completeness** (0-10): Does the answer fully address the query?
3. **Clarity** (0-10): Is the answer clear, well-structured, and easy to understand?
4. **Groundedness** (0-10): Is the answer well-grounded in the provided contexts?
5. **Helpfulness** (0-10): Would this answer be helpful to the user?

Respond ONLY with a JSON object in this exact format:
{{
  "accuracy": <score>,
  "completeness": <score>,
  "clarity": <score>,
  "groundedness": <score>,
  "helpfulness": <score>,
  "reasoning": "<brief explanation>"
}}"""

            judge_response = await llm_service.generate(
                prompt=judge_prompt,
                messages=[{"role": "user", "content": judge_prompt}],
                model_id=config.llm_judge_model,
                temperature=0.0  # Deterministic evaluation
            )

            # Parse JSON response
            try:
                scores = json.loads(judge_response['content'])

                # Normalize to 0-1 scale
                normalized_scores = {
                    k: v / 10.0 for k, v in scores.items()
                    if k != 'reasoning' and isinstance(v, (int, float))
                }

                return {
                    'method': 'llm_as_judge',
                    'model': config.llm_judge_model,
                    'scores': normalized_scores,
                    'reasoning': scores.get('reasoning', '')
                }
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM judge response: {judge_response['content']}")
                return {
                    'method': 'llm_as_judge',
                    'error': 'Failed to parse response',
                    'raw_response': judge_response['content']
                }

        except Exception as e:
            logger.error(f"LLM-as-a-Judge evaluation error: {e}")
            return {
                'method': 'llm_as_judge',
                'error': str(e),
                'scores': {}
            }

    async def _evaluate_deepeval(
        self,
        query: str,
        response: str,
        context_chunks: List[Dict]
    ) -> Dict[str, Any]:
        """
        DeepEval framework evaluation

        Metrics:
        - Answer Relevancy
        - Faithfulness
        - Contextual Precision
        - Contextual Recall
        - Hallucination
        """
        try:
            # Import DeepEval (optional dependency)
            try:
                from deepeval.metrics import (
                    AnswerRelevancyMetric,
                    FaithfulnessMetric,
                    ContextualPrecisionMetric,
                    HallucinationMetric
                )
                from deepeval.test_case import LLMTestCase
            except ImportError:
                logger.warning("DeepEval not installed. Install with: pip install deepeval")
                return {
                    'method': 'deepeval',
                    'error': 'DeepEval not installed',
                    'scores': {}
                }

            # Prepare test case
            contexts = [chunk.get('content', '') for chunk in context_chunks]

            test_case = LLMTestCase(
                input=query,
                actual_output=response,
                retrieval_context=contexts
            )

            # Initialize metrics
            metrics = [
                AnswerRelevancyMetric(),
                FaithfulnessMetric(),
                ContextualPrecisionMetric(),
                HallucinationMetric()
            ]

            # Evaluate
            results = {}
            for metric in metrics:
                metric.measure(test_case)
                results[metric.__class__.__name__.replace('Metric', '').lower()] = metric.score

            return {
                'method': 'deepeval',
                'scores': results
            }

        except Exception as e:
            logger.error(f"DeepEval evaluation error: {e}")
            return {
                'method': 'deepeval',
                'error': str(e),
                'scores': {}
            }

    async def _evaluate_semantic_similarity(
        self,
        response: str,
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate semantic similarity using embeddings"""
        try:
            if not ground_truth:
                return {
                    'method': 'semantic_similarity',
                    'scores': {'similarity': None},
                    'note': 'Ground truth required'
                }

            from app.services.embedding_service import embedding_service
            import numpy as np

            # Get embeddings
            response_emb = await embedding_service.get_embedding(response)
            ground_truth_emb = await embedding_service.get_embedding(ground_truth)

            # Calculate cosine similarity
            response_vec = np.array(response_emb)
            ground_truth_vec = np.array(ground_truth_emb)

            similarity = np.dot(response_vec, ground_truth_vec) / (
                np.linalg.norm(response_vec) * np.linalg.norm(ground_truth_vec)
            )

            return {
                'method': 'semantic_similarity',
                'scores': {
                    'similarity': float(similarity)
                }
            }

        except Exception as e:
            logger.error(f"Semantic similarity evaluation error: {e}")
            return {
                'method': 'semantic_similarity',
                'error': str(e),
                'scores': {}
            }

    async def _evaluate_bertscore(
        self,
        response: str,
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate using BERTScore"""
        try:
            if not ground_truth:
                return {
                    'method': 'bertscore',
                    'scores': {},
                    'note': 'Ground truth required'
                }

            # Import BERTScore (optional dependency)
            try:
                from bert_score import score as bert_score
            except ImportError:
                logger.warning("BERTScore not installed. Install with: pip install bert-score")
                return {
                    'method': 'bertscore',
                    'error': 'BERTScore not installed',
                    'scores': {}
                }

            P, R, F1 = bert_score([response], [ground_truth], lang='en', verbose=False)

            return {
                'method': 'bertscore',
                'scores': {
                    'precision': float(P[0]),
                    'recall': float(R[0]),
                    'f1': float(F1[0])
                }
            }

        except Exception as e:
            logger.error(f"BERTScore evaluation error: {e}")
            return {
                'method': 'bertscore',
                'error': str(e),
                'scores': {}
            }

    async def _evaluate_citation_accuracy(
        self,
        response: str,
        context_chunks: List[Dict]
    ) -> Dict[str, Any]:
        """Evaluate citation accuracy and source attribution"""
        try:
            # Check if response contains source references
            import re

            # Look for citation patterns like [1], [Source 1], etc.
            citation_pattern = r'\[(\d+|Source \d+)\]'
            citations = re.findall(citation_pattern, response)

            # Check if claims are grounded in contexts
            contexts_text = " ".join([chunk.get('content', '') for chunk in context_chunks])

            # Simple heuristic: split response into sentences and check grounding
            sentences = response.split('.')
            grounded_sentences = 0

            for sentence in sentences:
                if len(sentence.strip()) < 10:
                    continue
                # Check if key phrases from sentence appear in contexts
                words = set(sentence.lower().split())
                context_words = set(contexts_text.lower().split())
                overlap = len(words & context_words) / max(len(words), 1)
                if overlap > 0.3:  # 30% word overlap threshold
                    grounded_sentences += 1

            grounding_ratio = grounded_sentences / max(len([s for s in sentences if len(s.strip()) >= 10]), 1)

            return {
                'method': 'citation_accuracy',
                'scores': {
                    'citation_count': len(citations),
                    'has_citations': len(citations) > 0,
                    'grounding_ratio': grounding_ratio
                }
            }

        except Exception as e:
            logger.error(f"Citation accuracy evaluation error: {e}")
            return {
                'method': 'citation_accuracy',
                'error': str(e),
                'scores': {}
            }

    async def _evaluate_toxicity(self, response: str) -> Dict[str, Any]:
        """Evaluate toxicity/safety of response"""
        try:
            # You can integrate with APIs like Perspective API or use local models
            # For now, simple keyword-based check
            toxic_keywords = [
                'hate', 'violent', 'offensive', 'discrimination',
                'racist', 'sexist', 'harmful'
            ]

            response_lower = response.lower()
            toxicity_indicators = sum(1 for keyword in toxic_keywords if keyword in response_lower)

            # Normalize score (0 = no toxicity, 1 = high toxicity)
            toxicity_score = min(toxicity_indicators / 3.0, 1.0)

            return {
                'method': 'toxicity',
                'scores': {
                    'toxicity': toxicity_score,
                    'is_safe': toxicity_score < 0.2
                }
            }

        except Exception as e:
            logger.error(f"Toxicity evaluation error: {e}")
            return {
                'method': 'toxicity',
                'error': str(e),
                'scores': {}
            }

    async def _evaluate_bias(self, response: str) -> Dict[str, Any]:
        """Evaluate potential bias in response"""
        try:
            # Simple bias detection (can be enhanced with specialized models)
            bias_indicators = {
                'gender': ['he always', 'she always', 'men are', 'women are'],
                'racial': ['those people', 'they all'],
                'age': ['young people always', 'old people always']
            }

            response_lower = response.lower()
            detected_bias = {}

            for bias_type, indicators in bias_indicators.items():
                detected_bias[bias_type] = any(indicator in response_lower for indicator in indicators)

            overall_bias_score = sum(detected_bias.values()) / len(detected_bias)

            return {
                'method': 'bias_detection',
                'scores': {
                    'bias_score': overall_bias_score,
                    'detected_bias_types': [k for k, v in detected_bias.items() if v],
                    'is_unbiased': overall_bias_score < 0.2
                }
            }

        except Exception as e:
            logger.error(f"Bias detection error: {e}")
            return {
                'method': 'bias_detection',
                'error': str(e),
                'scores': {}
            }

    async def _evaluate_hallucination(
        self,
        response: str,
        context_chunks: List[Dict]
    ) -> Dict[str, Any]:
        """Detect hallucinations (claims not supported by context)"""
        try:
            from app.services.llm_service import llm_service

            contexts_text = "\n\n".join([
                chunk.get('content', '')[:500]
                for chunk in context_chunks[:5]
            ])

            hallucination_prompt = f"""Analyze if the following answer contains hallucinations (unsupported claims).

**Retrieved Contexts:**
{contexts_text}

**Generated Answer:**
{response}

Is every claim in the answer supported by the contexts? Respond with JSON:
{{
  "hallucination_score": <0.0 to 1.0, where 0 = no hallucinations, 1 = severe hallucinations>,
  "unsupported_claims": ["list", "of", "unsupported", "claims"],
  "explanation": "brief explanation"
}}"""

            hallucination_response = await llm_service.generate(
                prompt=hallucination_prompt,
                messages=[{"role": "user", "content": hallucination_prompt}],
                model_id="gpt-4-turbo-preview",
                temperature=0.0
            )

            try:
                result = json.loads(hallucination_response['content'])
                return {
                    'method': 'hallucination',
                    'scores': {
                        'hallucination_score': result.get('hallucination_score', 0),
                        'has_hallucinations': result.get('hallucination_score', 0) > 0.3,
                        'unsupported_claims_count': len(result.get('unsupported_claims', []))
                    },
                    'details': result
                }
            except json.JSONDecodeError:
                return {
                    'method': 'hallucination',
                    'error': 'Failed to parse response',
                    'scores': {}
                }

        except Exception as e:
            logger.error(f"Hallucination detection error: {e}")
            return {
                'method': 'hallucination',
                'error': str(e),
                'scores': {}
            }

    async def _evaluate_answer_relevancy(
        self,
        query: str,
        response: str
    ) -> Dict[str, Any]:
        """Evaluate how relevant the answer is to the query"""
        try:
            from app.services.embedding_service import embedding_service
            import numpy as np

            # Get embeddings
            query_emb = await embedding_service.get_embedding(query)
            response_emb = await embedding_service.get_embedding(response)

            # Calculate cosine similarity
            query_vec = np.array(query_emb)
            response_vec = np.array(response_emb)

            relevancy = np.dot(query_vec, response_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(response_vec)
            )

            return {
                'method': 'answer_relevancy',
                'scores': {
                    'relevancy': float(relevancy),
                    'is_relevant': float(relevancy) > 0.7
                }
            }

        except Exception as e:
            logger.error(f"Answer relevancy evaluation error: {e}")
            return {
                'method': 'answer_relevancy',
                'error': str(e),
                'scores': {}
            }

    async def _evaluate_context_precision(
        self,
        query: str,
        context_chunks: List[Dict]
    ) -> Dict[str, Any]:
        """Evaluate precision of retrieved contexts"""
        try:
            from app.services.embedding_service import embedding_service
            import numpy as np

            if not context_chunks:
                return {
                    'method': 'context_precision',
                    'scores': {'precision': 0.0}
                }

            # Get query embedding
            query_emb = await embedding_service.get_embedding(query)
            query_vec = np.array(query_emb)

            # Calculate relevance of each context
            relevance_scores = []
            for chunk in context_chunks:
                chunk_emb = chunk.get('embedding') or await embedding_service.get_embedding(chunk.get('content', ''))
                chunk_vec = np.array(chunk_emb)

                similarity = np.dot(query_vec, chunk_vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec)
                )
                relevance_scores.append(float(similarity))

            # Precision = ratio of highly relevant contexts
            threshold = 0.7
            precision = sum(1 for score in relevance_scores if score >= threshold) / len(relevance_scores)

            return {
                'method': 'context_precision',
                'scores': {
                    'precision': precision,
                    'avg_relevance': np.mean(relevance_scores),
                    'num_contexts': len(context_chunks)
                }
            }

        except Exception as e:
            logger.error(f"Context precision evaluation error: {e}")
            return {
                'method': 'context_precision',
                'error': str(e),
                'scores': {}
            }

    async def _evaluate_context_recall(
        self,
        context_chunks: List[Dict],
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate recall of retrieved contexts"""
        try:
            if not ground_truth:
                return {
                    'method': 'context_recall',
                    'scores': {},
                    'note': 'Ground truth required'
                }

            # Check if ground truth information is present in contexts
            contexts_text = " ".join([chunk.get('content', '') for chunk in context_chunks])

            # Split ground truth into key phrases
            ground_truth_words = set(ground_truth.lower().split())
            context_words = set(contexts_text.lower().split())

            # Calculate recall
            recall = len(ground_truth_words & context_words) / max(len(ground_truth_words), 1)

            return {
                'method': 'context_recall',
                'scores': {
                    'recall': recall
                }
            }

        except Exception as e:
            logger.error(f"Context recall evaluation error: {e}")
            return {
                'method': 'context_recall',
                'error': str(e),
                'scores': {}
            }

    async def _evaluate_faithfulness(
        self,
        response: str,
        context_chunks: List[Dict]
    ) -> Dict[str, Any]:
        """Evaluate faithfulness (groundedness) of response to contexts"""
        try:
            from app.services.embedding_service import embedding_service
            import numpy as np

            if not context_chunks:
                return {
                    'method': 'faithfulness',
                    'scores': {'faithfulness': 0.0}
                }

            # Get response embedding
            response_emb = await embedding_service.get_embedding(response)
            response_vec = np.array(response_emb)

            # Get context embeddings and calculate max similarity
            max_similarity = 0.0
            for chunk in context_chunks:
                chunk_emb = chunk.get('embedding') or await embedding_service.get_embedding(chunk.get('content', ''))
                chunk_vec = np.array(chunk_emb)

                similarity = np.dot(response_vec, chunk_vec) / (
                    np.linalg.norm(response_vec) * np.linalg.norm(chunk_vec)
                )
                max_similarity = max(max_similarity, float(similarity))

            return {
                'method': 'faithfulness',
                'scores': {
                    'faithfulness': max_similarity,
                    'is_faithful': max_similarity > 0.7
                }
            }

        except Exception as e:
            logger.error(f"Faithfulness evaluation error: {e}")
            return {
                'method': 'faithfulness',
                'error': str(e),
                'scores': {}
            }

    def _aggregate_results(
        self,
        evaluation_results: List[Any],
        enabled_methods: List[EvaluationMethod]
    ) -> Dict[str, Any]:
        """Aggregate evaluation results from multiple methods"""
        aggregated = {
            'evaluations': {},
            'errors': []
        }

        for i, result in enumerate(evaluation_results):
            if isinstance(result, Exception):
                aggregated['errors'].append({
                    'method': enabled_methods[i].value,
                    'error': str(result)
                })
            elif isinstance(result, dict):
                method = result.get('method', enabled_methods[i].value)
                aggregated['evaluations'][method] = result

                if 'error' in result:
                    aggregated['errors'].append({
                        'method': method,
                        'error': result['error']
                    })

        return aggregated

    def _calculate_overall_score(self, results: Dict[str, Any]) -> float:
        """Calculate weighted overall score from all evaluations"""
        scores = []
        weights = {
            'ragas': 0.3,
            'llm_as_judge': 0.3,
            'answer_relevancy': 0.15,
            'faithfulness': 0.15,
            'hallucination': 0.1
        }

        for method, eval_result in results.get('evaluations', {}).items():
            method_scores = eval_result.get('scores', {})

            # Extract numeric scores
            for key, value in method_scores.items():
                if isinstance(value, (int, float)) and value is not None:
                    weight = weights.get(method, 0.1)
                    scores.append((value, weight))

        if not scores:
            return 0.0

        # Weighted average
        weighted_sum = sum(score * weight for score, weight in scores)
        total_weight = sum(weight for _, weight in scores)

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _get_cache_key(
        self,
        query: str,
        response: str,
        context_chunks: List[Dict]
    ) -> str:
        """Generate cache key for evaluation result"""
        import hashlib

        key_data = f"{query}:{response}:{len(context_chunks)}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    async def _check_cache(
        self,
        cache_key: str,
        db: Optional[AsyncSession]
    ) -> Optional[Dict]:
        """Check evaluation cache"""
        try:
            if not db:
                return None

            query = sql_text("""
                SELECT result FROM evaluation_cache
                WHERE cache_key = :cache_key
                AND created_at > NOW() - INTERVAL '1 hour'
                LIMIT 1
            """)

            result = await db.execute(query, {"cache_key": cache_key})
            row = result.first()

            if row:
                return row.result

            return None

        except Exception as e:
            logger.warning(f"Error checking evaluation cache: {e}")
            return None

    async def _cache_result(
        self,
        cache_key: str,
        result: Dict,
        ttl_seconds: int,
        db: AsyncSession
    ):
        """Cache evaluation result"""
        try:
            query = sql_text("""
                INSERT INTO evaluation_cache (cache_key, result, ttl_seconds)
                VALUES (:cache_key, :result, :ttl_seconds)
                ON CONFLICT (cache_key) DO UPDATE
                SET result = :result, created_at = NOW()
            """)

            await db.execute(
                query,
                {
                    "cache_key": cache_key,
                    "result": json.dumps(result),
                    "ttl_seconds": ttl_seconds
                }
            )
            await db.commit()

        except Exception as e:
            logger.warning(f"Error caching evaluation result: {e}")
            await db.rollback()

    async def _store_evaluation(
        self,
        query: str,
        response: str,
        results: Dict[str, Any],
        db: AsyncSession
    ):
        """Store evaluation results in database"""
        try:
            query_sql = sql_text("""
                INSERT INTO evaluation_results (query, response, scores, overall_score, metadata)
                VALUES (:query, :response, :scores, :overall_score, :metadata)
            """)

            await db.execute(
                query_sql,
                {
                    "query": query[:1000],
                    "response": response[:2000],
                    "scores": json.dumps(results.get('evaluations', {})),
                    "overall_score": results.get('overall_score', 0.0),
                    "metadata": json.dumps(results.get('metadata', {}))
                }
            )
            await db.commit()

        except Exception as e:
            logger.warning(f"Error storing evaluation results: {e}")
            await db.rollback()


# Singleton instance
evaluation_service = EvaluationService()
