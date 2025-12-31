import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { Upload, CheckCircle, XCircle, Loader2 } from 'lucide-react';

interface AgentWorkspaceFileUploadProps {
  sessionId: string;
  projectId?: string;
  currentUser?: {
    id: string;
    username: string;
    role: string;
    department?: string;
    team?: string;
  };
  onUploadComplete?: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const AgentWorkspaceFileUpload: React.FC<AgentWorkspaceFileUploadProps> = ({
  sessionId,
  projectId,
  currentUser,
  onUploadComplete
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setUploading(true);
    setUploadStatus('idle');
    setMessage('');

    for (const file of acceptedFiles) {
      try {
        const formData = new FormData();
        formData.append('file', file);

        // Add project context
        if (projectId) {
          formData.append('project_id', projectId);
        }

        // Add organizational context
        formData.append('role', currentUser?.role || 'user');
        formData.append('department', currentUser?.department || 'default');
        formData.append('team', currentUser?.team || 'default-team');
        formData.append('username', currentUser?.username || 'anonymous');
        formData.append('project_name', 'agent-workspace'); // Could be dynamic

        console.log('📤 Uploading to agent workspace:', file.name);

        const response = await axios.post(
          `${API_URL}/api/v1/agent/upload-workspace-file`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
              if (progressEvent.total) {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                setUploadProgress(percentCompleted);
              }
            }
          }
        );

        console.log('✅ File uploaded:', response.data);
        setUploadStatus('success');
        setMessage(`✅ ${file.name} uploaded to agent workspace!`);

        // Notify parent component
        if (onUploadComplete) {
          onUploadComplete();
        }

      } catch (error: any) {
        console.error('❌ Upload error:', error);
        setUploadStatus('error');
        setMessage(`❌ Failed to upload ${file.name}: ${error.response?.data?.detail || error.message}`);
      }
    }

    setUploading(false);
    setUploadProgress(0);

    // Clear message after 5 seconds
    setTimeout(() => {
      setUploadStatus('idle');
      setMessage('');
    }, 5000);

  }, [projectId, currentUser, onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled: uploading,
    multiple: true
  });

  return (
    <div className="space-y-2">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-3 text-center transition-colors cursor-pointer ${
          isDragActive
            ? 'border-[#6b9080] dark:border-[#85c4a6] bg-[#f0f7f4] dark:bg-[#2b3d37]'
            : 'border-slate-300 dark:border-slate-600 hover:border-[#6b9080] dark:hover:border-[#85c4a6]'
        } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-1">
          {uploading ? (
            <>
              <Loader2 className="w-6 h-6 text-[#6b9080] dark:text-[#85c4a6] animate-spin" />
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Uploading... {uploadProgress}%
              </p>
            </>
          ) : (
            <>
              <Upload className="w-6 h-6 text-slate-400" />
              <p className="text-xs text-slate-600 dark:text-slate-400">
                {isDragActive ? 'Drop files here' : 'Drag & drop or click to upload'}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-500">
                Files will be available in /workspace/
              </p>
            </>
          )}
        </div>
      </div>

      {/* Status Message */}
      {uploadStatus !== 'idle' && message && (
        <div
          className={`flex items-center gap-2 p-2 rounded text-xs ${
            uploadStatus === 'success'
              ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800'
              : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800'
          }`}
        >
          {uploadStatus === 'success' ? (
            <CheckCircle className="w-4 h-4 flex-shrink-0" />
          ) : (
            <XCircle className="w-4 h-4 flex-shrink-0" />
          )}
          <span className="flex-1">{message}</span>
        </div>
      )}
    </div>
  );
};

export default AgentWorkspaceFileUpload;
