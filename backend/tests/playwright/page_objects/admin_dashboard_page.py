"""Admin Dashboard Page Object."""
from playwright.sync_api import Page, expect
from .base_page import BasePage
import time


class AdminDashboardPage(BasePage):
    """Page object for Admin Dashboard."""

    # Navigation Selectors
    ADMIN_LINK = 'a[href="/admin"], button:has-text("Admin")'
    USERS_TAB = 'button:has-text("Users"), [role="tab"]:has-text("Users")'
    ROLES_TAB = 'button:has-text("Roles"), [role="tab"]:has-text("Roles")'
    DEPARTMENTS_TAB = 'button:has-text("Departments"), [role="tab"]:has-text("Departments")'
    PERMISSIONS_TAB = 'button:has-text("Permissions"), [role="tab"]:has-text("Permissions")'

    # RBAC Tab (Users management is under RBAC)
    RBAC_TAB = 'button:has-text("RBAC")'

    # Users Management
    CREATE_USER_BUTTON = 'button:has-text("Create User"), button:has-text("Add User"), button:has-text("New User")'
    # Note: Inputs don't have name/placeholder attributes, use type and position
    USERNAME_INPUT = 'input[type="text"]'
    EMAIL_INPUT = 'input[type="email"]'
    FULL_NAME_INPUT = 'input[type="text"]'  # Second text input
    PASSWORD_INPUT = 'input[type="password"]'
    ROLE_SELECT = 'select'
    SAVE_USER_BUTTON = 'button:has-text("Create User"):not(:has-text("Add")), button:has-text("Save")'

    # Users Table
    USERS_TABLE = 'table'
    USER_ROW = 'tr:has(td)'
    EDIT_USER_BUTTON = 'button:has-text("Edit"), button[title*="Edit"]'
    DELETE_USER_BUTTON = 'button:has-text("Delete"), button[title*="Delete"]'

    # Roles Management
    CREATE_ROLE_BUTTON = 'button:has-text("Create Role"), button:has-text("Add Role"), button:has-text("New Role")'
    ROLE_NAME_INPUT = 'input[name="name"], input[placeholder*="Role Name"]'
    ROLE_DESCRIPTION_INPUT = 'textarea[name="description"], input[name="description"]'
    SAVE_ROLE_BUTTON = 'button:has-text("Save"), button:has-text("Create"), button[type="submit"]'

    # Departments Management
    CREATE_DEPARTMENT_BUTTON = 'button:has-text("Create Department"), button:has-text("Add Department")'
    DEPARTMENT_NAME_INPUT = 'input[name="name"], input[placeholder*="Department"]'
    SAVE_DEPARTMENT_BUTTON = 'button:has-text("Save"), button:has-text("Create"), button[type="submit"]'

    # Permissions Matrix
    PERMISSION_CHECKBOX = 'input[type="checkbox"]'
    SAVE_PERMISSIONS_BUTTON = 'button:has-text("Save Permissions"), button:has-text("Update Permissions")'

    # Common Modals
    MODAL = '[role="dialog"], .modal, [class*="Modal"]'
    MODAL_CLOSE = 'button:has-text("Cancel"), button:has-text("Close"), button[aria-label="Close"]'
    CONFIRM_BUTTON = 'button:has-text("Confirm"), button:has-text("Yes"), button:has-text("OK")'

    # Toast/Notification
    TOAST_SUCCESS = '[role="alert"]:has-text("Success"), [class*="toast"]:has-text("Success")'
    TOAST_ERROR = '[role="alert"]:has-text("Error"), [class*="toast"]:has-text("Error")'

    def __init__(self, page: Page, base_url: str = "http://localhost:3001"):
        super().__init__(page, base_url)

    def navigate_to_admin(self):
        """Navigate to admin dashboard."""
        self.navigate_to("/admin")
        time.sleep(2)  # Wait for admin page to load
        self.wait_for_navigation()

    # === Users Management Methods ===

    def click_users_tab(self):
        """Click on Users tab (under RBAC)."""
        # First click RBAC tab if not already there
        if self.page.locator(self.RBAC_TAB).count() > 0:
            self.click(self.RBAC_TAB)
            time.sleep(1)
        # Then click Users sub-tab
        self.click(self.USERS_TAB)
        time.sleep(1)

    def click_create_user(self):
        """Click Create User button (toggles inline form)."""
        self.click(self.CREATE_USER_BUTTON)
        time.sleep(1)
        # Wait for username input to appear (inline form, not modal)
        self.wait_for_element(self.USERNAME_INPUT)

    def fill_user_form(self, username: str, email: str, password: str, role: str = "user"):
        """Fill user creation/edit form.
        Note: Inputs don't have name attributes, using order:
        - First text input: username
        - Email input: email
        - Second text input: full name (we'll use username)
        - Password input: password
        """
        # Get all text inputs
        text_inputs = self.page.locator('input[type="text"]').all()
        if len(text_inputs) >= 1:
            text_inputs[0].fill(username)  # Username
        if len(text_inputs) >= 2:
            text_inputs[1].fill(username)  # Full name (use username)

        # Fill email
        self.fill(self.EMAIL_INPUT, email)

        # Fill password
        if self.is_visible(self.PASSWORD_INPUT):
            self.fill(self.PASSWORD_INPUT, password)

        # Select role if dropdown is visible
        if self.page.locator(self.ROLE_SELECT).count() > 0:
            self.page.select_option(self.ROLE_SELECT, role)

    def save_user(self):
        """Click Save button for user."""
        self.click(self.SAVE_USER_BUTTON)
        time.sleep(2)  # Wait for save operation

    def find_user_in_table(self, username: str) -> bool:
        """Check if user exists in table."""
        return self.page.locator(f'tr:has-text("{username}")').count() > 0

    def click_edit_user(self, username: str):
        """Click edit button for specific user (toggles inline form)."""
        user_row = self.page.locator(f'tr:has-text("{username}")')
        user_row.locator(self.EDIT_USER_BUTTON).first.click()
        time.sleep(1)
        # Wait for username input to appear (inline form, not modal)
        self.wait_for_element(self.USERNAME_INPUT)

    def click_delete_user(self, username: str):
        """Click delete button for specific user."""
        user_row = self.page.locator(f'tr:has-text("{username}")')
        user_row.locator(self.DELETE_USER_BUTTON).first.click()
        time.sleep(1)

    def confirm_delete(self):
        """Confirm deletion in modal."""
        self.click(self.CONFIRM_BUTTON)
        time.sleep(2)

    # === Roles Management Methods ===

    def click_roles_tab(self):
        """Click on Roles tab (under RBAC)."""
        # First click RBAC tab if not already there
        if self.page.locator(self.RBAC_TAB).count() > 0:
            self.click(self.RBAC_TAB)
            time.sleep(1)
        # Then click Roles sub-tab
        self.click(self.ROLES_TAB)
        time.sleep(1)

    def click_create_role(self):
        """Click Create Role button (toggles inline form)."""
        self.click(self.CREATE_ROLE_BUTTON)
        time.sleep(1)
        # Wait for role name input to appear (inline form, not modal)
        self.wait_for_element(self.ROLE_NAME_INPUT)

    def fill_role_form(self, name: str, description: str = ""):
        """Fill role creation/edit form."""
        self.fill(self.ROLE_NAME_INPUT, name)
        if description and self.is_visible(self.ROLE_DESCRIPTION_INPUT):
            self.fill(self.ROLE_DESCRIPTION_INPUT, description)

    def save_role(self):
        """Click Save button for role."""
        self.click(self.SAVE_ROLE_BUTTON)
        time.sleep(2)

    def find_role_in_table(self, role_name: str) -> bool:
        """Check if role exists in table."""
        return self.page.locator(f'tr:has-text("{role_name}")').count() > 0

    def click_edit_role(self, role_name: str):
        """Click edit button for specific role (toggles inline form)."""
        role_row = self.page.locator(f'tr:has-text("{role_name}")')
        role_row.locator(self.EDIT_USER_BUTTON).first.click()
        time.sleep(1)
        # Wait for role name input to appear (inline form, not modal)
        self.wait_for_element(self.ROLE_NAME_INPUT)

    def click_delete_role(self, role_name: str):
        """Click delete button for specific role."""
        role_row = self.page.locator(f'tr:has-text("{role_name}")')
        role_row.locator(self.DELETE_USER_BUTTON).first.click()
        time.sleep(1)

    # === Departments Management Methods ===

    def click_departments_tab(self):
        """Click on Departments tab (under RBAC)."""
        # First click RBAC tab if not already there
        if self.page.locator(self.RBAC_TAB).count() > 0:
            self.click(self.RBAC_TAB)
            time.sleep(1)
        # Then click Departments sub-tab
        self.click(self.DEPARTMENTS_TAB)
        time.sleep(1)

    def click_create_department(self):
        """Click Create Department button (toggles inline form)."""
        self.click(self.CREATE_DEPARTMENT_BUTTON)
        time.sleep(1)
        # Wait for department name input to appear (inline form, not modal)
        self.wait_for_element(self.DEPARTMENT_NAME_INPUT)

    def fill_department_form(self, name: str):
        """Fill department creation form."""
        self.fill(self.DEPARTMENT_NAME_INPUT, name)

    def save_department(self):
        """Click Save button for department."""
        self.click(self.SAVE_DEPARTMENT_BUTTON)
        time.sleep(2)

    def find_department_in_table(self, dept_name: str) -> bool:
        """Check if department exists in table."""
        return self.page.locator(f'tr:has-text("{dept_name}")').count() > 0

    # === Permissions Management Methods ===

    def click_permissions_tab(self):
        """Click on Permissions tab."""
        self.click(self.PERMISSIONS_TAB)
        time.sleep(1)

    def toggle_permission(self, role: str, module: str, permission_type: str):
        """Toggle a specific permission checkbox.

        Args:
            role: Role name (e.g., "Admin", "User")
            module: Module name (e.g., "chat", "admin")
            permission_type: Permission type (e.g., "read", "write", "delete", "share")
        """
        # This is a simplified version - actual selector will depend on UI structure
        checkbox_selector = f'[data-role="{role}"][data-module="{module}"][data-permission="{permission_type}"]'
        if self.is_visible(checkbox_selector):
            self.click(checkbox_selector)

    def save_permissions(self):
        """Save permissions changes."""
        self.click(self.SAVE_PERMISSIONS_BUTTON)
        time.sleep(2)

    # === Common Methods ===

    def close_modal(self):
        """Close any open modal."""
        if self.is_visible(self.MODAL):
            self.click(self.MODAL_CLOSE)
            time.sleep(1)

    def is_success_toast_visible(self) -> bool:
        """Check if success toast is visible."""
        return self.is_visible(self.TOAST_SUCCESS)

    def is_error_toast_visible(self) -> bool:
        """Check if error toast is visible."""
        return self.is_visible(self.TOAST_ERROR)

    def get_table_row_count(self) -> int:
        """Get number of rows in current table (excluding header)."""
        return self.page.locator(self.USER_ROW).count()
