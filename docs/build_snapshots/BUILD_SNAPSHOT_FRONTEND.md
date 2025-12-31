# Frontend Build Snapshot

**Generated**: 2025-11-25
**Purpose**: Complete snapshot of all dependencies and versions used in frontend build for reproducibility

---

## 🐳 Docker Base Image

```dockerfile
FROM node:20-alpine AS base
```

### Base Image Details
- **Image**: `node:20-alpine`
- **Node.js Version**: 20.x LTS
- **Base OS**: Alpine Linux (lightweight)
- **Package Manager**: npm (included with Node.js)
- **Alpine Version**: Latest compatible with Node 20

### Multi-Stage Build
The Dockerfile uses multi-stage builds for optimization:
1. **base**: Base Node.js 20 Alpine image
2. **deps**: Install dependencies only
3. **builder**: Build production artifacts
4. **runner**: Minimal production runtime

---

## 📦 Node.js & npm Versions

```bash
Node.js: 20.x LTS (from node:20-alpine)
npm: 10.x (bundled with Node 20)
```

---

## 🔧 Alpine System Packages

```bash
libc6-compat    # glibc compatibility layer for Alpine
```

Installed via `apk add --no-cache libc6-compat` to ensure compatibility with Node.js native modules.

---

## 📚 Production Dependencies

### Core Framework
```json
"next": "14.1.0"
"react": "^18.2.0"
"react-dom": "^18.2.0"
```

### GraphQL & API
```json
"graphql": "^16.8.1"
"graphql-request": "^6.1.0"
"axios": "^1.6.7"
```

### UI Components & Rendering
```json
"react-markdown": "^9.0.1"
"react-syntax-highlighter": "^15.5.0"
"react-dropzone": "^14.2.3"
"lucide-react": "^0.316.0"
```

### Utilities
```json
"date-fns": "^3.3.1"
"clsx": "^2.1.0"
"tailwind-merge": "^2.2.1"
```

---

## 🛠️ Development Dependencies

### TypeScript
```json
"typescript": "^5.3.3"
"@types/node": "^20.11.17"
"@types/react": "^18.2.55"
"@types/react-dom": "^18.2.19"
```

### Styling (Tailwind CSS)
```json
"tailwindcss": "^3.4.1"
"@tailwindcss/typography": "^0.5.10"
"autoprefixer": "^10.4.17"
"postcss": "^8.4.35"
```

### Linting
```json
"eslint": "^8.56.0"
"eslint-config-next": "14.1.0"
```

---

## 📦 Complete npm Package Tree

### Resolved Versions (from package-lock.json)

When you run `npm ci`, these exact versions will be installed:

#### Production Dependencies

**Next.js & React Ecosystem:**
- `next@14.1.0`
- `react@18.2.0`
- `react-dom@18.2.0`
- `@next/swc-*` (platform-specific binaries)
- `styled-jsx@5.1.1` (CSS-in-JS for Next.js)
- `client-only@0.0.1`
- `server-only@0.0.1`

**GraphQL:**
- `graphql@16.8.1`
- `graphql-request@6.1.0`
- `@graphql-typed-document-node/core@3.2.0`

**HTTP Client:**
- `axios@1.6.7`
- `follow-redirects@1.15.5`
- `form-data@4.0.0`
- `proxy-from-env@1.1.0`

**Markdown & Syntax Highlighting:**
- `react-markdown@9.0.1`
- `react-syntax-highlighter@15.5.0`
- `@types/hast@3.0.4`
- `@types/mdast@4.0.3`
- `@types/unist@3.0.2`
- `hast-util-*` (multiple packages)
- `mdast-util-*` (multiple packages)
- `micromark-*` (multiple packages)
- `remark-parse@11.0.0`
- `remark-rehype@11.1.0`
- `unified@11.0.4`
- `refractor@4.8.1`
- `prismjs@1.29.0`

**File Upload:**
- `react-dropzone@14.2.3`
- `attr-accept@2.2.2`
- `file-selector@0.6.0`

**Icons:**
- `lucide-react@0.316.0`

**Utilities:**
- `date-fns@3.3.1`
- `clsx@2.1.0`
- `tailwind-merge@2.2.1`

#### Development Dependencies

**TypeScript:**
- `typescript@5.3.3`
- `@types/node@20.11.17`
- `@types/react@18.2.55`
- `@types/react-dom@18.2.19`
- Plus many `@types/*` packages for dependencies

**Tailwind CSS:**
- `tailwindcss@3.4.1`
- `@tailwindcss/typography@0.5.10`
- `autoprefixer@10.4.17`
- `postcss@8.4.35`
- `postcss-import@15.1.0`
- `postcss-js@4.0.1`
- `postcss-load-config@4.0.2`
- `postcss-nested@6.0.1`

**Linting:**
- `eslint@8.56.0`
- `eslint-config-next@14.1.0`
- Plus 100+ eslint plugins and dependencies

**Build Tools:**
- `@swc/helpers@0.5.2`
- `busboy@1.6.0`
- `caniuse-lite@1.0.30001584`
- `nanoid@3.3.7`
- `picocolors@1.0.0`
- `source-map-js@1.0.2`

---

## 🔍 How to Reproduce This Build

### Method 1: Using Exact package-lock.json
```bash
# Ensure package-lock.json is present and unchanged
npm ci  # This installs EXACT versions from package-lock.json
```

