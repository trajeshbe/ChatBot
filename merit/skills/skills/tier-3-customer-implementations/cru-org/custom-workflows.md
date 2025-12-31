# Custom-workflows - Cru-org

**Tier**: 3 (Customer Bespoke)
**Customer**: Cru-org
**Enabled Modules**: core-rag
**Source**: `.claude/skills/client-pocs/cru-poc.md`

## Overview
Customer-specific implementation for cru-org: custom-workflows

## Configuration
See: `customers/cru-org.yaml`

## Custom Prompts
See: `prompt_engineering/prompt/customer_cru-org_prompts.yaml`

## Source Material
Original POC: `.claude/skills/client-pocs/cru-poc.md`

## Deployment
```bash
helm install rag-cru-org ./infrastructure/helm \
  -f values.yaml \
  -f customers/cru-org.yaml
```
