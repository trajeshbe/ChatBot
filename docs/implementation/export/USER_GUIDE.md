# Export System - User Guide

**Last Updated**: 2026-01-04
**Audience**: End Users, Customers

---

## Overview

The Export Wizard allows you to create complete, deployable packages of RAG modules including all source code, configurations, and infrastructure needed for standalone deployment.

---

## Prerequisites

- Access to a module interface (Tier 2 or Tier 3)
- Appropriate permissions for exporting
- Customer information ready

---

## Step-by-Step Guide

### Step 1: Navigate to Module

1. Open the application
2. Navigate to the desired module (e.g., Procurement Matcher, British Council, etc.)
3. Locate the **Export** button (usually in the top-right corner)

### Step 2: Launch Export Wizard

Click the **Export** button. The Export Wizard will open with multiple configuration steps.

---

## Export Wizard Steps

### 🎯 Step 1: Basic Information

**Required Fields**:
- **Customer Name**: Your organization name
- **Customer Email**: Contact email for support
- **Module**: Pre-selected based on current module

**Example**:
```
Customer Name: Acme Corporation
Customer Email: deploy@acmecorp.com
Module: Procurement Matcher
```

---

### 🚀 Step 2: Deployment Type

Choose how you plan to deploy the exported package:

| Option | Best For | Includes |
|--------|----------|----------|
| **Docker Compose** | Quick local deployment, development | docker-compose.yml, Dockerfiles |
| **Kubernetes** | Production cloud deployment | K8s manifests, Helm charts |
| **AWS CloudFormation** | AWS-specific deployment | CloudFormation templates, IAM policies |
| **Bare Metal** | Traditional VM deployment | Systemd services, install scripts |

**Recommendation**: Start with **Docker Compose** for testing, then use **Kubernetes** or **AWS** for production.

---

### 📜 Step 3: License Tier

Select the appropriate license tier:

| Tier | Features | Price | Max Users |
|------|----------|-------|-----------|
| **Trial** | 30-day evaluation, basic features | Free | 5 |
| **Professional** | Full features, 1-year license | Standard | 50 |
| **Enterprise** | Full features, multi-year, SLA | Premium | Unlimited |
| **Custom** | Negotiated terms | Custom | Negotiated |

**License Duration**:
- Trial: 30 days
- Professional: 1 year (renewable)
- Enterprise: 1-3 years
- Custom: As agreed

---

### ⚙️ Step 4: Export Options

Configure what to include in the export package:

#### Documents & Embeddings
- ☑️ **Include Embeddings**: Pre-computed vector embeddings (faster startup)
- ☑️ **Include Sample Data**: Test data for validation

**Recommendation**: Enable both for complete package

#### Fine-Tuned Models
- ☑️ **Include Fine-Tuned Models**: If module uses custom models
- ⚠️ Models > 50GB: Download instructions provided instead

#### Infrastructure
- ☑️ **Include Monitoring**: Grafana dashboards, Prometheus configs
- ☑️ **Include Logging**: Loki, log aggregation setup

**Recommendation**: Enable for production deployments

#### Advanced Options
- **Max Users**: Override license tier default
- **Custom Domain**: For SSL certificates
- **Database Backup**: Include current database snapshot

---

### 📋 Step 5: Review

Review all configuration before export:

```
Customer: Acme Corporation (deploy@acmecorp.com)
Module: Procurement Matcher
Deployment: Docker Compose
License: Professional (1 year)

Options:
✅ Include embeddings
✅ Include monitoring
✅ Include sample data
✅ Fine-tuned models (if available)

Estimated Package Size: 2-5 GB
Estimated Export Time: 2-5 minutes
```

**Actions**:
- ✏️ **Edit**: Go back to modify any step
- ✅ **Confirm**: Start export process

---

### ⏳ Step 6: Export Progress

Watch real-time progress as the package is created:

```
Progress: 60%

✅ Extracting configuration
✅ Exporting documents (125/125)
✅ Exporting embeddings (1,234/1,234)
🔄 Extracting module source code...
⏸️ Exporting fine-tuned models
⏸️ Generating infrastructure
⏸️ Creating package
```

**Typical Duration**: 2-5 minutes depending on:
- Number of documents
- Embedding count
- Model size
- Deployment complexity

---

### ✅ Step 7: Download

Once export completes:

```
🎉 Export Complete!

Package: acme-corp-matcher-20260104-103000.tar.gz
Size: 2.3 GB
Checksum: a1b2c3d4e5f6...

[Download Package]  [View Manifest]  [Generate Report]
```

**Actions**:
- **Download Package**: Get the .tar.gz file
- **View Manifest**: See detailed package contents
- **Generate Report**: PDF summary for records

---

## After Export

### 1. Verify Download

Check the downloaded file:

```bash
# Verify file integrity
sha256sum acme-corp-matcher-*.tar.gz

# Should match the checksum shown in wizard
```

### 2. Extract Package

