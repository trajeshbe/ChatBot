# Playwright Test Suite for Admin Dashboard RBAC

## Overview

This directory contains comprehensive Playwright-based UI tests for the Admin Dashboard's RBAC (Role-Based Access Control) functionality. These tests verify all CRUD operations across Users, Roles, Departments, and Permissions management.

## Features

✅ **Comprehensive Test Coverage**: Full CRUD operations for all admin dashboard modules
✅ **Detailed Reporting**: HTML and JSON reports with screenshots at each test step
✅ **Screenshot Capture**: Before/after screenshots for every test step
✅ **Page Object Model**: Maintainable, reusable page objects
✅ **Cleanup Fixtures**: Automatic cleanup of test data
✅ **Configurable**: Environment-based configuration for flexibility

## Directory Structure

```
backend/tests/playwright/
├── README.md                          # This file
├── conftest.py                        # Pytest fixtures and configuration
├── test_reporter.py                   # Test reporting with screenshots
│
├── page_objects/                      # Page Object Models
│   ├── base_page.py                   # Base page with common methods
│   ├── login_page.py                  # Login page object
│   └── admin_dashboard_page.py        # Admin dashboard page object
│
├── test_users_crud.py                 # Users CRUD tests
├── test_roles_crud.py                 # Roles CRUD tests
├── test_departments.py                # Departments tests
│
└── test_results/                      # Test results and screenshots
    ├── *.png                          # Screenshots (before/after for each step)
    ├── users_crud_test_report.html    # Users test HTML report
    ├── users_crud_test_report.json    # Users test JSON report
    ├── roles_crud_test_report.html    # Roles test HTML report
    ├── roles_crud_test_report.json    # Roles test JSON report
    ├── departments_test_report.html   # Departments test HTML report
    └── departments_test_report.json   # Departments test JSON report
```

## Prerequisites

1. **Services Running**: Ensure backend and frontend services are running
   ```bash
   docker-compose up -d backend frontend postgres
   ```

2. **Admin User**: Ensure admin user exists (username: `admin`, password: `admin123`)

3. **Playwright Installed**: Playwright is already installed in the backend container

## Configuration

Configure tests via environment variables in `conftest.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `FRONTEND_URL` | `http://localhost:3001` | Frontend URL |
| `ADMIN_USERNAME` | `admin` | Admin username for login |
| `ADMIN_PASSWORD` | `admin123` | Admin password |
| `HEADLESS` | `true` | Run browser in headless mode |
| `SLOW_MO` | `0` | Slow down browser actions by N ms |
| `SCREENSHOT_ON_FAILURE` | `true` | Take screenshots on test failure |

## Running Tests

### Run All Tests

```bash
# Inside backend container
docker-compose exec backend pytest backend/tests/playwright/ -v

# Or from host (if pytest available)
cd backend
pytest tests/playwright/ -v
```

### Run Specific Test Suite

```bash
# Users CRUD tests only
pytest tests/playwright/test_users_crud.py -v

# Roles CRUD tests only
pytest tests/playwright/test_roles_crud.py -v

# Departments tests only
pytest tests/playwright/test_departments.py -v
```

### Run Specific Test

```bash
# Run single test
pytest tests/playwright/test_users_crud.py::test_user_create -v

# Run with detailed output
pytest tests/playwright/test_users_crud.py::test_user_create -vvs
```

### Run in Non-Headless Mode (See Browser)

```bash
# Export environment variable
export HEADLESS=false

# Run tests
pytest tests/playwright/ -v
```

### Run with Slow Motion (Debug)

```bash
# Slow down by 1000ms (1 second) per action
export SLOW_MO=1000

# Run tests
pytest tests/playwright/ -v
```

## Test Cases

### Users CRUD Tests (`test_users_crud.py`)

| Test ID | Test Name | Description | Steps |
|---------|-----------|-------------|-------|
| **TC_USER_001** | Create New User | Verify admin can create user | 1. Navigate to Users tab<br>2. Click Create User<br>3. Fill form<br>4. Save<br>5. Verify in table |
| **TC_USER_002** | View Users List | Verify admin can view users | 1. Navigate to Users tab<br>2. Verify table displayed |
| **TC_USER_003** | Update Existing User | Verify admin can update user (PATCH) | 1. Click Edit<br>2. Update fields<br>3. Save<br>4. Verify changes |
| **TC_USER_004** | Soft Delete User | Verify admin can deactivate user | 1. Click Delete<br>2. Confirm<br>3. Verify removed |

### Roles CRUD Tests (`test_roles_crud.py`)

