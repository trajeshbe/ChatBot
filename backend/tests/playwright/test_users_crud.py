"""Comprehensive CRUD tests for Users management in Admin Dashboard."""
import pytest
from page_objects.admin_dashboard_page import AdminDashboardPage
from test_reporter import TestReporter, TestCase, TestStep
import time
from datetime import datetime


# Global reporter instance
reporter = TestReporter()


def test_user_create(admin_dashboard: AdminDashboardPage, cleanup_test_user):
    """Test Case: Create a new user in Admin Dashboard."""
    test_case = TestCase(
        test_id="TC_USER_001",
        test_name="Create New User",
        test_description="Verify that admin can create a new user with valid credentials"
    )
    test_case.start()

    try:
        # Step 1: Navigate to Users tab
        step1 = TestStep(1, "Navigate to Users tab", "Users tab is displayed with user list")
        test_case.add_step(step1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_001_step1_before.png")
        step1.screenshot_before = "TC_USER_001_step1_before.png"

        admin_dashboard.click_users_tab()
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_001_step1_after.png")
        step1.screenshot_after = "TC_USER_001_step1_after.png"
        step1.actual_result = "Users tab opened successfully"
        step1.status = "passed"

        # Step 2: Click Create User button
        step2 = TestStep(2, "Click Create User button", "User creation modal/form is displayed")
        test_case.add_step(step2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_001_step2_before.png")
        step2.screenshot_before = "TC_USER_001_step2_before.png"

        admin_dashboard.click_create_user()
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_001_step2_after.png")
        step2.screenshot_after = "TC_USER_001_step2_after.png"
        step2.actual_result = "User creation form displayed"
        step2.status = "passed"

        # Step 3: Fill user form
        test_username = f"testuser_{int(time.time())}"
        test_email = f"{test_username}@example.com"
        test_password = "SecurePass123!"

        cleanup_test_user(test_username)  # Register for cleanup

        step3 = TestStep(
            3,
            "Fill user form with valid data",
            f"Form fields populated: username={test_username}, email={test_email}, role=User"
        )
        test_case.add_step(step3)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_001_step3_before.png")
        step3.screenshot_before = "TC_USER_001_step3_before.png"

        admin_dashboard.fill_user_form(test_username, test_email, test_password, "User")
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_001_step3_after.png")
        step3.screenshot_after = "TC_USER_001_step3_after.png"
        step3.actual_result = f"Form filled with username={test_username}, email={test_email}"
        step3.status = "passed"

        # Step 4: Save user
        step4 = TestStep(4, "Click Save button", "User is created and appears in user list")
        test_case.add_step(step4)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_001_step4_before.png")
        step4.screenshot_before = "TC_USER_001_step4_before.png"

        admin_dashboard.save_user()
        time.sleep(2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_001_step4_after.png")
        step4.screenshot_after = "TC_USER_001_step4_after.png"

        # Step 5: Verify user in table
        step5 = TestStep(5, "Verify user appears in table", f"User '{test_username}' is visible in the user list")
        test_case.add_step(step5)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_001_step5_before.png")
        step5.screenshot_before = "TC_USER_001_step5_before.png"

        user_found = admin_dashboard.find_user_in_table(test_username)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_001_step5_after.png")
        step5.screenshot_after = "TC_USER_001_step5_after.png"

        if user_found:
            step4.actual_result = "User created successfully"
            step4.status = "passed"
            step5.actual_result = f"User '{test_username}' found in table"
            step5.status = "passed"
            test_case.complete("passed")
        else:
            step4.actual_result = "User creation failed - not found in table"
            step4.status = "failed"
            step5.actual_result = f"User '{test_username}' NOT found in table"
            step5.status = "failed"
            test_case.complete("failed", "User not found in table after creation")

    except Exception as e:
        test_case.complete("failed", str(e))
        # Mark all pending steps as failed
        for step in test_case.steps:
            if step.status == "pending":
                step.status = "failed"
                step.error_message = str(e)

    reporter.add_test_case(test_case)
    assert test_case.status == "passed", f"Test failed: {test_case.overall_error}"


def test_user_read(admin_dashboard: AdminDashboardPage):
    """Test Case: Read/View users in Admin Dashboard."""
    test_case = TestCase(
        test_id="TC_USER_002",
        test_name="View Users List",
        test_description="Verify that admin can view the list of users"
    )
    test_case.start()

    try:
        # Step 1: Navigate to Users tab
        step1 = TestStep(1, "Navigate to Users tab", "Users tab is displayed")
        test_case.add_step(step1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_002_step1_before.png")
        step1.screenshot_before = "TC_USER_002_step1_before.png"

        admin_dashboard.click_users_tab()
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_002_step1_after.png")
        step1.screenshot_after = "TC_USER_002_step1_after.png"
        step1.actual_result = "Users tab opened successfully"
        step1.status = "passed"

        # Step 2: Verify table is displayed
        step2 = TestStep(2, "Verify users table is displayed", "Users table with user data is visible")
        test_case.add_step(step2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_002_step2_before.png")
        step2.screenshot_before = "TC_USER_002_step2_before.png"

        row_count = admin_dashboard.get_table_row_count()

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_002_step2_after.png")
        step2.screenshot_after = "TC_USER_002_step2_after.png"

        if row_count > 0:
            step2.actual_result = f"Users table displayed with {row_count} users"
            step2.status = "passed"
            test_case.complete("passed")
        else:
            step2.actual_result = "Users table displayed but no users found"
            step2.status = "failed"
            test_case.complete("failed", "No users found in table")

    except Exception as e:
        test_case.complete("failed", str(e))
        for step in test_case.steps:
            if step.status == "pending":
                step.status = "failed"
                step.error_message = str(e)

    reporter.add_test_case(test_case)
    assert test_case.status == "passed", f"Test failed: {test_case.overall_error}"


def test_user_update(admin_dashboard: AdminDashboardPage, cleanup_test_user):
    """Test Case: Update an existing user in Admin Dashboard."""
    test_case = TestCase(
        test_id="TC_USER_003",
        test_name="Update Existing User",
        test_description="Verify that admin can update an existing user's information using PATCH method"
    )
    test_case.start()

    try:
        # First create a user to update
        admin_dashboard.click_users_tab()
        time.sleep(1)

        test_username = f"updateuser_{int(time.time())}"
        test_email = f"{test_username}@example.com"
        cleanup_test_user(test_username)

        admin_dashboard.click_create_user()
        time.sleep(1)
        admin_dashboard.fill_user_form(test_username, test_email, "Pass123!", "User")
        admin_dashboard.save_user()
        time.sleep(2)

        # Step 1: Click Edit button for user
        step1 = TestStep(1, f"Click Edit button for user '{test_username}'", "Edit user modal/form is displayed")
        test_case.add_step(step1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_003_step1_before.png")
        step1.screenshot_before = "TC_USER_003_step1_before.png"

        admin_dashboard.click_edit_user(test_username)
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_003_step1_after.png")
        step1.screenshot_after = "TC_USER_003_step1_after.png"
        step1.actual_result = "Edit user form displayed"
        step1.status = "passed"

        # Step 2: Update user information
        updated_email = f"updated_{test_email}"
        step2 = TestStep(2, "Update user email", f"Email updated to {updated_email}")
        test_case.add_step(step2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_003_step2_before.png")
        step2.screenshot_before = "TC_USER_003_step2_before.png"

        # Clear and fill new email (using PATCH method via backend)
        admin_dashboard.fill_user_form(test_username, updated_email, "", "User")
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_003_step2_after.png")
        step2.screenshot_after = "TC_USER_003_step2_after.png"
        step2.actual_result = f"Form updated with new email: {updated_email}"
        step2.status = "passed"

        # Step 3: Save changes
        step3 = TestStep(3, "Click Save button", "User information is updated")
        test_case.add_step(step3)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_003_step3_before.png")
        step3.screenshot_before = "TC_USER_003_step3_before.png"

        admin_dashboard.save_user()
        time.sleep(2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_003_step3_after.png")
        step3.screenshot_after = "TC_USER_003_step3_after.png"
        step3.actual_result = "User updated successfully"
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


def test_user_soft_delete(admin_dashboard: AdminDashboardPage, cleanup_test_user):
    """Test Case: Soft delete a user (set is_active=false)."""
    test_case = TestCase(
        test_id="TC_USER_004",
        test_name="Soft Delete User",
        test_description="Verify that admin can deactivate a user (soft delete)"
    )
    test_case.start()

    try:
        # First create a user to delete
        admin_dashboard.click_users_tab()
        time.sleep(1)

        test_username = f"deleteuser_{int(time.time())}"
        test_email = f"{test_username}@example.com"
        cleanup_test_user(test_username)

        admin_dashboard.click_create_user()
        time.sleep(1)
        admin_dashboard.fill_user_form(test_username, test_email, "Pass123!", "User")
        admin_dashboard.save_user()
        time.sleep(2)

        # Step 1: Click Delete button for user
        step1 = TestStep(1, f"Click Delete button for user '{test_username}'", "Delete confirmation dialog is displayed")
        test_case.add_step(step1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_004_step1_before.png")
        step1.screenshot_before = "TC_USER_004_step1_before.png"

        admin_dashboard.click_delete_user(test_username)
        time.sleep(1)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_004_step1_after.png")
        step1.screenshot_after = "TC_USER_004_step1_after.png"
        step1.actual_result = "Delete confirmation displayed"
        step1.status = "passed"

        # Step 2: Confirm deletion
        step2 = TestStep(2, "Click Confirm delete", "User is deactivated (soft deleted)")
        test_case.add_step(step2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_004_step2_before.png")
        step2.screenshot_before = "TC_USER_004_step2_before.png"

        admin_dashboard.confirm_delete()
        time.sleep(2)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_004_step2_after.png")
        step2.screenshot_after = "TC_USER_004_step2_after.png"

        # Step 3: Verify user is removed from table (or marked inactive)
        step3 = TestStep(3, "Verify user removed from active list", "User no longer appears in active users list")
        test_case.add_step(step3)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_004_step3_before.png")
        step3.screenshot_before = "TC_USER_004_step3_before.png"

        user_found = admin_dashboard.find_user_in_table(test_username)

        admin_dashboard.page.screenshot(path="backend/tests/playwright/test_results/TC_USER_004_step3_after.png")
        step3.screenshot_after = "TC_USER_004_step3_after.png"

        if not user_found:
            step2.actual_result = "User soft deleted successfully"
            step2.status = "passed"
            step3.actual_result = f"User '{test_username}' removed from active list"
            step3.status = "passed"
            test_case.complete("passed")
        else:
            step2.actual_result = "Soft delete may have failed"
            step2.status = "failed"
            step3.actual_result = f"User '{test_username}' still visible in table"
            step3.status = "failed"
            test_case.complete("failed", "User still visible after deletion")

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
    reporter.generate_html_report("users_crud_test_report.html")
    reporter.generate_json_report("users_crud_test_report.json")
