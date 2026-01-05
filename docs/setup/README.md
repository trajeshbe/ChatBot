# Database & Installation Documentation

> **Purpose**: Central hub for all setup and installation documentation

---

## 🚀 Quick Start - I'm New Here!

**Want to install from scratch on a new machine?**

👉 **Start here**: [FRESH_INSTALLATION_GUIDE.md](./FRESH_INSTALLATION_GUIDE.md)

This comprehensive guide walks you through:
- Prerequisites and system requirements
- Step-by-step installation (with screenshots)
- Configuration and first-time setup
- Common issues and solutions
- Post-installation verification

**Time Required**: 30-45 minutes

---

## 📚 Documentation Index

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[FRESH_INSTALLATION_GUIDE.md](./FRESH_INSTALLATION_GUIDE.md)** | Complete installation from scratch | New machine setup |
| **[DATABASE_SETUP_GUIDE.md](./DATABASE_SETUP_GUIDE.md)** | Database initialization details | Database-specific setup |
| **[DATABASE_QUICK_REFERENCE.md](./DATABASE_QUICK_REFERENCE.md)** | Command cheat sheet | Daily operations |
| **[../../DB_SETUP_IMPLEMENTATION_SUMMARY.md](../../DB_SETUP_IMPLEMENTATION_SUMMARY.md)** | Technical implementation | Developers |

---

## 🎯 Quick Navigation

### I Want To...

**Install the app for the first time**
→ [FRESH_INSTALLATION_GUIDE.md](./FRESH_INSTALLATION_GUIDE.md)