| Test ID | Test Name | Description | Steps |
|---------|-----------|-------------|-------|
| **TC_ROLE_001** | Create New Role | Verify admin can create role | 1. Navigate to Roles tab<br>2. Click Create Role<br>3. Fill form<br>4. Save<br>5. Verify in table |
| **TC_ROLE_002** | View Roles List | Verify admin can view roles | 1. Navigate to Roles tab<br>2. Verify table displayed |
| **TC_ROLE_003** | Update Existing Role | Verify admin can update role | 1. Click Edit<br>2. Update fields<br>3. Save<br>4. Verify changes |
| **TC_ROLE_004** | Delete Role | Verify admin can delete role | 1. Click Delete<br>2. Confirm<br>3. Verify removed |

### Departments Tests (`test_departments.py`)

| Test ID | Test Name | Description | Steps |
|---------|-----------|-------------|-------|
| **TC_DEPT_001** | Create New Department | Verify admin can create department | 1. Navigate to Departments tab<br>2. Click Create Department<br>3. Fill form<br>4. Save<br>5. Verify in table |
| **TC_DEPT_002** | View Departments List | Verify admin can view departments | 1. Navigate to Departments tab<br>2. Verify table displayed |

**Note**: Department UPDATE and DELETE endpoints are not yet implemented in the backend.

## Test Reports

After running tests, comprehensive HTML and JSON reports are generated in `test_results/` directory.

### HTML Report Features

- **Summary Dashboard**: Total tests, passed, failed, pass rate
- **Expandable Test Cases**: Click to expand/collapse test details
- **Step-by-Step Results**: Each test step shows:
  - Step number and description
  - Expected result
  - Actual result
  - Status (passed/failed)
  - **Before screenshot**: State before action
  - **After screenshot**: State after action
  - Error messages (if failed)
- **Color-Coded Status**: Green (passed), Red (failed)
- **Duration Tracking**: Test execution time for each test case

### Viewing Reports

```bash
# Open HTML report in browser
open backend/tests/playwright/test_results/users_crud_test_report.html

# Or use Python HTTP server
cd backend/tests/playwright/test_results
python -m http.server 8080
# Then navigate to http://localhost:8080
```

### Report Structure

**HTML Report** (`*_test_report.html`):
- Interactive HTML with expandable test cases
- Embedded screenshots (before/after each step)
- Summary statistics
- Color-coded pass/fail status

**JSON Report** (`*_test_report.json`):
- Machine-readable format for CI/CD integration
- Detailed test results including:
  - Session timestamps
  - Test case metadata
  - Step-by-step results
  - Screenshot paths
  - Error messages

## Page Object Model

### BasePage (`base_page.py`)

Base class providing common page methods:
- `navigate_to(path)`: Navigate to a URL
- `wait_for_element(selector)`: Wait for element visibility
- `click(selector)`: Click an element
- `fill(selector, value)`: Fill input field
- `screenshot(filename)`: Take screenshot

### LoginPage (`login_page.py`)

Handles login functionality:
- `navigate()`: Go to login page
- `login(username, password)`: Perform login
- `is_logged_in()`: Check if logged in

### AdminDashboardPage (`admin_dashboard_page.py`)

Comprehensive admin dashboard interactions:

**Navigation:**
- `navigate_to_admin()`: Go to admin dashboard
- `click_users_tab()`: Switch to Users tab
- `click_roles_tab()`: Switch to Roles tab
- `click_departments_tab()`: Switch to Departments tab
- `click_permissions_tab()`: Switch to Permissions tab

**Users Management:**
- `click_create_user()`: Open user creation form
- `fill_user_form(username, email, password, role)`: Fill user form
- `save_user()`: Save user
- `find_user_in_table(username)`: Check if user exists
- `click_edit_user(username)`: Edit specific user
- `click_delete_user(username)`: Delete specific user
- `confirm_delete()`: Confirm deletion modal

**Roles Management:**
- `click_create_role()`: Open role creation form
- `fill_role_form(name, description)`: Fill role form
- `save_role()`: Save role
- `find_role_in_table(role_name)`: Check if role exists
- `click_edit_role(role_name)`: Edit specific role
- `click_delete_role(role_name)`: Delete specific role

**Departments Management:**
- `click_create_department()`: Open department creation form
- `fill_department_form(name)`: Fill department form
- `save_department()`: Save department
- `find_department_in_table(dept_name)`: Check if department exists

**Common:**
- `close_modal()`: Close any modal
- `is_success_toast_visible()`: Check for success message
- `is_error_toast_visible()`: Check for error message
- `get_table_row_count()`: Get table row count

## Fixtures

### Session Fixtures
- `playwright_instance`: Playwright session instance
- `browser`: Browser instance (Chromium)

### Function Fixtures
- `context`: Fresh browser context per test
- `page`: Fresh page per test
- `logged_in_admin_page`: Page with admin already logged in
- `admin_dashboard`: Admin dashboard page object with logged-in admin
- `cleanup_test_user`: Auto-cleanup test users
- `cleanup_test_role`: Auto-cleanup test roles
- `cleanup_test_department`: Auto-cleanup test departments

