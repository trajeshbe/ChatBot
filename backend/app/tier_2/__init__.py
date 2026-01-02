"""
Tier 2: Domain Vertical Modules

Pluggable modules that extend tier_1 core platform for specific use cases and industries.
Each module is self-contained with its own routes, services, and schemas.

Available Modules:
- document_intelligence: Document extraction, schema extraction, table extraction
- construction: Construction metrics, planning, mine scope, etc. (coming soon)
- procurement: Matcher, vendor recommendation, tender intelligence (coming soon)
- hr_talent: Talent search, skill matching, pulse analysis (coming soon)
- agriculture: Agri taxonomy, agronomy decision support (coming soon)
- marketing: Email campaign analyzer, bounce intelligence (coming soon)
- ecommerce: Fashion tagging, product categorization (coming soon)
- maritime: Report generation, vessel analytics (coming soon)
- analytics: Bot detection, credit profiling, dashboards (coming soon)
"""

from .registry import ModuleRegistry

__all__ = ["ModuleRegistry"]

# Global module registry instance
registry = ModuleRegistry()
