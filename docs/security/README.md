# Security Documentation

Documentation for security features, encryption, and API key management.

---

## Documents

### Master Encryption Key

**`MASTER_ENCRYPTION_KEY_SETUP.md`**
- Quick setup and configuration guide
- Troubleshooting common issues
- Environment variable configuration
- Database schema verification
- Recent fixes (2025-11-20)
- **Status**: ✅ Fully operational

### API Key Management

**`API_KEY_MANAGEMENT_COMPLETE_GUIDE.md`** (1100+ lines)
- Complete end-to-end guide
- Version 2.0.0 (all fixes applied)
- Database-first with environment fallback
- Disaster recovery procedures
- Encryption/decryption workflows
- **Status**: ✅ Production ready

---

## Quick Links

- [Setup Encryption Key](./MASTER_ENCRYPTION_KEY_SETUP.md)
- [Complete API Key Guide](./API_KEY_MANAGEMENT_COMPLETE_GUIDE.md)
- [Back to Documentation Index](../DOCUMENTATION_INDEX.md)

---

## Recent Updates (2025-11-20)

### Fixes Applied
1. HTTP 422 Error on Ollama model pull
2. MASTER_ENCRYPTION_KEY configuration in docker-compose.yml
3. Database schema (meta_info column, api_key_encrypted type)
4. Complete fallback logic (database → environment)

### Features
- Fernet symmetric encryption (AES-128 CBC)
- Base64-encoded encrypted storage (TEXT type)
- Comprehensive logging with API key source indicators
- Resilient architecture with automatic fallback

---

**Last Updated**: 2025-11-20