**Just setup the database**
→ [DATABASE_SETUP_GUIDE.md - Quick Start](./DATABASE_SETUP_GUIDE.md#quick-start)

**Find a specific command**
→ [DATABASE_QUICK_REFERENCE.md](./DATABASE_QUICK_REFERENCE.md)

**Troubleshoot an issue**
→ [FRESH_INSTALLATION_GUIDE.md - Troubleshooting](./FRESH_INSTALLATION_GUIDE.md#troubleshooting)

**Understand the architecture**
→ [DATABASE_SETUP_GUIDE.md - Architecture](./DATABASE_SETUP_GUIDE.md#database-architecture)

---

## ⚡ Quick Commands

### Complete Fresh Installation

```bash
# One-command installation
./scripts/setup/initialize-fresh-install.sh
```

### Database Only

```bash
# Start PostgreSQL
docker-compose up -d postgres
sleep 10

# Initialize database
./scripts/setup/setup-database-complete.sh
```

### Reset Everything

```bash
# Complete clean installation (⚠️  deletes all data)
./scripts/setup/initialize-fresh-install.sh --clean
```

---

## 📖 Documentation Guide

### For First-Time Users

1. **Read**: [FRESH_INSTALLATION_GUIDE.md](./FRESH_INSTALLATION_GUIDE.md)
   - Complete step-by-step instructions
   - Prerequisites and requirements
   - Configuration guide
   - First-time usage
   - Troubleshooting

2. **Bookmark**: [DATABASE_QUICK_REFERENCE.md](./DATABASE_QUICK_REFERENCE.md)
   - Quick commands for daily use
   - Database queries
   - Maintenance operations

### For Experienced Users

1. **Quick Setup**: Run `./scripts/setup/initialize-fresh-install.sh`
2. **Reference**: [DATABASE_QUICK_REFERENCE.md](./DATABASE_QUICK_REFERENCE.md)
3. **Deep Dive**: [DATABASE_SETUP_GUIDE.md](./DATABASE_SETUP_GUIDE.md)

### For Developers

1. **Implementation**: [DB_SETUP_IMPLEMENTATION_SUMMARY.md](../../DB_SETUP_IMPLEMENTATION_SUMMARY.md)
2. **Architecture**: [DATABASE_SETUP_GUIDE.md - Architecture](./DATABASE_SETUP_GUIDE.md#database-architecture)
3. **Scripts**: Review `scripts/setup/` directory

---

## 🔐 Default Credentials

After installation:

```
URL:      http://localhost:3001
Username: admin
Password: admin123
```

**⚠️  CRITICAL**: Change this password immediately!

---

## 🆘 Getting Help

### Quick Diagnostics

```bash
# Check all services
./scripts/maintenance/validate-services.sh

# Diagnose backend
./scripts/debugging/diagnose-backend.sh

# Check database
docker exec rag-postgres psql -U postgres -d ragchatbot -c "SELECT COUNT(*) FROM users;"
```

### Documentation

- **Installation Issues**: [FRESH_INSTALLATION_GUIDE.md - Troubleshooting](./FRESH_INSTALLATION_GUIDE.md#troubleshooting)
- **Database Issues**: [DATABASE_SETUP_GUIDE.md - Troubleshooting](./DATABASE_SETUP_GUIDE.md#troubleshooting)
- **Quick Commands**: [DATABASE_QUICK_REFERENCE.md](./DATABASE_QUICK_REFERENCE.md)

### Common Issues

| Issue | Quick Fix |
|-------|-----------|
| Services won't start | `docker-compose down && docker-compose up -d` |
| Database connection error | `docker-compose restart postgres && sleep 10` |
| Frontend can't connect | `docker-compose restart backend frontend` |
| Out of memory | Increase Docker memory to 8+ GB |

---

## 📊 What Gets Installed

### Services

- ✅ Backend API (FastAPI)
- ✅ Frontend (Next.js)
- ✅ PostgreSQL (with pgvector)
- ✅ Redis (caching)
- ✅ MinIO (object storage)
- ⭕ Ollama (optional, local LLM)

### Database

- ✅ 90+ tables
- ✅ 7 departments, 33 teams
- ✅ 5 roles with RBAC
- ✅ Vector search enabled
- ✅ Audit logging
- ✅ Default admin user

### Features

- ✅ RAG Chat with document Q&A
- ✅ File upload (PDF, DOCX, TXT, JSON)
- ✅ Web scraping
- ✅ Data extraction
- ✅ Module management
- ✅ User management
- ✅ Analytics & metrics

---

## 🎓 Learning Path

### Beginner

1. Follow [FRESH_INSTALLATION_GUIDE.md](./FRESH_INSTALLATION_GUIDE.md)
2. Complete first-time usage section
3. Upload a test document
4. Ask your first question

### Intermediate

1. Explore all modules in UI
2. Learn database operations from [DATABASE_QUICK_REFERENCE.md](./DATABASE_QUICK_REFERENCE.md)
3. Configure organizational structure
4. Set up additional users

### Advanced

1. Study [DATABASE_SETUP_GUIDE.md](./DATABASE_SETUP_GUIDE.md)
2. Review database architecture
3. Customize configurations
4. Set up monitoring and backups

---

## 🔄 Maintenance

### Daily

```bash
# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f backend
```

### Weekly

```bash
# Backup database
docker exec rag-postgres pg_dump -U postgres ragchatbot > backup_$(date +%Y%m%d).sql

# Clean Docker
docker system prune -f
```

### Monthly

```bash
# Update images
docker-compose pull
docker-compose down
docker-compose up -d

# Vacuum database
docker exec rag-postgres psql -U postgres -d ragchatbot -c "VACUUM ANALYZE;"
```

---

## 📦 Files in This Directory

```
docs/setup/
├── README.md                      # This file - central hub
├── FRESH_INSTALLATION_GUIDE.md    # NEW! Complete installation guide
├── DATABASE_SETUP_GUIDE.md        # Database initialization details
└── DATABASE_QUICK_REFERENCE.md    # Command reference
```

---

## 🌟 Success Checklist

After installation, you should be able to:

- [ ] Access frontend at http://localhost:3001
- [ ] Log in with default credentials
- [ ] Upload a document
- [ ] Create a chat session
- [ ] Ask questions about your document
- [ ] View API documentation
- [ ] Access MinIO console
- [ ] Run database queries

---

## 📞 Support

**Documentation**:
- Project: `../../README.md`
- Architecture: `../../CLAUDE.md`
- Status: `../../STATUS.md`

**Scripts**:
- Setup: `../../scripts/setup/`
- Maintenance: `../../scripts/maintenance/`
- Debugging: `../../scripts/debugging/`

**Need Help?**
1. Check troubleshooting sections in guides
2. Run diagnostic scripts
3. Review logs
4. Check GitHub issues

---

**Last Updated**: 2026-01-05
**Documentation Version**: 2.0
**Maintainer**: Enterprise RAG Team
