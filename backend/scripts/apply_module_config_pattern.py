#!/usr/bin/env python3
"""
Automated Module Configuration Pattern Application Script

Applies the module config integration pattern to all tier_2 modules:
1. Updates service constructors to accept config parameter
2. Updates LLM calls to use config parameters
3. Updates routes to load and pass config

Usage:
    python scripts/apply_module_config_pattern.py --dry-run  # Preview changes
    python scripts/apply_module_config_pattern.py            # Apply changes
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict
import argparse

# Module directories and their module names
MODULES_TO_UPDATE = {
    "construction": ["planning_classifier", "estimator_au"],
    "agriculture": ["agri_taxonomy", "agronomy_decision"],
    "hr_talent": ["talent_pulse", "talent_search", "taxonomy_skillmatch"],
    "procurement": ["matcher", "spend_smart", "tender_intelligence", "vendor_recommendation"],
    "document_intelligence": ["generic_rag", "relation_extractor"],
    "industry_verticals": ["legal_document", "real_estate", "healthcare_diagnostics"],
    "advanced_capabilities": ["code_analysis", "multilingual_translator"],
    "ecommerce": ["product_recommendation"],
    "maritime": ["maritime_logistics"],
}


def update_service_constructor(content: str, service_class_name: str) -> str:
    """Update service constructor to accept config parameter."""

    # Pattern to match the __init__ method
    init_pattern = r'(    def __init__\(self, db: Session, settings: Settings)\):'

    # Check if already updated
    if "config: Optional[Dict[str, Any]] = None" in content:
        print(f"    ⏭️  Constructor already updated")
        return content

    # Add Optional and Any to imports if not present
    if "from typing import" in content and "Optional" not in content:
        content = re.sub(
            r'(from typing import [^\n]+)',
            r'\1, Optional, Any',
            content
        )
    elif "from typing import" in content and "Any" not in content:
        content = re.sub(
            r'(from typing import [^\n]+)',
            r'\1, Any',
            content
        )

    # Update __init__ signature
    replacement = r'\1, config: Optional[Dict[str, Any]] = None):'
    content = re.sub(init_pattern, replacement, content)

    # Add config storage after settings
    settings_pattern = r'(        self\.settings = settings)\n'
    config_storage = r'\1\n        self.config = config or {}\n'
    content = re.sub(settings_pattern, config_storage, content)

    # Add log message after tier_1 initialization
    log_pattern = r'(        logger\.info\("✓ \w+Service initialized[^"]*"\))'
    log_addition = r'\1\n        if config:\n            logger.info(f"✓ Using module config with model: {config.get(\'llm\', {}).get(\'default\', {}).get(\'model\', \'default\')}")'
    content = re.sub(log_pattern, log_addition, content)

    print(f"    ✅ Constructor updated")
    return content


def update_llm_calls(content: str) -> Tuple[str, int]:
    """Update LLM calls to use config parameters."""

    # Pattern to match llm_service.generate_response calls
    # Matches multiline calls with model/temperature/max_tokens
    llm_pattern = r'(            )(response|llm_response) = await self\.llm_service\.generate_response\(\s+prompt=prompt,\s+model="([^"]+)",\s+temperature=([0-9.]+)(?:,\s+max_tokens=(\d+))?\s+\)'

    def replace_llm_call(match):
        indent = match.group(1)
        var_name = match.group(2)
        model = match.group(3)
        temp = match.group(4)
        max_tokens = match.group(5)

        # Build the replacement
        replacement = f"""{indent}# Get LLM parameters from module config
{indent}llm_config = self.config.get('llm', {{}}).get('default', {{}})
{indent}model = llm_config.get('model', '{model}')
{indent}temperature = llm_config.get('temperature', {temp})"""

        if max_tokens:
            replacement += f"\n{indent}max_tokens = llm_config.get('max_tokens', {max_tokens})"

        replacement += f"""

