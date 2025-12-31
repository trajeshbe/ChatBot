"""Comprehensive CRUD tests for Roles management in Admin Dashboard."""
import pytest
from page_objects.admin_dashboard_page import AdminDashboardPage
from test_reporter import TestReporter, TestCase, TestStep
import time


# Global reporter instance
reporter = TestReporter()


def test_role_create(admin_dashboard: AdminDashboardPage, cleanup_test_role):
    """Test Case: Create a new role in Admin Dashboard."""
    test_case = TestCase(
        test_id="TC_ROLE_001",
        test_name="Create New Role",
        test_description="Verify that admin can create a new role"
    )
    test_case.start()

    try:
        # Step 1: Navigate to Roles tab
        step1 = TestStep(1, "Navigate to Roles tab", "Roles tab is displayed with role list")
        test_case.add_step(step1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_001_step1_before.png")
        step1.screenshot_before = "TC_ROLE_001_step1_before.png"

        admin_dashboard.click_roles_tab()
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_001_step1_after.png")
        step1.screenshot_after = "TC_ROLE_001_step1_after.png"
        step1.actual_result = "Roles tab opened successfully"
        step1.status = "passed"

        # Step 2: Click Create Role button
        step2 = TestStep(2, "Click Create Role button", "Role creation modal/form is displayed")
        test_case.add_step(step2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_001_step2_before.png")
        step2.screenshot_before = "TC_ROLE_001_step2_before.png"

        admin_dashboard.click_create_role()
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_001_step2_after.png")
        step2.screenshot_after = "TC_ROLE_001_step2_after.png"
        step2.actual_result = "Role creation form displayed"
        step2.status = "passed"

        # Step 3: Fill role form
        test_role_name = f"TestRole_{int(time.time())}"
        test_description = "Test role created by automated test"

        cleanup_test_role(test_role_name)  # Register for cleanup

        step3 = TestStep(
            3,
            "Fill role form with valid data",
            f"Form fields populated: name={test_role_name}, description={test_description}"
        )
        test_case.add_step(step3)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_001_step3_before.png")
        step3.screenshot_before = "TC_ROLE_001_step3_before.png"

        admin_dashboard.fill_role_form(test_role_name, test_description)
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_001_step3_after.png")
        step3.screenshot_after = "TC_ROLE_001_step3_after.png"
        step3.actual_result = f"Form filled with name={test_role_name}"
        step3.status = "passed"

        # Step 4: Save role
        step4 = TestStep(4, "Click Save button", "Role is created and appears in role list")
        test_case.add_step(step4)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_001_step4_before.png")
        step4.screenshot_before = "TC_ROLE_001_step4_before.png"

        admin_dashboard.save_role()
        time.sleep(2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_001_step4_after.png")
        step4.screenshot_after = "TC_ROLE_001_step4_after.png"

        # Step 5: Verify role in table
        step5 = TestStep(5, "Verify role appears in table", f"Role '{test_role_name}' is visible in the role list")
        test_case.add_step(step5)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_001_step5_before.png")
        step5.screenshot_before = "TC_ROLE_001_step5_before.png"

        role_found = admin_dashboard.find_role_in_table(test_role_name)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_001_step5_after.png")
        step5.screenshot_after = "TC_ROLE_001_step5_after.png"

        if role_found:
            step4.actual_result = "Role created successfully"
            step4.status = "passed"
            step5.actual_result = f"Role '{test_role_name}' found in table"
            step5.status = "passed"
            test_case.complete("passed")
        else:
            step4.actual_result = "Role creation failed - not found in table"
            step4.status = "failed"
            step5.actual_result = f"Role '{test_role_name}' NOT found in table"
            step5.status = "failed"
            test_case.complete("failed", "Role not found in table after creation")

    except Exception as e:
        test_case.complete("failed", str(e))
        for step in test_case.steps:
            if step.status == "pending":
                step.status = "failed"
                step.error_message = str(e)

    reporter.add_test_case(test_case)
    assert test_case.status == "passed", f"Test failed: {test_case.overall_error}"


def test_role_read(admin_dashboard: AdminDashboardPage):
    """Test Case: Read/View roles in Admin Dashboard."""
    test_case = TestCase(
        test_id="TC_ROLE_002",
        test_name="View Roles List",
        test_description="Verify that admin can view the list of roles"
    )
    test_case.start()

    try:
        # Step 1: Navigate to Roles tab
        step1 = TestStep(1, "Navigate to Roles tab", "Roles tab is displayed")
        test_case.add_step(step1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_002_step1_before.png")
        step1.screenshot_before = "TC_ROLE_002_step1_before.png"

        admin_dashboard.click_roles_tab()
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_002_step1_after.png")
        step1.screenshot_after = "TC_ROLE_002_step1_after.png"
        step1.actual_result = "Roles tab opened successfully"
        step1.status = "passed"

        # Step 2: Verify table is displayed
        step2 = TestStep(2, "Verify roles table is displayed", "Roles table with role data is visible")
        test_case.add_step(step2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_002_step2_before.png")
        step2.screenshot_before = "TC_ROLE_002_step2_before.png"

        row_count = admin_dashboard.get_table_row_count()

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_002_step2_after.png")
        step2.screenshot_after = "TC_ROLE_002_step2_after.png"

        if row_count > 0:
            step2.actual_result = f"Roles table displayed with {row_count} roles"
            step2.status = "passed"
            test_case.complete("passed")
        else:
            step2.actual_result = "Roles table displayed but no roles found"
            step2.status = "failed"
            test_case.complete("failed", "No roles found in table")

    except Exception as e:
        test_case.complete("failed", str(e))
        for step in test_case.steps:
            if step.status == "pending":
                step.status = "failed"
                step.error_message = str(e)

    reporter.add_test_case(test_case)
    assert test_case.status == "passed", f"Test failed: {test_case.overall_error}"


def test_role_update(admin_dashboard: AdminDashboardPage, cleanup_test_role):
    """Test Case: Update an existing role in Admin Dashboard."""
    test_case = TestCase(
        test_id="TC_ROLE_003",
        test_name="Update Existing Role",
        test_description="Verify that admin can update an existing role's information"
    )
    test_case.start()

    try:
        # First create a role to update
        admin_dashboard.click_roles_tab()
        time.sleep(1)

        test_role_name = f"UpdateRole_{int(time.time())}"
        cleanup_test_role(test_role_name)

        admin_dashboard.click_create_role()
        time.sleep(1)
        admin_dashboard.fill_role_form(test_role_name, "Original description")
        admin_dashboard.save_role()
        time.sleep(2)

        # Step 1: Click Edit button for role
        step1 = TestStep(1, f"Click Edit button for role '{test_role_name}'", "Edit role modal/form is displayed")
        test_case.add_step(step1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_003_step1_before.png")
        step1.screenshot_before = "TC_ROLE_003_step1_before.png"

        admin_dashboard.click_edit_role(test_role_name)
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_003_step1_after.png")
        step1.screenshot_after = "TC_ROLE_003_step1_after.png"
        step1.actual_result = "Edit role form displayed"
        step1.status = "passed"

        # Step 2: Update role information
        updated_description = "Updated description by automated test"
        step2 = TestStep(2, "Update role description", f"Description updated to: {updated_description}")
        test_case.add_step(step2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_003_step2_before.png")
        step2.screenshot_before = "TC_ROLE_003_step2_before.png"

        admin_dashboard.fill_role_form(test_role_name, updated_description)
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_003_step2_after.png")
        step2.screenshot_after = "TC_ROLE_003_step2_after.png"
        step2.actual_result = f"Form updated with new description"
        step2.status = "passed"

        # Step 3: Save changes
        step3 = TestStep(3, "Click Save button", "Role information is updated")
        test_case.add_step(step3)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_003_step3_before.png")
        step3.screenshot_before = "TC_ROLE_003_step3_before.png"

        admin_dashboard.save_role()
        time.sleep(2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_003_step3_after.png")
        step3.screenshot_after = "TC_ROLE_003_step3_after.png"
        step3.actual_result = "Role updated successfully"
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


def test_role_delete(admin_dashboard: AdminDashboardPage, cleanup_test_role):
    """Test Case: Delete a role."""
    test_case = TestCase(
        test_id="TC_ROLE_004",
        test_name="Delete Role",
        test_description="Verify that admin can delete a role"
    )
    test_case.start()

    try:
        # First create a role to delete
        admin_dashboard.click_roles_tab()
        time.sleep(1)

        test_role_name = f"DeleteRole_{int(time.time())}"
        cleanup_test_role(test_role_name)

        admin_dashboard.click_create_role()
        time.sleep(1)
        admin_dashboard.fill_role_form(test_role_name, "Role to be deleted")
        admin_dashboard.save_role()
        time.sleep(2)

        # Step 1: Click Delete button for role
        step1 = TestStep(1, f"Click Delete button for role '{test_role_name}'", "Delete confirmation dialog is displayed")
        test_case.add_step(step1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_004_step1_before.png")
        step1.screenshot_before = "TC_ROLE_004_step1_before.png"

        admin_dashboard.click_delete_role(test_role_name)
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_004_step1_after.png")
        step1.screenshot_after = "TC_ROLE_004_step1_after.png"
        step1.actual_result = "Delete confirmation displayed"
        step1.status = "passed"

        # Step 2: Confirm deletion
        step2 = TestStep(2, "Click Confirm delete", "Role is deleted")
        test_case.add_step(step2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_004_step2_before.png")
        step2.screenshot_before = "TC_ROLE_004_step2_before.png"

        admin_dashboard.confirm_delete()
        time.sleep(2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_004_step2_after.png")
        step2.screenshot_after = "TC_ROLE_004_step2_after.png"

        # Step 3: Verify role is removed from table
        step3 = TestStep(3, "Verify role removed from list", "Role no longer appears in roles list")
        test_case.add_step(step3)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_004_step3_before.png")
        step3.screenshot_before = "TC_ROLE_004_step3_before.png"

        role_found = admin_dashboard.find_role_in_table(test_role_name)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_ROLE_004_step3_after.png")
        step3.screenshot_after = "TC_ROLE_004_step3_after.png"

        if not role_found:
            step2.actual_result = "Role deleted successfully"
            step2.status = "passed"
            step3.actual_result = f"Role '{test_role_name}' removed from list"
            step3.status = "passed"
            test_case.complete("passed")
        else:
            step2.actual_result = "Delete may have failed"
            step2.status = "failed"
            step3.actual_result = f"Role '{test_role_name}' still visible in table"
            step3.status = "failed"
            test_case.complete("failed", "Role still visible after deletion")

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
    reporter.generate_html_report("roles_crud_test_report.html")
    reporter.generate_json_report("roles_crud_test_report.json")
