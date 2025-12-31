# BidRadar - Tender Intelligence Platform Documentation

Welcome to the comprehensive documentation for BidRadar, an AI-powered tender discovery and intelligence platform.

## Documentation Structure

This documentation suite consists of 5 comprehensive documents designed for different audiences and purposes:

### 📋 [01_PROJECT_OVERVIEW.md](./01_PROJECT_OVERVIEW.md)
**Audience**: Executives, Product Managers, Business Stakeholders

**Contents**:
- Executive summary and value propositions
- Platform capabilities and features
- Business model and use cases
- Key differentiators and performance metrics
- Data model and system architecture overview
- Deployment infrastructure
- Security and privacy considerations
- Future roadmap

**When to use**: Understanding what BidRadar is, why it was built, and the business value it provides.

---

### 🏗️ [02_TECHNICAL_ARCHITECTURE.md](./02_TECHNICAL_ARCHITECTURE.md)
**Audience**: Software Architects, Technical Leads, Senior Developers

**Contents**:
- Detailed system architecture
- Component design patterns
- Database schema and optimization strategies
- Machine learning pipeline architecture
- AI integration patterns
- Frontend architecture (Streamlit)
- Performance optimization techniques
- Error handling and logging strategies
- Testing approach

**When to use**: Understanding the technical design, architecture decisions, and implementation details.

---

### 👥 [03_USER_GUIDE.md](./03_USER_GUIDE.md)
**Audience**: End Users, Vendors, Business Development Teams

**Contents**:
- Getting started guide
- Dashboard and analytics features
- Smart search (natural language and advanced filters)
- AI Assistant usage and modes
- Tender recommendations system
- Vendor profile management
- Alert center and notifications
- Best practices and workflows
- Troubleshooting and FAQs

**When to use**: Learning how to use the platform effectively, from basic features to advanced workflows.

---

### 🚀 [04_DEPLOYMENT_GUIDE.md](./04_DEPLOYMENT_GUIDE.md)
**Audience**: DevOps Engineers, System Administrators, Infrastructure Teams

**Contents**:
- Prerequisites and system requirements
- Environment setup and dependency installation
- Configuration management
- Database initialization and migration
- Running in development and production modes
- Docker and container deployment
- Nginx reverse proxy configuration
- Monitoring and maintenance procedures
- Backup and recovery strategies
- Security hardening
- Scaling strategies (vertical and horizontal)

**When to use**: Deploying, configuring, and maintaining BidRadar in various environments.

---

### 💻 [05_API_DEVELOPER_REFERENCE.md](./05_API_DEVELOPER_REFERENCE.md)
**Audience**: Developers, Integration Engineers, Technical Contributors

**Contents**:
- Complete API reference for all components
- Database API (CRUD operations, queries, analytics)
- Machine Learning API (recommendations, clustering, insights)
- AI Assistant API (chat, document analysis, market intelligence)
- Web Scraper API (data extraction, processing)
- Data Processor API (semantic enhancement, feature engineering)
- Frontend integration patterns
- Extension points for customization
- Code examples and workflows
- Testing strategies
- Contributing guidelines

**When to use**: Developing new features, integrating with BidRadar, or extending functionality.

---

## Quick Navigation

### I want to...

**...understand what BidRadar does**
→ Start with [Project Overview](./01_PROJECT_OVERVIEW.md)

**...learn how to use BidRadar**
→ Read the [User Guide](./03_USER_GUIDE.md)

**...deploy BidRadar to production**
→ Follow the [Deployment Guide](./04_DEPLOYMENT_GUIDE.md)

**...understand the technical architecture**
→ Study the [Technical Architecture](./02_TECHNICAL_ARCHITECTURE.md)

**...develop new features or integrate**
→ Reference the [API Developer Guide](./05_API_DEVELOPER_REFERENCE.md)

**...troubleshoot an issue**
→ Check relevant troubleshooting sections in [User Guide](./03_USER_GUIDE.md) or [Deployment Guide](./04_DEPLOYMENT_GUIDE.md)

---

## Platform Overview

**BidRadar** is an AI-powered tender intelligence platform that helps businesses discover, analyze, and track procurement opportunities in the UK public sector.

### Key Features

- **🔍 Smart Search**: Natural language queries and advanced filtering
- **🎯 Personalized Recommendations**: ML-powered tender matching
- **🤖 AI Assistant**: Conversational AI for analysis and guidance
- **📊 Analytics Dashboard**: Real-time market intelligence
- **🔔 Automated Alerts**: Never miss relevant opportunities
- **📄 Document Analysis**: AI-powered tender document insights

### Technology Stack

- **Frontend**: Streamlit (Python)
- **Backend**: Python 3.11+
- **Database**: SQLite (development) / PostgreSQL (production)
- **ML/AI**: scikit-learn, spaCy, OpenAI GPT-4o
- **Web Scraping**: BeautifulSoup, trafilatura
- **Visualization**: Plotly

---

## Getting Started

### For Users

