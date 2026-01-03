/**
 * Module metadata for Tier 2 and Tier 3 modules
 * Maps module IDs to human-readable names and types
 */

export interface ModuleConfig {
  id: string;
  name: string;
  type: 'tier2' | 'tier3';
  tier: 2 | 3;
  category?: string;
  description?: string;
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
  'grant-thornton': {
    id: 'grant-thornton',
    name: 'Grant Thornton POC',
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

// Tier 2 Domain Vertical Modules (IDs MUST match SidebarModern.tsx for routing!)
export const TIER2_MODULES: Record<string, ModuleConfig> = {
  // ========================================
  // DOCUMENT INTELLIGENCE (3 modules)
  // ========================================
  'document-extract': {
    id: 'document-extract',
    name: '18-Field Extraction',
    type: 'tier2',
    tier: 2,
    category: 'document_intelligence',
    description: 'Extract 18 structured fields from planning documents'
  },
  'relation-extractor': {
    id: 'relation-extractor',
    name: 'Relation Extractor',
    type: 'tier2',
    tier: 2,
    category: 'document_intelligence',
    description: 'Extract entities and relationships from documents'
  },
  'generic-rag': {
    id: 'generic-rag',
    name: 'Generic RAG',
    type: 'tier2',
    tier: 2,
    category: 'document_intelligence',
    description: 'General-purpose RAG query system'
  },

  // ========================================
  // CONSTRUCTION (4 modules)
  // ========================================
  'construction': {
    id: 'construction',
    name: 'Building Metrics',
    type: 'tier2',
    tier: 2,
    category: 'construction',
    description: 'Construction project metrics extraction and analysis'
  },
  'planning-classifier': {
    id: 'planning-classifier',
    name: 'Planning Classifier',
    type: 'tier2',
    tier: 2,
    category: 'construction',
    description: 'Classify planning documents by type and purpose using AI vision'
  },
  'mine-scope': {
    id: 'mine-scope',
    name: 'Mine Scope Analysis',
    type: 'tier2',
    tier: 2,
    category: 'construction',
    description: 'Mining scope analysis with requirements, metrics, and risk assessment'
  },
  'estimator-au': {
    id: 'estimator-au',
    name: 'AU Cost Estimator',
    type: 'tier2',
    tier: 2,
    category: 'construction',
    description: 'Australian construction cost estimation and forecasting'
  },

  // ========================================
  // PROCUREMENT (4 modules)
  // ========================================
  'matcher': {
    id: 'matcher',
    name: 'PO-Invoice Matcher',
    type: 'tier2',
    tier: 2,
    category: 'procurement',
    description: 'Match purchase orders to invoices with variance analysis'
  },
  'vendor-recommendation': {
    id: 'vendor-recommendation',
    name: 'Vendor Recommendation',
    type: 'tier2',
    tier: 2,
    category: 'procurement',
    description: 'AI-powered vendor recommendations with multi-criteria scoring'
  },
  'tender-intelligence': {
    id: 'tender-intelligence',
    name: 'Tender Intelligence',
    type: 'tier2',
    tier: 2,
    category: 'procurement',
    description: 'Analyze tenders/RFPs with bid recommendations'
  },
  'spend-smart': {
    id: 'spend-smart',
    name: 'Spend Analytics',
    type: 'tier2',
    tier: 2,
    category: 'procurement',
    description: 'Procurement spend analysis and optimization'
  },

  // ========================================
  // HR & TALENT (3 modules)
  // ========================================
  'talent-search': {
    id: 'talent-search',
    name: 'Talent Search',
    type: 'tier2',
    tier: 2,
    category: 'hr_talent',
    description: 'AI-powered candidate-to-job matching with multi-dimensional scoring'
  },
  'taxonomy-skillmatch': {
    id: 'taxonomy-skillmatch',
    name: 'Skill Taxonomy',
    type: 'tier2',
    tier: 2,
    category: 'hr_talent',
    description: 'Map skills to taxonomy and match skillsets with gap analysis'
  },
  'talent-pulse': {
    id: 'talent-pulse',
    name: 'Employee Engagement',
    type: 'tier2',
    tier: 2,
    category: 'hr_talent',
    description: 'Employee sentiment, engagement, and attrition risk analysis'
  },

  // ========================================
  // AGRICULTURE (2 modules)
  // ========================================
  'agri-taxonomy': {
    id: 'agri-taxonomy',
    name: 'Crop Taxonomy',
    type: 'tier2',
    tier: 2,
    category: 'agriculture',
    description: 'Classify crops with scientific taxonomy and growing requirements'
  },
  'agronomy-decision': {
    id: 'agronomy-decision',
    name: 'Agronomy Decisions',
    type: 'tier2',
    tier: 2,
    category: 'agriculture',
    description: 'AI-powered crop and farming decision support'
  },

  // ========================================
  // MARKETING (2 modules)
  // ========================================
  'sentiment-social': {
    id: 'sentiment-social',
    name: 'Social Sentiment',
    type: 'tier2',
    tier: 2,
    category: 'marketing',
    description: 'Social media sentiment analysis and brand monitoring'
  },
  'campaign-optimizer': {
    id: 'campaign-optimizer',
    name: 'Campaign Optimizer',
    type: 'tier2',
    tier: 2,
    category: 'marketing',
    description: 'Marketing campaign optimization and ROI analysis'
  },

  // ========================================
  // E-COMMERCE (1 module)
  // ========================================
  'product-recommendation': {
    id: 'product-recommendation',
    name: 'Product Recommendations',
    type: 'tier2',
    tier: 2,
    category: 'ecommerce',
    description: 'AI-powered product recommendations'
  },

  // ========================================
  // MARITIME (1 module)
  // ========================================
  'maritime-logistics': {
    id: 'maritime-logistics',
    name: 'Logistics Optimizer',
    type: 'tier2',
    tier: 2,
    category: 'maritime',
    description: 'Maritime logistics and shipping optimization'
  },

  // ========================================
  // ANALYTICS (4 modules)
  // ========================================
  'predictive-analytics': {
    id: 'predictive-analytics',
    name: 'Predictive Analytics',
    type: 'tier2',
    tier: 2,
    category: 'analytics',
    description: 'ML-powered predictive analytics and forecasting'
  },
  'customer-churn': {
    id: 'customer-churn',
    name: 'Churn Predictor',
    type: 'tier2',
    tier: 2,
    category: 'analytics',
    description: 'Predict customer churn with ML models'
  },
  'sales-performance': {
    id: 'sales-performance',
    name: 'Sales Performance',
    type: 'tier2',
    tier: 2,
    category: 'analytics',
    description: 'Analyze and forecast sales performance'
  },
  'financial-anomaly': {
    id: 'financial-anomaly',
    name: 'Financial Anomaly',
    type: 'tier2',
    tier: 2,
    category: 'analytics',
    description: 'Detect financial anomalies and fraud patterns'
  },

  // ========================================
  // INDUSTRY VERTICALS (5 modules)
  // ========================================
  'healthcare-diagnostics': {
    id: 'healthcare-diagnostics',
    name: 'Healthcare Diagnostics',
    type: 'tier2',
    tier: 2,
    category: 'industry_verticals',
    description: 'Medical diagnosis support and healthcare analytics'
  },
  'legal-document': {
    id: 'legal-document',
    name: 'Legal Document Analyzer',
    type: 'tier2',
    tier: 2,
    category: 'industry_verticals',
    description: 'Legal document analysis, contract review, and clause extraction'
  },
  'real-estate-valuation': {
    id: 'real-estate-valuation',
    name: 'Real Estate Valuation',
    type: 'tier2',
    tier: 2,
    category: 'industry_verticals',
    description: 'Property valuation and real estate market analysis'
  },
  'insurance-risk': {
    id: 'insurance-risk',
    name: 'Insurance Risk Assessor',
    type: 'tier2',
    tier: 2,
    category: 'industry_verticals',
    description: 'Insurance risk assessment and underwriting support'
  },
  'educational-content': {
    id: 'educational-content',
    name: 'Educational Content',
    type: 'tier2',
    tier: 2,
    category: 'industry_verticals',
    description: 'Educational content generation and curriculum planning'
  },

  // ========================================
  // ADVANCED CAPABILITIES (2 modules)
  // ========================================
  'multilingual-translator': {
    id: 'multilingual-translator',
    name: 'Multilingual Translator',
    type: 'tier2',
    tier: 2,
    category: 'advanced_capabilities',
    description: 'Multi-language translation with context preservation'
  },
  'code-analysis': {
    id: 'code-analysis',
    name: 'Code Analysis & Review',
    type: 'tier2',
    tier: 2,
    category: 'advanced_capabilities',
    description: 'Analyze code quality, security, and performance'
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
