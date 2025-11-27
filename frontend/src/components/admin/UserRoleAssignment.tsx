import React, { useState, useEffect } from 'react';
import { Users, Shield, Plus, X, Search, Check, AlertCircle, Loader2, UserPlus, UserMinus } from 'lucide-react';

interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
}

interface Role {
  id: string;
  name: string;
  description: string;
  is_system_role: boolean;
}

interface Department {
  id: string;
  name: string;
  code: string;
  parent_id: string | null;
}

interface UserRole {
  id: string;
  user_id: string;
  role_id: string;
  role_name: string;
  department_id: string | null;
  department_name: string | null;
  assigned_by: string | null;
  assigned_at: string;
  expires_at: string | null;
  is_active?: boolean;
}

interface AssignRoleFormData {
  user_id: string;
  role_id: string;
  department_id: string | null;
  expires_at: string | null;
}

export const UserRoleAssignment: React.FC = () => {
  // State
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userRoles, setUserRoles] = useState<UserRole[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAssignForm, setShowAssignForm] = useState(false);
  const [assignFormData, setAssignFormData] = useState<AssignRoleFormData>({
    user_id: '',
    role_id: '',
    department_id: null,
    expires_at: null,
  });

  // Fetch users, roles, and departments on mount
  useEffect(() => {
    fetchUsers();
    fetchRoles();
    fetchDepartments();
  }, []);

  // Fetch user roles when a user is selected
  useEffect(() => {
    if (selectedUser) {
      fetchUserRoles(selectedUser.id);
    }
  }, [selectedUser]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/v1/admin/users');
      if (!response.ok) {
        throw new Error(`Failed to fetch users: ${response.statusText}`);
      }
      const data = await response.json();
      // API returns array directly, not wrapped in {users: [...]}
      setUsers(Array.isArray(data) ? data : (data.users || []));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const fetchRoles = async () => {
    try {
      const response = await fetch('/api/v1/rbac/roles');
      if (!response.ok) {
        throw new Error(`Failed to fetch roles: ${response.statusText}`);
      }
      const data = await response.json();
      setRoles(data.items || []);
    } catch (err) {
      console.error('Failed to fetch roles:', err);
    }
  };

  const fetchDepartments = async () => {
    try {
      const response = await fetch('/api/v1/rbac/departments');
      if (!response.ok) {
        throw new Error(`Failed to fetch departments: ${response.statusText}`);
      }
      const data = await response.json();
      setDepartments(data.items || []);
    } catch (err) {
      console.error('Failed to fetch departments:', err);
    }
  };

  const fetchUserRoles = async (userId: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`/api/v1/rbac/user-roles/${userId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch user roles: ${response.statusText}`);
      }
      const data = await response.json();
      // API returns array directly
      setUserRoles(Array.isArray(data) ? data : (data.roles || []));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch user roles');
    } finally {
      setLoading(false);
    }
  };

  const handleAssignRole = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;

    try {
      setError(null);
      const requestData = {
        user_id: selectedUser.id,
        role_id: assignFormData.role_id,
        department_id: assignFormData.department_id || null,
        expires_at: assignFormData.expires_at || null,
      };

      const response = await fetch('/api/v1/rbac/user-roles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to assign role');
      }

      // Refresh the user's roles list
      await fetchUserRoles(selectedUser.id);

      // Close the form and reset
      setShowAssignForm(false);
      setAssignFormData({
        user_id: '',
        role_id: '',
        department_id: null,
        expires_at: null,
      });

      // Show success message (optional - can be removed if annoying)
      alert('Role assigned successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to assign role');
    }
  };

  const handleRevokeRole = async (userRoleId: string) => {
    if (!selectedUser) return;
    if (!confirm('Are you sure you want to revoke this role?')) return;

    try {
      setError(null);

      const response = await fetch(`/api/v1/rbac/user-role-assignment/${userRoleId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to revoke role');
      }

      await fetchUserRoles(selectedUser.id);
      alert('Role revoked successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to revoke role');
    }
  };

  const handleSelectUser = (user: User) => {
    setSelectedUser(user);
    setShowAssignForm(false);
    setError(null);
  };

  const handleStartAssignRole = () => {
    setShowAssignForm(true);
    setError(null);
    setAssignFormData({
      user_id: selectedUser?.id || '',
      role_id: '',
      department_id: null,
      expires_at: null,
    });
  };

  const handleCancelAssign = () => {
    setShowAssignForm(false);
    setAssignFormData({
      user_id: '',
      role_id: '',
      department_id: null,
      expires_at: null,
    });
  };

  // Filter users based on search query
  const filteredUsers = users.filter((user) =>
    user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (user.full_name && user.full_name.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  // Check if a role is already assigned
  const isRoleAssigned = (roleId: string) => {
    return userRoles.some((ur) => ur.role_id === roleId);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">User Role Assignment</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Assign and manage user roles for access control
          </p>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800 dark:text-red-200">Error</p>
            <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Content: Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: User List */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
            {/* Search Bar */}
            <div className="p-4 border-b border-slate-200 dark:border-slate-700">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search users..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>

            {/* User List */}
            <div className="divide-y divide-slate-200 dark:divide-slate-700 max-h-[600px] overflow-y-auto">
              {loading && !selectedUser ? (
                <div className="p-8 text-center">
                  <Loader2 className="w-8 h-8 text-primary-500 animate-spin mx-auto" />
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">Loading users...</p>
                </div>
              ) : filteredUsers.length === 0 ? (
                <div className="p-8 text-center">
                  <Users className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto" />
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">No users found</p>
                </div>
              ) : (
                filteredUsers.map((user) => (
                  <button
                    key={user.id}
                    onClick={() => handleSelectUser(user)}
                    className={`w-full p-4 text-left hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors ${
                      selectedUser?.id === user.id ? 'bg-primary-50 dark:bg-primary-900/20' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                          {user.username}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                          {user.email}
                        </p>
                      </div>
                      {selectedUser?.id === user.id && (
                        <Check className="w-4 h-4 text-primary-600 dark:text-primary-400 flex-shrink-0 ml-2" />
                      )}
                    </div>
                    {!user.is_active && (
                      <span className="inline-block mt-2 text-xs px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded">
                        Inactive
                      </span>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: User Roles */}
        <div className="lg:col-span-2">
          {selectedUser ? (
            <div className="space-y-6">
              {/* User Info Header */}
              <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                      {selectedUser.username}
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                      {selectedUser.email}
                    </p>
                  </div>
                  <button
                    onClick={handleStartAssignRole}
                    disabled={showAssignForm}
                    className="flex items-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <UserPlus className="w-4 h-4" />
                    <span>Assign Role</span>
                  </button>
                </div>
              </div>

              {/* Assign Role Form */}
              {showAssignForm && (
                <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-primary-200 dark:border-primary-700 p-6">
                  <h4 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                    Assign New Role
                  </h4>
                  <form onSubmit={handleAssignRole} className="space-y-4">
                    {/* Role Selection */}
                    <div>
                      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Role <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={assignFormData.role_id}
                        onChange={(e) => setAssignFormData({ ...assignFormData, role_id: e.target.value })}
                        className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                        required
                      >
                        <option value="">Select a role</option>
                        {roles.map((role) => (
                          <option
                            key={role.id}
                            value={role.id}
                            disabled={isRoleAssigned(role.id)}
                          >
                            {role.name} {isRoleAssigned(role.id) ? '(Already assigned)' : ''}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Department Selection (Optional) */}
                    <div>
                      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Department (Optional)
                      </label>
                      <select
                        value={assignFormData.department_id || ''}
                        onChange={(e) =>
                          setAssignFormData({
                            ...assignFormData,
                            department_id: e.target.value || null,
                          })
                        }
                        className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="">All departments</option>
                        {departments.map((dept) => (
                          <option key={dept.id} value={dept.id}>
                            {dept.name}
                          </option>
                        ))}
                      </select>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        Leave empty for global role assignment
                      </p>
                    </div>

                    {/* Expiration Date (Optional) */}
                    <div>
                      <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Expiration Date (Optional)
                      </label>
                      <input
                        type="datetime-local"
                        value={assignFormData.expires_at || ''}
                        onChange={(e) =>
                          setAssignFormData({ ...assignFormData, expires_at: e.target.value || null })
                        }
                        className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        Leave empty for permanent role assignment
                      </p>
                    </div>

                    {/* Form Actions */}
                    <div className="flex justify-end space-x-3 pt-4">
                      <button
                        type="button"
                        onClick={handleCancelAssign}
                        className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-4 py-2 bg-primary-600 hover:bg-primary-700 dark:bg-primary-500 dark:hover:bg-primary-600 text-white rounded-lg transition-colors"
                      >
                        Assign Role
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {/* Current Roles */}
              <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
                <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
                  <h4 className="text-lg font-semibold text-slate-900 dark:text-white">
                    Current Roles ({userRoles.length})
                  </h4>
                </div>
                <div className="p-6">
                  {loading ? (
                    <div className="py-8 text-center">
                      <Loader2 className="w-8 h-8 text-primary-500 animate-spin mx-auto" />
                      <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">Loading roles...</p>
                    </div>
                  ) : userRoles.length === 0 ? (
                    <div className="py-8 text-center">
                      <Shield className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto" />
                      <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
                        No roles assigned to this user
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {userRoles.map((userRole) => (
                        <div
                          key={userRole.id}
                          className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700"
                        >
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <Shield className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                              <h5 className="text-sm font-semibold text-slate-900 dark:text-white">
                                {userRole.role_name}
                              </h5>
                            </div>
                            <div className="mt-2 space-y-1">
                              {userRole.department_name && (
                                <p className="text-xs text-slate-600 dark:text-slate-400">
                                  <span className="font-medium">Department:</span> {userRole.department_name}
                                </p>
                              )}
                              <p className="text-xs text-slate-600 dark:text-slate-400">
                                <span className="font-medium">Granted:</span>{' '}
                                {new Date(userRole.assigned_at).toLocaleDateString()}
                              </p>
                              {userRole.expires_at && (
                                <p className="text-xs text-slate-600 dark:text-slate-400">
                                  <span className="font-medium">Expires:</span>{' '}
                                  {new Date(userRole.expires_at).toLocaleDateString()}
                                </p>
                              )}
                            </div>
                          </div>
                          <button
                            onClick={() => handleRevokeRole(userRole.id)}
                            className="ml-4 p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                            title="Revoke role"
                          >
                            <UserMinus className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-12 text-center">
              <Users className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto" />
              <p className="text-slate-600 dark:text-slate-400 mt-4">
                Select a user from the list to manage their roles
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserRoleAssignment;
