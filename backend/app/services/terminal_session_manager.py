"""
Terminal Session Manager

Manages interactive PTY (pseudo-terminal) sessions for Claude CLI.
Enables bidirectional communication with user input/output streaming.

Features:
- PTY process management with asyncio
- Async read/write operations
- Terminal resizing support
- Session lifecycle management
- Multiple concurrent sessions
"""

import os
import asyncio
import logging
from typing import Dict, Optional, AsyncIterator
from dataclasses import dataclass
import ptyprocess
import signal

logger = logging.getLogger(__name__)

@dataclass
class TerminalSession:
    """Represents an active PTY terminal session"""
    task_id: str
    process: ptyprocess.PtyProcess
    read_queue: asyncio.Queue
    write_queue: asyncio.Queue
    is_running: bool = True

    async def read_output(self) -> AsyncIterator[str]:
        """
        Async generator that yields terminal output line by line

        Yields:
            str: Terminal output (with ANSI codes preserved)
        """
        while self.is_running:
            try:
                # Read from PTY with timeout
                output = await asyncio.wait_for(
                    self.read_queue.get(),
                    timeout=0.1
                )
                yield output
            except asyncio.TimeoutError:
                # No output available, check if process is still running
                # Check process type: ptyprocess has isalive(), asyncio subprocess has returncode
                if hasattr(self.process, 'isalive'):
                    # ptyprocess
                    if not self.process.isalive():
                        self.is_running = False
                        break
                elif hasattr(self.process, 'returncode'):
                    # asyncio subprocess - returncode is None if still running
                    if self.process.returncode is not None:
                        self.is_running = False
                        break
                continue
            except Exception as e:
                logger.error(f"Error reading terminal output: {e}")
                break

    async def write_input(self, data: str):
        """
        Write user input to terminal stdin

        Args:
            data: User input string
        """
        try:
            logger.info(f"🔧 write_input called for task {self.task_id}, data: {repr(data[:50])}")

            # Check if this is a ptyprocess or asyncio subprocess
            if hasattr(self.process, 'isalive'):
                # ptyprocess - synchronous write
                logger.info(f"🔧 Detected ptyprocess")
                if self.process.isalive():
                    self.process.write(data.encode('utf-8'))
                    logger.info(f"✅ Wrote {len(data)} bytes to PTY")
                else:
                    logger.warning(f"⚠️ PTY process not alive!")
            elif hasattr(self.process, 'stdin'):
                # asyncio subprocess - async write
                logger.info(f"🔧 Detected asyncio subprocess, stdin={self.process.stdin}")
                if self.process.stdin:
                    logger.info(f"🔧 stdin exists, is_closing={self.process.stdin.is_closing()}")
                    if not self.process.stdin.is_closing():
                        self.process.stdin.write(data.encode('utf-8'))
                        await self.process.stdin.drain()
                        logger.info(f"✅ Wrote {len(data)} bytes to subprocess stdin")
                    else:
                        logger.warning(f"⚠️ subprocess stdin is closing!")
                else:
                    logger.warning(f"⚠️ subprocess stdin is None!")
            else:
                logger.error(f"❌ Unknown process type: {type(self.process)}")
        except Exception as e:
            logger.error(f"❌ Error writing to terminal: {e}", exc_info=True)

    async def resize(self, rows: int, cols: int):
        """
        Resize the terminal window (only works with ptyprocess, not asyncio subprocess)

        Args:
            rows: Number of rows
            cols: Number of columns
        """
        try:
            # Only ptyprocess supports resize
            if hasattr(self.process, 'isalive') and self.process.isalive():
                self.process.setwinsize(rows, cols)
                logger.debug(f"Resized terminal to {rows}x{cols}")
            else:
                logger.debug(f"Resize not supported for asyncio subprocess")
        except Exception as e:
            logger.error(f"Error resizing terminal: {e}")

    async def close(self):
        """Close the terminal session and cleanup"""
        self.is_running = False
        try:
            # Check process type and terminate accordingly
            if hasattr(self.process, 'isalive'):
                # ptyprocess
                if self.process.isalive():
                    # Send SIGTERM
                    self.process.kill(signal.SIGTERM)
                    # Wait for graceful shutdown
                    await asyncio.sleep(0.5)
                    # Force kill if still alive
                    if self.process.isalive():
                        self.process.kill(signal.SIGKILL)
            elif hasattr(self.process, 'returncode'):
                # asyncio subprocess
                if self.process.returncode is None:
                    self.process.terminate()
                    try:
                        await asyncio.wait_for(self.process.wait(), timeout=0.5)
                    except asyncio.TimeoutError:
                        self.process.kill()
                        await self.process.wait()
            logger.info(f"Closed terminal session for task: {self.task_id}")
        except Exception as e:
            logger.error(f"Error closing terminal session: {e}")


