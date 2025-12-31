# Profile-matcher-implementation - British-council

**Tier**: 3 (Customer Bespoke)
**Customer**: British-council
**Enabled Modules**: core-rag, nlp-processing
**Source**: `.claude/skills/client-pocs/british-council-poc.md`

## Overview
Customer-specific implementation for british-council: profile-matcher-implementation

## Configuration
See: `customers/british-council.yaml`

## Custom Prompts
See: `prompt_engineering/prompt/customer_british-council_prompts.yaml`

## Source Material
Original POC: `.claude/skills/client-pocs/british-council-poc.md`

## Deployment
```bash
helm install rag-british-council ./infrastructure/helm \
  -f values.yaml \
  -f customers/british-council.yaml
```
