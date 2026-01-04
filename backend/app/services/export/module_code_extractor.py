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
        logger.info(f"   ✓ package.json generated with {len(npm_deps)} packages")

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
        """Generate requirements.txt file."""
        with open(output_path, 'w') as f:
            f.write("# Module-specific Python dependencies\n")
            f.write("# Generated by Export Wizard\n\n")

            for package, version in sorted(dependencies.items()):
                if version and version != "latest":
                    f.write(f"{package}=={version}\n")
                else:
                    f.write(f"{package}\n")

    async def _generate_package_json(
        self,
        output_path: Path,
        module_name: str,
        display_name: str,
        dependencies: Dict[str, str]
    ):
        """Generate package.json file."""
        package_data = {
            "name": f"{module_name}-standalone",
            "version": "1.0.0",
            "description": f"{display_name} - Standalone Deployment",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint"
            },
            "dependencies": dependencies,
            "engines": {
                "node": ">=18.0.0",
                "npm": ">=9.0.0"
            }
        }

        with open(output_path, 'w') as f:
            json.dump(package_data, f, indent=2)

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