# Global session store
_sessions: Dict[str, TerminalSession] = {}


async def create_terminal_session(
    task_id: str,
    command: list,
    cwd: str = "/workspace",
    env: Optional[dict] = None,
    use_pty: bool = True  # NEW: Option to use asyncio subprocess instead of ptyprocess
) -> TerminalSession:
    """
    Create a new PTY terminal session

    Args:
        task_id: Unique task identifier
        command: Command to execute (e.g., ["claude", "."] or ["docker", "exec", ...])
        cwd: Working directory
        env: Environment variables
        use_pty: If True, use ptyprocess; if False, use asyncio subprocess (for docker exec -it)

    Returns:
        TerminalSession: Active terminal session
    """
    logger.info(f"🖥️ Creating terminal session for task: {task_id}")
    logger.info(f"Command: {' '.join(command)}")
    logger.info(f"Using {'ptyprocess' if use_pty else 'asyncio subprocess (docker exec -it)'}")

    # Prepare environment
    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    # Spawn PTY process
    try:
        if use_pty:
            # Use ptyprocess for PTY allocation on host
            if command[0] == "docker" and "exec" in command:
                logger.info("Using PTY-enabled docker exec wrapper")

            process = ptyprocess.PtyProcess.spawn(
                command,
                cwd=cwd,
                env=process_env,
                dimensions=(24, 80)  # Default terminal size
            )
            logger.info(f"✅ PTY process spawned with PID: {process.pid}")
        else:
            # Use asyncio subprocess - let docker exec -it handle PTY inside container
            logger.info("Using asyncio subprocess (docker handles PTY allocation)")
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,  # Merge stderr into stdout
                cwd=cwd,
                env=process_env
            )
            logger.info(f"✅ Subprocess spawned with PID: {process.pid}")

        # Create queues for async I/O
        read_queue = asyncio.Queue()
        write_queue = asyncio.Queue()

        # Create session
        session = TerminalSession(
            task_id=task_id,
            process=process,
            read_queue=read_queue,
            write_queue=write_queue
        )

        # Start background reader task
        if use_pty:
            asyncio.create_task(_read_pty_output(session))
        else:
            asyncio.create_task(_read_subprocess_output(session))

        # Store session
        _sessions[task_id] = session

        return session

    except Exception as e:
        logger.error(f"❌ Failed to create terminal session: {e}")
        logger.exception(e)  # Full traceback
        raise


async def _read_pty_output(session: TerminalSession):
    """
    Background task that continuously reads from PTY and queues output

    Args:
        session: Terminal session to read from
    """
    logger.info(f"Started PTY reader for task: {session.task_id}")

    try:
        while session.is_running and session.process.isalive():
            try:
                # Read with timeout to avoid blocking
                output = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: session.process.read(1024).decode('utf-8', errors='ignore')
                )

                if output:
                    # Queue output for WebSocket transmission
                    await session.read_queue.put(output)

            except EOFError:
                # Process ended
                logger.info(f"PTY process ended for task: {session.task_id}")
                break
            except Exception as e:
                logger.error(f"Error reading from PTY: {e}")
                await asyncio.sleep(0.1)

    finally:
        session.is_running = False
        logger.info(f"PTY reader stopped for task: {session.task_id}")


async def _read_subprocess_output(session: TerminalSession):
    """
    Background task that continuously reads from asyncio subprocess stdout and queues output

    Args:
        session: Terminal session to read from
    """
    logger.info(f"Started subprocess reader for task: {session.task_id}")

    try:
        while session.is_running:
            try:
                # Read from subprocess stdout
                chunk = await session.process.stdout.read(1024)

                if not chunk:
                    # EOF - process ended
                    logger.info(f"Subprocess ended for task: {session.task_id}")
                    break

                output = chunk.decode('utf-8', errors='ignore')
                if output:
                    # Queue output for WebSocket transmission
                    await session.read_queue.put(output)

            except Exception as e:
                logger.error(f"Error reading from subprocess: {e}")
                break

    finally:
        session.is_running = False
        logger.info(f"Subprocess reader stopped for task: {session.task_id}")


async def get_terminal_session(task_id: str) -> Optional[TerminalSession]:
    """
    Get an existing terminal session

    Args:
        task_id: Task identifier

    Returns:
        TerminalSession or None if not found
    """
    return _sessions.get(task_id)


async def close_terminal_session(task_id: str):
    """
    Close and remove a terminal session

    Args:
        task_id: Task identifier
    """
    session = _sessions.get(task_id)
    if session:
        await session.close()
        del _sessions[task_id]
        logger.info(f"Removed terminal session for task: {task_id}")


async def close_all_sessions():
    """Close all active terminal sessions (cleanup on shutdown)"""
    logger.info(f"Closing {len(_sessions)} terminal sessions")
    for task_id in list(_sessions.keys()):
        await close_terminal_session(task_id)
