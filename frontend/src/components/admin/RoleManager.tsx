/**
 * Role Manager Component
 *
 * Allows administrators to create, edit, and manage roles in the RBAC system.
 */

import React, { useState, useEffect } from 'react';
import {
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  Shield,
  Users,
  AlertTriangle,
} from 'lucide-react';

// Types
interface Role {
  id: string;
  name: string;
  description: string;
  parent_role_id: string | null;
  is_system_role: boolean;
  created_at: string;
  updated_at: string | null;
}

interface RoleFormData {
  name: string;
  description: string;
  parent_role_id: string | null;
  is_system_role: boolean;
}

const RoleManager: React.FC = () => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [formData, setFormData] = useState<RoleFormData>({
    name: '',
    description: '',
    parent_role_id: null,
    is_system_role: false,
  });

  // Fetch roles
  useEffect(() => {
    fetchRoles();
  }, []);

  const fetchRoles = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/v1/rbac/roles');

      if (!response.ok) {
        throw new Error(`Failed to fetch roles: ${response.statusText}`);
      }

      const data = await response.json();
      setRoles(data.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch roles');
      console.error('Error fetching roles:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setIsCreating(true);
    setEditingRole(null);
    setFormData({
      name: '',
      description: '',
      parent_role_id: null,
      is_system_role: false,
    });
  };

  const handleEdit = (role: Role) => {
    if (role.is_system_role) {
      alert('System roles cannot be edited');
      return;
    }
    setEditingRole(role);
    setIsCreating(false);
    setFormData({
      name: role.name,
      description: role.description,
      parent_role_id: role.parent_role_id,
      is_system_role: role.is_system_role,
    });
  };

  const handleCancel = () => {
    setIsCreating(false);
    setEditingRole(null);
    setFormData({
      name: '',
      description: '',
      parent_role_id: null,
      is_system_role: false,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      setError(null);

      if (editingRole) {
        // Update existing role
        const response = await fetch(`/api/v1/rbac/roles/${editingRole.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to update role');
        }
      } else {
        // Create new role
        const response = await fetch('/api/v1/rbac/roles', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to create role');
        }
      }

      // Refresh roles list
      await fetchRoles();
      handleCancel();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save role');
      console.error('Error saving role:', err);
    }
  };

  const handleDelete = async (role: Role) => {
    if (role.is_system_role) {
      alert('System roles cannot be deleted');
      return;
    }

    if (!confirm(`Are you sure you want to delete the role "${role.name}"?`)) {
      return;
    }

    try {
      setError(null);
      const response = await fetch(`/api/v1/rbac/roles/${role.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete role');
      }

      // Refresh roles list
      await fetchRoles();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete role');
      console.error('Error deleting role:', err);
    }
  };

  // Get role name by ID (for parent role display)
  const getRoleName = (roleId: string | null): string => {
    if (!roleId) return 'None';
    const role = roles.find((r) => r.id === roleId);
    return role ? role.name : 'Unknown';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Shield className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Role Management
          </h2>
        </div>
        <button
          onClick={handleCreate}
          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Create Role</span>
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="flex items-start space-x-3 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800 dark:text-red-200">
              Error
            </p>
            <p className="text-sm text-red-700 dark:text-red-300 mt-1">
              {error}
            </p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Create/Edit Form */}
      {(isCreating || editingRole) && (
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
            {editingRole ? 'Edit Role' : 'Create New Role'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Role Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="e.g., DataAnalyst"
                required
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Role description"
                rows={3}
              />
            </div>

            {/* Parent Role */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Parent Role (Optional)
              </label>
              <select
                value={formData.parent_role_id || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    parent_role_id: e.target.value || null,
                  })
                }
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="">None</option>
                {roles
                  .filter((r) => !editingRole || r.id !== editingRole.id)
                  .map((role) => (
                    <option key={role.id} value={role.id}>
                      {role.name}
                    </option>
                  ))}
              </select>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                For hierarchical role structures (optional)
              </p>
            </div>

            {/* System Role Checkbox (only for new roles) */}
            {!editingRole && (
              <div className="flex items-start space-x-3">
                <input
                  type="checkbox"
                  id="is_system_role"
                  checked={formData.is_system_role}
                  onChange={(e) =>
                    setFormData({ ...formData, is_system_role: e.target.checked })
                  }
                  className="mt-1 w-4 h-4 text-primary-600 focus:ring-primary-500 border-slate-300 dark:border-slate-600 rounded"
                />
                <div>
                  <label
                    htmlFor="is_system_role"
                    className="text-sm font-medium text-slate-700 dark:text-slate-300 cursor-pointer"
                  >
                    System Role
                  </label>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    System roles cannot be deleted or modified
                  </p>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-3 pt-4 border-t border-slate-200 dark:border-slate-700">
              <button
                type="submit"
                className="flex items-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
              >
                <Save className="w-4 h-4" />
                <span>{editingRole ? 'Update' : 'Create'}</span>
              </button>
              <button
                type="button"
                onClick={handleCancel}
                className="flex items-center space-x-2 px-4 py-2 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
                <span>Cancel</span>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Roles List */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
              Loading roles...
            </p>
          </div>
        ) : roles.length === 0 ? (
          <div className="p-8 text-center">
            <Shield className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
            <p className="text-slate-600 dark:text-slate-400">
              No roles found
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Parent Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                {roles.map((role) => (
                  <tr
                    key={role.id}
                    className="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        <Shield className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                        <span className="font-medium text-slate-900 dark:text-slate-100">
                          {role.name}
                        </span>
                        {role.is_system_role && (
                          <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded">
                            System
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">
                      {role.description || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">
                      {getRoleName(role.parent_role_id)}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">
                      {role.is_system_role ? 'System' : 'Custom'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleEdit(role)}
                          disabled={role.is_system_role}
                          className={`p-2 rounded-lg transition-colors ${
                            role.is_system_role
                              ? 'text-slate-300 dark:text-slate-600 cursor-not-allowed'
                              : 'text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20'
                          }`}
                          title={
                            role.is_system_role
                              ? 'System roles cannot be edited'
                              : 'Edit role'
                          }
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(role)}
                          disabled={role.is_system_role}
                          className={`p-2 rounded-lg transition-colors ${
                            role.is_system_role
                              ? 'text-slate-300 dark:text-slate-600 cursor-not-allowed'
                              : 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                          }`}
                          title={
                            role.is_system_role
                              ? 'System roles cannot be deleted'
                              : 'Delete role'
                          }
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
              <Shield className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Total Roles
              </p>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {roles.length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                System Roles
              </p>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {roles.filter((r) => r.is_system_role).length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-secondary-100 dark:bg-secondary-900/30 rounded-lg">
              <Users className="w-5 h-5 text-secondary-600 dark:text-secondary-400" />
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Custom Roles
              </p>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {roles.filter((r) => !r.is_system_role).length}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoleManager;
