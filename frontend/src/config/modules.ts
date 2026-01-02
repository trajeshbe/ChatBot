/**
 * Module metadata for Tier 2 and Tier 3 modules
 * Maps module IDs to human-readable names and types
 */

export interface ModuleConfig {
  id: string;
  name: string;
  type: 'tier2' | 'tier3';
  tier: 2 | 3;
}

// Tier 3 Customer POC Modules
export const TIER3_MODULES: Record<string, ModuleConfig> = {
  'british-council': {
    id: 'british-council',
    name: 'British Council POC',
    type: 'tier3',
    tier: 3
  },
  'cru': {
    id: 'cru',
    name: 'CRU POC',
    type: 'tier3',
    tier: 3
  },
  'gt-motive': {
    id: 'gt-motive',
    name: 'GT Motive POC',
    type: 'tier3',
    tier: 3
  },
  'solera': {
    id: 'solera',
    name: 'Solera POC',
    type: 'tier3',
    tier: 3
  },
  'construction-monitor': {
    id: 'construction-monitor',
    name: 'Construction Monitor POC',
    type: 'tier3',
    tier: 3
  }
};

// Tier 2 Domain Vertical Modules (to be implemented)
export const TIER2_MODULES: Record<string, ModuleConfig> = {
  'document-intelligence': {
    id: 'document-intelligence',
    name: 'Document Intelligence',
    type: 'tier2',
    tier: 2
  },
  'generic-rag': {
    id: 'generic-rag',
    name: 'Generic RAG',
    type: 'tier2',
    tier: 2
  },
  'predictive-analytics': {
    id: 'predictive-analytics',
    name: 'Predictive Analytics',
    type: 'tier2',
    tier: 2
  },
  'multilingual-translator': {
    id: 'multilingual-translator',
    name: 'Multilingual Translator',
    type: 'tier2',
    tier: 2
  },
  'financial-anomaly': {
    id: 'financial-anomaly',
    name: 'Financial Anomaly Detection',
    type: 'tier2',
    tier: 2
  },
  'legal-document': {
    id: 'legal-document',
    name: 'Legal Document Processing',
    type: 'tier2',
    tier: 2
  },
  'insurance-risk': {
    id: 'insurance-risk',
    name: 'Insurance Risk Assessment',
    type: 'tier2',
    tier: 2
  },
  'estimator-one-au': {
    id: 'estimator-one-au',
    name: 'EstimatorOne (AU)',
    type: 'tier2',
    tier: 2
  },
  'mine-scope': {
    id: 'mine-scope',
    name: 'Mine Scope Analysis',
    type: 'tier2',
    tier: 2
  },
  'educational-content': {
    id: 'educational-content',
    name: 'Educational Content Management',
    type: 'tier2',
    tier: 2
  }
};

// Combined module lookup
export const ALL_MODULES: Record<string, ModuleConfig> = {
  ...TIER2_MODULES,
  ...TIER3_MODULES
};

// Helper function to get module config
export const getModuleConfig = (moduleId: string): ModuleConfig | null => {
  return ALL_MODULES[moduleId] || null;
};

// Helper to check if a module ID is a Tier 2/3 module
export const isModuleId = (tabId: string): boolean => {
  return tabId in ALL_MODULES;
};

// Helper to determine module type
export const getModuleType = (moduleId: string): 'tier2' | 'tier3' | null => {
  const module = getModuleConfig(moduleId);
  return module ? module.type : null;
};
