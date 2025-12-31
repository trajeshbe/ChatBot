# Tier 3: Customer Implementations

**Status**: Bespoke Configurations
**Purpose**: Customer-specific deployments and configurations

## Customer Configurations

Place customer YAML configs in `configs/` directory.

Example:
```yaml
# configs/acme-corp.yaml
customer:
  name: "Acme Corp"
  industry: "financial_services"

enabled_modules:
  - core_rag
  - financial_document_analysis

rag_settings:
  top_k: 10
  min_similarity: 0.75
```

## Examples

See `_examples/` for reference implementations:
- british-council
- construction-monitoring
- grant-thornton

## Config Loader (TO BE IMPLEMENTED)

See `loader.py` for YAML config loading.

See [THREE_TIER_REORGANIZATION_PLAN.md](../../docs/architecture/THREE_TIER_REORGANIZATION_PLAN.md) for full details.
