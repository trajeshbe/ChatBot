"""Tests for Departments management in Admin Dashboard."""
import pytest
from page_objects.admin_dashboard_page import AdminDashboardPage
from test_reporter import TestReporter, TestCase, TestStep
import time


# Global reporter instance
reporter = TestReporter()


def test_department_create(admin_dashboard: AdminDashboardPage):
    """Test Case: Create a new department in Admin Dashboard."""
    test_case = TestCase(
        test_id="TC_DEPT_001",
        test_name="Create New Department",
        test_description="Verify that admin can create a new department"
    )
    test_case.start()

    try:
        # Step 1: Navigate to Departments tab
        step1 = TestStep(1, "Navigate to Departments tab", "Departments tab is displayed with department list")
        test_case.add_step(step1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_DEPT_001_step1_before.png")
        step1.screenshot_before = "TC_DEPT_001_step1_before.png"

        admin_dashboard.click_departments_tab()
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_DEPT_001_step1_after.png")
        step1.screenshot_after = "TC_DEPT_001_step1_after.png"
        step1.actual_result = "Departments tab opened successfully"
        step1.status = "passed"

        # Step 2: Click Create Department button
        step2 = TestStep(2, "Click Create Department button", "Department creation modal/form is displayed")
        test_case.add_step(step2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_DEPT_001_step2_before.png")
        step2.screenshot_before = "TC_DEPT_001_step2_before.png"

        admin_dashboard.click_create_department()
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_DEPT_001_step2_after.png")
        step2.screenshot_after = "TC_DEPT_001_step2_after.png"
        step2.actual_result = "Department creation form displayed"
        step2.status = "passed"

        # Step 3: Fill department form
        test_dept_name = f"TestDept_{int(time.time())}"

        step3 = TestStep(
            3,
            "Fill department form with valid data",
            f"Form field populated: name={test_dept_name}"
        )
        test_case.add_step(step3)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_DEPT_001_step3_before.png")
        step3.screenshot_before = "TC_DEPT_001_step3_before.png"

        admin_dashboard.fill_department_form(test_dept_name)
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_DEPT_001_step3_after.png")
        step3.screenshot_after = "TC_DEPT_001_step3_after.png"
        step3.actual_result = f"Form filled with name={test_dept_name}"
        step3.status = "passed"

        # Step 4: Save department
        step4 = TestStep(4, "Click Save button", "Department is created and appears in department list")
        test_case.add_step(step4)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_DEPT_001_step4_before.png")
        step4.screenshot_before = "TC_DEPT_001_step4_before.png"

        admin_dashboard.save_department()
        time.sleep(2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_DEPT_001_step4_after.png")
        step4.screenshot_after = "TC_DEPT_001_step4_after.png"

        # Step 5: Verify department in table
        step5 = TestStep(5, "Verify department appears in table", f"Department '{test_dept_name}' is visible in the list")
        test_case.add_step(step5)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_DEPT_001_step5_before.png")
        step5.screenshot_before = "TC_DEPT_001_step5_before.png"

        dept_found = admin_dashboard.find_department_in_table(test_dept_name)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_DEPT_001_step5_after.png")
        step5.screenshot_after = "TC_DEPT_001_step5_after.png"

        if dept_found:
            step4.actual_result = "Department created successfully"
            step4.status = "passed"
            step5.actual_result = f"Department '{test_dept_name}' found in table"
            step5.status = "passed"
            test_case.complete("passed")
        else:
            step4.actual_result = "Department creation failed - not found in table"
            step4.status = "failed"
            step5.actual_result = f"Department '{test_dept_name}' NOT found in table"
            step5.status = "failed"
            test_case.complete("failed", "Department not found in table after creation")

    except Exception as e:
        test_case.complete("failed", str(e))
        for step in test_case.steps:
            if step.status == "pending":
                step.status = "failed"
                step.error_message = str(e)

    reporter.add_test_case(test_case)
    assert test_case.status == "passed", f"Test failed: {test_case.overall_error}"


def test_department_read(admin_dashboard: AdminDashboardPage):
    """Test Case: Read/View departments in Admin Dashboard."""
    test_case = TestCase(
        test_id="TC_DEPT_002",
        test_name="View Departments List",
        test_description="Verify that admin can view the list of departments"
    )
    test_case.start()

    try:
        # Step 1: Navigate to Departments tab
        step1 = TestStep(1, "Navigate to Departments tab", "Departments tab is displayed")
        test_case.add_step(step1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_DEPT_002_step1_before.png")
        step1.screenshot_before = "TC_DEPT_002_step1_before.png"

        admin_dashboard.click_departments_tab()
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_DEPT_002_step1_after.png")
        step1.screenshot_after = "TC_DEPT_002_step1_after.png"
        step1.actual_result = "Departments tab opened successfully"
        step1.status = "passed"

        # Step 2: Verify table is displayed
        step2 = TestStep(2, "Verify departments table is displayed", "Departments table with department data is visible")
        test_case.add_step(step2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_DEPT_002_step2_before.png")
        step2.screenshot_before = "TC_DEPT_002_step2_before.png"

        row_count = admin_dashboard.get_table_row_count()

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_DEPT_002_step2_after.png")
        step2.screenshot_after = "TC_DEPT_002_step2_after.png"

        if row_count > 0:
            step2.actual_result = f"Departments table displayed with {row_count} departments"
            step2.status = "passed"
            test_case.complete("passed")
        else:
            step2.actual_result = "Departments table displayed but no departments found"
            step2.status = "failed"
            test_case.complete("failed", "No departments found in table")

    except Exception as e:
        test_case.complete("failed", str(e))
        for step in test_case.steps:
            if step.status == "pending":
                step.status = "failed"
                step.error_message = str(e)

    reporter.add_test_case(test_case)
    assert test_case.status == "passed", f"Test failed: {test_case.overall_error}"


@pytest.fixture(scope="module", autouse=True)
def generate_report():
    """Generate test report after all tests complete."""
    yield
    # Generate reports
    reporter.generate_html_report("departments_test_report.html")
    reporter.generate_json_report("departments_test_report.json")
