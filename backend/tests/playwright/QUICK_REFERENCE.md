# Playwright RBAC Testing - Quick Reference

Quick commands and examples for running Admin Dashboard Playwright tests.

---

## One-Line Commands

```bash
# Run all tests
docker-compose exec backend pytest backend/tests/playwright/ -v

# Run with visible browser (non-headless)
docker-compose exec backend bash -c "export HEADLESS=false && pytest backend/tests/playwright/ -v"

# Run specific test file
docker-compose exec backend pytest backend/tests/playwright/test_users_crud.py -v

# Run single test
docker-compose exec backend pytest backend/tests/playwright/test_users_crud.py::test_user_create -vvs

# View HTML report
open backend/tests/playwright/test_results/users_crud_test_report.html
```

---

## Test Files

| File | Tests | Description |
|------|-------|-------------|
| `test_users_crud.py` | 4 tests | Users CRUD operations |
| `test_roles_crud.py` | 4 tests | Roles CRUD operations |
| `test_departments.py` | 2 tests | Departments create/read |

---

## Test Cases Quick Reference

### Users Tests

```bash
# All users tests
pytest backend/tests/playwright/test_users_crud.py -v

# Individual tests
pytest backend/tests/playwright/test_users_crud.py::test_user_create -v
pytest backend/tests/playwright/test_users_crud.py::test_user_read -v
pytest backend/tests/playwright/test_users_crud.py::test_user_update -v
pytest backend/tests/playwright/test_users_crud.py::test_user_soft_delete -v
```

**Test Cases**:
- ✅ TC_USER_001: Create new user
- ✅ TC_USER_002: View users list
- ✅ TC_USER_003: Update user (PATCH method)
- ✅ TC_USER_004: Soft delete user (deactivate)

### Roles Tests

```bash
# All roles tests
pytest backend/tests/playwright/test_roles_crud.py -v

# Individual tests
pytest backend/tests/playwright/test_roles_crud.py::test_role_create -v
pytest backend/tests/playwright/test_roles_crud.py::test_role_read -v
pytest backend/tests/playwright/test_roles_crud.py::test_role_update -v
pytest backend/tests/playwright/test_roles_crud.py::test_role_delete -v
```

**Test Cases**:
- ✅ TC_ROLE_001: Create new role
- ✅ TC_ROLE_002: View roles list
- ✅ TC_ROLE_003: Update role
- ✅ TC_ROLE_004: Delete role

### Departments Tests

```bash
# All departments tests
pytest backend/tests/playwright/test_departments.py -v

# Individual tests
pytest backend/tests/playwright/test_departments.py::test_department_create -v
pytest backend/tests/playwright/test_departments.py::test_department_read -v
```

**Test Cases**:
- ✅ TC_DEPT_001: Create new department
- ✅ TC_DEPT_002: View departments list

---

## Environment Configuration

Set these before running tests:

```bash
# Run with visible browser
export HEADLESS=false

# Slow down for debugging (1 second per action)
export SLOW_MO=1000

# Change frontend URL
export FRONTEND_URL=http://localhost:3001

# Change admin credentials
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=admin123

# Then run tests
pytest backend/tests/playwright/ -v
```

---

## Viewing Reports

### HTML Reports

**Generated reports**:
- `backend/tests/playwright/test_results/users_crud_test_report.html`
- `backend/tests/playwright/test_results/roles_crud_test_report.html`
- `backend/tests/playwright/test_results/departments_test_report.html`

**View in browser**:
```bash
# macOS
open backend/tests/playwright/test_results/users_crud_test_report.html

# Linux
xdg-open backend/tests/playwright/test_results/users_crud_test_report.html

# Windows
start backend/tests/playwright/test_results/users_crud_test_report.html

# Or use HTTP server
cd backend/tests/playwright/test_results
python -m http.server 8080
# Navigate to: http://localhost:8080
```

### JSON Reports

```bash
# View JSON report
cat backend/tests/playwright/test_results/users_crud_test_report.json | jq .

# Get pass rate
cat backend/tests/playwright/test_results/users_crud_test_report.json | jq '.passed_tests, .failed_tests, .total_tests'
```

---

## Screenshots

**Location**: `backend/tests/playwright/test_results/`

**Naming**: `<TEST_ID>_step<N>_<before|after>.png`

