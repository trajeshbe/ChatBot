# Document-intelligence - Construction-monitoring

**Tier**: 3 (Customer Bespoke)
**Customer**: Construction-monitoring
**Enabled Modules**: data-extraction, nlp-processing
**Source**: `.claude/skills/client-pocs/construction-monitor-poc.md`

## Overview
Customer-specific implementation for construction-monitoring: document-intelligence

## Configuration
See: `customers/construction-monitoring.yaml`

## Custom Prompts
See: `prompt_engineering/prompt/customer_construction-monitoring_prompts.yaml`

## Source Material
Original POC: `.claude/skills/client-pocs/construction-monitor-poc.md`

## Deployment
```bash
helm install rag-construction-monitoring ./infrastructure/helm \
  -f values.yaml \
  -f customers/construction-monitoring.yaml
```
