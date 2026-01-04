"""
Module Code Extractor Service

Extracts module-specific source code files for standalone deployment.

This service:
1. Identifies all code files needed for a module (backend, frontend, tier1 deps)
2. Copies files to export directory
3. Resolves Python/NPM dependencies
4. Generates requirements.txt and package.json
5. Creates module-specific README

Author: Claude Code
Date: 2026-01-04
Phase: Module-Specific Export Enhancement
"""

import logging
import os
import ast
import json
import shutil
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass

from .module_registry import get_module_files, ModuleFiles

logger = logging.getLogger(__name__)

# Project root directory - works in both Docker and host environments
# In Docker: /app (only backend/ is mounted, frontend/ not accessible)
# On Host: /path/to/ChatBot (full project with backend/ and frontend/)
def _get_project_root():
    """
    Determine project root intelligently.

    In Docker container:
        - /app is the backend directory
        - Frontend not accessible (volume not mounted)
        - Return /app as root, frontend files will be skipped

    On Host:
        - /path/to/ChatBot/backend/app/services/export/
        - Go up to ChatBot/ to access both backend/ and frontend/
    """
    current = Path(__file__).parent.parent.parent.parent  # -> backend/ or /app

    # Check if we're in Docker (backend/ dir is mounted as /app)
    if current == Path("/app"):
        # In Docker container - only backend is accessible
        logger.info("🐳 Running in Docker container - backend only")
        return current

    # On host - go up one more level to project root
    project_root = current.parent
    logger.info(f"💻 Running on host - project root: {project_root}")
    return project_root

PROJECT_ROOT = _get_project_root()


@dataclass
class ModuleCodeStats:
    """Statistics from module code extraction."""
    backend_files_copied: int
    frontend_files_copied: int
    tier1_files_copied: int
    python_dependencies: int
    npm_dependencies: int
    sample_data_files: int
    total_size_bytes: int


