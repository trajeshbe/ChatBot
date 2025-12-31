# Platform Infrastructure - Core Platform

**Tier**: 1 (Core Platform)
**Status**: Always Deployed
**Source**: Merit ML Platform + Enterprise RAG Stack

---

## Overview

Kubernetes-based infrastructure with Istio service mesh, Argo CD GitOps, and Tekton CI/CD pipelines.

## Key Technologies

- **Orchestration**: Kubernetes 1.28+
- **Service Mesh**: Istio Ambient Mode
- **GitOps**: Argo CD (app-of-apps pattern)
- **CI/CD**: Tekton Pipelines
- **Local Dev**: Skaffold with profiles
- **Policy**: OPA Gatekeeper

## Architecture Reference

See: [Enterprise 3-Tier Architecture Plan](../../Enterprise%203%20Tier%20AI%20Architecure%20plan/enterprise-rag-three-tier-architecture-plan.md) - Part 1, Section 1.3

## Quick Reference

### Deploy with Argo CD
```bash
kubectl apply -f infrastructure/argocd/app-of-apps.yaml
```

### Local Development
```bash
skaffold dev --profile=local
```

## Related Skills
- [Database & Vector Storage](database-vector-storage.md)
- [Observability & Monitoring](observability-monitoring.md)
