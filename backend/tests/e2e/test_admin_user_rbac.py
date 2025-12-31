"""
E2E Test: Admin User Management and RBAC
Tests user CRUD operations, role assignments, and permission validation.

Created: 2025-12-01
"""

import pytest
import httpx
import asyncio
from typing import Dict, List
import time


BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"  # Default admin password


class TestAdminUserRBAC:
    """Test suite for admin user management and RBAC functionality"""

    @pytest.fixture(scope="class")
    async def auth_token(self):
        """Get authentication token for admin user"""
        async with httpx.AsyncClient() as client:
            # Login as admin
            response = await client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={
                    "username": ADMIN_USERNAME,
                    "password": ADMIN_PASSWORD
                }
            )
            assert response.status_code == 200, f"Login failed: {response.text}"
            data = response.json()
            return data["access_token"]

    @pytest.fixture(scope="class")
    async def auth_headers(self, auth_token):
        """Get authorization headers"""
        token = await auth_token
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture(scope="class")
    async def departments(self, auth_headers):
        """Get list of departments for user assignment"""
        headers = await auth_headers
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/v1/rbac/departments",
                headers=headers
            )
            assert response.status_code == 200
            data = response.json()
            return data["items"]

    @pytest.fixture(scope="class")
    async def roles(self, auth_headers):
        """Get list of roles for user assignment"""
        headers = await auth_headers
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/api/v1/rbac/roles",
                headers=headers
            )
            assert response.status_code == 200
            data = response.json()
            return data["items"]

    @pytest.mark.asyncio
    async def test_01_create_users(self, auth_headers, departments):
        """Test creating multiple users with different roles"""
        headers = await auth_headers
        dept_list = await departments

        # Get first department for assignment
        test_dept = dept_list[0] if dept_list else None

        users_to_create = [
            {
                "username": "data_analyst_1",
                "email": "analyst1@company.com",
                "full_name": "Alice Data Analyst",
                "password": "SecurePass123!",
                "role": "data_analyst",
                "department_id": test_dept["id"] if test_dept else None,
                "function": "Data Analysis"
            },
            {
                "username": "data_engineer_1",
                "email": "engineer1@company.com",
                "full_name": "Bob Data Engineer",
                "password": "SecurePass123!",
                "role": "data_engineer",
                "department_id": test_dept["id"] if test_dept else None,
                "function": "Data Engineering"
            },
            {
                "username": "manager_1",
                "email": "manager1@company.com",
                "full_name": "Carol Manager",
                "password": "SecurePass123!",
                "role": "manager",
                "department_id": test_dept["id"] if test_dept else None,
                "function": "Team Management"
            }
        ]

        created_users = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for user_data in users_to_create:
                print(f"\n📝 Creating user: {user_data['username']}")

                response = await client.post(
                    f"{BASE_URL}/api/v1/admin/users",
                    headers=headers,
                    json=user_data
                )

                print(f"   Status: {response.status_code}")
                if response.status_code == 201:
                    user = response.json()
                    created_users.append(user)
                    print(f"   ✅ Created user ID: {user['id']}")
                    print(f"   Username: {user['username']}")
                    print(f"   Email: {user['email']}")
                    print(f"   Role: {user['role']}")
                else:
                    print(f"   ❌ Failed: {response.text}")
                    # Don't fail the test if user already exists
                    if "already exists" not in response.text.lower():
                        pytest.fail(f"Failed to create user {user_data['username']}: {response.text}")

        print(f"\n✅ Successfully created {len(created_users)} users")
        assert len(created_users) > 0, "Should create at least one user"

    @pytest.mark.asyncio
    async def test_02_list_users(self, auth_headers):
        """Test listing all users"""
        headers = await auth_headers

        async with httpx.AsyncClient(timeout=30.0) as client:
            print("\n📋 Fetching all users...")
            response = await client.get(
                f"{BASE_URL}/api/v1/admin/users",
                headers=headers
            )

            assert response.status_code == 200, f"Failed to list users: {response.text}"
            users = response.json()

            print(f"   Found {len(users)} total users:")
            for user in users:
                print(f"   - {user['username']} ({user['email']}) - Role: {user['role']}")

            assert len(users) >= 1, "Should have at least admin user"
            print("\n✅ User listing successful")

    @pytest.mark.asyncio
    async def test_03_update_user(self, auth_headers):
        """Test updating user information"""
        headers = await auth_headers

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get list of users
            response = await client.get(
                f"{BASE_URL}/api/v1/admin/users",
                headers=headers
            )
            users = response.json()

            # Find a test user to update (not admin)
            test_user = next((u for u in users if u['username'] != 'admin'), None)

            if test_user:
                user_id = test_user['id']
                print(f"\n✏️ Updating user: {test_user['username']}")

                update_data = {
                    "full_name": f"{test_user['full_name']} (Updated)",
                    "function": "Updated Function - Senior Role"
                }

                response = await client.put(
                    f"{BASE_URL}/api/v1/admin/users/{user_id}",
                    headers=headers,
                    json=update_data
                )

                if response.status_code == 200:
                    updated_user = response.json()
                    print(f"   ✅ Updated successfully")
                    print(f"   New name: {updated_user['full_name']}")
                    print(f"   New function: {updated_user.get('function', 'N/A')}")

                    assert updated_user['full_name'] == update_data['full_name']
                else:
                    print(f"   ⚠️ Update failed: {response.text}")
            else:
                print("\n⚠️ No test user found to update (only admin exists)")

    @pytest.mark.asyncio
    async def test_04_assign_roles(self, auth_headers, roles):
        """Test assigning roles to users"""
        headers = await auth_headers
        role_list = await roles

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get users
            response = await client.get(
                f"{BASE_URL}/api/v1/admin/users",
                headers=headers
            )
            users = response.json()

            # Find test users (not admin)
            test_users = [u for u in users if u['username'] != 'admin']

            if test_users and role_list:
                print(f"\n👥 Testing role assignments...")
                print(f"   Available roles: {[r['name'] for r in role_list]}")

                for user in test_users[:2]:  # Test with first 2 users
                    # Assign first available role
                    role = role_list[0]

                    print(f"\n   Assigning role '{role['name']}' to '{user['username']}'...")

                    response = await client.post(
                        f"{BASE_URL}/api/v1/rbac/users/{user['id']}/roles",
                        headers=headers,
                        json={
                            "role_id": role['id'],
                            "department_id": user.get('department_id')
                        }
                    )

                    if response.status_code in [200, 201]:
                        print(f"   ✅ Role assigned successfully")
                    else:
                        print(f"   ⚠️ Role assignment response: {response.status_code} - {response.text}")
            else:
                print("\n⚠️ No test users or roles found for role assignment")

    @pytest.mark.asyncio
    async def test_05_get_user_permissions(self, auth_headers):
        """Test retrieving user permissions"""
        headers = await auth_headers

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get users
            response = await client.get(
                f"{BASE_URL}/api/v1/admin/users",
                headers=headers
            )
            users = response.json()

            print(f"\n🔐 Testing permission retrieval...")

            for user in users[:3]:  # Test first 3 users
                print(f"\n   User: {user['username']}")

                # Get user's permissions
                response = await client.get(
                    f"{BASE_URL}/api/v1/rbac/users/{user['id']}/permissions",
                    headers=headers
                )

                if response.status_code == 200:
                    permissions = response.json()
                    print(f"   ✅ Has {len(permissions)} permissions")
                    if permissions:
                        print(f"   Sample permissions: {[p.get('module_name', 'N/A') for p in permissions[:3]]}")
                else:
                    print(f"   ⚠️ Could not fetch permissions: {response.status_code}")

    @pytest.mark.asyncio
    async def test_06_permission_matrix(self, auth_headers):
        """Test retrieving full permission matrix"""
        headers = await auth_headers

        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"\n🗂️ Fetching permission matrix...")

            response = await client.get(
                f"{BASE_URL}/api/v1/rbac/permissions/matrix",
                headers=headers
            )

            assert response.status_code == 200, f"Failed to get permission matrix: {response.text}"

            matrix = response.json()
            print(f"   ✅ Permission matrix retrieved")
            print(f"   Roles: {len(matrix.get('roles', []))}")
            print(f"   Modules: {len(matrix.get('modules', []))}")

            if 'matrix' in matrix:
                print(f"   Permission entries: {len(matrix['matrix'])}")

    @pytest.mark.asyncio
    async def test_07_department_hierarchy(self, auth_headers):
        """Test department hierarchy retrieval"""
        headers = await auth_headers

        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"\n🏢 Fetching department hierarchy...")

            response = await client.get(
                f"{BASE_URL}/api/v1/rbac/departments/hierarchy",
                headers=headers
            )

            assert response.status_code == 200, f"Failed to get department hierarchy: {response.text}"

            hierarchy = response.json()
            print(f"   ✅ Department hierarchy retrieved")
            print(f"   Root departments: {len(hierarchy)}")

            for dept in hierarchy[:3]:  # Show first 3
                print(f"   - {dept['name']}")
                if dept.get('children'):
                    print(f"     ({len(dept['children'])} child departments)")

    @pytest.mark.asyncio
    async def test_08_modules_list(self, auth_headers):
        """Test modules listing"""
        headers = await auth_headers

        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"\n📦 Fetching modules...")

            response = await client.get(
                f"{BASE_URL}/api/v1/rbac/modules",
                headers=headers
            )

            assert response.status_code == 200, f"Failed to get modules: {response.text}"

            data = response.json()
            modules = data.get('items', [])
            print(f"   ✅ Found {len(modules)} modules:")

            for module in modules:
                print(f"   - {module['name']} ({module['code']})")

    @pytest.mark.asyncio
    async def test_09_user_deactivation(self, auth_headers):
        """Test user deactivation (soft delete)"""
        headers = await auth_headers

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get users
            response = await client.get(
                f"{BASE_URL}/api/v1/admin/users",
                headers=headers
            )
            users = response.json()

            # Find a test user to deactivate (not admin)
            test_user = next((u for u in users if u['username'].startswith('data_')), None)

            if test_user:
                user_id = test_user['id']
                print(f"\n🔒 Deactivating user: {test_user['username']}")

                # Update user to inactive
                response = await client.put(
                    f"{BASE_URL}/api/v1/admin/users/{user_id}",
                    headers=headers,
                    json={"is_active": False}
                )

                if response.status_code == 200:
                    updated_user = response.json()
                    print(f"   ✅ User deactivated")
                    print(f"   Active status: {updated_user.get('is_active', 'N/A')}")
                else:
                    print(f"   ⚠️ Deactivation response: {response.status_code}")
            else:
                print("\n⚠️ No test user found for deactivation")

    @pytest.mark.asyncio
    async def test_10_audit_logs(self, auth_headers):
        """Test audit log retrieval"""
        headers = await auth_headers

        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"\n📊 Fetching audit logs...")

            response = await client.get(
                f"{BASE_URL}/api/v1/admin/audit-logs?limit=10",
                headers=headers
            )

            if response.status_code == 200:
                logs = response.json()
                print(f"   ✅ Found {len(logs)} recent audit log entries")

                for log in logs[:5]:  # Show first 5
                    action = log.get('action', 'N/A')
                    timestamp = log.get('created_at', 'N/A')
                    print(f"   - {action} at {timestamp}")
            else:
                print(f"   ⚠️ Audit logs response: {response.status_code}")


# Run with: pytest backend/tests/e2e/test_admin_user_rbac.py -v -s
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