1. Read the [Getting Started](./03_USER_GUIDE.md#getting-started) section
2. Learn about [Dashboard features](./03_USER_GUIDE.md#dashboard-analytics)
3. Try [Smart Search](./03_USER_GUIDE.md#smart-search)
4. Set up your [Vendor Profile](./03_USER_GUIDE.md#vendor-profile-management)
5. Explore [Best Practices](./03_USER_GUIDE.md#best-practices)

### For Developers

1. Review [Architecture Overview](./02_TECHNICAL_ARCHITECTURE.md#system-architecture-overview)
2. Study [Component Design](./02_TECHNICAL_ARCHITECTURE.md#component-design)
3. Reference [API Documentation](./05_API_DEVELOPER_REFERENCE.md#core-components-api)
4. Check [Code Examples](./05_API_DEVELOPER_REFERENCE.md#code-examples)
5. Follow [Contributing Guidelines](./05_API_DEVELOPER_REFERENCE.md#contributing-guidelines)

### For Operations

1. Check [Prerequisites](./04_DEPLOYMENT_GUIDE.md#prerequisites)
2. Follow [Installation](./04_DEPLOYMENT_GUIDE.md#installation) steps
3. Configure [Environment](./04_DEPLOYMENT_GUIDE.md#configuration)
4. Set up [Monitoring](./04_DEPLOYMENT_GUIDE.md#monitoring-maintenance)
5. Plan [Backups](./04_DEPLOYMENT_GUIDE.md#backup-recovery)

---

## Common Tasks

### Running the Application (Development)

```bash
# Activate virtual environment
source venv/bin/activate

# Run application
streamlit run app.py

# Access at http://localhost:8501
```

### Scraping New Tenders

```python
from utils.web_scraper import TenderScraper
from utils.data_processor import DataProcessor
from utils.database import Database

scraper = TenderScraper()
processor = DataProcessor()
db = Database()

# Scrape and process
tenders = scraper.scrape_lupc_tenders()
processed = processor.process_tender_batch(tenders)
db.store_tenders(processed)
```

### Getting Recommendations

```python
from utils.database import Database
from utils.ml_engine import MLEngine

db = Database()
ml_engine = MLEngine()

# Get vendor profile
vendor = db.get_vendor_by_name("Your Company")

# Generate recommendations
recommendations = ml_engine.get_recommendations(vendor, limit=10)

# View top matches
for rec in recommendations[:5]:
    print(f"{rec['title']}: {rec['match_score']:.1%}")
```

---

## Support & Resources

### Documentation

- **Project Overview**: Business context and capabilities
- **Technical Architecture**: System design and implementation
- **User Guide**: How to use the platform
- **Deployment Guide**: Infrastructure and operations
- **API Reference**: Developer documentation

### Additional Resources

- **Source Code**: `/mnt/d/Data/Projects/KIAA/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/meritsoftwareservice-merit-aiml-prototypes-eee5b0412c06/tender_intelligence/`
- **Demo Data**: `create_demo_data.py`
- **Database Schema**: See [Database API](./05_API_DEVELOPER_REFERENCE.md#database-api)

### Getting Help

1. **Check Documentation**: Search relevant documents above
2. **Review Examples**: See [Code Examples](./05_API_DEVELOPER_REFERENCE.md#code-examples)
3. **Troubleshooting**: Check troubleshooting sections in User Guide and Deployment Guide
4. **Contact Support**: Reach out to the development team

---

## Document Versions

| Document | Version | Last Updated | Status |
|----------|---------|--------------|--------|
| Project Overview | 1.0 | December 2025 | Current |
| Technical Architecture | 1.0 | December 2025 | Current |
| User Guide | 1.0 | December 2025 | Current |
| Deployment Guide | 1.0 | December 2025 | Current |
| API Developer Reference | 1.0 | December 2025 | Current |

### Change History

**v1.0 (December 2025)**
- Initial comprehensive documentation release
- All 5 documents published
- Complete platform coverage

---

## Contributing to Documentation

Documentation improvements are welcome! When updating documentation:

1. **Maintain Structure**: Keep the 5-document organization
2. **Update All Affected Docs**: Changes may impact multiple documents
3. **Version Control**: Update version numbers and change history
4. **Review Cycle**: Quarterly reviews scheduled
5. **Audience Focus**: Ensure content matches intended audience

### Documentation Standards

- **Clear Headings**: Use hierarchical structure
- **Code Examples**: Include working examples
- **Cross-References**: Link between documents
- **Screenshots**: Use when helpful (not included in text-only version)
- **Consistency**: Maintain terminology and formatting

---

## License & Copyright

**Copyright** © 2025 Merit Software Services
**Status**: Internal Use / Prototype

---

## Contact

**Development Team**: AI/ML Prototyping Team
**Last Updated**: December 2025
**Next Review**: March 2026

---

## Quick Reference Card

### Essential Commands

```bash
# Start application
streamlit run app.py

# Run tests
python -m pytest tests/

# Create demo data
python create_demo_data.py

# Database shell
sqlite3 tender_platform.db

# View logs
tail -f tender_platform.log
```

### Key Concepts

- **Tender**: Procurement opportunity
- **Vendor**: Supplier/business looking for opportunities
- **Match Score**: 0-1 score indicating tender-vendor fit
- **Semantic Tags**: AI-identified categories
- **Urgency Score**: Time-based priority (0-1)
- **Complexity Score**: Tender difficulty (0-1)

### File Locations

- **Application**: `app.py`
- **Database**: `tender_platform.db`
- **Utilities**: `utils/`
- **Pages**: `pages/`
- **Configuration**: `.streamlit/config.toml`, `.env`
- **Logs**: `tender_platform.log`

---

**Happy Building with BidRadar!** 🎯
