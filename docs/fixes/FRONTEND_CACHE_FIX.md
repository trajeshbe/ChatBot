# Fix: Next.js Webpack Cache Errors in Docker

## Problem

You're seeing this error in the frontend logs:

```
ENOENT: no such file or directory, rename '/app/.next/cache/webpack/client-development-fallback/0.pack.gz_' -> '/app/.next/cache/webpack/client-development-fallback/0.pack.gz'
```

**Root Cause**: Next.js webpack cache has file permission or volume mounting issues in Docker development mode.

**Impact**:
- Fast Refresh does full page reloads instead of hot module replacement
- Slower development experience
- Error messages clutter logs

---

## Solution 1: Quick Fix (Recommended - Already Applied)

I've already updated your `docker-compose.yml` to use a named volume for the Next.js cache:

```yaml
frontend:
  volumes:
    - ./frontend:/app
    - /app/node_modules
    - frontend_nextjs_cache:/app/.next  # Named volume instead of anonymous
```

### Apply the Fix

Run this script to clear cache and restart with the new configuration:

```bash
./fix-frontend-cache.sh
```

**What it does:**
1. Stops the frontend container
2. Removes old containers and orphaned volumes
3. Rebuilds frontend with fresh cache
4. Restarts the container

**Expected Result**: No more webpack cache errors!

---

## Solution 2: Disable Webpack Cache (Alternative)

If the named volume still has issues, you can disable webpack caching entirely in development:

### Option A: Use the Alternative Config

```bash
# Backup current config
cp frontend/next.config.js frontend/next.config.js.bak

# Use the dev config (disables webpack cache)
cp frontend/next.config.dev.js frontend/next.config.js

# Rebuild frontend
docker compose build frontend
docker compose up -d frontend
```

### Option B: Manual Edit

Edit `frontend/next.config.js` and add:

```javascript
module.exports = {
  // ... existing config ...
  webpack: (config, { dev, isServer }) => {
    if (dev) {
      config.cache = false;
    }
    return config;
  },
}
```

---

## Solution 3: Clean Slate (Nuclear Option)

If nothing else works, completely reset the frontend:

```bash
# Stop and remove everything
docker compose down -v frontend

# Remove frontend images
docker rmi rag-frontend

# Remove all Next.js cache from host
rm -rf frontend/.next
rm -rf frontend/node_modules

# Rebuild from scratch
docker compose build frontend --no-cache
docker compose up -d frontend
```

---

## Verification

After applying any solution, verify it worked:

```bash
# Watch logs for errors
docker compose logs -f frontend

# You should NOT see:
# ❌ ENOENT: no such file or directory, rename
# ❌ [webpack.cache.PackFileCacheStrategy] Caching failed

# You should see:
# ✅ Ready on http://localhost:3000
# ✅ Fast Refresh enabled (with hot updates working)
```

---

## Why This Happens

Docker volume mounting can cause issues with webpack's cache because:

1. **File System Differences**: Host OS (Windows/Mac) vs. Container OS (Linux)
2. **Permission Mismatches**: Container user vs. volume owner
3. **Anonymous Volumes**: Race conditions with temp file renaming
4. **inotify Limitations**: File watching doesn't work well across Docker volumes

## What Changed

### Before (Problematic):
```yaml
volumes:
  - ./frontend:/app
  - /app/node_modules
  - /app/.next  # Anonymous volume - causes issues
```

### After (Fixed):
```yaml
volumes:
  - ./frontend:/app
  - /app/node_modules
  - frontend_nextjs_cache:/app/.next  # Named volume - stable
```

**Named volumes** have proper ownership and permissions managed by Docker, avoiding temp file rename conflicts.

---

## Trade-offs

### Named Volume (Solution 1)
✅ **Pros**:
- Caching works properly
- Faster builds
- Hot Module Replacement works

❌ **Cons**:
- Cache persists between restarts (may need occasional clearing)
- Slightly more complex setup

### Disabled Cache (Solution 2)
✅ **Pros**:
- No volume issues
- Simpler setup
- Always fresh builds

❌ **Cons**:
- Slower builds (no caching)
- Slightly longer startup time

---

## Recommendation

**Use Solution 1** (named volume) - already applied in your `docker-compose.yml`.

Only use Solution 2 (disabled cache) if:
- You continue to see errors with the named volume
- Build speed isn't critical for your workflow
- You want the absolute simplest setup

---

## Additional Resources

- [Next.js Docker Best Practices](https://nextjs.org/docs/deployment#docker-image)
- [Docker Volume Documentation](https://docs.docker.com/storage/volumes/)
- [Webpack Cache Documentation](https://webpack.js.org/configuration/cache/)

---

## Status

✅ **Fixed**: Updated `docker-compose.yml` with named volume for `.next` cache
✅ **Script Created**: `./fix-frontend-cache.sh` to apply the fix
✅ **Alternative Created**: `frontend/next.config.dev.js` with cache disabled

**Next Step**: Run `./fix-frontend-cache.sh` to apply the changes!
