/**
 * Module Router - Maps module IDs to their specialized UI components
 *
 * This component routes each Tier 2 Domain Vertical and Tier 3 Customer Solution
 * to its dedicated, specialized UI component instead of using a generic interface.
 */

import React from 'react';

// Tier 2 - Analytics
import CustomerChurnPanel from './tier2/analytics/CustomerChurnPanel';
import FinancialAnomalyPanel from './tier2/analytics/FinancialAnomalyPanel';
import PredictiveAnalyticsPanel from './tier2/analytics/PredictiveAnalyticsPanel';
import SalesPerformancePanel from './tier2/analytics/SalesPerformancePanel';

// Tier 2 - Construction
import EstimatorAUPanel from './tier2/construction/EstimatorAUPanel';
import BuildingMetricsPanel from './tier2/construction/BuildingMetricsPanel';
import MineScopePanel from './tier2/construction/MineScopePanel';
import PlanningClassifierPanel from './tier2/construction/PlanningClassifierPanel';

// Tier 2 - Agriculture
import AgronomyDecisionPanel from './tier2/agriculture/AgronomyDecisionPanel';
import AgriTaxonomyPanel from './tier2/agriculture/AgriTaxonomyPanel';

// Tier 2 - Procurement
import SpendSmartPanel from './tier2/procurement/SpendSmartPanel';
import ProcurementMatcherPanel from './tier2/procurement/ProcurementMatcherPanel';
import TenderIntelligencePanel from './tier2/procurement/TenderIntelligencePanel';
import VendorRecommendationPanel from './tier2/procurement/VendorRecommendationPanel';

// Tier 2 - Maritime
import MaritimeReportPanel from './tier2/maritime/MaritimeReportPanel';

// Tier 2 - Marketing
import CampaignOptimizerPanel from './tier2/marketing/CampaignOptimizerPanel';
import SentimentSocialPanel from './tier2/marketing/SentimentSocialPanel';

// Tier 2 - E-commerce
import ProductRecommendationPanel from './tier2/ecommerce/ProductRecommendationPanel';

// Tier 2 - Industry Verticals
import EducationalContentPanel from './tier2/industry_verticals/EducationalContentPanel';
import HealthcareDiagnosticsPanel from './tier2/industry_verticals/HealthcareDiagnosticsPanel';
import InsuranceRiskPanel from './tier2/industry_verticals/InsuranceRiskPanel';
import LegalDocumentPanel from './tier2/industry_verticals/LegalDocumentPanel';
import RealEstatePanel from './tier2/industry_verticals/RealEstatePanel';

// Tier 2 - Advanced Capabilities
import CodeAnalysisPanel from './tier2/advanced_capabilities/CodeAnalysisPanel';
import MultilingualTranslatorPanel from './tier2/advanced_capabilities/MultilingualTranslatorPanel';

// Tier 2 - HR/Talent
import TalentPulsePanel from './tier2/hr_talent/TalentPulsePanel';
import TalentSearchPanel from './tier2/hr_talent/TalentSearchPanel';
import TaxonomySkillmatchPanel from './tier2/hr_talent/TaxonomySkillmatchPanel';

// Tier 2 - Document Intelligence
import RelationExtractorPanel from './tier2/document_intelligence/RelationExtractorPanel';

// Tier 3 - Customer Solutions
import BritishCouncilRecommender from './BritishCouncilRecommender';
import CRUMiningIntelligence from './CRUMiningIntelligence';
import GrantThorntonExtraction from './GrantThorntonExtraction';
import GtMotiveExtraction from './GtMotiveExtraction';
import SoleraClaimsProcessing from './SoleraClaimsProcessing';

// Fallback for modules without specialized components
import EnhancedModulePanel from './EnhancedModulePanel';

interface ModuleRouterProps {
  moduleId: string;
  moduleName: string;
  moduleType: 'tier2' | 'tier3';
  moduleCategory?: string;
  moduleDescription?: string;
  sessionId: string;
}

/**
 * Module ID to Component mapping
 * Maps each module ID to its specialized React component
 */
const MODULE_COMPONENTS: Record<string, React.ComponentType<any>> = {
  // Analytics (4 modules)
  'customer-churn': CustomerChurnPanel,
  'financial-anomaly': FinancialAnomalyPanel,
  'predictive-analytics': PredictiveAnalyticsPanel,
  'sales-performance': SalesPerformancePanel,

  // Construction (4 modules)
  'estimator-au': EstimatorAUPanel,
  'construction': BuildingMetricsPanel,
  'mine-scope': MineScopePanel,
  'planning-classifier': PlanningClassifierPanel,

  // Agriculture (2 modules)
  'agronomy-decision': AgronomyDecisionPanel,
  'agri-taxonomy': AgriTaxonomyPanel,

  // Procurement (4 modules)
  'spend-smart': SpendSmartPanel,
  'matcher': ProcurementMatcherPanel,
  'tender-intelligence': TenderIntelligencePanel,
  'vendor-recommendation': VendorRecommendationPanel,

  // Maritime (1 module)
  'maritime-logistics': MaritimeReportPanel,

  // Marketing (2 modules)
  'campaign-optimizer': CampaignOptimizerPanel,
  'sentiment-social': SentimentSocialPanel,

  // E-commerce (1 module)
  'product-recommendation': ProductRecommendationPanel,

  // Industry Verticals (5 modules)
  'educational-content': EducationalContentPanel,
  'healthcare-diagnostics': HealthcareDiagnosticsPanel,
  'insurance-risk': InsuranceRiskPanel,
  'legal-document': LegalDocumentPanel,
  'real-estate': RealEstatePanel,

  // Advanced Capabilities (2 modules)
  'code-analysis': CodeAnalysisPanel,
  'multilingual-translator': MultilingualTranslatorPanel,

  // HR/Talent (3 modules)
  'talent-pulse': TalentPulsePanel,
  'talent-search': TalentSearchPanel,
  'taxonomy-skillmatch': TaxonomySkillmatchPanel,

  // Document Intelligence (1 module with specialized UI)
  'relation-extractor': RelationExtractorPanel,

  // Tier 3 - Customer Solutions (6 POCs)
  'british-council': BritishCouncilRecommender,
  'cru': CRUMiningIntelligence,
  'grant-thornton': GrantThorntonExtraction,
  'gt-motive': GtMotiveExtraction,
  'solera': SoleraClaimsProcessing,
  // 'construction-monitor': ConstructionMonitorPanel, // TODO: Create if needed
};

/**
 * ModuleRouter Component
 *
 * Dynamically renders the appropriate specialized component for each module.
 * Falls back to EnhancedModulePanel for modules without specialized components.
 */
const ModuleRouter: React.FC<ModuleRouterProps> = ({
  moduleId,
  moduleName,
  moduleType,
  moduleCategory,
  moduleDescription,
  sessionId
}) => {
  // Get the specialized component for this module
  const SpecializedComponent = MODULE_COMPONENTS[moduleId];

  // If a specialized component exists, use it
  if (SpecializedComponent) {
    return <SpecializedComponent />;
  }

  // Fallback to generic EnhancedModulePanel for modules without specialized UI
  console.warn(`No specialized component found for module: ${moduleId}. Using EnhancedModulePanel.`);

  return (
    <EnhancedModulePanel
      moduleId={moduleId}
      moduleName={moduleName}
      moduleType={moduleType}
      moduleCategory={moduleCategory}
      moduleDescription={moduleDescription}
      sessionId={sessionId}
      supportsFileUpload={true}
    />
  );
};

export default ModuleRouter;
