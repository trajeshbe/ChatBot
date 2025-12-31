# Tier 3: Customer Implementations

**Status**: Customer-Specific
**Purpose**: Bespoke configurations, integrations, and business logic per customer

---

## Overview

Tier 3 skills provide customer-specific guidance for implementing and customizing the Enterprise RAG Platform. Each customer folder contains implementation details, configuration overrides, and custom integrations.

---

## Customer Implementations

| Customer | Industry | Enabled Modules | Key Capabilities |
|----------|----------|-----------------|------------------|
| [**British Council**](british-council/) | Education | core-rag, nlp-processing | Course recommendations, profile matching |
| [**Construction Monitoring**](construction-monitoring/) | Construction | data-extraction, nlp-processing | Document intelligence, planning analysis |
| [**CRU Organization**](cru-org/) | Research | core-rag | Custom research workflows |
| [**Grant Thornton**](grant-thornton/) | Financial Services | analytics-engine, domain-verticals/financial | Financial analysis, audit workflows |
| [**GT Motive**](gt-motive/) | Automotive | analytics-engine | Automotive parts intelligence |
| [**Solera**](solera/) | Insurance | analytics-engine, data-extraction | Claims processing, damage assessment |

---

## Customer Onboarding Checklist

When implementing for a new customer:

### Phase 1: Discovery (Day 1-2)
- [ ] Identify customer use case and requirements
- [ ] Select appropriate Tier 2 modules
- [ ] Define custom integrations needed
- [ ] Document business logic requirements

### Phase 2: Configuration (Day 2-3)
- [ ] Create customer configuration file (`customers/[customer-id].yaml`)
- [ ] Configure module overrides
- [ ] Define customer-specific prompts
- [ ] Set up branding and UI customization

### Phase 3: Integration (Day 3-4)
- [ ] Implement SSO/authentication integration
- [ ] Set up webhook endpoints
- [ ] Configure external API integrations
- [ ] Implement custom data connectors

### Phase 4: Deployment (Day 4-5)
- [ ] Create Helm values override file
- [ ] Create Argo CD application manifest
- [ ] Deploy to staging environment
- [ ] Run integration tests

### Phase 5: Validation (Day 5)
- [ ] User acceptance testing
- [ ] Performance testing
- [ ] Security review
- [ ] Go-live approval

**Target**: < 5 days from kickoff to production

---

## Customer Configuration Template

### Directory Structure

```
tier-3-customer-implementations/[customer-name]/
├── README.md                           # Customer overview
├── [implementation-name].md            # Primary implementation skill
├── [feature-1].md                      # Feature-specific skills
├── [feature-2].md
└── config/                             # Configuration examples
    ├── customer-config.yaml            # Customer config
    ├── helm-values.yaml                # Deployment config
    └── prompts.yaml                    # Custom prompts
```

### Customer Configuration File

```yaml
# customers/[customer-id].yaml
customer_id: "customer-name"
customer_name: "Customer Display Name"
environment: "production"

# Branding
branding:
  logo_url: "https://cdn.customer.com/logo.svg"
  primary_color: "#1E3A8A"
  secondary_color: "#3B82F6"
  company_name: "Customer AI Assistant"
  custom_css: |
    .chat-header { background: linear-gradient(135deg, #1E3A8A, #3B82F6); }

# Integration
integrations:
  webhook_url: "https://api.customer.com/webhooks/ai-events"
  api_key_header: "X-Customer-API-Key"
  sso_config:
    provider: "okta"  # or "azure", "auth0"
    domain: "customer.okta.com"
    client_id: "${CUSTOMER_SSO_CLIENT_ID}"

# Modules
modules:
  enabled_modules:
    - core-rag
    - data-extraction
    - nlp-processing

  module_configs:
    core-rag:
      retrieval:
        top_k: 10
        similarity_threshold: 0.7
      generation:
        max_tokens: 2048
        temperature: 0.5

# Custom prompts
system_prompts:
  main: |
    You are the Customer AI Assistant.
    [Customer-specific instructions]

  extraction: |
    Extract data from Customer documents.
    [Customer-specific format]

# Feature flags
feature_flags:
  enable_streaming: true
  enable_document_upload: true
  enable_export: true

# Resource limits
rate_limits:
  requests_per_minute: 120
  tokens_per_day: 500000
  documents_per_month: 5000
```

---

## Customer Implementation Patterns

### Pattern 1: Chatbot with Custom Knowledge Base

**Modules**: core-rag
**Customization**: Domain-specific prompts, custom branding

```yaml
modules:
  enabled_modules: [core-rag]

  module_configs:
    core-rag:
      generation_prompt: |
        You are [Customer]'s AI assistant.
        Use [Customer] terminology and cite sources.
```

### Pattern 2: Document Intelligence Pipeline

**Modules**: data-extraction, nlp-processing
**Customization**: Custom extraction schemas, validation rules

```yaml
modules:
  enabled_modules: [data-extraction, nlp-processing]

extraction_schemas:
  customer_document:
    type: object
    properties:
      field1: {type: string}
      field2: {type: number}
```

### Pattern 3: Analytics Dashboard

**Modules**: analytics-engine, domain-verticals/[industry]
**Customization**: Custom metrics, visualization preferences

```yaml
modules:
  enabled_modules: [analytics-engine, domain-verticals/financial]

  module_configs:
    analytics-engine:
      metrics:
        - revenue
        - gross_margin
        - customer_specific_metric
```

### Pattern 4: Multi-Module Solution

