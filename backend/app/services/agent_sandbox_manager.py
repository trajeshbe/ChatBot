"""
Agent Sandbox Manager

Manages Docker containers for autonomous agent execution.
Backend launches containers, monitors execution, collects artifacts.
"""

import asyncio
import docker
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, AsyncIterator
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class AgentSandboxManager:
    """
    Manages agent execution in isolated Docker containers

    Responsibilities:
    - Launch containers with task config
    - Monitor execution and stream events
    - Collect artifacts after completion
    - Clean up containers
    """

    def __init__(self):
        """Initialize Docker client and settings"""
        try:
            self.docker_client = docker.from_env()
            self.image_name = "chatbot-agent-runtime:latest"
            self.network_name = "chatbot_rag-network"  # Use existing docker-compose network (changed from chatbot_default)

            # Container resource limits
            self.resource_limits = {
                "mem_limit": "1g",  # 1GB RAM limit
                "cpu_period": 100000,
                "cpu_quota": 50000,  # 50% of 1 CPU
                "pids_limit": 100  # Max 100 processes
            }

            logger.info("🐳 Docker client initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {str(e)}")
            raise

    async def execute_task(
        self,
        task: str,
        task_id: str,
        session_id: str,
        agent_type: str = "local_mini",
        context: Dict[str, Any] = None,
        max_iterations: int = 20,
        uploaded_files: list = None,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute task in sandbox container

        Args:
            task: Task description/query
            task_id: Unique task ID
            session_id: Session ID
            agent_type: 'local_mini' or 'claude_cli'
            context: Additional context (uploaded files, etc.)
            max_iterations: Max iterations for agentic loop
            uploaded_files: List of uploaded files to mount
            model_id: LLM model to use (from UI selection)

        Returns:
            Task execution result with artifacts
        """

        logger.info(f"🚀 Launching sandbox container for task {task_id}")

        # Prepare task config
        task_config = {
            "task_id": task_id,
            "session_id": session_id,
            "task": task,
            "agent_type": agent_type,
            "max_iterations": max_iterations,
            "context": context or {},
            "uploaded_files": uploaded_files or []
        }

        # Create workspace directory (host)
        workspace_path = Path(f"/tmp/agent_workspaces/{task_id}")
        workspace_path.mkdir(parents=True, exist_ok=True)

        input_dir = workspace_path / "input"
        output_dir = workspace_path / "output"
        artifacts_dir = workspace_path / "artifacts"

        for dir_path in [input_dir, output_dir, artifacts_dir]:
            dir_path.mkdir(exist_ok=True)

        # Copy uploaded files to input directory
        if uploaded_files:
            await self._copy_uploaded_files(uploaded_files, input_dir)

        # Save task config
        config_file = input_dir / "task_config.json"
        with open(config_file, 'w') as f:
            json.dump(task_config, f, indent=2)

        # Build environment variables
        env_vars = {
            "TASK_ID": task_id,
            "SESSION_ID": session_id,
            "AGENT_TYPE": agent_type,
            "AGENT_MAX_ITERATIONS": str(max_iterations),
            "AGENT_WORKSPACE": "/workspace"
        }

        # Add LLM credentials based on agent type
        if agent_type == "local_mini":
            env_vars["OLLAMA_BASE_URL"] = "http://rag-ollama:11434"

            # Use UI-selected model for code generation, fallback to default if None
            code_model = model_id or "qwen2.5-coder:7b"
            vision_model = "llama3.2-vision:11b"  # Keep default for vision-specific tasks

            # If UI model supports vision, use it for vision tasks too
            vision_capable_models = ['vision', 'qwen2.5vl', 'gpt-4o', 'gpt-4-vision', 'claude-3']
            if model_id and any(vm in model_id.lower() for vm in vision_capable_models):
                vision_model = model_id
                logger.info(f"✅ Using UI-selected vision model for code generation: {vision_model}")

            env_vars["AGENT_CODE_MODEL"] = code_model
            env_vars["AGENT_VISION_MODEL"] = vision_model

            logger.info(f"🎯 Agent sandbox using code model: {code_model}")
            logger.info(f"🎯 Agent sandbox using vision model: {vision_model}")

        elif agent_type == "claude_cli":
            import os
            env_vars["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "")

            # Pass model_id for Claude agents too
            if model_id:
                env_vars["AGENT_MODEL_ID"] = model_id
                logger.info(f"🎯 Claude CLI agent using model: {model_id}")
            else:
                env_vars["AGENT_MODEL_ID"] = "claude-sonnet-4.5"  # Default

        # Launch container
        container = None
        try:
            logger.info(f"📦 Creating container with image {self.image_name}")

            container = self.docker_client.containers.run(
                image=self.image_name,
                name=f"agent-{task_id}",
                detach=True,
                remove=False,  # Keep for log inspection
                network=self.network_name,
                environment=env_vars,
                volumes={
                    str(workspace_path): {
                        'bind': '/workspace',
                        'mode': 'rw'
                    }
                },
                stdin_open=True,
                **self.resource_limits
            )

            logger.info(f"✅ Container {container.short_id} started")

            # Send task config via stdin
            container_input = json.dumps(task_config).encode('utf-8')
            await asyncio.to_thread(container.attach_socket, params={'stdin': 1, 'stream': 1})

            # Wait for container to complete
            logger.info(f"⏳ Waiting for container to complete...")

            exit_status = await asyncio.to_thread(container.wait, timeout=600)

            # Get logs
            logs = await asyncio.to_thread(container.logs, stdout=True, stderr=True)
            logs_text = logs.decode('utf-8')

            logger.info(f"📋 Container completed with exit code: {exit_status['StatusCode']}")

            # Read result from output directory
            result_file = output_dir / "result.json"
            if result_file.exists():
                with open(result_file, 'r') as f:
                    result = json.load(f)
            else:
                result = {
                    "success": False,
                    "error": "No result file generated",
                    "logs": logs_text
                }

            # Collect artifacts
            artifacts = []
            for artifact_file in artifacts_dir.iterdir():
                if artifact_file.is_file():
                    artifacts.append({
                        "name": artifact_file.name,
                        "path": str(artifact_file),
                        "size": artifact_file.stat().st_size,
                        "type": artifact_file.suffix
                    })

            result["artifacts"] = artifacts
            result["task_id"] = task_id
            result["container_id"] = container.short_id
            result["logs"] = logs_text

            return result

        except docker.errors.ImageNotFound:
            logger.error(f"❌ Image {self.image_name} not found. Build it first.")
            return {
                "success": False,
                "error": f"Agent runtime image not found: {self.image_name}",
                "task_id": task_id
            }

        except docker.errors.APIError as e:
            logger.error(f"❌ Docker API error: {str(e)}")
            return {
                "success": False,
                "error": f"Docker error: {str(e)}",
                "task_id": task_id
            }

        except Exception as e:
            logger.error(f"❌ Execution error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "task_id": task_id
            }

        finally:
            # Cleanup container (optional - can keep for debugging)
            if container:
                try:
                    logger.info(f"🧹 Removing container {container.short_id}")
                    await asyncio.to_thread(container.remove, force=True)
                except Exception as e:
                    logger.warning(f"Failed to remove container: {str(e)}")

    async def _copy_uploaded_files(
        self,
        uploaded_files: list,
        input_dir: Path
    ):
        """Copy uploaded files to container input directory"""
        # TODO: Implement file copying from MinIO or local storage
        # For now, this is a placeholder
        logger.info(f"📁 Copying {len(uploaded_files)} files to input directory")
        pass

    async def stream_logs(
        self,
        container_id: str
    ) -> AsyncIterator[str]:
        """
        Stream logs from running container

        Yields log lines as they appear
        """
        try:
            container = self.docker_client.containers.get(container_id)

            for line in container.logs(stream=True, follow=True):
                yield line.decode('utf-8')

        except Exception as e:
            logger.error(f"Error streaming logs: {str(e)}")
            yield f"ERROR: {str(e)}\n"

    def get_container_status(self, container_id: str) -> Dict[str, Any]:
        """Get container status"""
        try:
            container = self.docker_client.containers.get(container_id)
            return {
                "id": container.short_id,
                "status": container.status,
                "created": container.attrs['Created'],
                "started": container.attrs['State'].get('StartedAt'),
                "finished": container.attrs['State'].get('FinishedAt')
            }
        except Exception as e:
            return {"error": str(e)}

    def list_running_containers(self) -> list:
        """List all running agent containers"""
        try:
            containers = self.docker_client.containers.list(
                filters={"name": "agent-"}
            )
            return [{
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "created": c.attrs['Created']
            } for c in containers]
        except Exception as e:
            logger.error(f"Error listing containers: {str(e)}")
            return []

    def cleanup_old_containers(self, max_age_hours: int = 24):
        """Remove old stopped containers"""
        try:
            containers = self.docker_client.containers.list(
                all=True,
                filters={"name": "agent-"}
            )

            removed = 0
            for container in containers:
                # Check age
                created = datetime.fromisoformat(
                    container.attrs['Created'].replace('Z', '+00:00')
                )
                age_hours = (datetime.now(created.tzinfo) - created).total_seconds() / 3600

                if age_hours > max_age_hours and container.status != 'running':
                    container.remove(force=True)
                    removed += 1

            logger.info(f"🧹 Removed {removed} old containers")
            return removed

        except Exception as e:
            logger.error(f"Error cleaning up containers: {str(e)}")
            return 0


# Global instance
agent_sandbox_manager = AgentSandboxManager()
