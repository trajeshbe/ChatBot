import React, { useState, useEffect } from 'react';
import {
  Cpu, HardDrive, DollarSign, CheckCircle, XCircle,
  AlertTriangle, Info, Search, Filter, ChevronDown,
  Zap, Clock, Shield, ExternalLink
} from 'lucide-react';

/**
 * ModelCatalog - Base Model Selection with Cost & VRAM Estimation
 *
 * Features:
 * - Model family browsing (LLaMA, Qwen, Mistral, GPT-style)
 * - Real-time cost & VRAM estimation
 * - Training compatibility indicators (Full FT / LoRA / QLoRA)
 * - Context length and license info
 * - Recommendations based on data size
 */

interface BaseModel {
  id: string;
  name: string;
  family: string;
  size: string; // e.g., "7B", "13B", "70B"
  contextLength: number;
  license: string;
  compatibility: {
    fullFineTune: boolean;
    lora: boolean;
    qlora: boolean;
  };
  vramRequirements: {
    fullFT: number;
    lora: number;
    qlora: number;
  };
  trainingCost: {
    fullFT: number; // $/hour
    lora: number;
    qlora: number;
  };
  recommended: boolean;
  tags: string[];
}

interface ModelCatalogProps {
  userRole: string;
  onSelectModel?: (model: BaseModel) => void;
}