**Modules**: core-rag, data-extraction, analytics-engine
**Customization**: Workflow orchestration, custom integrations

```yaml
modules:
  enabled_modules:
    - core-rag
    - data-extraction
    - analytics-engine

workflows:
  document_analysis:
    1. data-extraction.extract(document)
    2. analytics-engine.analyze(extracted_data)
    3. core-rag.answer_questions(document, analysis)
```

---

## Custom Integration Examples

### SSO Integration (Okta)

```yaml
integrations:
  sso_config:
    provider: "okta"
    domain: "customer.okta.com"
    client_id: "${SSO_CLIENT_ID}"
    client_secret: "${SSO_CLIENT_SECRET}"
    redirect_uri: "https://customer-rag.company.com/auth/callback"
```

### Webhook Integration

```yaml
integrations:
  webhook_url: "https://api.customer.com/webhooks/ai"
  webhook_events:
    - document_processed
    - extraction_complete
    - query_answered
  webhook_headers:
    X-API-Key: "${CUSTOMER_WEBHOOK_KEY}"
    Content-Type: "application/json"
```

### External API Integration

```yaml
integrations:
  external_apis:
    crm:
      url: "https://api.customer.com/crm"
      auth_type: "bearer"
      token: "${CRM_API_TOKEN}"
    erp:
      url: "https://api.customer.com/erp"
      auth_type: "api_key"
      key: "${ERP_API_KEY}"
```

---

## Deployment Configuration

### Helm Values Override

```yaml
# infrastructure/helm/customers/[customer-id].yaml
customer:
  id: "customer-name"
  name: "Customer Display Name"

replicas: 3

resources:
  requests:
    memory: "4Gi"
    cpu: "2000m"
  limits:
    memory: "8Gi"
    cpu: "4000m"

modules:
  core-rag:
    enabled: true
  data-extraction:
    enabled: true

branding:
  primaryColor: "#1E3A8A"
  secondaryColor: "#3B82F6"

ingress:
  host: "customer-rag.company.com"
  tls:
    enabled: true
    secretName: "customer-tls"
```

### Argo CD Application

```yaml
# infrastructure/argocd/apps/customer-[customer-id].yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: rag-platform-customer
  namespace: argocd
  labels:
    customer: customer-name
spec:
  project: default
  source:
    repoURL: https://github.com/company/rag-platform.git
    targetRevision: HEAD
    path: infrastructure/helm
    helm:
      valueFiles:
        - values.yaml
        - values-production.yaml
        - customers/customer-name.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: rag-customer-name
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

---

## Customer Skill Template

Each customer folder should contain:

### 1. README.md (Customer Overview)

```markdown
# [Customer Name] Implementation

**Industry**: [Industry]
**Use Case**: [Primary use case]
**Enabled Modules**: [List of modules]
**Go-Live Date**: [Date]

## Overview
[Brief description of the implementation]

## Business Context
[Customer requirements and success criteria]

## Architecture
[Customer-specific architecture diagram]

## Skills
- [Implementation Skill 1](skill-1.md)
- [Implementation Skill 2](skill-2.md)
```

### 2. Implementation Skills

Feature-specific skills following the Tier 3 template (see below).

### 3. Configuration Files

Example configurations for reference.

---

## Monitoring & SLAs

### Customer-Specific Monitoring

```yaml
# Grafana dashboard configuration
customer_monitoring:
  dashboards:
    - name: "Customer Overview"
      metrics:
        - request_rate
        - response_time
        - error_rate
        - token_usage

  alerts:
    - name: "High Error Rate"
      condition: error_rate > 5%
      severity: critical
    - name: "Slow Response"
      condition: p95_latency > 2s
      severity: warning

  sla_targets:
    availability: 99.9%
    p95_latency: < 1s
    error_rate: < 1%
```

---

## Best Practices

### 1. Keep Customer Logic Separate

✅ **DO**: Use YAML configuration overrides
❌ **DON'T**: Fork code for customer customizations

### 2. Document Customer-Specific Decisions

✅ **DO**: Document why custom configs were chosen
❌ **DON'T**: Leave undocumented magic values

### 3. Version Customer Configurations

✅ **DO**: Track config changes in git
❌ **DON'T**: Make undocumented production changes

### 4. Test Customer Configs

✅ **DO**: Test in staging before production
❌ **DON'T**: Deploy untested configurations

---

## Troubleshooting

### Common Issues

**Issue**: Customer-specific prompts not loading
```bash
# Check prompt path configuration
cat config/common_config.yaml | grep prompt_path

# Verify prompt file exists
ls -la prompt_engineering/prompt/customer_[id]_prompts.yaml
```

**Issue**: Module not enabled for customer
```bash
# Check customer configuration
cat customers/[customer-id].yaml | grep enabled_modules

# Verify module registration
kubectl logs -n rag-[customer] deployment/rag-backend | grep "Module.*enabled"
```

**Issue**: Custom integration failing
```bash
# Check integration logs
kubectl logs -n rag-[customer] deployment/rag-backend | grep "integration"

# Verify credentials
kubectl get secret -n rag-[customer] customer-integration-secrets -o yaml
```

---

## Related Documentation

- [Tier 1 Core Platform](../tier-1-core-platform/)
- [Tier 2 Modules](../tier-2-modules/)
- [Customer Onboarding Process](../../SKILLS_REORGANIZATION_SUMMARY.md)

---

**Last Updated**: 2025-12-23
**Active Customers**: 6
**Total Skills**: 12
**Status**: Production Ready
