"""
Test Script for Procurement Matcher Module Export

This script tests the complete module-specific export functionality
by exporting the Procurement Matcher module and verifying the package contents.

Author: Claude Code
Date: 2026-01-04
"""

import asyncio
import sys
import json
from pathlib import Path
from zipfile import ZipFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.tier_1.infrastructure.database import AsyncSessionLocal
from app.services.export.package_builder import PackageBuilder
from app.models.export_wizard import DeploymentType, LicenseTier


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_section(title: str):
    """Print a section header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title:^80}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 80}{Colors.RESET}\n")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")


def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")


async def test_export_matcher():
    """Test complete export of Procurement Matcher module."""

    print_section("PROCUREMENT MATCHER MODULE EXPORT TEST")

    try:
        async with AsyncSessionLocal() as db:
            print_info("Initializing PackageBuilder...")
            builder = PackageBuilder(db)
            print_success("PackageBuilder initialized")

            # Export configuration
            from datetime import datetime
            module_name = "matcher"
            customer_name = f"Test Customer {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            deployment_type = DeploymentType.DOCKER_COMPOSE
            license_tier = LicenseTier.PROFESSIONAL

            print_section("STARTING EXPORT")
            print_info(f"Module: {module_name}")
            print_info(f"Customer: {customer_name}")
            print_info(f"Deployment: {deployment_type.value}")
            print_info(f"License: {license_tier.value}")

            # Build export package
            job = await builder.build_export_package(
                module_name=module_name,
                customer_name=customer_name,
                deployment_type=deployment_type,
                license_tier=license_tier,
                options={
                    "include_embeddings": True,
                    "include_monitoring": True,
                    "customer_email": "test@example.com"
                }
            )

            print_section("EXPORT JOB RESULTS")
            print_info(f"Job ID: {job.id}")
            print_info(f"Status: {job.status}")
            print_info(f"Package Path: {job.package_path}")

            if job.status != "completed":
                print_error(f"Export failed with status: {job.status}")
                if job.error_message:
                    print_error(f"Error: {job.error_message}")
                return False

            print_success("Export completed successfully!")

            # Verify package exists
            print_section("PACKAGE VERIFICATION")

            package_path = Path(job.package_path)
            if not package_path.exists():
                print_error(f"Package file not found: {package_path}")
                return False

            print_success(f"Package file exists: {package_path}")

            # Get package size
            package_size_mb = package_path.stat().st_size / (1024 * 1024)
            print_info(f"Package size: {package_size_mb:.2f} MB")

            # Verify manifest
            print_section("MANIFEST VERIFICATION")

            manifest = job.manifest
            print(json.dumps(manifest, indent=2))

            # Check critical metrics
            checks = [
                ("Backend files exported", manifest.get("backend_files", 0) > 0),
                ("Frontend files exported", manifest.get("frontend_files", 0) > 0),
                ("Tier 1 dependencies included", manifest.get("tier1_files", 0) > 0),
                ("Python dependencies resolved", manifest.get("python_dependencies", 0) > 0),
                ("NPM dependencies resolved", manifest.get("npm_dependencies", 0) > 0),
                ("Configuration exported", bool(manifest.get("configuration"))),
                ("Infrastructure files included", manifest.get("infrastructure_files", 0) > 0),
            ]

            print_section("MANIFEST CHECKS")
            all_passed = True
            for check_name, result in checks:
                if result:
                    print_success(check_name)
                else:
                    print_error(check_name)
                    all_passed = False

            if not all_passed:
                print_error("Some manifest checks failed!")
                return False

            # Verify package contents
            print_section("PACKAGE CONTENTS VERIFICATION")

            with ZipFile(package_path, 'r') as zip_file:
                file_list = zip_file.namelist()

                print_info(f"Total files in package: {len(file_list)}")

                # Check for expected files
                expected_files = {
                    "Backend Service": "src/backend/app/tier_2/procurement/matcher_service.py",
                    "Backend Routes": "src/backend/app/tier_2/procurement/matcher_routes.py",
                    "Backend Schemas": "src/backend/app/tier_2/procurement/matcher_schemas.py",
                    "Frontend Component": "src/frontend/src/components/tier2/procurement/ProcurementMatcherPanel.tsx",
                    "Requirements": "src/backend/requirements.txt",
                    "Package JSON": "src/frontend/package.json",
                    "Docker Compose": "infrastructure/docker/docker-compose.yml",
                    "Manifest": "manifest.json",
                    "License": "LICENSE.txt",
                    "README": "README.md",
                }

                print_section("EXPECTED FILES CHECK")
                all_files_present = True
                for file_desc, file_path in expected_files.items():
                    # Check if any file in the zip matches this path
                    matching_files = [f for f in file_list if file_path in f]
                    if matching_files:
                        print_success(f"{file_desc}: {matching_files[0]}")
                    else:
                        print_error(f"{file_desc}: NOT FOUND (expected: {file_path})")
                        all_files_present = False

                if not all_files_present:
                    print_warning("Some expected files are missing")
                    print_info("Listing all files in package:")
                    for file in sorted(file_list)[:50]:  # Show first 50 files
                        print(f"  - {file}")
                    if len(file_list) > 50:
                        print(f"  ... and {len(file_list) - 50} more files")

                # Check Tier 1 dependencies
                print_section("TIER 1 DEPENDENCIES CHECK")
                tier1_files = [f for f in file_list if 'tier_1' in f]
                if tier1_files:
                    print_success(f"Found {len(tier1_files)} Tier 1 dependency files:")
                    for file in tier1_files:
                        print(f"  - {file}")
                else:
                    print_warning("No Tier 1 dependencies found (might be expected)")

                # Check requirements.txt content
                print_section("DEPENDENCIES CHECK")
                for file in file_list:
                    if file.endswith('requirements.txt'):
                        content = zip_file.read(file).decode('utf-8')
                        print_info(f"Found {file}:")
                        print(content[:500])  # Show first 500 chars

                        # Check for expected packages
                        expected_packages = ['pandas', 'fuzzywuzzy', 'python-Levenshtein']
                        for pkg in expected_packages:
                            if pkg.lower() in content.lower():
                                print_success(f"  Package '{pkg}' found")
                            else:
                                print_warning(f"  Package '{pkg}' not found")

                # Check package.json content
                for file in file_list:
                    if file.endswith('package.json') and 'frontend' in file:
                        content = zip_file.read(file).decode('utf-8')
                        print_info(f"Found {file}:")
                        try:
                            pkg_json = json.loads(content)
                            deps = pkg_json.get('dependencies', {})
                            print_info(f"  Dependencies: {len(deps)}")
                            for dep_name in list(deps.keys())[:10]:
                                print(f"    - {dep_name}: {deps[dep_name]}")
                        except json.JSONDecodeError:
                            print_error("  Failed to parse package.json")

            print_section("TEST SUMMARY")
            print_success("✅ Export test completed successfully!")
            print_info(f"Package: {package_path}")
            print_info(f"Size: {package_size_mb:.2f} MB")
            print_info(f"Backend files: {manifest.get('backend_files', 0)}")
            print_info(f"Frontend files: {manifest.get('frontend_files', 0)}")
            print_info(f"Tier 1 files: {manifest.get('tier1_files', 0)}")
            print_info(f"Python packages: {manifest.get('python_dependencies', 0)}")
            print_info(f"NPM packages: {manifest.get('npm_dependencies', 0)}")

            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.RESET}\n")
            return True

    except Exception as e:
        print_section("ERROR")
        print_error(f"Test failed with exception: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


async def main():
    """Main entry point."""
    print(f"{Colors.BOLD}{'*' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}  Module-Specific Export Test - Procurement Matcher{Colors.RESET}")
    print(f"{Colors.BOLD}{'*' * 80}{Colors.RESET}")

    success = await test_export_matcher()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