export default function ModelCatalog({ userRole, onSelectModel }: ModelCatalogProps) {
  const [models, setModels] = useState<BaseModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFamily, setSelectedFamily] = useState<string>('all');
  const [selectedModel, setSelectedModel] = useState<BaseModel | null>(null);
  const [trainingMethod, setTrainingMethod] = useState<'fullFT' | 'lora' | 'qlora'>('qlora');
  const [datasetSize, setDatasetSize] = useState<number>(1000); // Number of samples

  // Fetch models from backend
  useEffect(() => {
    const fetchModels = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('access_token');
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

        const response = await fetch(`${apiUrl}/api/v1/finetuning/base-models`, {
          headers
        });

        if (response.ok) {
          const data = await response.json();
          setModels(data.models || []);
        }
      } catch (error) {
        console.error('Error fetching models:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchModels();
  }, []);

  // Filter models
  const filteredModels = models.filter(model => {
    const matchesSearch = model.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         model.family.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFamily = selectedFamily === 'all' || model.family === selectedFamily;
    return matchesSearch && matchesFamily;
  });

  // Get unique families for filter
  const families = ['all', ...Array.from(new Set(models.map(m => m.family)))];

  // Calculate estimated training time based on dataset size
  const estimateTrainingTime = (model: BaseModel): string => {
    // Rough heuristic: samples per hour based on model size and method
    const samplesPerHour: { [key: string]: number } = {
      '7B': trainingMethod === 'qlora' ? 1000 : trainingMethod === 'lora' ? 800 : 400,
      '13B': trainingMethod === 'qlora' ? 600 : trainingMethod === 'lora' ? 400 : 200,
      '70B': trainingMethod === 'qlora' ? 150 : trainingMethod === 'lora' ? 100 : 50,
    };

    const rate = samplesPerHour[model.size] || 500;
    const hours = Math.ceil(datasetSize / rate);

    if (hours < 1) return '< 1 hour';
    if (hours === 1) return '~1 hour';
    if (hours < 24) return `~${hours} hours`;
    const days = Math.ceil(hours / 24);
    return `~${days} day${days > 1 ? 's' : ''}`;
  };

  // Calculate estimated cost
  const estimateCost = (model: BaseModel): number => {
    const costPerHour = model.trainingCost[trainingMethod];
    const time = estimateTrainingTime(model);
    const hours = time.includes('day')
      ? parseInt(time.match(/\d+/)?.[0] || '1') * 24
      : parseInt(time.match(/\d+/)?.[0] || '1');
    return costPerHour * hours;
  };

  // Get recommendation for model
  const getRecommendation = (model: BaseModel): { show: boolean; message: string; type: 'success' | 'warning' | 'info' } => {
    if (datasetSize < 100) {
      return { show: true, message: 'Dataset too small for fine-tuning', type: 'warning' };
    }

    if (datasetSize < 1000 && model.size === '70B') {
      return { show: true, message: 'Model may be overkill for dataset size', type: 'warning' };
    }

    if (datasetSize > 100000 && model.size === '7B') {
      return { show: true, message: 'Consider a larger model for this dataset', type: 'info' };
    }

    if (model.recommended) {
      return { show: true, message: 'Recommended for your data size', type: 'success' };
    }

    return { show: false, message: '', type: 'info' };
  };

  return (
    <div className="p-6 space-y-6">
      {/* Search and Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search models..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        <div className="flex gap-3">
          <select
            value={selectedFamily}
            onChange={(e) => setSelectedFamily(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            {families.map(family => (
              <option key={family} value={family}>
                {family === 'all' ? 'All Families' : family}
              </option>
            ))}
          </select>

          <div className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800">
            <Filter className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              {filteredModels.length} models
            </span>
          </div>
        </div>
      </div>

      {/* Training Method & Dataset Size Inputs */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
          Cost Estimation Parameters
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Training Method
            </label>
            <div className="flex gap-2">
              {(['qlora', 'lora', 'fullFT'] as const).map(method => (
                <button
                  key={method}
                  onClick={() => setTrainingMethod(method)}
                  className={`
                    flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all
                    ${trainingMethod === method
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                    }
                  `}
                >
                  {method === 'qlora' ? 'QLoRA' : method === 'lora' ? 'LoRA' : 'Full FT'}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Dataset Size: {datasetSize.toLocaleString()} samples
            </label>
            <input
              type="range"
              min="100"
              max="100000"
              step="100"
              value={datasetSize}
              onChange={(e) => setDatasetSize(parseInt(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>100</span>
              <span>50K</span>
              <span>100K</span>
            </div>
          </div>
        </div>
      </div>

      {/* Model Grid */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredModels.map(model => {
            const recommendation = getRecommendation(model);
            const estimatedCost = estimateCost(model);
            const estimatedTime = estimateTrainingTime(model);
            const vramReq = model.vramRequirements[trainingMethod];

            return (
              <div
                key={model.id}
                className={`
                  relative bg-white dark:bg-gray-800 rounded-lg border-2 p-5
                  transition-all duration-200 cursor-pointer
                  ${selectedModel?.id === model.id
                    ? 'border-indigo-600 dark:border-indigo-500 shadow-lg'
                    : 'border-gray-200 dark:border-gray-700 hover:border-indigo-400 dark:hover:border-indigo-600'
                  }
                `}
                onClick={() => {
                  setSelectedModel(model);
                  onSelectModel?.(model);
                }}
              >
                {/* Recommendation Badge */}
                {recommendation.show && (
                  <div className={`
                    absolute -top-2 -right-2 px-2 py-1 rounded-full text-xs font-semibold flex items-center gap-1
                    ${recommendation.type === 'success' ? 'bg-green-500 text-white' :
                      recommendation.type === 'warning' ? 'bg-orange-500 text-white' :
                      'bg-blue-500 text-white'}
                  `}>
                    {recommendation.type === 'success' && <Zap className="w-3 h-3" />}
                    {recommendation.type === 'warning' && <AlertTriangle className="w-3 h-3" />}
                    {recommendation.type === 'info' && <Info className="w-3 h-3" />}
                    {recommendation.message}
                  </div>
                )}

                {/* Model Header */}
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                      {model.name}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded">
                        {model.family}
                      </span>
                      <span className="text-xs px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded font-semibold">
                        {model.size}
                      </span>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-xs text-gray-500 dark:text-gray-400">Context</div>
                    <div className="text-sm font-semibold text-gray-900 dark:text-white">
                      {(model.contextLength / 1000).toFixed(0)}K
                    </div>
                  </div>
                </div>

                {/* Training Compatibility */}
                <div className="grid grid-cols-3 gap-2 mb-3">
                  {[
                    { key: 'fullFineTune', label: 'Full FT', enabled: model.compatibility.fullFineTune },
                    { key: 'lora', label: 'LoRA', enabled: model.compatibility.lora },
                    { key: 'qlora', label: 'QLoRA', enabled: model.compatibility.qlora },
                  ].map(({ key, label, enabled }) => (
                    <div
                      key={key}
                      className={`
                        flex items-center justify-center gap-1 px-2 py-1.5 rounded text-xs font-medium
                        ${enabled
                          ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                          : 'bg-gray-50 dark:bg-gray-700/50 text-gray-400 dark:text-gray-500'
                        }
                      `}
                    >
                      {enabled ? (
                        <CheckCircle className="w-3 h-3" />
                      ) : (
                        <XCircle className="w-3 h-3" />
                      )}
                      <span>{label}</span>
                    </div>
                  ))}
                </div>

                {/* Cost & VRAM Estimation */}
                <div className="space-y-2 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                      <HardDrive className="w-4 h-4" />
                      <span>VRAM Required</span>
                    </div>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {vramReq} GB
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                      <Clock className="w-4 h-4" />
                      <span>Est. Time</span>
                    </div>
                    <span className="font-semibold text-gray-900 dark:text-white">
                      {estimatedTime}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-sm pt-2 border-t border-gray-200 dark:border-gray-600">
                    <div className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
                      <DollarSign className="w-4 h-4" />
                      <span>Est. Cost</span>
                    </div>
                    <span className="font-bold text-indigo-600 dark:text-indigo-400">
                      ${estimatedCost.toFixed(2)}
                    </span>
                  </div>
                </div>

                {/* License */}
                <div className="mt-3 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
                    <Shield className="w-3 h-3" />
                    <span>License: {model.license}</span>
                  </div>
                  <button className="flex items-center gap-1 text-indigo-600 dark:text-indigo-400 hover:underline">
                    <span>Details</span>
                    <ExternalLink className="w-3 h-3" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* No Results */}
      {!loading && filteredModels.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            No models match your search criteria
          </p>
        </div>
      )}
    </div>
  );
}
