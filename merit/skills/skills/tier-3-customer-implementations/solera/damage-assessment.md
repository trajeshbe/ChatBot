# Damage-assessment - Solera

**Tier**: 3 (Customer Bespoke)
**Customer**: Solera
**Enabled Modules**: analytics-engine, data-extraction
**Source**: `.claude/skills/client-pocs/solera-poc.md`

## Overview
Customer-specific implementation for solera: damage-assessment

## Configuration
See: `customers/solera.yaml`

## Custom Prompts
See: `prompt_engineering/prompt/customer_solera_prompts.yaml`

## Source Material
Original POC: `.claude/skills/client-pocs/solera-poc.md`

## Deployment
```bash
helm install rag-solera ./infrastructure/helm \
  -f values.yaml \
  -f customers/solera.yaml
```