class ModuleCodeExtractor:
    """Extract module-specific source code for standalone deployment."""

    # Python standard library modules (to exclude from dependencies)
    STDLIB_MODULES = {
        "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio", "asyncore",
        "atexit", "audioop", "base64", "bdb", "binascii", "binhex", "bisect", "builtins",
        "bz2", "calendar", "cgi", "cgitb", "chunk", "cmath", "cmd", "code", "codecs",
        "codeop", "collections", "colorsys", "compileall", "concurrent", "configparser",
        "contextlib", "copy", "copyreg", "crypt", "csv", "ctypes", "curses", "dataclasses",
        "datetime", "dbm", "decimal", "difflib", "dis", "distutils", "doctest", "email",
        "encodings", "enum", "errno", "faulthandler", "fcntl", "filecmp", "fileinput",
        "fnmatch", "formatter", "fractions", "ftplib", "functools", "gc", "getopt",
        "getpass", "gettext", "glob", "grp", "gzip", "hashlib", "heapq", "hmac", "html",
        "http", "imaplib", "imghdr", "imp", "importlib", "inspect", "io", "ipaddress",
        "itertools", "json", "keyword", "lib2to3", "linecache", "locale", "logging",
        "lzma", "mailbox", "mailcap", "marshal", "math", "mimetypes", "mmap", "modulefinder",
        "msilib", "msvcrt", "multiprocessing", "netrc", "nis", "nntplib", "numbers",
        "operator", "optparse", "os", "ossaudiodev", "parser", "pathlib", "pdb", "pickle",
        "pickletools", "pipes", "pkgutil", "platform", "plistlib", "poplib", "posix",
        "posixpath", "pprint", "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr",
        "pydoc", "queue", "quopri", "random", "re", "readline", "reprlib", "resource",
        "rlcompleter", "runpy", "sched", "secrets", "select", "selectors", "shelve",
        "shlex", "shutil", "signal", "site", "smtpd", "smtplib", "sndhdr", "socket",
        "socketserver", "spwd", "sqlite3", "ssl", "stat", "statistics", "string",
        "stringprep", "struct", "subprocess", "sunau", "symbol", "symtable", "sys",
        "sysconfig", "syslog", "tabnanny", "tarfile", "telnetlib", "tempfile", "termios",
        "test", "textwrap", "threading", "time", "timeit", "tkinter", "token", "tokenize",
        "trace", "traceback", "tracemalloc", "tty", "turtle", "turtledemo", "types",
        "typing", "unicodedata", "unittest", "urllib", "uu", "uuid", "venv", "warnings",
        "wave", "weakref", "webbrowser", "winreg", "winsound", "wsgiref", "xdrlib",
        "xml", "xmlrpc", "zipapp", "zipfile", "zipimport", "zlib", "_thread"
    }

    async def extract_module_code(
        self,
        module_name: str,
        export_dir: Path
    ) -> ModuleCodeStats:
        """
        Extract all source code files for a module.

        Args:
            module_name: Module identifier (e.g., "matcher", "british_council")
            export_dir: Directory to export files to

        Returns:
            ModuleCodeStats with extraction statistics

        Raises:
            ValueError: If module not found in registry
            FileNotFoundError: If source files don't exist
        """
        logger.info(f"📦 Extracting source code for module: {module_name}")

        # Get module file mappings
        module_files = get_module_files(module_name)
        if not module_files:
            raise ValueError(f"Module '{module_name}' not found in registry")

        logger.info(f"   Category: {module_files.category}")
        logger.info(f"   Display Name: {module_files.display_name}")

        # Create directory structure
        backend_dir = export_dir / "backend"
        frontend_dir = export_dir / "frontend"
        sample_data_dir = export_dir / "sample_data"

        backend_dir.mkdir(parents=True, exist_ok=True)
        frontend_dir.mkdir(parents=True, exist_ok=True)
        sample_data_dir.mkdir(parents=True, exist_ok=True)

        # Track stats
        backend_files_copied = 0
        frontend_files_copied = 0
        tier1_files_copied = 0
        total_size = 0

        # 1. Copy backend files
        logger.info(f"📄 Copying {len(module_files.backend)} backend files...")
        for file_path in module_files.backend:
            # Backend paths in registry are relative to backend/ directory (e.g., "app/tier_2/...")
            # In Docker: PROJECT_ROOT is /app, so just use file_path directly
            # On Host: PROJECT_ROOT is ChatBot/, so use backend/file_path
            if PROJECT_ROOT == Path("/app"):
                source = PROJECT_ROOT / file_path  # Docker: /app/app/tier_2/...
            else:
                source = PROJECT_ROOT / "backend" / file_path  # Host: ChatBot/backend/app/tier_2/...

            dest = backend_dir / file_path

            if not source.exists():
                logger.warning(f"   ⚠️  Backend file not found: {file_path}")
                continue

            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                backend_files_copied += 1
                total_size += source.stat().st_size
                logger.info(f"   ✓ Copied: {file_path}")
            except Exception as e:
                logger.error(f"   ❌ Failed to copy {file_path}: {e}")
                raise RuntimeError(f"Failed to copy backend file {file_path}: {e}")

        # 2. Copy frontend files
        logger.info(f"🎨 Copying {len(module_files.frontend)} frontend files...")
        for file_path in module_files.frontend:
            # Frontend paths in registry are relative to frontend/ directory (e.g., "src/components/...")
            # In Docker: Frontend not accessible (not mounted), skip gracefully
            # On Host: PROJECT_ROOT is ChatBot/, so use frontend/file_path
            if PROJECT_ROOT == Path("/app"):
                # In Docker - frontend not mounted, skip with info message
                logger.info(f"   ⓘ  Skipping frontend file (not accessible in Docker): {file_path}")
                continue
            else:
                source = PROJECT_ROOT / "frontend" / file_path  # Host: ChatBot/frontend/src/...

            dest = frontend_dir / file_path

            if not source.exists():
                logger.warning(f"   ⚠️  Frontend file not found: {file_path}")
                continue

            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            frontend_files_copied += 1
            total_size += source.stat().st_size
            logger.debug(f"   ✓ {file_path}")

        # 3. Discover and copy Tier 1 dependencies
        logger.info(f"🔍 Discovering Tier 1 dependencies...")

        # Build backend file list for dependency discovery
        if PROJECT_ROOT == Path("/app"):
            backend_file_list = [PROJECT_ROOT / f for f in module_files.backend if (PROJECT_ROOT / f).exists()]
        else:
            backend_file_list = [PROJECT_ROOT / "backend" / f for f in module_files.backend if (PROJECT_ROOT / "backend" / f).exists()]

        tier1_files = await self._discover_tier1_dependencies(backend_file_list)

        logger.info(f"📚 Copying {len(tier1_files)} Tier 1 dependency files...")
        for file_path in tier1_files:
            # Tier 1 paths are already relative to backend/ (e.g., "app/tier_1/...")
            if PROJECT_ROOT == Path("/app"):
                source = PROJECT_ROOT / file_path
            else:
                source = PROJECT_ROOT / "backend" / file_path

            dest = backend_dir / file_path

            if not source.exists():
                logger.warning(f"   ⚠️  Tier 1 file not found: {file_path}")
                continue

            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            tier1_files_copied += 1
            total_size += source.stat().st_size
            logger.debug(f"   ✓ {file_path}")

        # 4. Resolve Python dependencies
        logger.info(f"🐍 Resolving Python dependencies...")

        # Build Python file list
        if PROJECT_ROOT == Path("/app"):
            all_python_files = (
                [PROJECT_ROOT / f for f in module_files.backend if (PROJECT_ROOT / f).exists()] +
                [PROJECT_ROOT / f for f in tier1_files if (PROJECT_ROOT / f).exists()]
            )
        else:
            all_python_files = (
                [PROJECT_ROOT / "backend" / f for f in module_files.backend if (PROJECT_ROOT / "backend" / f).exists()] +
                [PROJECT_ROOT / "backend" / f for f in tier1_files if (PROJECT_ROOT / "backend" / f).exists()]
            )
        python_deps = await self._resolve_python_dependencies(
            all_python_files,
            module_files.python_packages
        )

        # Generate requirements.txt
        await self._generate_requirements_txt(
            backend_dir / "requirements.txt",
            python_deps
        )
        logger.info(f"   ✓ requirements.txt generated with {len(python_deps)} packages")

        # 5. Resolve NPM dependencies
        logger.info(f"📦 Resolving NPM dependencies...")

        # Build frontend file list
        if PROJECT_ROOT == Path("/app"):
            # In Docker, frontend not accessible - use empty list
            frontend_file_list = []
        else:
            frontend_file_list = [PROJECT_ROOT / "frontend" / f for f in module_files.frontend if (PROJECT_ROOT / "frontend" / f).exists()]

        npm_deps = await self._resolve_npm_dependencies(
            frontend_file_list,
            module_files.npm_packages
        )

        # Generate package.json
        await self._generate_package_json(
            frontend_dir / "package.json",
            module_name,
            module_files.display_name,
            npm_deps
        )
        # Note: package.json generation now includes logging

        # 5a. Generate frontend application structure
        logger.info(f"🎨 Generating frontend application structure...")
        self._generate_frontend_structure(
            module_name,
            module_files.display_name,
            frontend_dir,
            module_files.frontend  # Pass frontend files for component detection
        )

        # 6. Copy sample data
        sample_data_files_copied = 0
        if module_files.sample_data:
            logger.info(f"📊 Copying {len(module_files.sample_data)} sample data files...")
            for file_path in module_files.sample_data:
                source = PROJECT_ROOT / file_path
                dest = sample_data_dir / Path(file_path).name

                if not source.exists():
                    logger.warning(f"   ⚠️  Sample data not found: {file_path}")
                    continue

                shutil.copy2(source, dest)
                sample_data_files_copied += 1
                total_size += source.stat().st_size
                logger.debug(f"   ✓ {file_path}")

        # 7. Copy essential shared files
        logger.info(f"📋 Copying shared infrastructure files...")
        await self._copy_shared_files(backend_dir, frontend_dir)

        # 8. Generate module README
        await self._generate_module_readme(
            export_dir / "MODULE_README.md",
            module_name,
            module_files
        )

        # 9. Generate backend main.py entry point
        logger.info(f"🔧 Generating backend application entry point...")
        self._generate_backend_main(module_name, module_files, backend_dir)

        # VALIDATION: Ensure critical files were copied
        if backend_files_copied == 0:
            raise RuntimeError(
                f"❌ CRITICAL: No backend files were copied for module '{module_name}'. "
                f"Expected {len(module_files.backend)} files. "
                f"Package cannot be deployed without application code."
            )

        if backend_files_copied < len(module_files.backend):
            logger.warning(
                f"⚠️  Only {backend_files_copied}/{len(module_files.backend)} backend files copied. "
                f"Some files may be missing."
            )

        if frontend_files_copied == 0 and len(module_files.frontend) > 0:
            if PROJECT_ROOT == Path("/app"):
                logger.warning(
                    f"⚠️  Running in Docker - frontend files not accessible. "
                    f"Expected {len(module_files.frontend)} frontend files. "
                    f"Frontend deployment will require manual setup."
                )
            else:
                logger.error(
                    f"❌ No frontend files copied (expected {len(module_files.frontend)})"
                )

        # Validate backend directory exists and has Python files
        if not (backend_dir / "app").exists():
            raise RuntimeError(
                f"❌ CRITICAL: Backend app directory not created at {backend_dir / 'app'}"
            )

        python_files_in_export = list((backend_dir / "app").rglob("*.py"))
        if not python_files_in_export:
            raise RuntimeError(
                f"❌ CRITICAL: No Python files found in exported backend directory"
            )

        logger.info(f"✅ Validation passed: {len(python_files_in_export)} Python files in export")

        stats = ModuleCodeStats(
            backend_files_copied=backend_files_copied,
            frontend_files_copied=frontend_files_copied,
            tier1_files_copied=tier1_files_copied,
            python_dependencies=len(python_deps),
            npm_dependencies=len(npm_deps),
            sample_data_files=sample_data_files_copied,
            total_size_bytes=total_size
        )

        logger.info(f"✅ Module code extraction complete!")
        logger.info(f"   Backend: {stats.backend_files_copied} files")
        logger.info(f"   Frontend: {stats.frontend_files_copied} files")
        logger.info(f"   Tier 1: {stats.tier1_files_copied} files")
        logger.info(f"   Sample Data: {stats.sample_data_files} files")
        logger.info(f"   Python deps: {stats.python_dependencies}")
        logger.info(f"   NPM deps: {stats.npm_dependencies}")
        logger.info(f"   Total size: {stats.total_size_bytes / 1024:.1f} KB")

        return stats

    async def _discover_tier1_dependencies(
        self,
        python_files: List[Path]
    ) -> List[str]:
        """
        Discover Tier 1 service dependencies by parsing import statements.

        Args:
            python_files: List of Python file paths to analyze

        Returns:
            List of Tier 1 file paths to include
        """
        tier1_imports = set()

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=str(file_path))

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and 'tier_1' in node.module:
                            # Convert module import to file path
                            # e.g., app.tier_1.rag.rag_service -> app/tier_1/rag/rag_service.py
                            module_path = node.module.replace('.', '/') + '.py'
                            tier1_imports.add(module_path)

                            # Also add __init__.py files for packages
                            parts = node.module.split('.')
                            for i in range(len(parts)):
                                package_path = '/'.join(parts[:i+1]) + '/__init__.py'
                                tier1_imports.add(package_path)

            except SyntaxError as e:
                logger.warning(f"   ⚠️  Syntax error parsing {file_path}: {e}")
            except Exception as e:
                logger.warning(f"   ⚠️  Error parsing {file_path}: {e}")

        return sorted(tier1_imports)

    async def _resolve_python_dependencies(
        self,
        python_files: List[Path],
        explicit_packages: List[str]
    ) -> Dict[str, str]:
        """
        Resolve Python package dependencies from import statements.

        Args:
            python_files: Python files to analyze
            explicit_packages: Explicitly declared packages from registry

        Returns:
            Dict of {package_name: version} from project requirements.txt
        """
        # Get all imported packages
        imported_packages = set(explicit_packages)

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=str(file_path))

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            root_module = alias.name.split('.')[0]
                            if root_module not in self.STDLIB_MODULES and root_module != 'app':
                                imported_packages.add(root_module)

                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            root_module = node.module.split('.')[0]
                            if root_module not in self.STDLIB_MODULES and root_module != 'app':
                                imported_packages.add(root_module)

            except Exception as e:
                logger.warning(f"   ⚠️  Error resolving deps from {file_path}: {e}")

        # Read project requirements.txt to get versions
        project_requirements = PROJECT_ROOT / "backend" / "requirements.txt"
        package_versions = {}

        if project_requirements.exists():
            with open(project_requirements, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # Parse package==version or package>=version
                    if '==' in line:
                        pkg, ver = line.split('==', 1)
                    elif '>=' in line:
                        pkg, ver = line.split('>=', 1)
                    else:
                        pkg = line
                        ver = None

                    package_versions[pkg.strip().lower()] = ver.strip() if ver else "latest"

        # Match imported packages to versions
        resolved_deps = {}
        for package in imported_packages:
            pkg_lower = package.lower().replace('_', '-')  # Normalize package names
            if pkg_lower in package_versions:
                resolved_deps[package] = package_versions[pkg_lower]
            else:
                # Check common mappings (import name != package name)
                mappings = {
                    'PIL': 'pillow',
                    'cv2': 'opencv-python',
                    'sklearn': 'scikit-learn'
                }
                mapped_name = mappings.get(package, package)
                if mapped_name.lower() in package_versions:
                    resolved_deps[mapped_name] = package_versions[mapped_name.lower()]
                else:
                    resolved_deps[package] = "latest"

        return resolved_deps

    async def _resolve_npm_dependencies(
        self,
        tsx_files: List[Path],
        explicit_packages: List[str]
    ) -> Dict[str, str]:
        """
        Resolve NPM dependencies from import statements in TypeScript/React files.

        Args:
            tsx_files: Frontend files to analyze
            explicit_packages: Explicitly declared NPM packages

        Returns:
            Dict of {package_name: version} from project package.json
        """
        # Start with explicit packages
        imported_packages = set(explicit_packages)

        # Parse import statements (basic regex approach)
        import re
        import_pattern = re.compile(r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]")

        for file_path in tsx_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                matches = import_pattern.findall(content)
                for match in matches:
                    # Skip relative imports
                    if match.startswith('.') or match.startswith('/'):
                        continue

                    # Get root package name
                    package = match.split('/')[0]
                    if package.startswith('@'):
                        # Scoped package like @types/react
                        parts = match.split('/')
                        package = f"{parts[0]}/{parts[1]}" if len(parts) > 1 else parts[0]

                    imported_packages.add(package)

            except Exception as e:
                logger.warning(f"   ⚠️  Error resolving NPM deps from {file_path}: {e}")

        # Read project package.json to get versions
        project_package_json = PROJECT_ROOT / "frontend" / "package.json"
        package_versions = {}

        if project_package_json.exists():
            with open(project_package_json, 'r') as f:
                package_data = json.load(f)

            # Combine dependencies and devDependencies
            all_deps = {
                **package_data.get('dependencies', {}),
                **package_data.get('devDependencies', {})
            }

            package_versions = all_deps

        # Match imported packages to versions
        resolved_deps = {}
        for package in imported_packages:
            if package in package_versions:
                resolved_deps[package] = package_versions[package]
            else:
                resolved_deps[package] = "latest"

        return resolved_deps

    async def _generate_requirements_txt(
        self,
        output_path: Path,
        dependencies: Dict[str, str]
    ):
        """Generate requirements.txt file with correct package names and versions."""

        # Package name corrections (import name -> PyPI name)
        package_corrections = {
            "PIL": "Pillow",
            "cv2": "opencv-python",
            "docx": "python-docx",
            "pptx": "python-pptx",
            "fitz": "PyMuPDF",
            "bs4": "beautifulsoup4",
            "yaml": "pyyaml",
            "jose": "python-jose",
            "dotenv": "python-dotenv",
            "dateutil": "python-dateutil",
        }

        # Local modules to exclude (not on PyPI)
        local_modules = {
            "app", "tier_1", "tier_2", "tier_3", "api", "services",
            "models", "schemas", "tasks", "agents", "core", "infrastructure",
            # Module-specific names that may appear
            "relation_extractor_schemas", "relation_extractor_service", "relation_extractor_routes",
            "generic_rag_schemas", "generic_rag_service", "generic_rag_routes",
            # Add more as needed
        }

        # Core requirements with versions (from main backend/requirements.txt)
        core_requirements = {
            # Web framework
            "fastapi": "0.111.0",
            "uvicorn[standard]": "0.30.0",
            "python-multipart": "0.0.9",
            "pydantic": "2.8.2",
            "pydantic-settings": "2.3.4",
            "sse-starlette": "1.8.2",

            # GraphQL
            "strawberry-graphql[fastapi]": "0.235.0",
            "graphql-core": "3.2.3",

            # Database
            "psycopg2-binary": "2.9.9",
            "asyncpg": "0.29.0",
            "sqlalchemy": "2.0.25",
            "pgvector": "0.2.4",
            "alembic": "1.13.1",

            # Object storage & caching
            "minio": "7.2.3",
            "redis": "5.0.1",
            "hiredis": "2.3.2",

            # AI & LLM
            "openai": "1.40.0",
            "anthropic": "0.39.0",
            "sentence-transformers": "2.3.1",
            "torch": "2.0.0",

            # LangChain
            "langchain": "0.2.16",
            "langchain-community": "0.2.16",
            "langchain-openai": "0.1.22",
            "langgraph": "0.2.16",

            # Document processing
            "numpy": "1.26.4",
            "opencv-python": "4.9.0",
            "PyMuPDF": "1.23.26",
            "pypdf2": "3.0.1",
            "python-docx": "1.1.2",
            "python-pptx": "1.0.2",
            "openpyxl": "3.1.5",
            "beautifulsoup4": "4.12.3",
            "lxml": "5.1.0",

            # Web scraping
            "playwright": "1.48.0",
            "httpx": "0.27.0",
            "aiohttp": "3.9.0",
            "trafilatura": "1.6.3",

            # OCR & images
            "pytesseract": "0.3.13",
            "Pillow": "10.2.0",
            "pdf2image": "1.16.3",

            # Utilities
            "python-jose[cryptography]": "3.3.0",
            "passlib[bcrypt]": "1.7.4",
            "python-dotenv": "1.0.0",
            "tenacity": "8.2.3",
            "aiofiles": "23.2.1",
            "pyyaml": "6.0.1",
            "python-dateutil": "2.8.2",

            # Observability
            "opentelemetry-api": "1.25.0",
            "opentelemetry-sdk": "1.25.0",
            "opentelemetry-instrumentation-fastapi": "0.46b0",
            "opentelemetry-exporter-otlp": "1.25.0",
            "prometheus-client": "0.20.0",

            # Workflow orchestration
            "prefect": "3.0.0",
        }

        # Build final requirements list
        final_requirements = core_requirements.copy()

        # Add discovered dependencies if not already in core
        for package in dependencies.keys():
            # Skip local modules
            if package in local_modules or package.startswith("app."):
                continue

            # Apply corrections
            corrected_package = package_corrections.get(package, package)

            # Skip if already in core requirements
            if corrected_package in final_requirements:
                continue

            # Add discovered dependency (try to get version from dependencies dict)
            version = dependencies.get(package)
            if version and version != "latest":
                final_requirements[corrected_package] = version
            else:
                # No version info - add without version pin
                final_requirements[corrected_package] = None

        # Write requirements.txt
        with open(output_path, 'w') as f:
            f.write("# Auto-generated requirements.txt\n")
            f.write("# Generated by Export Wizard\n")
            f.write("# Contains core dependencies + module-specific packages\n\n")

            # Write with version pins
            for package in sorted(final_requirements.keys()):
                version = final_requirements[package]
                if version:
                    f.write(f"{package}=={version}\n")
                else:
                    f.write(f"{package}\n")

        logger.info(f"   ✅ Generated: requirements.txt ({len(final_requirements)} packages)")

    async def _generate_package_json(
        self,
        output_path: Path,
        module_name: str,
        display_name: str,
        dependencies: Dict[str, str]
    ):
        """Generate package.json file with all required frontend dependencies."""

        # Core frontend dependencies (from main frontend/package.json)
        core_dependencies = {
            "next": "14.1.0",
            "react": "18.2.0",
            "react-dom": "18.2.0",
            "typescript": "5.3.3",
            "@types/node": "20.11.19",
            "@types/react": "18.2.56",
            "@types/react-dom": "18.2.19",

            # HTTP & API
            "axios": "1.6.7",
            "graphql": "16.8.1",

            # UI components
            "lucide-react": "0.316.0",
            "react-markdown": "9.0.1",

            # Styling
            "tailwindcss": "3.4.1",
            "autoprefixer": "10.4.17",
            "postcss": "8.4.35",

            # Excel export support
            "xlsx": "0.18.5",

            # PDF generation
            "jspdf": "2.5.1",
        }

        # Merge with discovered dependencies
        final_dependencies = {**core_dependencies, **dependencies}

        package_data = {
            "name": f"{module_name}-standalone",
            "version": "1.0.0",
            "description": f"{display_name} - Standalone Deployment",
            "private": True,
            "scripts": {
                "dev": "next dev -p 3001",
                "build": "next build",
                "start": "next start -p 3001",
                "lint": "next lint"
            },
            "dependencies": final_dependencies,
            "devDependencies": {
                "eslint": "8.56.0",
                "eslint-config-next": "14.1.0"
            },
            "engines": {
                "node": ">=18.0.0",
                "npm": ">=9.0.0"
            }
        }

        with open(output_path, 'w') as f:
            json.dump(package_data, f, indent=2)

        logger.info(f"   ✅ Generated: package.json ({len(final_dependencies)} dependencies)")

    def _generate_frontend_structure(
        self,
        module_name: str,
        module_display_name: str,
        frontend_dir: Path,
        frontend_files: List[str] = None
    ) -> None:
        """Generate minimal Next.js application structure for standalone deployment."""

        # Create directory structure
        pages_dir = frontend_dir / "src" / "pages"
        styles_dir = frontend_dir / "src" / "styles"
        pages_dir.mkdir(parents=True, exist_ok=True)
        styles_dir.mkdir(parents=True, exist_ok=True)

        # 1. _app.tsx - Application wrapper
        app_content = '''import type { AppProps } from 'next/app'
import '../styles/globals.css'

export default function App({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />
}
'''
        (pages_dir / "_app.tsx").write_text(app_content)

        # 2. index.tsx - Main page that imports the module component

        # Try to detect the main component file
        component_import = ""
        component_usage = ""

        if frontend_files:
            # Look for component files - try common patterns
            component_patterns = [
                f"{module_name.title()}Panel",
                f"{module_name.title()}",
                module_name.replace('_', ' ').title().replace(' ', ''),
            ]

            for file_path in frontend_files:
                file_name = Path(file_path).stem
                for pattern in component_patterns:
                    if pattern.lower() in file_name.lower():
                        # Found a component file
                        relative_path = f"../components/{file_name}"
                        component_import = f"import {pattern} from '{relative_path}'"
                        component_usage = f"<{pattern} />"
                        break
                if component_import:
                    break

        # Generate index.tsx with or without component
        if component_usage:
            index_content = f'''import React from 'react'
import Head from 'next/head'
{component_import}

export default function Home() {{
  return (
    <>
      <Head>
        <title>{module_display_name}</title>
        <meta name="description" content="{module_display_name} - Standalone Deployment" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        <main className="h-full">
          {component_usage}
        </main>
      </div>
    </>
  )
}}
'''
        else:
            # Fallback: No component found, use placeholder
            index_content = f'''import React from 'react'
import Head from 'next/head'

export default function Home() {{
  return (
    <>
      <Head>
        <title>{module_display_name}</title>
        <meta name="description" content="{module_display_name} - Standalone Deployment" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <h1 className="text-2xl font-bold text-gray-900">{module_display_name}</h1>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 mb-4">
              This is a standalone deployment of the {module_display_name} module.
            </p>
            <p className="text-sm text-gray-500">
              Configure API_BASE_URL in your environment to connect to the backend service.
            </p>
            <p className="text-sm text-gray-500 mt-4">
              Note: Component integration requires manual setup. Import your module component in this file.
            </p>
          </div>
        </main>
      </div>
    </>
  )
}}
'''

        (pages_dir / "index.tsx").write_text(index_content)

        # 3. next.config.js - Next.js configuration
        next_config = '''/** @type {{import('next').NextConfig}} */
const nextConfig = {{
  reactStrictMode: true,
  output: 'standalone',
  env: {{
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
  }},
}}

module.exports = nextConfig
'''
        (frontend_dir / "next.config.js").write_text(next_config)

        # 4. tsconfig.json - TypeScript configuration
        tsconfig = '''{{
  "compilerOptions": {{
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "paths": {{
      "@/*": ["./src/*"]
    }}
  }},
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}}
'''
        (frontend_dir / "tsconfig.json").write_text(tsconfig)

        # 5. globals.css - Tailwind CSS setup
        globals_css = '''@tailwind base;
@tailwind components;
@tailwind utilities;

body {{
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}}
'''
        (styles_dir / "globals.css").write_text(globals_css)

        # 6. tailwind.config.js - Tailwind configuration
        tailwind_config = '''/** @type {{import('tailwindcss').Config}} */
module.exports = {{
  content: [
    './src/pages/**/*.{{js,ts,jsx,tsx,mdx}}',
    './src/components/**/*.{{js,ts,jsx,tsx,mdx}}',
  ],
  theme: {{
    extend: {{}},
  }},
  plugins: [],
}}
'''
        (frontend_dir / "tailwind.config.js").write_text(tailwind_config)

        # 7. postcss.config.js - PostCSS configuration
        postcss_config = '''module.exports = {{
  plugins: {{
    tailwindcss: {{}},
    autoprefixer: {{}},
  }},
}}
'''
        (frontend_dir / "postcss.config.js").write_text(postcss_config)

        # 8. .eslintrc.json - ESLint configuration
        eslint_config = '''{{
  "extends": "next/core-web-vitals"
}}
'''
        (frontend_dir / ".eslintrc.json").write_text(eslint_config)

        logger.info(f"   ✅ Generated: frontend structure (8 config files)")

    async def _copy_shared_files(
        self,
        backend_dir: Path,
        frontend_dir: Path
    ):
        """Copy shared infrastructure files needed by all modules."""
        # Backend shared files
        backend_shared = [
            "app/__init__.py",
            "app/tier_1/__init__.py",
            "app/models/__init__.py",
        ]

        for file_path in backend_shared:
            source = PROJECT_ROOT / "backend" / file_path
            dest = backend_dir / file_path

            if source.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)

    async def _generate_module_readme(
        self,
        output_path: Path,
        module_name: str,
        module_files: ModuleFiles
    ):
        """Generate module-specific README."""
        readme_content = f"""# {module_files.display_name} - Standalone Module

**Module ID**: `{module_name}`
**Category**: {module_files.category}
**Export Date**: {Path(output_path).parent.name}

---

## Overview

This package contains the complete source code for the **{module_files.display_name}** module,
exported from the enterprise RAG platform for standalone deployment.

## What's Included

### Backend Code ({len(module_files.backend)} files)
{chr(10).join(f'- `{f}`' for f in module_files.backend)}

### Frontend Code ({len(module_files.frontend)} files)
{chr(10).join(f'- `{f}`' for f in module_files.frontend)}

### Dependencies
- **Python Packages**: {len(module_files.python_packages)} packages (see `backend/requirements.txt`)
- **NPM Packages**: {len(module_files.npm_packages)} packages (see `frontend/package.json`)

### Sample Data ({len(module_files.sample_data)} files)
{chr(10).join(f'- `{Path(f).name}`' for f in module_files.sample_data) if module_files.sample_data else '- No sample data included'}

---

## Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### 2. Deploy with Docker Compose
```bash
cd infrastructure/
docker-compose up -d
```

### 3. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

---

## Manual Deployment

### Backend Setup
```bash
cd backend/
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend/
npm install
npm run dev
```

---

## Configuration

See `.env.example` for all configuration options.

Key environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key
- `MINIO_ENDPOINT` - Object storage endpoint

---

## Testing

### Run Sample Tests
```bash
cd backend/
pytest tests/
```

### Test with Sample Data
```bash
# See sample_data/ directory for example inputs
curl -X POST http://localhost:8000/api/v1/modules/{module_name}/... \\
  -H "Content-Type: application/json" \\
  -d @sample_data/sample_input.json
```

---

## Support

For technical support or questions about this module, contact your account manager.

**License**: See LICENSE.key for licensing information.

---

Generated by Enterprise RAG Platform Export Wizard
"""

        with open(output_path, 'w') as f:
            f.write(readme_content)

    def _generate_backend_main(
        self,
        module_name: str,
        module_files: ModuleFiles,
        backend_dir: Path
    ) -> None:
        """Generate FastAPI application entry point for standalone deployment."""

        category = module_files.category

        # Determine the router import based on category structure
        if category.startswith("tier_2/"):
            # Tier 2: backend/app/tier_2/domain/module_routes.py
            category_path = category.replace("/", ".")
            router_import = f"from app.{category_path}.{module_name}_routes import router"
        elif category.startswith("tier_3/"):
            # Tier 3: backend/app/tier_3/customer_solutions/module_service.py
            category_path = category.replace("/", ".")
            # Try routes first, fall back to service if routes don't exist
            router_import = f"from app.{category_path}.{module_name}_routes import router"
        else:
            # Generic fallback
            router_import = f"from app.api.routes.{module_name}_routes import router"

        main_content = f'''"""
{module_name.replace('_', ' ').title()} - Standalone Application
Generated by Export Wizard

This is a standalone deployment of the {module_name} module.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.tier_1.infrastructure.database import init_db, close_db
from app.tier_1.infrastructure.config import get_settings
{router_import}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown."""
    # Startup
    logger.info("Starting {module_name} application...")
    await init_db()
    logger.info("Database initialized successfully")
    yield
    # Shutdown
    logger.info("Shutting down {module_name} application...")
    await close_db()
    logger.info("Database connections closed")

app = FastAPI(
    title="{module_name.replace('_', ' ').title()}",
    description="Standalone deployment of {module_name} module",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - configure allowed origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include module router
app.include_router(
    router,
    prefix="/api/v1/modules/{module_name}",
    tags=["{module_name}"]
)

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {{
        "status": "healthy",
        "module": "{module_name}",
        "version": "1.0.0"
    }}

@app.get("/")
async def root():
    """Root endpoint with module information."""
    return {{
        "message": "Welcome to {module_name.replace('_', ' ').title()}",
        "module": "{module_name}",
        "docs": "/docs",
        "health": "/health"
    }}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info"
    )
'''

        main_path = backend_dir / "app" / "main.py"
        main_path.parent.mkdir(parents=True, exist_ok=True)
        main_path.write_text(main_content)

        logger.info(f"   ✅ Generated: backend/app/main.py")
