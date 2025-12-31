# Audit-workflows - Grant-thornton

**Tier**: 3 (Customer Bespoke)
**Customer**: Grant-thornton
**Enabled Modules**: analytics-engine, domain-verticals/financial
**Source**: `.claude/skills/client-pocs/grand-thornton-poc.md`

## Overview
Customer-specific implementation for grant-thornton: audit-workflows

## Configuration
See: `customers/grant-thornton.yaml`

## Custom Prompts
See: `prompt_engineering/prompt/customer_grant-thornton_prompts.yaml`

## Source Material
Original POC: `.claude/skills/client-pocs/grand-thornton-poc.md`

## Deployment
```bash
helm install rag-grant-thornton ./infrastructure/helm \
  -f values.yaml \
  -f customers/grant-thornton.yaml
```
