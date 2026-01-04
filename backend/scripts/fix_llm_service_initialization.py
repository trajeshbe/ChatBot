#!/usr/bin/env python3
"""
Fix LLMService initialization across all tier_2 modules.

CRITICAL BUG: LLMService.__init__() takes no arguments, but all modules
were incorrectly updated to pass (db, settings).

This script fixes:
    WRONG: self.llm_service = LLMService(db, settings)
    CORRECT: self.llm_service = LLMService()
"""

import re
from pathlib import Path

# Find all tier_2 service files
tier2_path = Path("app/tier_2")
service_files = list(tier2_path.rglob("*_service.py"))

print(f"Found {len(service_files)} service files")
print("="*80)

fixed_count = 0
for service_file in service_files:
    content = service_file.read_text()
    original_content = content

    # Fix LLMService initialization
    content = re.sub(
        r'self\.llm_service = LLMService\(db, settings\)',
        r'self.llm_service = LLMService()',
        content
    )

    # Fix RAGService initialization if exists
    content = re.sub(
        r'self\.rag_service = RAGService\(db, settings\)',
        r'self.rag_service = RAGService()',
        content
    )

    if content != original_content:
        service_file.write_text(content)
        fixed_count += 1
        print(f"✅ Fixed: {service_file.relative_to('app/tier_2')}")

print("="*80)
print(f"Fixed {fixed_count} service files")
print("✅ All LLMService initializations corrected!")
