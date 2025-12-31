# Procurement Matcher - Documentation Index

## Overview

This documentation provides comprehensive guidance for the Procurement Matcher AI-powered prototype application. The application offers three core functionalities:

1. **Legal Case Matching**: Match precedent legal cases with current cases based on legal issues and reasoning
2. **Procurement Vendor Matching**: Evaluate vendor capabilities against procurement requirements
3. **Vendor Taxonomy Classification**: Extract structured information from unstructured vendor descriptions

## Documentation Structure

The documentation is organized into five comprehensive guides:

### 1. [System Overview](01_overview.md)
**Purpose**: High-level introduction to the application

**Contents**:
- Executive summary and objectives
- System architecture and components
- Technology stack overview
- Key features and use cases
- Future enhancement roadmap

**Audience**: All users, stakeholders, management

**When to Read**: Start here for understanding what the application does and why

---

### 2. [Technical Architecture](02_technical_architecture.md)
**Purpose**: Deep dive into system design and implementation

**Contents**:
- Detailed architecture and design patterns
- Component breakdown and interactions
- Class hierarchy and inheritance structure
- Data models and schemas
- Integration points (LangChain, OpenAI, Streamlit)
- Performance and scalability considerations
- Security architecture

**Audience**: Developers, architects, technical leads

**When to Read**: Before modifying code or extending functionality

---

### 3. [API Reference](03_api_reference.md)
**Purpose**: Complete reference for all classes, methods, and interfaces

**Contents**:
- Module and file structure
- Class reference with detailed method signatures
- Data model specifications (Pydantic models)
- Prompt template documentation
- Configuration schema
- Code examples and usage patterns
- Error codes and handling

**Audience**: Developers, integrators

**When to Read**: During development, debugging, or API integration

---

### 4. [User Guide](04_user_guide.md)
**Purpose**: Step-by-step instructions for end users

**Contents**:
- Getting started guide
- Detailed workflows for each module
- File preparation best practices
- Result interpretation guidance
- Troubleshooting common issues
- Tips and tricks for optimal results

**Audience**: End users, business analysts, legal professionals, procurement managers

**When to Read**: Before using the application or when encountering issues

---

### 5. [Deployment Guide](05_deployment_guide.md)
**Purpose**: Instructions for deploying in various environments

**Contents**:
- Local development setup
- Production deployment procedures
- Docker containerization
- Cloud deployment options (AWS, Azure, GCP, Heroku)
- Configuration management
- Security hardening
- Monitoring and maintenance
- Backup and disaster recovery
- Scaling strategies

**Audience**: DevOps engineers, system administrators, deployment teams

**When to Read**: When setting up new environments or deploying updates

---

## Quick Start Guide

### For Users

