# Maintenance Scripts

Scripts for system maintenance, validation, and monitoring.

## Available Scripts

### Service Validation

#### `validate-services.sh`
Validate all services are running and healthy.
- Checks Docker containers
- Validates service endpoints
- Tests database connectivity
- Verifies LLM availability

```bash
./validate-services.sh
```

---

### Setup Verification

#### `verify-complete-setup.sh`
Verify complete system setup and configuration.
- Checks all services
- Validates database schema
- Tests document upload
- Validates RAG pipeline

```bash
./verify-complete-setup.sh
```

---

### Monitoring

#### `watch-upload-realtime.sh`
Monitor document uploads in real-time.
```bash
./watch-upload-realtime.sh
```

---

## 🔄 Regular Maintenance Tasks

### Daily
```bash
# Validate services
./validate-services.sh

# Check for errors
../debugging/check-backend-errors.sh
```

### Weekly
```bash
# Verify complete setup
./verify-complete-setup.sh

# Run integration tests
../testing/test-integration.sh
```

### Monthly
```bash
# Database maintenance
docker-compose exec postgres vacuumdb -U postgres -d ragchatbot --analyze

# Check disk usage
docker system df

# Review logs
docker-compose logs --tail=1000 > logs-$(date +%Y%m%d).txt
```

---

## 🔗 Related Documentation

- [../../docs/guides/ADMIN_GUIDE.md](../../docs/guides/ADMIN_GUIDE.md)
- [../../docs/debugging/](../../docs/debugging/)

---

**Last Updated**: 2025-11-16
