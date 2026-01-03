import { Settings } from 'lucide-react'
import POCConfigManager from './POCConfigManager'
import React, { useState } from 'react';
import axios from 'axios';

interface VehicleInfo {
  vin: string;
  make: string;
  model: string;
  year: string;
}

interface DamageAssessment {
  severity: 'minor' | 'moderate' | 'severe' | 'total_loss';
  affected_parts: string[];
  estimated_cost_range: string;
  description: string;
}

interface ClaimResults {
  vehicle_info: VehicleInfo;
  damage_assessment: DamageAssessment;
  ocr_confidence: number;
  ocr_engine_used: string;
  processing_time_ms: number;
  claim_id?: string;
}

export default function SoleraClaimsProcessing() {
  const [files, setFiles] = useState<File[]>([]);
  const [showConfig, setShowConfig] = useState(false)
  const [claimInfo, setClaimInfo] = useState({
    claimant_name: '',
    policy_number: '',
    incident_date: '',
  });
  const [results, setResults] = useState<ClaimResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleSubmit = async () => {
    if (files.length === 0) {
      setError('Please upload at least one vehicle photo');
      return;
    }

    if (!claimInfo.claimant_name || !claimInfo.policy_number) {
      setError('Please fill in all claim information');
      return;
    }

    setLoading(true);
    setError(null);
    const formData = new FormData();

    files.forEach((file, index) => {
      formData.append('files', file);
    });

    formData.append('claimant_name', claimInfo.claimant_name);
    formData.append('policy_number', claimInfo.policy_number);
    formData.append('incident_date', claimInfo.incident_date);

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/customer/solera/process-claim',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      setResults(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Solera claims processing error:', err);
      setError(err.response?.data?.detail || 'Claims processing failed. Please try again.');
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = async () => {
    if (!results?.claim_id) return;

    try {
      const response = await axios.get(
        `http://localhost:8000/api/v1/customer/solera/download-report/${results.claim_id}`,
        {
          responseType: 'blob',
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `claim_report_${results.claim_id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('PDF download error:', err);
      setError('PDF download failed. Please try again.');
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'minor': return 'bg-green-100 text-green-800 border-green-300';
      case 'moderate': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'severe': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'total_loss': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-start justify-between mb-6">
            <div className="flex-1">
<div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          Solera - Insurance Claims Processing
        </h1>
        <p className="text-gray-600">
          Automated VIN extraction and damage assessment using Multi-OCR + Vision AI
        </p>
      </div>
            </div>
            <button
              onClick={() => setShowConfig(!showConfig)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              <Settings className="w-4 h-4" />
              Configure
            </button>
          </div>

          {/* Configuration Panel */}
          {showConfig && (
            <div className="mb-6">
              <POCConfigManager
                moduleName="solera"
                onClose={() => setShowConfig(false)}
              />
            </div>
          )}

      {/* Claim Information Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Claim Information</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Claimant Name *
            </label>
            <input
              type="text"
              value={claimInfo.claimant_name}
              onChange={(e) => setClaimInfo({...claimInfo, claimant_name: e.target.value})}
              className="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="John Doe"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Policy Number *
            </label>
            <input
              type="text"
              value={claimInfo.policy_number}
              onChange={(e) => setClaimInfo({...claimInfo, policy_number: e.target.value})}
              className="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="POL-123456"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Incident Date
            </label>
            <input
              type="date"
              value={claimInfo.incident_date}
              onChange={(e) => setClaimInfo({...claimInfo, incident_date: e.target.value})}
              className="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload Vehicle Photos (VIN + Damage):
          </label>
          <input
            type="file"
            accept=".jpg,.jpeg,.png"
            multiple
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
          />
          {files.length > 0 && (
            <p className="mt-2 text-sm text-gray-600">
              {files.length} file(s) selected ({(files.reduce((sum, f) => sum + f.size, 0) / 1024).toFixed(1)} KB total)
            </p>
          )}
        </div>

        <button
          onClick={handleSubmit}
          disabled={files.length === 0 || loading}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
        >
          {loading ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing Claim...
            </span>
          ) : (
            'Process Claim'
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <svg className="h-5 w-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-sm font-medium text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Results Section */}
      {results && (
        <div className="space-y-6">
          {/* Vehicle Information */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Vehicle Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">VIN</p>
                <p className="text-lg font-mono font-semibold text-gray-900">{results.vehicle_info.vin}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Vehicle</p>
                <p className="text-lg font-semibold text-gray-900">
                  {results.vehicle_info.year} {results.vehicle_info.make} {results.vehicle_info.model}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">OCR Confidence</p>
                <div className="flex items-center mt-1">
                  <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                    <div
                      className={`h-2 rounded-full ${
                        results.ocr_confidence >= 0.9 ? 'bg-green-500' :
                        results.ocr_confidence >= 0.7 ? 'bg-yellow-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${results.ocr_confidence * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium">{(results.ocr_confidence * 100).toFixed(1)}%</span>
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-600">OCR Engine</p>
                <p className="text-lg font-medium text-gray-900">{results.ocr_engine_used}</p>
              </div>
            </div>
          </div>

          {/* Damage Assessment */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-800">Damage Assessment</h2>
              {results.claim_id && (
                <button
                  onClick={downloadPDF}
                  className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition flex items-center text-sm"
                >
                  <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  Download PDF Report
                </button>
              )}
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-600 mb-2">Severity Level</p>
                <span className={`px-4 py-2 rounded-full text-sm font-semibold border ${getSeverityColor(results.damage_assessment.severity)}`}>
                  {results.damage_assessment.severity.replace('_', ' ').toUpperCase()}
                </span>
              </div>

              <div>
                <p className="text-sm text-gray-600 mb-2">Estimated Cost</p>
                <p className="text-2xl font-bold text-gray-900">{results.damage_assessment.estimated_cost_range}</p>
              </div>

              <div>
                <p className="text-sm text-gray-600 mb-2">Affected Parts</p>
                <div className="flex flex-wrap gap-2">
                  {results.damage_assessment.affected_parts.map((part, idx) => (
                    <span key={idx} className="px-3 py-1 bg-gray-100 border border-gray-300 rounded-full text-sm text-gray-700">
                      {part}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-sm text-gray-600 mb-2">Description</p>
                <p className="text-gray-700 leading-relaxed">{results.damage_assessment.description}</p>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <p className="text-xs text-gray-500">
                  Processing Time: {results.processing_time_ms.toFixed(0)}ms
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
