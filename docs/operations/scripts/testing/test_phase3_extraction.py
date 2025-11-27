#!/usr/bin/env python3
"""
Phase 3 Extraction Workflow - End-to-End Test Script

This script tests the complete extraction workflow including:
- Job creation
- Progress monitoring
- Result download
- Multiple output formats
- Delivery channels
"""

import httpx
import asyncio
import json
import time
from typing import Dict, Any
import sys


# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/extraction"


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


async def test_1_simple_extraction():
    """Test 1: Simple extraction with download delivery"""
    print_header("TEST 1: Simple Extraction (Excel + Download)")

    async with httpx.AsyncClient(timeout=300.0) as client:
        # Create extraction job
        print_info("Creating extraction job...")

        job_request = {
            "urls": [
                "https://example.com",
                "https://httpbin.org/html"
            ],
            "output_format": "excel",
            "delivery_method": "download",
            "scrape_config": {
                "compliance_level": "balanced",
                "max_concurrent_requests": 2
            }
        }

        response = await client.post(f"{API_BASE}/jobs", json=job_request)

        if response.status_code != 200:
            print_error(f"Failed to create job: {response.text}")
            return None

        job = response.json()
        job_id = job['job_id']

        print_success(f"Job created: {job_id}")
        print(f"   URLs: {job['urls_count']}")
        print(f"   Format: {job['output_format']}")
        print(f"   Delivery: {job['delivery_method']}")

        # Monitor progress
        print_info("Monitoring job progress...")

        while True:
            await asyncio.sleep(2)

            status_response = await client.get(f"{API_BASE}/jobs/{job_id}")

            if status_response.status_code != 200:
                print_error(f"Failed to get status: {status_response.text}")
                return None

            status = status_response.json()

            # Print progress
            progress = status['progress_percentage']
            current_step = status['current_step']
            print(f"   Progress: {progress:5.1f}% - {current_step}")

            # Check if complete
            if status['status'] in ['completed', 'completed_with_errors', 'failed']:
                break

        # Print final results
        print()
        if status['status'] == 'completed':
            print_success("Job completed successfully!")
        elif status['status'] == 'completed_with_errors':
            print_warning("Job completed with errors")
        else:
            print_error("Job failed")

        print(f"\n{Colors.BOLD}Results:{Colors.ENDC}")
        print(f"   Status: {status['status']}")
        print(f"   URLs Processed: {status['urls_processed']}/{status['urls_total']}")
        print(f"   Successful: {status['successful_scrapes']}")
        print(f"   Failed: {status['failed_scrapes']}")
        print(f"   Records Extracted: {status['records_extracted']}")
        print(f"   Quality Score: {status['quality_score']:.2f}%")
        print(f"   Duration: {status['total_duration_seconds']:.2f}s")

        if status.get('output_file_path'):
            print(f"   Output File: {status['output_file_path']}")

        if status.get('errors'):
            print_warning(f"\n   Errors ({len(status['errors'])}):")
            for error in status['errors'][:3]:  # Show first 3 errors
                print(f"      - {error.get('step')}: {error.get('error')}")

        return job_id


async def test_2_multiple_formats():
    """Test 2: Test multiple output formats"""
    print_header("TEST 2: Multiple Output Formats")

    formats_to_test = ['csv', 'json', 'xml', 'parquet']

    async with httpx.AsyncClient(timeout=300.0) as client:
        for output_format in formats_to_test:
            print_info(f"Testing {output_format.upper()} format...")

            job_request = {
                "urls": ["https://example.com"],
                "output_format": output_format,
                "delivery_method": "download"
            }

            response = await client.post(f"{API_BASE}/jobs", json=job_request)

            if response.status_code != 200:
                print_error(f"Failed to create job: {response.text}")
                continue

            job = response.json()
            job_id = job['job_id']

            # Wait for completion (simplified - no detailed monitoring)
            await asyncio.sleep(10)

            status_response = await client.get(f"{API_BASE}/jobs/{job_id}")
            status = status_response.json()

            if status['status'] == 'completed':
                print_success(f"{output_format.upper()}: ✓ Generated successfully")
            else:
                print_error(f"{output_format.upper()}: ✗ Failed - {status.get('status')}")


async def test_3_parallel_processing():
    """Test 3: Parallel processing with many URLs"""
    print_header("TEST 3: Parallel Processing (10 URLs)")

    async with httpx.AsyncClient(timeout=300.0) as client:
        print_info("Creating job with 10 URLs...")

        job_request = {
            "urls": [
                "https://example.com",
                "https://httpbin.org/html",
                "https://httpbin.org/json",
                "https://httpbin.org/uuid",
                "https://httpbin.org/headers",
                "https://www.ietf.org/rfc/rfc2616.txt",
                "https://jsonplaceholder.typicode.com/posts/1",
                "https://jsonplaceholder.typicode.com/users/1",
                "https://jsonplaceholder.typicode.com/comments/1",
                "https://api.github.com/zen"
            ],
            "output_format": "excel",
            "delivery_method": "download",
            "scrape_config": {
                "max_concurrent_requests": 5  # Process 5 at a time
            }
        }

        start_time = time.time()

        response = await client.post(f"{API_BASE}/jobs", json=job_request)
        job = response.json()
        job_id = job['job_id']

        print_success(f"Job created: {job_id}")
        print_info("Processing URLs in parallel...")

        # Monitor with progress bar
        while True:
            await asyncio.sleep(1)

            status_response = await client.get(f"{API_BASE}/jobs/{job_id}")
            status = status_response.json()

            # Simple progress indicator
            progress = status['progress_percentage']
            processed = status['urls_processed']
            total = status['urls_total']

            bar_length = 40
            filled = int(bar_length * progress / 100)
            bar = '█' * filled + '░' * (bar_length - filled)

            print(f"\r   [{bar}] {progress:5.1f}% - {processed}/{total} URLs", end='', flush=True)

            if status['status'] in ['completed', 'completed_with_errors', 'failed']:
                break

        print()  # New line after progress bar

        end_time = time.time()
        total_time = end_time - start_time

        print_success(f"Completed in {total_time:.2f}s")
        print(f"   Throughput: {10 / total_time:.2f} URLs/second")
        print(f"   Records: {status['records_extracted']}")
        print(f"   Quality: {status['quality_score']:.2f}%")


