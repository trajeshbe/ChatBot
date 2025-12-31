# Creating Playwright Test Cases - Complete Guide

**Date**: 2025-12-01
**Purpose**: Learn how to create, run, and demonstrate Playwright UI tests with visual browser mode

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Test Case Structure](#test-case-structure)
3. [Creating Your First Test](#creating-your-first-test)
4. [Running Tests Visually](#running-tests-visually)
5. [Test Reporter Features](#test-reporter-features)
6. [Best Practices](#best-practices)
7. [Common Patterns](#common-patterns)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Install Playwright (One-Time Setup)

```bash
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot
source virtual_env_for_testing/bin/activate

# Install Playwright and pytest
pip install playwright pytest pytest-asyncio

# Install browser binaries
playwright install chromium
```

### 2. Verify Installation

```bash
playwright --version
# Should output: Version 1.48.0 or similar
```

---

## Test Case Structure

### Directory Layout

```
backend/tests/playwright/
├── conftest.py                    # Pytest fixtures (browser, login, etc.)
├── test_reporter.py               # HTML/JSON report generator
├── page_objects/                  # Page Object Model
│   ├── base_page.py              # Base class with common methods
│   ├── login_page.py             # Login page interactions
│   └── admin_dashboard_page.py   # Admin dashboard interactions
├── test_users_crud.py            # User management tests
├── test_roles_crud.py            # Role management tests
├── test_departments.py           # Department tests
└── test_results/                 # Generated screenshots and reports
    ├── *.png                     # Screenshots
    ├── *_test_report.html        # HTML reports
    └── *_test_report.json        # JSON reports
```

### Test Case Anatomy

```python
import pytest
from page_objects.admin_dashboard_page import AdminDashboardPage
from test_reporter import TestReporter, TestCase, TestStep
import time

# Global reporter instance
reporter = TestReporter()

def test_your_feature(admin_dashboard: AdminDashboardPage):
    """Test Case: Description of what this test does."""

    # 1. Create test case
    test_case = TestCase(
        test_id="TC_FEATURE_001",
        test_name="Test Feature Name",
        test_description="Detailed description of what we're testing"
    )
    test_case.start()

    try:
        # 2. Define test steps
        step1 = TestStep(
            step_number=1,
            description="What action we're taking",
            expected_result="What should happen"
        )
        test_case.add_step(step1)

        # 3. Take BEFORE screenshot
        admin_dashboard.page.screenshot(
            path="backend/tests/playwright/test_results/TC_FEATURE_001_step1_before.png"
        )
        step1.screenshot_before = "TC_FEATURE_001_step1_before.png"

        # 4. Perform action
        admin_dashboard.some_action()
        time.sleep(1)

        # 5. Take AFTER screenshot
        admin_dashboard.page.screenshot(
            path="backend/tests/playwright/test_results/TC_FEATURE_001_step1_after.png"
        )
        step1.screenshot_after = "TC_FEATURE_001_step1_after.png"

        # 6. Record results
        step1.actual_result = "What actually happened"
        step1.status = "passed"  # or "failed"

        # 7. Mark test complete
        test_case.complete("passed")

    except Exception as e:
        test_case.complete("failed", str(e))
        for step in test_case.steps:
            if step.status == "pending":
                step.status = "failed"
                step.error_message = str(e)

    # 8. Add to reporter and assert
    reporter.add_test_case(test_case)
    assert test_case.status == "passed", f"Test failed: {test_case.overall_error}"
```

---

## Creating Your First Test

### Example: Testing a New Feature

Let's create a test for adding a new department.

#### Step 1: Create Test File

Create `backend/tests/playwright/test_my_feature.py`:

```python
"""Tests for My Feature in Admin Dashboard."""
import pytest
from page_objects.admin_dashboard_page import AdminDashboardPage
from test_reporter import TestReporter, TestCase, TestStep
import time
from datetime import datetime

# Global reporter instance
reporter = TestReporter()

def test_create_department(admin_dashboard: AdminDashboardPage):
    """Test Case: Create a new department."""
    test_case = TestCase(
        test_id="TC_DEPT_001",
        test_name="Create New Department",
        test_description="Verify admin can create a new department"
    )
    test_case.start()

    try:
        # Step 1: Navigate to Departments
        step1 = TestStep(
            1,
            "Navigate to Departments tab",
            "Departments tab is displayed"
        )
        test_case.add_step(step1)

        admin_dashboard.page.screenshot(
            path="backend/tests/playwright/test_results/TC_DEPT_001_step1_before.png"
        )
        step1.screenshot_before = "TC_DEPT_001_step1_before.png"

        admin_dashboard.click_departments_tab()
        time.sleep(1)

        admin_dashboard.page.screenshot(
            path="backend/tests/playwright/test_results/TC_DEPT_001_step1_after.png"
        )
        step1.screenshot_after = "TC_DEPT_001_step1_after.png"
        step1.actual_result = "Departments tab opened"
        step1.status = "passed"

        # Step 2: Click Create Department
        step2 = TestStep(
            2,
            "Click Create Department button",
            "Department creation form appears"
        )
        test_case.add_step(step2)

        admin_dashboard.page.screenshot(
            path="backend/tests/playwright/test_results/TC_DEPT_001_step2_before.png"
        )
        step2.screenshot_before = "TC_DEPT_001_step2_before.png"

        admin_dashboard.click_create_department()
        time.sleep(1)

        admin_dashboard.page.screenshot(
            path="backend/tests/playwright/test_results/TC_DEPT_001_step2_after.png"
        )
        step2.screenshot_after = "TC_DEPT_001_step2_after.png"
        step2.actual_result = "Form displayed"
        step2.status = "passed"

        # Step 3: Fill and submit
        dept_name = f"Test_Dept_{int(time.time())}"

        step3 = TestStep(
            3,
            f"Fill department name: {dept_name}",
            "Department is created"
        )
        test_case.add_step(step3)

        admin_dashboard.page.screenshot(
            path="backend/tests/playwright/test_results/TC_DEPT_001_step3_before.png"
        )
        step3.screenshot_before = "TC_DEPT_001_step3_before.png"

        admin_dashboard.fill_department_form(dept_name)
        admin_dashboard.save_department()
        time.sleep(2)

        admin_dashboard.page.screenshot(
            path="backend/tests/playwright/test_results/TC_DEPT_001_step3_after.png"
        )
        step3.screenshot_after = "TC_DEPT_001_step3_after.png"
        step3.actual_result = f"Department {dept_name} created"
        step3.status = "passed"

        test_case.complete("passed")

    except Exception as e:
        test_case.complete("failed", str(e))
        for step in test_case.steps:
            if step.status == "pending":
                step.status = "failed"
                step.error_message = str(e)

    reporter.add_test_case(test_case)
    assert test_case.status == "passed", f"Test failed: {test_case.overall_error}"
```

#### Step 2: Test the Test

Run it to make sure it works:

```bash
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot
source virtual_env_for_testing/bin/activate

pytest backend/tests/playwright/test_my_feature.py::test_create_department -v
```

---

## Running Tests Visually

### Standard Visual Mode (Slow Motion)

Perfect for **demonstrations** and **debugging**:

```bash
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot
source virtual_env_for_testing/bin/activate

# Set environment variables for visual mode
export HEADLESS=false      # Show browser window
export SLOW_MO=1000         # 1 second delay per action

# Run single test
pytest backend/tests/playwright/test_my_feature.py::test_create_department -vvs

# Run all tests in a file
pytest backend/tests/playwright/test_users_crud.py -vvs

# Run all tests
pytest backend/tests/playwright/ -vvs
```

### Different Speed Settings

```bash
# Very slow (2 seconds per action) - for presentations
export SLOW_MO=2000
pytest backend/tests/playwright/test_my_feature.py -vvs

# Medium speed (500ms per action) - for debugging
export SLOW_MO=500
pytest backend/tests/playwright/test_my_feature.py -vvs

# Normal speed (no delay) - for quick validation
export SLOW_MO=0
pytest backend/tests/playwright/test_my_feature.py -vvs
```

### Running with RUN_TESTS.sh Script

```bash
# Run all tests (headless by default)
./backend/tests/playwright/RUN_TESTS.sh

# Run specific test suite
./backend/tests/playwright/RUN_TESTS.sh users
./backend/tests/playwright/RUN_TESTS.sh roles
./backend/tests/playwright/RUN_TESTS.sh departments

# Run in visible mode with slow motion
export HEADLESS=false
export SLOW_MO=1000
./backend/tests/playwright/RUN_TESTS.sh users
```

### What You'll See

When running in visual mode:

1. **Browser Window Opens**: Chrome/Chromium browser appears on screen
2. **Actions Happen Slowly**: Each click, type, navigation happens with delay
3. **You Can Watch**: See exactly what the test is doing
4. **Screenshots Taken**: Before/after screenshots saved automatically
5. **Browser Closes**: When test completes, browser closes automatically

---

## Test Reporter Features

### HTML Report

After running tests, open the HTML report:

```bash
# Open report in browser
open backend/tests/playwright/test_results/users_crud_test_report.html

# Or on Linux with default browser
xdg-open backend/tests/playwright/test_results/users_crud_test_report.html

# Or start HTTP server
cd backend/tests/playwright/test_results
python -m http.server 8080
# Navigate to: http://localhost:8080
```

### Report Contents

The HTML report includes:

- **Test Summary**: Total tests, passed, failed, duration
- **Test Case Details**: Each test with ID, name, description
- **Step-by-Step Results**: All steps with:
  - Expected result
  - Actual result
  - Status (passed/failed)
  - **Before screenshot** (embedded image)
  - **After screenshot** (embedded image)
  - Error messages (if failed)
- **Color Coding**: Green for passed, red for failed
- **Timestamps**: When each step executed

### JSON Report

For CI/CD integration:

```bash
# View JSON report
cat backend/tests/playwright/test_results/users_crud_test_report.json | jq .

# Extract specific data
jq '.test_cases[0].steps[] | {step: .step_number, status: .status}' \
  backend/tests/playwright/test_results/users_crud_test_report.json
```

---

## Best Practices

### 1. Naming Conventions

**Test IDs**:
```python
TC_MODULE_NUMBER
TC_USER_001   # First user test
TC_USER_002   # Second user test
TC_ROLE_001   # First role test
```

**Screenshot Names**:
```python
TC_USER_001_step1_before.png
TC_USER_001_step1_after.png
TC_USER_001_step2_before.png
```

### 2. Screenshot Strategy

**Always capture**:
- BEFORE screenshot (shows initial state)
- Perform action
- AFTER screenshot (shows result)

```python
# BEFORE
page.screenshot(path="...step1_before.png")
step.screenshot_before = "...step1_before.png"

# ACTION
admin_dashboard.click_something()
time.sleep(1)  # Wait for UI to update

# AFTER
page.screenshot(path="...step1_after.png")
step.screenshot_after = "...step1_after.png"
```

### 3. Wait Strategies

**Use appropriate waits**:

```python
# Wait for element to appear
admin_dashboard.wait_for_element('button:has-text("Submit")')

# Wait for navigation
with page.expect_navigation(timeout=10000, wait_until="networkidle"):
    page.click('button:has-text("Login")')

# Simple time-based wait (use sparingly)
time.sleep(1)  # Wait for animation to complete
```

### 4. Error Handling

**Always use try-except**:

```python
try:
    # Test steps here
    test_case.complete("passed")
except Exception as e:
    test_case.complete("failed", str(e))
    # Mark all pending steps as failed
    for step in test_case.steps:
        if step.status == "pending":
            step.status = "failed"
            step.error_message = str(e)

# Always add to reporter and assert
reporter.add_test_case(test_case)
assert test_case.status == "passed", f"Test failed: {test_case.overall_error}"
```

### 5. Cleanup

**Use fixtures for cleanup**:

```python
def test_user_create(admin_dashboard: AdminDashboardPage, cleanup_test_user):
    # Test creates user
    test_username = f"testuser_{int(time.time())}"

    # Register for cleanup
    cleanup_test_user(test_username)

    # Test continues...
    # User will be automatically deleted after test
```

---

## Common Patterns

### Pattern 1: Navigate to Page

```python
step = TestStep(1, "Navigate to Settings", "Settings page displayed")
test_case.add_step(step)

page.screenshot(path="...step1_before.png")
step.screenshot_before = "...step1_before.png"

admin_dashboard.navigate_to("/settings")
time.sleep(1)

page.screenshot(path="...step1_after.png")
step.screenshot_after = "...step1_after.png"
step.actual_result = "Settings page loaded"
step.status = "passed"
```

### Pattern 2: Fill Form

```python
step = TestStep(2, "Fill form", "Form populated with data")
test_case.add_step(step)

page.screenshot(path="...step2_before.png")
step.screenshot_before = "...step2_before.png"

# Fill multiple fields
page.fill('input[name="username"]', "testuser")
page.fill('input[name="email"]', "test@example.com")
page.fill('input[name="password"]', "SecurePass123!")
time.sleep(0.5)

page.screenshot(path="...step2_after.png")
step.screenshot_after = "...step2_after.png"
step.actual_result = "Form filled with test data"
step.status = "passed"
```

### Pattern 3: Click and Verify

```python
step = TestStep(3, "Click Save button", "User saved successfully")
test_case.add_step(step)

page.screenshot(path="...step3_before.png")
step.screenshot_before = "...step3_before.png"

page.click('button:has-text("Save")')
time.sleep(2)  # Wait for save operation

page.screenshot(path="...step3_after.png")
step.screenshot_after = "...step3_after.png"

# Verify success
if page.locator('text=/success|saved/i').count() > 0:
    step.actual_result = "User saved successfully"
    step.status = "passed"
else:
    step.actual_result = "Save failed - no success message"
    step.status = "failed"
```

### Pattern 4: Table Verification

```python
step = TestStep(4, "Verify in table", "User appears in user list")
test_case.add_step(step)

page.screenshot(path="...step4_before.png")
step.screenshot_before = "...step4_before.png"

# Search in table
found = page.locator(f'tr:has-text("{username}")').count() > 0

page.screenshot(path="...step4_after.png")
step.screenshot_after = "...step4_after.png"

if found:
    step.actual_result = f"User '{username}' found in table"
    step.status = "passed"
else:
    step.actual_result = f"User '{username}' NOT found in table"
    step.status = "failed"
    raise AssertionError(f"User not found: {username}")
```

---

## Troubleshooting

### Issue 1: Browser Doesn't Open

**Problem**: Running with `HEADLESS=false` but browser doesn't appear

**Solution**:
```bash
# Check if X display is available (Linux/WSL)
echo $DISPLAY

# If empty, set it
export DISPLAY=:0

# Try again
export HEADLESS=false
pytest backend/tests/playwright/test_my_feature.py -vvs
```

### Issue 2: Element Not Found

**Problem**: `Timeout waiting for selector`

**Solution**:
```python
# Use more flexible selectors
page.click('button:has-text("Save"), button:has-text("Submit"), button[type="submit"]')

# Or increase timeout
page.wait_for_selector('button', timeout=30000)  # 30 seconds

# Or use visible check
if page.is_visible('button:has-text("Save")'):
    page.click('button:has-text("Save")')
```

### Issue 3: Screenshots Not Saving

**Problem**: Screenshots not in test_results/

**Solution**:
```bash
# Create directory if it doesn't exist
mkdir -p backend/tests/playwright/test_results

# Check permissions
ls -la backend/tests/playwright/test_results

# Use absolute paths
from pathlib import Path
base_dir = Path(__file__).parent
screenshot_path = base_dir / "test_results" / "screenshot.png"
page.screenshot(path=str(screenshot_path))
```

### Issue 4: Tests Running Too Fast

**Problem**: Can't see what's happening even with SLOW_MO

**Solution**:
```python
# Add explicit waits between steps
time.sleep(2)  # 2 seconds

# Or increase SLOW_MO
export SLOW_MO=3000  # 3 seconds per action
```

### Issue 5: Browser Stays Open After Test

**Problem**: Browser window doesn't close

**Solution**:
```bash
# Check for zombie processes
ps aux | grep chromium

# Kill if needed
pkill chromium

# Make sure fixture closes browser
# In conftest.py:
@pytest.fixture
def browser(playwright_instance):
    browser = playwright_instance.chromium.launch(headless=HEADLESS)
    yield browser
    browser.close()  # Ensure this is called
```

---

## Quick Reference Commands

### Run Tests Visually

```bash
# Setup (one-time)
source virtual_env_for_testing/bin/activate

# Run in slow motion
export HEADLESS=false
export SLOW_MO=1000
pytest backend/tests/playwright/test_users_crud.py::test_user_create -vvs

# Run all tests
pytest backend/tests/playwright/ -vvs

# View results
open backend/tests/playwright/test_results/users_crud_test_report.html
```

### Create New Test

```bash
# 1. Copy existing test as template
cp backend/tests/playwright/test_users_crud.py \
   backend/tests/playwright/test_my_feature.py

# 2. Edit test file
# 3. Run test
pytest backend/tests/playwright/test_my_feature.py -vvs

# 4. View report
open backend/tests/playwright/test_results/my_feature_test_report.html
```

---

## Example: Complete Test File

```python
"""Example complete test file."""
import pytest
from page_objects.admin_dashboard_page import AdminDashboardPage
from test_reporter import TestReporter, TestCase, TestStep
import time

reporter = TestReporter()

def test_example_flow(admin_dashboard: AdminDashboardPage):
    """Test Case: Example complete flow."""
    test_case = TestCase(
        test_id="TC_EXAMPLE_001",
        test_name="Example Complete Flow",
        test_description="Demonstrates complete test with all features"
    )
    test_case.start()

    try:
        # Step 1
        step1 = TestStep(1, "Navigate to feature", "Feature page displayed")
        test_case.add_step(step1)

        admin_dashboard.page.screenshot(
            path="backend/tests/playwright/test_results/TC_EXAMPLE_001_step1_before.png"
        )
        step1.screenshot_before = "TC_EXAMPLE_001_step1_before.png"

        admin_dashboard.page.goto("http://localhost:3001/my-feature")
        time.sleep(1)

        admin_dashboard.page.screenshot(
            path="backend/tests/playwright/test_results/TC_EXAMPLE_001_step1_after.png"
        )
        step1.screenshot_after = "TC_EXAMPLE_001_step1_after.png"
        step1.actual_result = "Feature page loaded"
        step1.status = "passed"

        # Step 2
        step2 = TestStep(2, "Perform action", "Action completed")
        test_case.add_step(step2)

        admin_dashboard.page.screenshot(
            path="backend/tests/playwright/test_results/TC_EXAMPLE_001_step2_before.png"
        )
        step2.screenshot_before = "TC_EXAMPLE_001_step2_before.png"

        admin_dashboard.page.click('button:has-text("Do Something")')
        time.sleep(2)

        admin_dashboard.page.screenshot(
            path="backend/tests/playwright/test_results/TC_EXAMPLE_001_step2_after.png"
        )
        step2.screenshot_after = "TC_EXAMPLE_001_step2_after.png"
        step2.actual_result = "Action completed successfully"
        step2.status = "passed"

        test_case.complete("passed")

    except Exception as e:
        test_case.complete("failed", str(e))
        for step in test_case.steps:
            if step.status == "pending":
                step.status = "failed"
                step.error_message = str(e)

    reporter.add_test_case(test_case)
    assert test_case.status == "passed", f"Test failed: {test_case.overall_error}"
```

---

## Next Steps

1. **Review Existing Tests**: Look at `test_users_crud.py` for real examples
2. **Create Your First Test**: Follow the patterns above
3. **Run Visually**: Watch it execute with `HEADLESS=false SLOW_MO=1000`
4. **Review Report**: Open HTML report to see results
5. **Iterate**: Improve selectors and add more test cases

---

**Happy Testing!** 🎉

For more help, see:
- [Playwright Tests README](../../backend/tests/playwright/README.md)
- [Quick Reference](../../backend/tests/playwright/QUICK_REFERENCE.md)
- [Test Fixes Documentation](./PLAYWRIGHT_TEST_FIXES_2025-12-01.md)

---

**Created**: 2025-12-01
**Location**: `/docs/testing/CREATING_PLAYWRIGHT_TESTS_GUIDE.md`
