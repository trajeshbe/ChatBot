"""
Training Log Streamer

Streams container logs in real-time to:
- Log file (incremental writes)
- Database (error detection + progress updates)
- Python logger (debugging)
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from datetime import datetime
import docker
import re

logger = logging.getLogger(__name__)


class TrainingLogStreamer:
    """
    Real-time log streamer for training containers

    Features:
    - Async log streaming (non-blocking)
    - Incremental file writes
    - Error detection with regex patterns
    - Progress extraction (Epoch X/Y, Step X/Y, Loss)
    - Database updates
    """

    def __init__(
        self,
        container: docker.models.containers.Container,
        log_file: Path,
        job_id: str,
        db_callback: Optional[Callable] = None
    ):
        """
        Initialize log streamer

        Args:
            container: Docker container to stream from
            log_file: Path to write logs
            job_id: Fine-tuning job ID
            db_callback: Optional async callback to update database
        """
        self.container = container
        self.log_file = log_file
        self.job_id = job_id
        self.db_callback = db_callback
        self.is_streaming = False

        # Error detection patterns
        self.error_patterns = [
            r"(?i)error:",
            r"(?i)exception:",
            r"(?i)traceback",
            r"(?i)cuda out of memory",
            r"(?i)killed",
            r"(?i)segmentation fault",
            r"(?i)assertion.*failed",
            r"RuntimeError",
            r"ValueError",
            r"KeyError",
            r"ImportError",
            r"AttributeError",
            r"CUDA error",
            r"OOM",  # Out of memory
        ]

        # Progress extraction patterns
        self.progress_patterns = {
            'epoch': r'Epoch (\d+)/(\d+)',
            'step': r'Step (\d+)/(\d+)',
            'loss': r'Loss[:\s]+([0-9.]+)',
            'samples': r'Loaded (\d+).*samples',
            'stage_preprocessing': r'(?:Preprocessing|🔄 Preprocessing)',
            'stage_training': r'(?:Training|▶️  Training)',
            'stage_evaluation': r'(?:Evaluation|📊 Evaluation)',
            'stage_merging': r'(?:Merging|🔀 Merging)',
        }

    async def stream_logs(self) -> None:
        """
        Stream logs from container to file and database

        Runs until container stops
        """
        self.is_streaming = True
        logger.info(f"📡 Starting log stream for job {self.job_id}")

        try:
            # Create log file
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            # Stream logs with follow=True (like tail -f)
            # This runs in a thread to avoid blocking
            log_generator = await asyncio.to_thread(
                self._get_log_stream
            )

            # Process log lines
            with open(self.log_file, 'w', buffering=1) as f:  # Line buffering
                for log_chunk in log_generator:
                    if not self.is_streaming:
                        logger.info(f"🛑 Log streaming stopped by external signal for job {self.job_id}")
                        break

                    try:
                        # Decode log line
                        log_line = log_chunk.decode('utf-8', errors='replace').strip()

                        if not log_line:
                            continue

                        # Write to file immediately with timestamp
                        timestamp = datetime.utcnow().isoformat()
                        f.write(f"[{timestamp}] {log_line}\n")
                        f.flush()  # Force write to disk

                        # Log to Python logger (for backend debugging)
                        logger.debug(f"[{self.job_id}] {log_line}")

                        # Detect errors
                        if self._is_error(log_line):
                            logger.error(f"❌ Error detected in job {self.job_id}: {log_line}")
                            if self.db_callback:
                                await self.db_callback(
                                    job_id=self.job_id,
                                    status="failed",
                                    error_message=log_line[:500]  # Truncate to 500 chars
                                )

                        # Extract progress
                        progress = self._extract_progress(log_line)
                        if progress and self.db_callback:
                            await self.db_callback(
                                job_id=self.job_id,
                                **progress
                            )

                    except Exception as e:
                        logger.warning(f"Error processing log line: {e}")
                        continue

            logger.info(f"✅ Log streaming completed for job {self.job_id}")

        except Exception as e:
            logger.error(f"❌ Log streaming error for job {self.job_id}: {e}")
            if self.db_callback:
                try:
                    await self.db_callback(
                        job_id=self.job_id,
                        status="failed",
                        error_message=f"Log streaming failed: {str(e)}"
                    )
                except Exception as callback_error:
                    logger.error(f"Failed to update database after streaming error: {callback_error}")
        finally:
            self.is_streaming = False
            logger.info(f"📡 Log stream ended for job {self.job_id}")

    def _get_log_stream(self):
        """
        Get log stream generator from container

        This is a blocking operation, so it's called via asyncio.to_thread
        """
        return self.container.logs(
            stream=True,
            follow=True,
            stdout=True,
            stderr=True
        )

    def _is_error(self, log_line: str) -> bool:
        """
        Check if log line contains an error

        Args:
            log_line: Log line to check

        Returns:
            True if error detected
        """
        # IMPORTANT: Skip INFO, DEBUG, and WARNING level messages
        # Only flag actual ERROR and EXCEPTION level messages
        log_line_upper = log_line.upper()

        # Skip if it's an INFO, DEBUG, or WARNING message from a logger
        if any(level in log_line_upper for level in [' - INFO - ', ' - DEBUG - ', ' - WARNING - ']):
            return False

        # Now check error patterns
        for pattern in self.error_patterns:
            if re.search(pattern, log_line):
                return True
        return False

    def _extract_progress(self, log_line: str) -> Optional[Dict[str, Any]]:
        """
        Extract training progress from log line

        Returns:
            Dict with progress metrics or None
        """
        progress = {}

        # Extract epoch
        if match := re.search(self.progress_patterns['epoch'], log_line):
            progress['current_epoch'] = int(match.group(1))
            # Don't set total_epochs here - it's already set in job creation

        # Extract step
        if match := re.search(self.progress_patterns['step'], log_line):
            progress['current_step'] = int(match.group(1))
            # Don't set total_steps here - it's already set in job creation

        # Extract loss
        if match := re.search(self.progress_patterns['loss'], log_line):
            try:
                progress['train_loss'] = float(match.group(1))
            except ValueError:
                pass

        # Extract training stage
        for stage_key, stage_pattern in self.progress_patterns.items():
            if stage_key.startswith('stage_'):
                if re.search(stage_pattern, log_line):
                    stage_name = stage_key.replace('stage_', '')
                    progress['training_stage'] = stage_name
                    break

        return progress if progress else None

    def stop(self):
        """Stop log streaming"""
        if self.is_streaming:
            self.is_streaming = False
            logger.info(f"🛑 Stopping log stream for job {self.job_id}")