async def test_4_list_jobs():
    """Test 4: List all jobs"""
    print_header("TEST 4: List All Jobs")

    async with httpx.AsyncClient(timeout=30.0) as client:
        print_info("Fetching all jobs...")

        response = await client.get(f"{API_BASE}/jobs?limit=10")

        if response.status_code != 200:
            print_error(f"Failed to list jobs: {response.text}")
            return

        jobs = response.json()

        print_success(f"Found {len(jobs)} jobs")

        if jobs:
            print(f"\n{Colors.BOLD}Recent Jobs:{Colors.ENDC}")
            for job in jobs[:5]:  # Show first 5
                print(f"   {job['job_id'][:8]}... - {job['status']} - {job['urls_count']} URLs - {job['output_format']}")


async def test_5_download_result():
    """Test 5: Download a result file"""
    print_header("TEST 5: Download Result File")

    # First create a simple job
    async with httpx.AsyncClient(timeout=300.0) as client:
        print_info("Creating job for download test...")

        job_request = {
            "urls": ["https://example.com"],
            "output_format": "csv",
            "delivery_method": "download"
        }

        response = await client.post(f"{API_BASE}/jobs", json=job_request)
        job = response.json()
        job_id = job['job_id']

        # Wait for completion
        print_info("Waiting for job to complete...")
        await asyncio.sleep(10)

        # Get result info
        result_response = await client.get(f"{API_BASE}/jobs/{job_id}/result")

        if result_response.status_code != 200:
            print_warning("Job not ready yet or failed")
            return

        result = result_response.json()

        if result.get('download_url'):
            print_success("Result ready for download")
            print(f"   Download URL: {BASE_URL}{result['download_url']}")
            print(f"   File Size: {result.get('output_file_size', 0)} bytes")
            print(f"   Records: {result['records_extracted']}")
            print_info("You can download the file using the URL above")


async def test_6_error_handling():
    """Test 6: Error handling with invalid URLs"""
    print_header("TEST 6: Error Handling")

    async with httpx.AsyncClient(timeout=300.0) as client:
        print_info("Testing with invalid URLs...")

        job_request = {
            "urls": [
                "https://this-domain-definitely-does-not-exist-12345.com",
                "https://example.com"
            ],
            "output_format": "json",
            "delivery_method": "download"
        }

        response = await client.post(f"{API_BASE}/jobs", json=job_request)
        job = response.json()
        job_id = job['job_id']

        # Wait for completion
        await asyncio.sleep(10)

        status_response = await client.get(f"{API_BASE}/jobs/{job_id}")
        status = status_response.json()

        print(f"   Status: {status['status']}")
        print(f"   Successful: {status['successful_scrapes']}")
        print(f"   Failed: {status['failed_scrapes']}")

        if status['failed_scrapes'] > 0:
            print_success("Error handling working correctly")
        else:
            print_warning("Expected some failures, but got none")


async def run_all_tests():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("=" * 80)
    print("Phase 3 Extraction Workflow - End-to-End Test Suite".center(80))
    print("=" * 80)
    print(f"{Colors.ENDC}\n")

    print_info(f"Backend URL: {BASE_URL}")
    print_info("Make sure the backend is running before proceeding!\n")

    # Check backend is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print_success("Backend is running ✓\n")
            else:
                print_error("Backend health check failed")
                return
    except Exception as e:
        print_error(f"Cannot connect to backend: {e}")
        print_info("Please start the backend with: cd backend && uvicorn app.main:app --reload")
        return

    tests = [
        ("Simple Extraction", test_1_simple_extraction),
        ("Multiple Formats", test_2_multiple_formats),
        ("Parallel Processing", test_3_parallel_processing),
        ("List Jobs", test_4_list_jobs),
        ("Download Result", test_5_download_result),
        ("Error Handling", test_6_error_handling),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            await test_func()
            results.append((test_name, "PASS"))
        except Exception as e:
            print_error(f"Test failed: {e}")
            results.append((test_name, "FAIL"))

        await asyncio.sleep(2)  # Pause between tests

    # Print summary
    print_header("Test Summary")

    for test_name, result in results:
        if result == "PASS":
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    passed = sum(1 for _, r in results if r == "PASS")
    total = len(results)

    print(f"\n{Colors.BOLD}Overall: {passed}/{total} tests passed{Colors.ENDC}\n")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  Phase 3 Extraction Workflow Test Script")
    print("=" * 80)

    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
