import { Settings } from 'lucide-react'
import POCConfigManager from './POCConfigManager'
import React, { useState } from 'react';
import axios from 'axios';

interface PartCode {
  code: string;
  description: string;
  extraction_method: string;
  confidence: number;
  page_number?: number;
}

interface ExtractionResults {
  part_codes: PartCode[];
  brand: string;
  file_type: string;
  total_codes: number;
  processing_time_ms: number;
}

export default function GtMotiveExtraction() {
  const [file, setFile] = useState<File | null>(null);
  const [showConfig, setShowConfig] = useState(false)
  const [brand, setBrand] = useState('generic');
  const [useVision, setUseVision] = useState(true);
  const [results, setResults] = useState<ExtractionResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('brand', brand);
    formData.append('use_vision', useVision.toString());

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/customer/gt_motive/extract',
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
      console.error('GT Motive extraction error:', err);
      setError(err.response?.data?.detail || 'Extraction failed. Please try again.');
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const downloadExcel = async () => {
    if (!results) return;

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/customer/gt_motive/export-excel',
        {
          part_codes: results.part_codes,
          brand: results.brand,
        },
        {
          responseType: 'blob',
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${brand}_part_codes_${Date.now()}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Excel export error:', err);
      setError('Excel export failed. Please try again.');
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-start justify-between mb-6">
            <div className="flex-1">
<div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          GT Motive - Automotive Part Code Extraction
        </h1>
        <p className="text-gray-600">
          Extract part codes from automotive catalogs using multi-modal AI (Text + Vision)
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
                moduleName="gt_motive"
                onClose={() => setShowConfig(false)}
              />
            </div>
          )}

      {/* Configuration Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Configuration</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Vehicle Brand:
            </label>
            <select
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              className="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="generic">Generic (All Brands)</option>
              <option value="bmw">BMW</option>
              <option value="mercedes">Mercedes-Benz</option>
              <option value="audi">Audi</option>
              <option value="vw">Volkswagen</option>
              <option value="toyota">Toyota</option>
              <option value="ford">Ford</option>
            </select>
          </div>

          <div className="flex items-center">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={useVision}
                onChange={(e) => setUseVision(e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-sm font-medium text-gray-700">
                Use Claude Vision for technical diagrams
              </span>
            </label>
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload Catalog (PDF or Image):
          </label>
          <input
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
          />
          {file && (
            <p className="mt-2 text-sm text-gray-600">
              Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
            </p>
          )}
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || loading}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
        >
          {loading ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Extracting Part Codes...
            </span>
          ) : (
            'Extract Part Codes'
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
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-800">
                Extracted Part Codes ({results.total_codes})
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Brand: {results.brand.toUpperCase()} | Processing Time: {results.processing_time_ms.toFixed(0)}ms
              </p>
            </div>
            <button
              onClick={downloadExcel}
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition flex items-center"
            >
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
              Export to Excel
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Part Code
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Method
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Confidence
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Page
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {results.part_codes.map((pc, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap font-mono text-sm text-gray-900">
                      {pc.code}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {pc.description || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        pc.extraction_method === 'table' ? 'bg-blue-100 text-blue-800' :
                        pc.extraction_method === 'regex' ? 'bg-green-100 text-green-800' :
                        pc.extraction_method === 'vision' ? 'bg-purple-100 text-purple-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {pc.extraction_method}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      <div className="flex items-center">
                        <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                          <div
                            className={`h-2 rounded-full ${
                              pc.confidence >= 0.9 ? 'bg-green-500' :
                              pc.confidence >= 0.75 ? 'bg-yellow-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${pc.confidence * 100}%` }}
                          ></div>
                        </div>
                        {(pc.confidence * 100).toFixed(1)}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {pc.page_number || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
