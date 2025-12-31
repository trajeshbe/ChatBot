# Automotive-analysis - Gt-motive

**Tier**: 3 (Customer Bespoke)
**Customer**: Gt-motive
**Enabled Modules**: analytics-engine
**Source**: `.claude/skills/client-pocs/gt-motive-poc.md`

## Overview
Customer-specific implementation for gt-motive: automotive-analysis

## Configuration
See: `customers/gt-motive.yaml`

## Custom Prompts
See: `prompt_engineering/prompt/customer_gt-motive_prompts.yaml`

## Source Material
Original POC: `.claude/skills/client-pocs/gt-motive-poc.md`

## Deployment
```bash
helm install rag-gt-motive ./infrastructure/helm \
  -f values.yaml \
  -f customers/gt-motive.yaml
```
