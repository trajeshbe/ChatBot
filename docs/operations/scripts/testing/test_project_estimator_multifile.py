#!/usr/bin/env python3
"""
Test script for enhanced Project Estimator with multi-file upload.

This script tests the following:
1. Multi-file upload across 4 categories
2. File extraction and processing
3. BRD and cost estimation generation
4. Quality of output based on reference templates
"""

import requests
import json
from pathlib import Path
from typing import Dict, List

# Configuration
BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/v1/project-estimator/generate"

# File paths
ESTIMATE_ONE_DIR = Path("docs/features/project_estimator/estimate_one")
SAMPLE_DATA_DIR = ESTIMATE_ONE_DIR / "Sampe_data" / "110199_110199_Galleon_Gardens_Clubhouse_fullSet"

# Test files
SCOPE_FILES = [
    # We'll create a simple scope text file
]

SAMPLE_DATA_FILES = [
    SAMPLE_DATA_DIR / "A 0000 [A].pdf",
    SAMPLE_DATA_DIR / "A 0101 [A].pdf",
    SAMPLE_DATA_DIR / "A 1001 [C].pdf",
]

REFERENCE_BRD_FILES = [
    ESTIMATE_ONE_DIR / "EstimateOne_BRD_Document.docx",
]

COST_TEMPLATE_FILES = [
    ESTIMATE_ONE_DIR / "Estimate_One_Construction_Document_Extraction_Estimation (1).xlsx",
    ESTIMATE_ONE_DIR / "Project Size Sourcing.xlsx",
]


def test_multi_file_upload():
    """Test multi-file upload with sample files from estimate_one folder."""

    print("=" * 80)
    print("🧪 TESTING ENHANCED PROJECT ESTIMATOR - MULTI-FILE UPLOAD")
    print("=" * 80)
    print()

    # Project scope description
    project_scope = """
    Construction Document Extraction System

    Build an AI-powered system to extract and analyze construction project documents
    including architectural drawings, specifications, and project scopes. The system
    should automatically identify key information such as project details, materials,
    quantities, and cost estimates.

    Key Features:
    - PDF document processing for architectural drawings
    - Automated text and table extraction
    - Document classification and categorization
    - Integration with cost estimation tools
    - User-friendly dashboard for review and export
    """

    # Prepare files
    files_to_upload = []

    # Add sample data files (only those that exist)
    for sample_file in SAMPLE_DATA_FILES:
        if sample_file.exists():
            files_to_upload.append(('sample_data_files',
                                   (sample_file.name, open(sample_file, 'rb'), 'application/pdf')))
            print(f"✓ Added sample data file: {sample_file.name}")
        else:
            print(f"⚠ Sample file not found: {sample_file}")

    # Add reference BRD
    for brd_file in REFERENCE_BRD_FILES:
        if brd_file.exists():
            files_to_upload.append(('reference_brd_files',
                                   (brd_file.name, open(brd_file, 'rb'),
                                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document')))
            print(f"✓ Added reference BRD: {brd_file.name}")
        else:
            print(f"⚠ BRD file not found: {brd_file}")

    # Add cost templates
    for cost_file in COST_TEMPLATE_FILES:
        if cost_file.exists():
            files_to_upload.append(('cost_template_files',
                                   (cost_file.name, open(cost_file, 'rb'),
                                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')))
            print(f"✓ Added cost template: {cost_file.name}")
        else:
            print(f"⚠ Cost template file not found: {cost_file}")

    print(f"\n📊 Total files to upload: {len(files_to_upload)}")
    print()

    # Prepare form data
    data = {
        'project_scope': project_scope,
        'session_id': 'test_session_multifile_001',
        'model_id': 'gpt-4-turbo',
        'scenario_name': 'baseline'
    }

    # Send request
    print("🚀 Sending request to API endpoint...")
    print(f"   Endpoint: {API_ENDPOINT}")
    print()

    try:
        response = requests.post(
            API_ENDPOINT,
            data=data,
            files=files_to_upload,
            timeout=300  # 5 minutes timeout
        )

        # Close all file handles
        for _, file_tuple in files_to_upload:
            file_tuple[1].close()

        print(f"📡 Response Status Code: {response.status_code}")
        print()

        if response.status_code == 200:
            result = response.json()

            print("✅ SUCCESS - Estimation Generated!")
            print("=" * 80)
            print()

            # Display results
            print("📋 PROJECT DETAILS:")
            print(f"   Project Name: {result.get('project_name', 'N/A')}")
            print(f"   Total Cost: ${result.get('total_cost', 0):,.2f}")
            print(f"   Total Effort: {result.get('total_effort_hours', 0):,.1f} hours")
            print(f"   Duration: {result.get('duration_months', 0):.1f} months")
            print()

            # Check for enhanced features
            if 'template_analysis' in result:
                print("🎯 TEMPLATE ANALYSIS (ENHANCED):")
                ta = result['template_analysis']

                print(f"\n   Files Processed:")
                files_proc = ta.get('files_processed', {})
                print(f"      - Scope documents: {files_proc.get('scope_documents', 0)}")
                print(f"      - Sample files: {files_proc.get('sample_files', 0)}")
                print(f"      - BRD templates: {files_proc.get('brd_templates', 0)}")
                print(f"      - Cost templates: {files_proc.get('cost_templates', 0)}")

                if 'best_match' in ta:
                    bm = ta['best_match']
                    print(f"\n   Best Match:")
                    print(f"      - Template: {bm.get('template_name', 'N/A')}")
                    print(f"      - Similarity: {bm.get('similarity_score', 0):.2%}")

                if 'quality_metrics' in ta:
                    qm = ta['quality_metrics']
                    print(f"\n   Quality Metrics:")
                    print(f"      - Completeness: {qm.get('completeness_score', 0)}%")
                    print(f"      - Data Coverage: {qm.get('data_coverage', 0)}%")
                    print(f"      - Template Alignment: {qm.get('template_alignment', 0)}%")
                    print(f"      - Confidence: {qm.get('confidence_level', 'N/A')}")

            # Document URLs
            print(f"\n📄 GENERATED DOCUMENTS:")
            if 'brd_url' in result:
                print(f"   BRD: {result['brd_url']}")
            if 'cost_estimation_url' in result:
                print(f"   Cost Estimation: {result['cost_estimation_url']}")

            print()
            print("=" * 80)
            print("🎉 TEST PASSED - Multi-file upload working correctly!")
            print("=" * 80)

            return True

        else:
            print(f"❌ ERROR - Request failed!")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ ERROR - Request timeout (exceeded 5 minutes)")
        return False
    except Exception as e:
        print(f"❌ ERROR - Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_multi_file_upload()
    exit(0 if success else 1)
