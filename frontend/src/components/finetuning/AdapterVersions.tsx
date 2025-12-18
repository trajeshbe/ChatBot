import React from 'react';
import { GitBranch } from 'lucide-react';

export default function AdapterVersions({ userRole }: { userRole: string }) {
  return (
    <div className="p-6">
      <div className="flex items-center gap-2 mb-4">
        <GitBranch className="w-6 h-6 text-indigo-600" />
        <h2 className="text-2xl font-bold">Adapters & Versions</h2>
      </div>
      <p className="text-gray-600">Adapter versioning with Git-like diff coming soon...</p>
    </div>
  );
}