```bash
# Extract to deployment directory
tar -xzf acme-corp-matcher-*.tar.gz
cd acme-corp-matcher-*/
```

### 3. Review Contents

```bash
# Check README for deployment instructions
cat README.md

# View manifest
cat manifest.json

# List all files
find . -type f | head -20
```

### 4. Deploy

See [Deployment Guide](./DEPLOYMENT_GUIDE.md) for platform-specific instructions.

---

## Package Contents

Every export package includes:

### 📄 Documentation
- `README.md` - Deployment instructions
- `LICENSE.txt` - License agreement and terms
- `manifest.json` - Complete package metadata

### ⚙️ Configuration
- `config/module_config.json` - Module settings
- `config/.env.example` - Environment variables template
- `config/settings.yaml` - Additional configuration

### 💻 Source Code
- `src/backend/` - Python backend services
- `src/frontend/` - React frontend components
- `requirements.txt` - Python dependencies
- `package.json` - NPM dependencies

### 🗄️ Data
- `data/documents/` - Exported documents
- `data/embeddings/` - Pre-computed vectors
- `data/sample_data/` - Test data

### 🤖 Models (if applicable)
- `models/*/adapter_model/` - LoRA adapters
- `models/*/model/` - Full models (< 50GB)
- `models/DOWNLOAD_MODEL.md` - Instructions for large models

### 🚀 Infrastructure
- `infrastructure/docker/` - Docker Compose files
- `infrastructure/kubernetes/` - K8s manifests
- `infrastructure/aws/` - CloudFormation templates

### 🔧 Scripts
- `scripts/setup.sh` - Initial setup
- `scripts/deploy.sh` - Deployment automation
- `scripts/test.sh` - Validation tests

---

## Troubleshooting

### Export Fails to Start

**Symptoms**: Wizard doesn't open or shows error

**Solutions**:
1. Check permissions - ensure you have export access
2. Refresh page and try again
3. Check browser console for JavaScript errors
4. Contact support if issue persists

### Export Stuck at Specific Step

**Symptoms**: Progress bar doesn't move for > 5 minutes

**Solutions**:
1. Check backend logs for errors
2. Verify database connectivity
3. Check MinIO storage space
4. Cancel and retry export

### Download Fails

**Symptoms**: Download starts but file is incomplete

**Solutions**:
1. Use a download manager for large files
2. Check network stability
3. Verify MinIO access permissions
4. Contact support for direct file access

### Package Extraction Fails

**Symptoms**: `tar: Error opening archive`

**Solutions**:
1. Verify file integrity with checksum
2. Re-download if checksums don't match
3. Ensure enough disk space for extraction
4. Check file permissions

---

## Best Practices

### ✅ Before Export

1. **Test Module**: Ensure module works correctly before export
2. **Clean Data**: Remove test/temporary documents
3. **Verify Configuration**: Check all settings are production-ready
4. **Plan Deployment**: Know target infrastructure

### ✅ During Export

1. **Don't Close Browser**: Keep wizard tab open
2. **Stable Connection**: Ensure reliable internet
3. **Monitor Progress**: Watch for any warnings/errors
4. **Take Notes**: Document any special settings chosen

### ✅ After Export

1. **Backup Package**: Store package in safe location
2. **Verify Integrity**: Check checksum immediately
3. **Test Deployment**: Deploy to staging first
4. **Document Changes**: Note any custom configurations

---

## FAQ

### Q: How long does an export take?
**A**: Typically 2-5 minutes. Larger modules with many documents or fine-tuned models may take longer (up to 15 minutes).

### Q: Can I cancel an in-progress export?
**A**: Yes, click "Cancel" button. Partial export will be discarded.

### Q: How large are export packages?
**A**: Varies by module:
- Small (backend-only): 50-200 MB
- Medium (with documents): 500 MB - 2 GB
- Large (with models): 2-10 GB
- Very Large (large fine-tuned models): 10-50 GB

### Q: Can I export the same module multiple times?
**A**: Yes, each export creates a new package with unique timestamp.

### Q: Are exports encrypted?
**A**: Packages are not encrypted by default. License keys use JWT. For encryption, use your organization's secure file transfer.

### Q: Can I customize the export?
**A**: Yes, configure options in Step 4. For deep customization, contact support.

### Q: What if I lose the package file?
**A**: Exports are stored in MinIO for 30 days. Contact support to retrieve with your export job ID.

### Q: How do I renew an expired license?
**A**: Contact sales. New license key can be applied without re-export.

---

## Getting Help

### Documentation
- [Deployment Guide](./DEPLOYMENT_GUIDE.md) - Platform-specific deployment
- [Architecture](./ARCHITECTURE.md) - Technical details
- [Testing Guide](./TESTING_GUIDE.md) - Validation procedures

### Support
- **Email**: support@example.com
- **Documentation**: Check README.md in package
- **Emergency**: Contact your account manager

---

**Last Updated**: 2026-01-04
**Version**: 1.0.0
