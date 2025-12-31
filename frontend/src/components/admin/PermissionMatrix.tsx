/**
 * Permission Matrix Component
 *
 * Visual grid showing all role-module permissions with interactive editing.
 * Allows bulk permission updates across roles and modules.
 */

import React, { useState, useEffect } from 'react';
import {
  Grid,
  Check,
  X,
  Save,
  AlertTriangle,
  Eye,
  Edit,
  Trash2,
  Share2,
  RefreshCw,
} from 'lucide-react';

// Types
interface Module {
  id: string;
  name: string;
  code: string;
  description: string;
  icon: string;
  route: string;
  display_order: number;
  is_active: boolean;
}

interface Role {
  id: string;
  name: string;
  description: string;
  is_system_role: boolean;
}

interface Permission {
  can_read: boolean;
  can_write: boolean;
  can_delete: boolean;
  can_share: boolean;
}

interface PermissionMatrixRow {
  role_id: string;
  role_name: string;
  permissions: Record<string, Permission>;
}

interface PermissionMatrixData {
  roles: PermissionMatrixRow[];
  modules: Module[];
}

const PermissionMatrix: React.FC = () => {
  const [matrix, setMatrix] = useState<PermissionMatrixData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [changedPermissions, setChangedPermissions] = useState<Set<string>>(new Set());

  // Fetch permission matrix
  useEffect(() => {
    fetchMatrix();
  }, []);

  const fetchMatrix = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/v1/rbac/permissions/matrix');

      if (!response.ok) {
        throw new Error(`Failed to fetch permission matrix: ${response.statusText}`);
      }

      const data = await response.json();
      setMatrix(data);
      setChangedPermissions(new Set());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch permission matrix');
      console.error('Error fetching permission matrix:', err);
    } finally {
      setLoading(false);
    }
  };

  const togglePermission = (
    roleId: string,
    moduleCode: string,
    permissionType: 'can_read' | 'can_write' | 'can_delete' | 'can_share'
  ) => {
    if (!matrix) return;

    const roleRow = matrix.roles.find((r) => r.role_id === roleId);
    if (!roleRow) return;

    // Check if system role
    const role = matrix.roles.find((r) => r.role_id === roleId);
    // Note: We need role details to check is_system_role, for now allow all edits

    // Toggle the permission
    const currentPerm = roleRow.permissions[moduleCode];
    const newPerm = {
      ...currentPerm,
      [permissionType]: !currentPerm[permissionType],
    };

    // Update matrix
    const updatedMatrix = {
      ...matrix,
      roles: matrix.roles.map((r) =>
        r.role_id === roleId
          ? {
              ...r,
              permissions: {
                ...r.permissions,
                [moduleCode]: newPerm,
              },
            }
          : r
      ),
    };

    setMatrix(updatedMatrix);

    // Mark as changed
    const changeKey = `${roleId}:${moduleCode}`;
    setChangedPermissions(new Set(changedPermissions).add(changeKey));
  };

  const savePermissions = async () => {
    if (!matrix || changedPermissions.size === 0) return;

    try {
      setSaving(true);
      setError(null);

      // Group changes by role
      const changesByRole = new Map<string, Record<string, Permission>>();

      changedPermissions.forEach((changeKey) => {
        const [roleId, moduleCode] = changeKey.split(':');
        const roleRow = matrix.roles.find((r) => r.role_id === roleId);
        if (!roleRow) return;

        if (!changesByRole.has(roleId)) {
          changesByRole.set(roleId, {});
        }

        changesByRole.get(roleId)![moduleCode] = roleRow.permissions[moduleCode];
      });

      // Save each role's permissions
      for (const [roleId, permissions] of changesByRole.entries()) {
        const response = await fetch('/api/v1/rbac/permissions/bulk-update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            role_id: roleId,
            permissions: permissions,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to save permissions');
        }
      }

      // Clear changed set and refresh
      setChangedPermissions(new Set());
      await fetchMatrix();

      alert('Permissions saved successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save permissions');
      console.error('Error saving permissions:', err);
    } finally {
      setSaving(false);
    }
  };

  const hasChanges = changedPermissions.size > 0;

  // Permission icon component
  const PermissionIcon: React.FC<{ type: string }> = ({ type }) => {
    const iconClass = 'w-3 h-3';
    switch (type) {
      case 'can_read':
        return <Eye className={iconClass} />;
      case 'can_write':
        return <Edit className={iconClass} />;
      case 'can_delete':
        return <Trash2 className={iconClass} />;
      case 'can_share':
        return <Share2 className={iconClass} />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Loading permission matrix...
          </p>
        </div>
      </div>
    );
  }

  if (!matrix) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
        <p className="text-slate-600 dark:text-slate-400">
          Failed to load permission matrix
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Grid className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          <div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              Permission Matrix
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              {matrix.roles.length} roles × {matrix.modules.length} modules ={' '}
              {matrix.roles.length * matrix.modules.length} permissions
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchMatrix}
            disabled={saving}
            className="flex items-center space-x-2 px-4 py-2 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${saving ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          {hasChanges && (
            <button
              onClick={savePermissions}
              disabled={saving}
              className="flex items-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>
                {saving ? 'Saving...' : `Save ${changedPermissions.size} Changes`}
              </span>
            </button>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="flex items-start space-x-3 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800 dark:text-red-200">
              Error
            </p>
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

      {/* Legend */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">
          Permission Types
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded">
              <Eye className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                Read
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                View/access
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded">
              <Edit className="w-4 h-4 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                Write
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Create/edit
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded">
              <Trash2 className="w-4 h-4 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                Delete
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Remove</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded">
              <Share2 className="w-4 h-4 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                Share
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">Export</p>
            </div>
          </div>
        </div>
      </div>

      {/* Permission Matrix Table */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 dark:bg-slate-900/50 sticky top-0 z-10">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider border-r border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 sticky left-0 z-20">
                  Role / Module
                </th>
                {matrix.modules
                  .sort((a, b) => a.display_order - b.display_order)
                  .map((module) => (
                    <th
                      key={module.id}
                      className="px-3 py-3 text-center text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider border-l border-slate-200 dark:border-slate-700"
                    >
                      <div className="flex flex-col items-center space-y-1">
                        <span className="font-semibold">{module.name}</span>
                        <span className="text-xs text-slate-400 dark:text-slate-500 font-mono">
                          {module.code}
                        </span>
                      </div>
                    </th>
                  ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
              {matrix.roles.map((roleRow) => (
                <tr
                  key={roleRow.role_id}
                  className="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors"
                >
                  {/* Role Name (Sticky Column) */}
                  <td className="px-4 py-3 border-r border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 sticky left-0 z-10">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium text-slate-900 dark:text-slate-100">
                        {roleRow.role_name}
                      </span>
                    </div>
                  </td>

                  {/* Permission Cells */}
                  {matrix.modules
                    .sort((a, b) => a.display_order - b.display_order)
                    .map((module) => {
                      const perm = roleRow.permissions[module.code] || {
                        can_read: false,
                        can_write: false,
                        can_delete: false,
                        can_share: false,
                      };

                      return (
                        <td
                          key={module.id}
                          className="px-2 py-2 border-l border-slate-200 dark:border-slate-700"
                        >
                          <div className="grid grid-cols-2 gap-1">
                            {/* Read */}
                            <button
                              onClick={() =>
                                togglePermission(
                                  roleRow.role_id,
                                  module.code,
                                  'can_read'
                                )
                              }
                              className={`p-1.5 rounded transition-colors ${
                                perm.can_read
                                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                                  : 'bg-slate-100 dark:bg-slate-700 text-slate-400 dark:text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-600'
                              }`}
                              title="Read permission"
                            >
                              <Eye className="w-3 h-3 mx-auto" />
                            </button>

                            {/* Write */}
                            <button
                              onClick={() =>
                                togglePermission(
                                  roleRow.role_id,
                                  module.code,
                                  'can_write'
                                )
                              }
                              className={`p-1.5 rounded transition-colors ${
                                perm.can_write
                                  ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                                  : 'bg-slate-100 dark:bg-slate-700 text-slate-400 dark:text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-600'
                              }`}
                              title="Write permission"
                            >
                              <Edit className="w-3 h-3 mx-auto" />
                            </button>

                            {/* Delete */}
                            <button
                              onClick={() =>
                                togglePermission(
                                  roleRow.role_id,
                                  module.code,
                                  'can_delete'
                                )
                              }
                              className={`p-1.5 rounded transition-colors ${
                                perm.can_delete
                                  ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
                                  : 'bg-slate-100 dark:bg-slate-700 text-slate-400 dark:text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-600'
                              }`}
                              title="Delete permission"
                            >
                              <Trash2 className="w-3 h-3 mx-auto" />
                            </button>

                            {/* Share */}
                            <button
                              onClick={() =>
                                togglePermission(
                                  roleRow.role_id,
                                  module.code,
                                  'can_share'
                                )
                              }
                              className={`p-1.5 rounded transition-colors ${
                                perm.can_share
                                  ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400'
                                  : 'bg-slate-100 dark:bg-slate-700 text-slate-400 dark:text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-600'
                              }`}
                              title="Share permission"
                            >
                              <Share2 className="w-3 h-3 mx-auto" />
                            </button>
                          </div>
                        </td>
                      );
                    })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Grid className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Total Permissions
              </p>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {matrix.roles.length * matrix.modules.length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
              <Grid className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Roles</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {matrix.roles.length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-secondary-100 dark:bg-secondary-900/30 rounded-lg">
              <Grid className="w-5 h-5 text-secondary-600 dark:text-secondary-400" />
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Modules</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {matrix.modules.length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Unsaved Changes
              </p>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                {changedPermissions.size}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PermissionMatrix;