## Best Practices

### Writing New Tests

1. **Use Test Reporter**:
   ```python
   from test_reporter import TestReporter, TestCase, TestStep

   reporter = TestReporter()
   test_case = TestCase("TC_XXX_001", "Test Name", "Description")
   test_case.start()
   ```

2. **Add Steps with Screenshots**:
   ```python
   step1 = TestStep(1, "Action description", "Expected result")
   test_case.add_step(step1)

   # Before screenshot
   admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_XXX_001_step1_before.png")
   step1.screenshot_before = "TC_XXX_001_step1_before.png"

   # Perform action
   admin_dashboard.some_action()

   # After screenshot
   admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_XXX_001_step1_after.png")
   step1.screenshot_after = "TC_XXX_001_step1_after.png"
   step1.actual_result = "What happened"
   step1.status = "passed"  # or "failed"
   ```

3. **Complete Test Case**:
   ```python
   test_case.complete("passed")  # or "failed" with error message
   reporter.add_test_case(test_case)
   assert test_case.status == "passed", f"Test failed: {test_case.overall_error}"
   ```

4. **Generate Reports**:
   ```python
   @pytest.fixture(scope="module", autouse=True)
   def generate_report():
       yield
       reporter.generate_html_report("my_test_report.html")
       reporter.generate_json_report("my_test_report.json")
   ```

### Test Naming Convention

- Test files: `test_<module>_<action>.py` (e.g., `test_users_crud.py`)
- Test functions: `test_<entity>_<action>` (e.g., `test_user_create`)
- Test IDs: `TC_<MODULE>_<NUMBER>` (e.g., `TC_USER_001`)
- Screenshots: `<TEST_ID>_step<N>_<before|after>.png` (e.g., `TC_USER_001_step1_before.png`)

### Selectors

Use robust selectors in order of preference:
1. **Text-based**: `button:has-text("Save")`
2. **Role-based**: `[role="dialog"]`
3. **Data attributes**: `[data-testid="user-form"]`
4. **Name attributes**: `input[name="username"]`
5. **Type-based**: `input[type="email"]`
6. **Class/ID** (least preferred): `.user-modal`, `#user-form`

## Troubleshooting

### Tests Fail with "Element Not Found"

**Solution**: Increase wait times or update selectors
```python
# Increase timeout
admin_dashboard.wait_for_element(selector, timeout=20000)  # 20 seconds

# Or add explicit wait
time.sleep(2)
```

### Screenshots Not Captured

**Check**:
1. `test_results/` directory exists
2. Path is correct in screenshot calls
3. Write permissions are set

### Tests Pass Locally But Fail in CI

**Common Issues**:
1. Timing issues → Add `time.sleep()` or increase timeouts
2. Headless mode differences → Test with `HEADLESS=true` locally
3. Different screen resolutions → Set explicit viewport in `conftest.py`

### Admin Login Fails

**Check**:
1. Backend is running and accessible
2. Admin user exists in database
3. Credentials in `conftest.py` are correct
4. Frontend URL is correct

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run Playwright Tests
  run: |
    docker-compose exec -T backend pytest backend/tests/playwright/ -v

- name: Upload Test Reports
  uses: actions/upload-artifact@v3
  with:
    name: playwright-reports
    path: backend/tests/playwright/test_results/
```

### Parse JSON Reports

```python
import json

with open('test_results/users_crud_test_report.json') as f:
    report = json.load(f)

passed = report['passed_tests']
failed = report['failed_tests']
pass_rate = (passed / report['total_tests']) * 100
```

## Maintenance

### Updating Selectors

If UI changes, update selectors in `admin_dashboard_page.py`:

```python
# Old selector
CREATE_USER_BUTTON = 'button:has-text("Add User")'

# New selector (if button text changed)
CREATE_USER_BUTTON = 'button:has-text("Create New User")'
```

### Adding New Tests

1. Create test file: `test_<module>.py`
2. Import dependencies
3. Create test functions
4. Use Test Reporter for detailed reports
5. Add cleanup fixtures if needed
6. Update this README

## Support

For issues or questions:
- Check existing test examples in this directory
- Review error messages and screenshots in `test_results/`
- Check backend/frontend logs for API errors
- Refer to Playwright documentation: https://playwright.dev/python/

## Additional Resources

- **Playwright Python Docs**: https://playwright.dev/python/
- **Pytest Documentation**: https://docs.pytest.org/
- **Page Object Model Pattern**: https://playwright.dev/python/docs/pom

---

**Last Updated**: 2025-12-01
**Version**: 1.0.0
**Author**: AI Assistant (Automated Test Framework)