1. Read [System Overview](01_overview.md) to understand the application
2. Follow [User Guide - Getting Started](04_user_guide.md#getting-started)
3. Navigate to specific module instructions:
   - [Legal Case Matcher](04_user_guide.md#legal-case-matcher)
   - [Procurement Matcher](04_user_guide.md#procurement-matcher)
   - [Vendor Taxonomy](04_user_guide.md#vendor-taxonomy-classifier)

### For Developers

1. Review [Technical Architecture](02_technical_architecture.md)
2. Study [API Reference](03_api_reference.md)
3. Follow [Local Development Setup](05_deployment_guide.md#local-development-setup)
4. Refer to class and method documentation as needed

### For Deployment Engineers

1. Review [System Overview - Architecture](01_overview.md#system-architecture)
2. Follow [Deployment Guide](05_deployment_guide.md)
3. Choose deployment method:
   - [Local Development](05_deployment_guide.md#local-development-setup)
   - [Docker](05_deployment_guide.md#docker-deployment)
   - [AWS](05_deployment_guide.md#aws-deployment)
   - [Azure](05_deployment_guide.md#azure-deployment)
   - [GCP](05_deployment_guide.md#google-cloud-platform-deployment)
4. Implement [Security Hardening](05_deployment_guide.md#security-hardening)
5. Set up [Monitoring](05_deployment_guide.md#monitoring-and-maintenance)

---

## Key Concepts

### Application Modules

**Legal Profile Module** (`legal_profile.py`)
- Compares legal precedents with current cases
- Focuses on legal issues and reasoning patterns
- Returns confidence scores and justifications

**Procurement Module** (`procurement.py`)
- Matches vendor capabilities with requirements
- Analyzes feature and capability alignment
- Excludes commercial terms from evaluation

**Vendor Taxonomy Module** (`vendor_mapping.py`)
- Extracts structured taxonomy from text
- Categories: vendor info, services, compliance, geography, risk, sustainability
- Provides comprehensive vendor classification

### Core Technologies

- **Streamlit**: Web interface framework
- **LangChain**: LLM orchestration and prompt management
- **OpenAI GPT-4o-mini**: Language model for analysis
- **Pydantic**: Data validation and structured output
- **PyMuPDF**: PDF text extraction

### Data Flow

```
Input (PDF/TXT) → File Processing → Content Extraction →
Prompt Formation → LLM Analysis → JSON Parsing →
Validation → Display Results
```

---

## Common Tasks

### I want to...

**Use the application**
→ Read [User Guide - Getting Started](04_user_guide.md#getting-started)

**Understand how it works**
→ Read [System Overview](01_overview.md) and [Technical Architecture](02_technical_architecture.md)

**Extend functionality**
→ Read [Technical Architecture](02_technical_architecture.md) and [API Reference](03_api_reference.md)

**Deploy to production**
→ Read [Deployment Guide - Production Deployment](05_deployment_guide.md#production-deployment)

**Troubleshoot issues**
→ Read [User Guide - Troubleshooting](04_user_guide.md#troubleshooting)

**Integrate with other systems**
→ Read [API Reference](03_api_reference.md) and [Technical Architecture - Integration Points](02_technical_architecture.md#integration-points)

**Improve security**
→ Read [Deployment Guide - Security Hardening](05_deployment_guide.md#security-hardening)

**Scale the application**
→ Read [Deployment Guide - Scaling Considerations](05_deployment_guide.md#scaling-considerations)

**Monitor performance**
→ Read [Deployment Guide - Monitoring and Maintenance](05_deployment_guide.md#monitoring-and-maintenance)

---

## Prerequisites

### For Users
- Modern web browser
- PDF and TXT files for processing
- Basic understanding of domain (legal, procurement, or vendor analysis)

### For Developers
- Python 3.8+ (3.10+ recommended)
- Understanding of Python, LangChain, and Streamlit
- OpenAI API account and key

### For Deployment
- Python 3.8+ environment
- OpenAI API key
- Cloud account (AWS, Azure, or GCP) for cloud deployments
- Docker (for containerized deployments)

---

## System Requirements

### Minimum Requirements
- 2GB RAM
- 1GB disk space
- Python 3.8+
- Internet connectivity

### Recommended Requirements
- 4GB RAM
- 5GB disk space (for logs and data)
- Python 3.10+
- Stable internet connection
- SSD for faster file I/O

---

## File Formats

### Supported Input Formats

**PDF Files**:
- Text-based PDFs (not scanned images)
- Maximum size: 10MB (recommended)
- Used for: Vendor profiles, legal precedents

**TXT Files**:
- Plain text format
- UTF-8 encoding
- Used for: Requirements, current cases

### Output Formats

**Dataframe Display**:
- Interactive sortable tables
- CSV export capability

**JSON Structure** (internal):
- Pydantic-validated schemas
- Structured confidence scores and justifications

---

## Configuration Files

**config.yaml**:
- Application configuration
- LLM model settings
- Data path specifications

**.env**:
- Environment variables
- API keys (OPENAI_API_KEY)
- Sensitive configuration

**requirements.txt**:
- Python dependencies
- Version specifications

---

## Support and Resources

### Documentation Files

| File | Purpose | Audience |
|------|---------|----------|
| [01_overview.md](01_overview.md) | System overview | All users |
| [02_technical_architecture.md](02_technical_architecture.md) | Technical details | Developers |
| [03_api_reference.md](03_api_reference.md) | API documentation | Developers |
| [04_user_guide.md](04_user_guide.md) | User instructions | End users |
| [05_deployment_guide.md](05_deployment_guide.md) | Deployment procedures | DevOps |

### Additional Resources

**Application Logs**:
- Location: `./logs/`
- Info logs: `info_logs.json`
- Error logs: `error_logs.json`

**Configuration**:
- Main config: `config.yaml`
- Environment: `.env`

**Code Documentation**:
- See [API Reference](03_api_reference.md) for detailed code documentation
- Inline comments in source files

---

## Best Practices

### For Users
1. Prepare quality input files (clear, well-structured)
2. Review justifications, not just scores
3. Use batch sizes of 5-20 for optimal performance
4. Validate AI results with manual review

### For Developers
1. Follow existing code patterns
2. Maintain separation of concerns
3. Add comprehensive error handling
4. Document all changes
5. Test thoroughly before deployment

### For Deployment
1. Implement security measures first
2. Set up monitoring from day one
3. Regular backups are essential
4. Plan for scalability
5. Document environment-specific configurations

---

## Version Information

**Current Version**: 1.0 (Prototype)

**Last Updated**: December 2025

**Python Version**: 3.8+ (3.10+ recommended)

**Key Dependencies**:
- Streamlit >= 1.28.0
- LangChain >= 0.1.0
- OpenAI >= 1.3.0
- Pydantic >= 2.0.0

---

## Security Considerations

### Data Privacy
- Files processed are stored temporarily
- API calls to OpenAI include file content
- Implement data retention policies
- Consider on-premise LLM for sensitive data

### API Key Security
- Never commit API keys to version control
- Use environment variables or secrets management
- Rotate keys regularly
- Implement rate limiting

### Access Control
- No built-in authentication (prototype)
- Implement authentication for production
- Consider role-based access control
- Audit all access and operations

---

## Known Limitations

### Current Prototype Limitations
1. No user authentication
2. No persistent storage (session-based)
3. Synchronous processing only
4. Limited to OpenAI models
5. No batch API optimization
6. File size limits not enforced in code

### Recommended Enhancements
- Add user authentication and authorization
- Implement database for result persistence
- Add async processing for large batches
- Support multiple LLM providers
- Implement file validation and size limits
- Add export functionality (Excel, PDF reports)

---

## Troubleshooting Quick Reference

### Common Issues

**Can't start application**
→ Check Python version, install dependencies, verify config.yaml

**API errors**
→ Verify OPENAI_API_KEY in .env, check API quota

**PDF not reading**
→ Ensure PDF has selectable text, not password-protected

**Low confidence scores**
→ Improve requirement clarity, verify vendor match

**Slow processing**
→ Reduce batch size, check internet connection

For detailed troubleshooting, see [User Guide - Troubleshooting](04_user_guide.md#troubleshooting)

---

## Contributing

### For Internal Development

**Code Changes**:
1. Review [Technical Architecture](02_technical_architecture.md)
2. Study [API Reference](03_api_reference.md)
3. Follow existing patterns
4. Add tests for new features
5. Update documentation

**Documentation Updates**:
1. Keep documentation in sync with code
2. Update version information
3. Add examples for new features
4. Review for clarity and completeness

---

## Roadmap

### Planned Enhancements

**Short-term** (Next 3 months):
- User authentication
- File size validation
- Enhanced error messages
- Export functionality (CSV, Excel)

**Medium-term** (3-6 months):
- Database integration
- Async processing
- Advanced filtering
- Custom taxonomy management
- Multi-language support

**Long-term** (6-12 months):
- Integration APIs
- Advanced analytics
- Multi-LLM support
- Mobile interface
- Enterprise features

---

## Contact and Support

### For Issues

1. **Check Documentation**: Review relevant guide
2. **Check Logs**: View `./logs/error_logs.json`
3. **Check Configuration**: Verify `config.yaml` and `.env`
4. **Consult Troubleshooting**: See [User Guide - Troubleshooting](04_user_guide.md#troubleshooting)

### For Questions

- Technical questions: See [Technical Architecture](02_technical_architecture.md) or [API Reference](03_api_reference.md)
- Usage questions: See [User Guide](04_user_guide.md)
- Deployment questions: See [Deployment Guide](05_deployment_guide.md)

---

## License and Legal

This is a prototype application for internal evaluation. Ensure compliance with:
- OpenAI API Terms of Service
- Data protection regulations (GDPR, CCPA)
- Industry-specific compliance requirements
- Corporate security policies

---

## Acknowledgments

**Technologies Used**:
- Streamlit for web interface
- LangChain for LLM orchestration
- OpenAI for language models
- PyMuPDF for PDF processing
- Pydantic for data validation
- Loguru for logging

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | December 2025 | Initial documentation release |

---

## Navigation Tips

- Use table of contents at top of each document
- Cross-references link to relevant sections
- Code examples provided throughout
- Search for specific terms (Ctrl+F or Cmd+F)

---

**Happy Matching!**

For the best experience, start with the [System Overview](01_overview.md) to understand the application, then proceed to the guide most relevant to your role.
