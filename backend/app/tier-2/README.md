# Tier 2: Use-Case Modules

**Status**: Selectively Enabled
**Purpose**: Domain-specific capabilities enabled per customer

## Current Modules

- **construction_metrics/**: Building metrics extraction workflow
- **project_estimator/**: Project estimation workflow

## Module Registry (TO BE IMPLEMENTED)

See `registry.py` for dynamic module loading.

## Creating New Modules

See `_templates/module_template/` for starter template.

## Import Pattern

```python
from app.tier_2.construction_metrics.workflow import ConstructionMetricsWorkflow
```

See [THREE_TIER_REORGANIZATION_PLAN.md](../../docs/architecture/THREE_TIER_REORGANIZATION_PLAN.md) for full details.