{indent}{var_name} = await self.llm_service.generate_response(
{indent}    prompt=prompt,
{indent}    model=model,
{indent}    temperature=temperature"""

        if max_tokens:
            replacement += f",\n{indent}    max_tokens=max_tokens"

        replacement += f"\n{indent})"

        return replacement

    # Count replacements
    count = len(re.findall(llm_pattern, content, re.MULTILINE | re.DOTALL))

    # Apply replacements
    content = re.sub(llm_pattern, replace_llm_call, content, flags=re.MULTILINE | re.DOTALL)

    if count > 0:
        print(f"    ✅ Updated {count} LLM call(s)")
    else:
        print(f"    ⏭️  No LLM calls found to update")

    return content, count


def update_routes_file(content: str, module_name: str) -> str:
    """Update routes file to load and pass config."""

    # Check if already updated
    if "load_module_config" in content:
        print(f"    ⏭️  Routes already updated")
        return content

    # Update imports
    content = re.sub(
        r'from sqlalchemy\.orm import Session',
        'from sqlalchemy.ext.asyncio import AsyncSession',
        content
    )

    # Add module_config_helper import
    if "from app.services.module_config_helper import load_module_config" not in content:
        import_pattern = r'(from app\.tier_1\.infrastructure\.config import Settings, get_settings)'
        import_addition = r'\1\nfrom app.services.module_config_helper import load_module_config'
        content = re.sub(import_pattern, import_addition, content)

    # Update endpoint signatures (Session -> AsyncSession)
    content = re.sub(
        r'    db: Session = Depends\(get_db\)',
        '    db: AsyncSession = Depends(get_db)',
        content
    )

    # Find primary endpoint and add config loading
    # This is trickier - we need to find service instantiation and add config loading before it
    service_pattern = r'(        )(service = \w+Service\(db, settings)\)'

    def add_config_loading(match):
        indent = match.group(1)
        service_line = match.group(2)

        return f"""{indent}# Load module configuration
{indent}module_config = await load_module_config(db, "{module_name}")
{indent}logger.info(f"✓ Loaded config for {module_name}")

{indent}# Initialize service with config
{indent}{service_line}, config=module_config)"""

    content = re.sub(service_pattern, add_config_loading, content)

    print(f"    ✅ Routes updated")
    return content


def process_module(category: str, module_name: str, dry_run: bool = False) -> Dict[str, any]:
    """Process a single module."""

    print(f"\n🔧 Processing {category}/{module_name}...")

    results = {"service": False, "routes": False, "llm_calls": 0}

    # Paths
    base_path = Path(__file__).parent.parent / "app" / "tier_2" / category
    service_file = base_path / f"{module_name}_service.py"
    routes_file = base_path / f"{module_name}_routes.py"

    # Check files exist
    if not service_file.exists():
        print(f"  ❌ Service file not found: {service_file}")
        return results

    if not routes_file.exists():
        print(f"  ❌ Routes file not found: {routes_file}")
        return results

    # Process service file
    print(f"  📄 Updating service file...")
    with open(service_file, 'r') as f:
        service_content = f.read()

    original_service = service_content

    # Determine service class name
    service_class_pattern = r'class (\w+Service):'
    match = re.search(service_class_pattern, service_content)
    if not match:
        print(f"  ❌ Could not find service class")
        return results

    service_class_name = match.group(1)

    # Apply updates
    service_content = update_service_constructor(service_content, service_class_name)
    service_content, llm_count = update_llm_calls(service_content)

    results["llm_calls"] = llm_count

    if service_content != original_service:
        if not dry_run:
            with open(service_file, 'w') as f:
                f.write(service_content)
        results["service"] = True

    # Process routes file
    print(f"  📄 Updating routes file...")
    with open(routes_file, 'r') as f:
        routes_content = f.read()

    original_routes = routes_content
    routes_content = update_routes_file(routes_content, module_name)

    if routes_content != original_routes:
        if not dry_run:
            with open(routes_file, 'w') as f:
                f.write(routes_content)
        results["routes"] = True

    return results


def main():
    parser = argparse.ArgumentParser(description='Apply module config pattern to tier_2 modules')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    parser.add_argument('--module', help='Process specific module only (format: category/module_name)')
    args = parser.parse_args()

    print("=" * 80)
    print("Module Configuration Pattern Application")
    print("=" * 80)

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be modified\n")

    total_modules = 0
    total_updated = 0
    total_llm_calls = 0

    # Process modules
    if args.module:
        # Process single module
        category, module_name = args.module.split('/')
        results = process_module(category, module_name, args.dry_run)
        total_modules = 1
        if results["service"] or results["routes"]:
            total_updated += 1
        total_llm_calls += results["llm_calls"]
    else:
        # Process all modules
        for category, modules in MODULES_TO_UPDATE.items():
            for module_name in modules:
                results = process_module(category, module_name, args.dry_run)
                total_modules += 1
                if results["service"] or results["routes"]:
                    total_updated += 1
                total_llm_calls += results["llm_calls"]

    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Total modules processed: {total_modules}")
    print(f"Modules updated: {total_updated}")
    print(f"LLM calls updated: {total_llm_calls}")

    if args.dry_run:
        print("\n⚠️  This was a dry run. Run without --dry-run to apply changes.")
    else:
        print("\n✅ All updates applied successfully!")

    print("=" * 80)


if __name__ == "__main__":
    main()