**Examples**:
- `TC_USER_001_step1_before.png` - Before navigating to Users tab
- `TC_USER_001_step1_after.png` - After navigating to Users tab
- `FAILED_test_user_create.png` - Failure screenshot (auto-captured)

**View screenshots**:
```bash
# List all screenshots
ls -lh backend/tests/playwright/test_results/*.png

# View specific screenshot
open backend/tests/playwright/test_results/TC_USER_001_step1_after.png
```

---

## Debugging

### Run Single Test with Detailed Output

```bash
# Maximum verbosity
docker-compose exec backend pytest backend/tests/playwright/test_users_crud.py::test_user_create -vvs

# With stdout/stderr
docker-compose exec backend pytest backend/tests/playwright/test_users_crud.py::test_user_create -vvs --capture=no
```

### Run with Visible Browser + Slow Motion

```bash
docker-compose exec backend bash -c "export HEADLESS=false && export SLOW_MO=1000 && pytest backend/tests/playwright/test_users_crud.py::test_user_create -vvs"
```

### Check Test Discovery

```bash
# List all available tests
docker-compose exec backend pytest backend/tests/playwright/ --collect-only
```

### Troubleshooting

**Services not running?**
```bash
docker-compose ps
docker-compose up -d backend frontend postgres
```

**Admin user doesn't exist?**
```bash
docker-compose exec backend python create_admin_user.py
```

**Playwright not installed?**
```bash
docker-compose exec backend pip install playwright
docker-compose exec backend playwright install chromium
```

---

## CI/CD Integration

### Run in CI

```bash
# Non-interactive mode
docker-compose exec -T backend pytest backend/tests/playwright/ -v --tb=short

# Generate JUnit XML
docker-compose exec -T backend pytest backend/tests/playwright/ -v --junitxml=test-results.xml

# Upload artifacts (GitHub Actions)
- uses: actions/upload-artifact@v3
  with:
    name: playwright-reports
    path: backend/tests/playwright/test_results/
```

---

## File Structure Reference

```
backend/tests/playwright/
├── README.md                      # Full documentation
├── QUICK_REFERENCE.md            # This file
├── conftest.py                   # Fixtures
├── test_reporter.py              # Reporting
├── page_objects/
│   ├── base_page.py
│   ├── login_page.py
│   └── admin_dashboard_page.py
├── test_users_crud.py            # 4 tests
├── test_roles_crud.py            # 4 tests
├── test_departments.py           # 2 tests
└── test_results/
    ├── *.png                     # Screenshots
    ├── *_test_report.html        # HTML reports
    └── *_test_report.json        # JSON reports
```

---

## Common Patterns

### Adding New Test

```python
from test_reporter import TestReporter, TestCase, TestStep

reporter = TestReporter()

def test_my_new_feature(admin_dashboard):
    test_case = TestCase("TC_XXX_001", "My Test", "Description")
    test_case.start()

    try:
        # Step 1
        step1 = TestStep(1, "Do something", "Expected result")
        test_case.add_step(step1)

        # Before screenshot
        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_XXX_001_step1_before.png")
        step1.screenshot_before = "TC_XXX_001_step1_before.png"

        # Action
        admin_dashboard.some_action()

        # After screenshot
        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_XXX_001_step1_after.png")
        step1.screenshot_after = "TC_XXX_001_step1_after.png"
        step1.actual_result = "What happened"
        step1.status = "passed"

        test_case.complete("passed")
    except Exception as e:
        test_case.complete("failed", str(e))

    reporter.add_test_case(test_case)
    assert test_case.status == "passed"
```

---

## Useful Commands Summary

```bash
# Run tests
pytest backend/tests/playwright/ -v                        # All tests
pytest backend/tests/playwright/test_users_crud.py -v      # Users only
pytest backend/tests/playwright/test_users_crud.py::test_user_create -v  # Single test

# Debug mode
export HEADLESS=false && export SLOW_MO=1000
pytest backend/tests/playwright/ -vvs

# View reports
open backend/tests/playwright/test_results/users_crud_test_report.html
cat backend/tests/playwright/test_results/users_crud_test_report.json | jq .

# Screenshots
ls backend/tests/playwright/test_results/*.png
open backend/tests/playwright/test_results/TC_USER_001_step1_after.png
```

---

**For full documentation, see**: `backend/tests/playwright/README.md`
**For implementation details, see**: `docs/testing/PLAYWRIGHT_RBAC_TESTING_COMPLETE_2025-12-01.md`

---

**Last Updated**: 2025-12-01