### Method 2: Docker Build (Recommended)
```bash
# Build with no cache to ensure fresh dependencies
docker-compose build --no-cache frontend
```

### Method 3: Generate Fresh Snapshot (After Build)
```bash
# After build completes, capture exact versions:
docker-compose exec frontend npm list --all > frontend/npm-list-snapshot.txt
docker-compose exec frontend npm list --json > frontend/npm-list-snapshot.json
```

---

## 📝 Build Commands

### Development Build
```bash
npm run dev          # Start development server
```

### Production Build
```bash
npm run build        # Build for production
npm start            # Start production server
```

### Docker Build
```bash
docker-compose build --no-cache frontend
```

**Dockerfile Location**: `frontend/Dockerfile`
**Package Files**:
- `frontend/package.json`
- `frontend/package-lock.json`

---

## 🎯 Key Notes for Reproducibility

1. **Node Version Pinning**: Use `node:20-alpine` for consistent Node.js version
2. **package-lock.json**: CRITICAL - Always commit this file. It locks exact versions of all dependencies (including transitive)
3. **npm ci vs npm install**:
   - Use `npm ci` for exact reproducibility (installs from lock file)
   - Use `npm install` only when updating dependencies
4. **Alpine Linux**: Lightweight but may need `libc6-compat` for some native modules
5. **Multi-Stage Build**: Optimizes final image size (~200MB vs ~1GB)
6. **Next.js Version**: 14.1.0 - App Router architecture
7. **React Version**: 18.2.0 - Server Components support

---

## 🏗️ Build Stages Breakdown

### Stage 1: deps (Dependencies)
```dockerfile
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
```
- Installs exact dependencies from package-lock.json
- Cached separately for faster rebuilds

### Stage 2: builder (Build Artifacts)
```dockerfile
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build
```
- Builds optimized production bundle
- Generates `.next/` directory with:
  - Server-side code
  - Client-side JavaScript
  - Static assets
  - Next.js standalone server

### Stage 3: runner (Production Runtime)
```dockerfile
FROM base AS runner
WORKDIR /app
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```
- Minimal production image
- Non-root user for security
- Only production files included

---

## 🚨 Known Compatibility Notes

### Next.js 14 Requirements
- ✅ Node.js 18.17 or later (we use Node 20)
- ✅ React 18.2 or later
- ✅ TypeScript 5.x for type safety

### Alpine Linux Compatibility
- ✅ `libc6-compat` required for native Node modules
- ✅ All dependencies work with Alpine
- ⚠️ If you add new native dependencies, test on Alpine

### Browser Support
- Modern browsers (ES6+)
- Chrome, Firefox, Safari, Edge (latest 2 versions)
- Mobile browsers supported

---

## 📊 Build Statistics

- **Total npm Packages**: ~1,000+ (including all transitive dependencies)
- **Build Time (Docker)**:
  - With cache: ~2-3 minutes
  - No cache: ~5-10 minutes
- **Final Image Size**:
  - Builder stage: ~800MB
  - Production runner: ~200MB (multi-stage optimization)
- **Node.js Bundle Size**: ~50-100MB (optimized)

---

## 🔄 Update History

| Date | Change | Reason |
|------|--------|--------|
| 2025-11-25 | Initial snapshot created | Ensure reproducible builds |
| 2025-11-25 | Tool tracking UI fix | Backward compatible tool display |

---

## 🔐 Security Considerations

1. **Non-root User**: Production runs as `nextjs` user (UID 1001)
2. **Minimal Image**: Only production files in final stage
3. **No Dev Dependencies**: Dev deps removed in production build
4. **Telemetry Disabled**: Next.js telemetry opt-out
5. **Dependency Audit**: Run `npm audit` regularly

```bash
# Check for known vulnerabilities
npm audit

# Auto-fix where possible
npm audit fix
```

---

## 📝 Package Lock File

The `package-lock.json` file is **CRITICAL** for reproducibility. It contains:
- Exact version of every package
- Exact version of every transitive dependency
- SHA-512 integrity hashes for verification
- Resolved URLs for each package

**Size**: ~500KB
**Packages**: ~1,000+ entries

To verify integrity:
```bash
npm ci --audit --dry-run  # Verify without installing
```

---

## 🔄 Updating Dependencies

### Safe Update Process
```bash
# 1. Update specific package
npm update <package-name>

# 2. Update all minor/patch versions
npm update

# 3. Update to latest (including breaking changes)
npm install <package-name>@latest

# 4. Always test after updates
npm run build
npm test

# 5. Commit updated package-lock.json
git add package-lock.json
git commit -m "chore: update frontend dependencies"
```

---

**To update this snapshot after dependency changes:**
```bash
# After successful build:
docker-compose exec frontend npm list --all > frontend/npm-list-snapshot.txt
# Then manually update this document with new major version changes
```

---

## 📚 Additional Resources

- [Next.js 14 Documentation](https://nextjs.org/docs)
- [React 18 Documentation](https://react.dev)
- [Node.js 20 Release Notes](https://nodejs.org/en/blog/release/v20.0.0)
- [npm ci Documentation](https://docs.npmjs.com/cli/v10/commands/npm-ci)
- [Alpine Linux Package Manager](https://wiki.alpinelinux.org/wiki/Alpine_Package_Keeper)
