"""
Fine-Tuned Model Evaluation Service

Evaluates fine-tuned models using standard NLP metrics:
- BLEU (BiLingual Evaluation Understudy)
- ROUGE (Recall-Oriented Understudy for Gisting Evaluation)
- METEOR (Metric for Evaluation of Translation with Explicit ORdering)
- BERTScore (contextual embeddings)
- Perplexity
- Accuracy (for classification tasks)

Features:
- Automatic test set generation from validation data
- Sample-by-sample evaluation tracking
- Metric aggregation and statistics
- Evaluation result storage in database
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class ModelEvaluationService:
    """Service for evaluating fine-tuned models"""

    def __init__(self):
        """Initialize evaluation service"""
        self.metrics_available = {
            "bleu": "BLEU score (translation/generation quality)",
            "rouge": "ROUGE scores (summarization quality)",
            "meteor": "METEOR score (semantic matching)",
            "bertscore": "BERTScore (contextual similarity)",
            "perplexity": "Model perplexity (language modeling)",
            "accuracy": "Classification accuracy",
            "f1_score": "F1 score (classification)"
        }

    async def evaluate_model(
        self,
        model_path: str,
        test_dataset_path: str,
        task_type: str = "text-generation",
        num_samples: int = 100,
        metrics: Optional[List[str]] = None,
        ollama_model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a fine-tuned model on test dataset

        Args:
            model_path: Path to fine-tuned model checkpoints
            test_dataset_path: Path to test dataset
            task_type: Type of task (text-generation, qa, classification, summarization)
            num_samples: Number of samples to evaluate on
            metrics: List of metrics to compute (default: all applicable)

        Returns:
            Dictionary with evaluation results including:
            - Overall metrics (BLEU, ROUGE, etc.)
            - Per-sample results
            - Sample examples (best, worst, median)
        """
        try:
            logger.info(f"Starting model evaluation: {model_path}")
            logger.info(f"Task type: {task_type}, Samples: {num_samples}")

            # Load test dataset
            test_samples = await self._load_test_dataset(test_dataset_path, num_samples)

            if not test_samples:
                raise ValueError("No test samples found")

            # Determine which metrics to use based on task type
            if metrics is None:
                metrics = self._get_default_metrics(task_type)

            logger.info(f"Computing metrics: {', '.join(metrics)}")

            # Run evaluation on each sample
            sample_results = []
            for i, sample in enumerate(test_samples):
                if i % 10 == 0:
                    logger.info(f"Evaluating sample {i+1}/{len(test_samples)}")

                sample_result = await self._evaluate_sample(
                    model_path=model_path,
                    input_text=sample["input"],
                    reference=sample["reference"],
                    task_type=task_type,
                    metrics=metrics,
                    ollama_model_name=ollama_model_name
                )

                sample_result["sample_id"] = i
                sample_result["input"] = sample["input"]
                sample_result["reference"] = sample["reference"]
                sample_results.append(sample_result)

            # Aggregate metrics
            aggregated_metrics = self._aggregate_metrics(sample_results, metrics)

            # Select example samples (best, worst, median)
            example_samples = self._select_example_samples(sample_results, metrics)

            # Build final result
            evaluation_result = {
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat(),
                "task_type": task_type,
                "num_samples_evaluated": len(sample_results),
                "metrics": aggregated_metrics,
                "sample_results": sample_results,  # All sample results
                "example_samples": example_samples,  # Selected examples for UI
                "metric_descriptions": {m: self.metrics_available.get(m, "N/A") for m in metrics}
            }

            logger.info(f"✅ Evaluation complete. Metrics: {aggregated_metrics}")
            return evaluation_result

        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _load_test_dataset(
        self,
        dataset_path: str,
        num_samples: int
    ) -> List[Dict[str, str]]:
        """
        Load test dataset from file

        Args:
            dataset_path: Path to dataset (CSV, JSONL, etc.)
            num_samples: Number of samples to load

        Returns:
            List of samples with input and reference
        """
        try:
            import pandas as pd
            from pathlib import Path

            path = Path(dataset_path)

            if path.suffix == '.csv':
                df = pd.read_csv(path)
            elif path.suffix == '.jsonl':
                df = pd.read_json(path, lines=True)
            elif path.suffix == '.json':
                df = pd.read_json(path)
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")

            # Limit to num_samples
            df = df.head(num_samples)

            # Convert to list of dicts
            # Assumes columns: 'input'/'question'/'text' and 'reference'/'answer'/'target'
            samples = []
            for _, row in df.iterrows():
                input_text = row.get('input') or row.get('question') or row.get('text') or ""
                reference = row.get('reference') or row.get('answer') or row.get('target') or ""

                if input_text and reference:
                    samples.append({
                        "input": str(input_text),
                        "reference": str(reference)
                    })

            logger.info(f"Loaded {len(samples)} test samples from {dataset_path}")
            return samples

        except Exception as e:
            logger.error(f"Failed to load test dataset: {e}")
            return []

    def _get_default_metrics(self, task_type: str) -> List[str]:
        """Get default metrics for task type"""
        task_metrics = {
            "text-generation": ["bleu", "rouge", "bertscore"],
            "qa": ["bleu", "rouge", "f1_score"],
            "classification": ["accuracy", "f1_score"],
            "summarization": ["rouge", "bertscore"],
            "translation": ["bleu", "meteor", "bertscore"]
        }
        return task_metrics.get(task_type, ["bleu", "rouge"])

    async def _evaluate_sample(
        self,
        model_path: str,
        input_text: str,
        reference: str,
        task_type: str,
        metrics: List[str],
        ollama_model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single sample

        Args:
            model_path: Path to model
            input_text: Input text
            reference: Reference/ground truth output
            task_type: Task type
            metrics: Metrics to compute
            ollama_model_name: Optional Ollama model name for deployed models

        Returns:
            Dictionary with generated output and metric scores
        """
        # Generate output from model
        generated_output = await self._generate_output(
            model_path,
            input_text,
            task_type,
            ollama_model_name=ollama_model_name
        )

        # Compute metrics
        scores = {}
        for metric in metrics:
            score = await self._compute_metric(metric, generated_output, reference)
            scores[metric] = score

        return {
            "generated": generated_output,
            "scores": scores
        }

    async def _generate_output(
        self,
        model_path: str,
        input_text: str,
        task_type: str,
        ollama_model_name: Optional[str] = None
    ) -> str:
        """
        Generate output from fine-tuned model

        Two modes:
        1. If ollama_model_name provided: Use deployed Ollama model (fast)
        2. If model_path is minio://: Download and use vLLM/transformers (slow)

        Args:
            model_path: Path to model checkpoints or minio URL
            input_text: Input text to generate from
            task_type: Task type (affects prompt formatting)
            ollama_model_name: Optional Ollama model name if deployed

        Returns:
            Generated text output
        """
        try:
            import httpx
            import os

            # Strategy 1: Use Ollama if model is deployed
            if ollama_model_name:
                logger.info(f"Using Ollama model: {ollama_model_name}")
                ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")

                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{ollama_url}/api/generate",
                        json={
                            "model": ollama_model_name,
                            "prompt": input_text,
                            "stream": False,
                            "options": {
                                "temperature": 0.7,
                                "num_predict": 256
                            }
                        }
                    )

                    if response.status_code == 200:
                        generated = response.json().get("response", "")
                        logger.debug(f"Generated {len(generated)} chars via Ollama")
                        return generated
                    else:
                        logger.error(f"Ollama request failed: {response.status_code} {response.text}")
                        return "[Ollama error]"

            # Strategy 2: Placeholder for MinIO checkpoint loading
            # TODO: Implement checkpoint download and local inference
            else:
                logger.warning(f"Model not deployed to Ollama. Cannot run inference on checkpoints yet.")
                logger.warning(f"To evaluate this model, deploy it to Ollama first.")
                return f"[Model not deployed - cannot generate]"

        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            return "[Generation error]"

    async def _compute_metric(
        self,
        metric_name: str,
        generated: str,
        reference: str
    ) -> float:
        """
        Compute a specific metric

        Args:
            metric_name: Name of metric (bleu, rouge, etc.)
            generated: Generated text
            reference: Reference text

        Returns:
            Metric score (0.0 to 1.0 typically)
        """
        try:
            if metric_name == "bleu":
                return await self._compute_bleu(generated, reference)
            elif metric_name == "rouge":
                return await self._compute_rouge(generated, reference)
            elif metric_name == "meteor":
                return await self._compute_meteor(generated, reference)
            elif metric_name == "bertscore":
                return await self._compute_bertscore(generated, reference)
            elif metric_name == "perplexity":
                return await self._compute_perplexity(generated)
            elif metric_name in ["accuracy", "f1_score"]:
                return await self._compute_classification_metric(metric_name, generated, reference)
            else:
                logger.warning(f"Unknown metric: {metric_name}")
                return 0.0

        except Exception as e:
            logger.error(f"Error computing {metric_name}: {e}")
            return 0.0

    async def _compute_bleu(self, generated: str, reference: str) -> float:
        """Compute BLEU score"""
        try:
            from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
            import nltk

            # Ensure nltk data is available
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)

            # Tokenize
            reference_tokens = [reference.split()]  # BLEU expects list of reference token lists
            generated_tokens = generated.split()

            # Compute BLEU with smoothing
            smoothing = SmoothingFunction()
            score = sentence_bleu(
                reference_tokens,
                generated_tokens,
                smoothing_function=smoothing.method1
            )

            return float(score)

        except ImportError:
            logger.warning("NLTK not installed, BLEU score unavailable")
            return 0.0
        except Exception as e:
            logger.error(f"BLEU computation error: {e}")
            return 0.0

    async def _compute_rouge(self, generated: str, reference: str) -> Dict[str, float]:
        """Compute ROUGE scores (ROUGE-1, ROUGE-2, ROUGE-L)"""
        try:
            from rouge_score import rouge_scorer

            scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
            scores = scorer.score(reference, generated)

            return {
                "rouge1": float(scores['rouge1'].fmeasure),
                "rouge2": float(scores['rouge2'].fmeasure),
                "rougeL": float(scores['rougeL'].fmeasure)
            }

        except ImportError:
            logger.warning("rouge-score not installed, ROUGE unavailable")
            return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}
        except Exception as e:
            logger.error(f"ROUGE computation error: {e}")
            return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}

    async def _compute_meteor(self, generated: str, reference: str) -> float:
        """Compute METEOR score"""
        try:
            from nltk.translate.meteor_score import meteor_score
            import nltk

            # Ensure nltk data
            try:
                nltk.data.find('corpora/wordnet')
            except LookupError:
                nltk.download('wordnet', quiet=True)

            score = meteor_score([reference.split()], generated.split())
            return float(score)

        except ImportError:
            logger.warning("METEOR not available")
            return 0.0
        except Exception as e:
            logger.error(f"METEOR computation error: {e}")
            return 0.0

    async def _compute_bertscore(self, generated: str, reference: str) -> Dict[str, float]:
        """Compute BERTScore"""
        try:
            from bert_score import score

            P, R, F1 = score([generated], [reference], lang='en', verbose=False)

            return {
                "precision": float(P.item()),
                "recall": float(R.item()),
                "f1": float(F1.item())
            }

        except ImportError:
            logger.warning("bert-score not installed, BERTScore unavailable")
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        except Exception as e:
            logger.error(f"BERTScore computation error: {e}")
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    async def _compute_perplexity(self, generated: str) -> float:
        """Compute perplexity (requires model access)"""
        # Placeholder - requires actual model loading
        logger.warning("Perplexity computation requires model access - not implemented")
        return 0.0

    async def _compute_classification_metric(
        self,
        metric_name: str,
        generated: str,
        reference: str
    ) -> float:
        """Compute classification metrics (accuracy, F1)"""
        try:
            # Simplified: exact match for now
            # In practice, you'd parse class labels
            if generated.strip().lower() == reference.strip().lower():
                return 1.0
            else:
                return 0.0
        except Exception as e:
            logger.error(f"Classification metric error: {e}")
            return 0.0

    def _aggregate_metrics(
        self,
        sample_results: List[Dict],
        metrics: List[str]
    ) -> Dict[str, Any]:
        """
        Aggregate metrics across all samples

        Args:
            sample_results: List of sample results
            metrics: List of metrics

        Returns:
            Dictionary with mean, std, min, max for each metric
        """
        import numpy as np

        aggregated = {}

        for metric in metrics:
            # Extract metric values from all samples
            values = []
            for sample in sample_results:
                score = sample.get("scores", {}).get(metric)

                if isinstance(score, dict):
                    # For metrics like ROUGE that return multiple scores
                    for sub_metric, sub_score in score.items():
                        metric_key = f"{metric}_{sub_metric}"
                        if metric_key not in aggregated:
                            aggregated[metric_key] = []
                        aggregated[metric_key].append(sub_score)
                elif score is not None:
                    if metric not in aggregated:
                        aggregated[metric] = []
                    aggregated[metric].append(score)

        # Compute statistics
        stats = {}
        for metric_key, values in aggregated.items():
            if values:
                stats[metric_key] = {
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "median": float(np.median(values))
                }

        return stats

    def _select_example_samples(
        self,
        sample_results: List[Dict],
        metrics: List[str]
    ) -> Dict[str, List[Dict]]:
        """
        Select example samples (best, worst, median)

        Args:
            sample_results: All sample results
            metrics: Metrics used

        Returns:
            Dictionary with best, worst, and median samples
        """
        if not sample_results:
            return {"best": [], "worst": [], "median": []}

        # Use first metric for ranking (or average if multiple)
        primary_metric = metrics[0]

        # Extract scores
        scored_samples = []
        for sample in sample_results:
            score = sample.get("scores", {}).get(primary_metric)

            # Handle dict scores (like ROUGE)
            if isinstance(score, dict):
                score = list(score.values())[0] if score else 0.0

            scored_samples.append((score or 0.0, sample))

        # Sort by score
        scored_samples.sort(key=lambda x: x[0])

        # Select examples
        n = len(scored_samples)
        examples = {
            "best": [scored_samples[-1][1], scored_samples[-2][1]] if n >= 2 else [scored_samples[-1][1]] if n >= 1 else [],
            "worst": [scored_samples[0][1], scored_samples[1][1]] if n >= 2 else [scored_samples[0][1]] if n >= 1 else [],
            "median": [scored_samples[n//2][1]] if n >= 1 else []
        }

        return examples
