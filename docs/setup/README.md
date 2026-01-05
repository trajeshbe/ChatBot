# Database Setup Documentation

> **Purpose**: Central hub for all database setup and installation documentation

---

## Quick Links

| Document | Purpose | Audience |
|----------|---------|----------|
| **[DATABASE_SETUP_GUIDE.md](./DATABASE_SETUP_GUIDE.md)** | Complete setup guide | All users |
| **[DATABASE_QUICK_REFERENCE.md](./DATABASE_QUICK_REFERENCE.md)** | Command cheat sheet | Daily operations |
| **[../../DB_SETUP_IMPLEMENTATION_SUMMARY.md](../../DB_SETUP_IMPLEMENTATION_SUMMARY.md)** | Implementation summary | Developers |

---

## For New Users

### Fresh Installation

```bash
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot
./scripts/setup/initialize-fresh-install.sh
```

**Read**: [DATABASE_SETUP_GUIDE.md](./DATABASE_SETUP_GUIDE.md)

### Database Only

```bash
docker-compose up -d postgres
sleep 10
./scripts/setup/setup-database-complete.sh
```

### Quick Reference

For daily database operations, see [DATABASE_QUICK_REFERENCE.md](./DATABASE_QUICK_REFERENCE.md)

---

## Default Credentials

```
Username: admin
Password: admin123
```

**Change this password immediately in production!**

---

**Last Updated**: 2026-01-05
