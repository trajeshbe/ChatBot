# Enterprise Git Repository Strategy

> **Enterprise RAG Chatbot - Git Workflow & Release Management**
>
> **Purpose**: Establish enterprise-grade version control, branching strategy, and release management for AI/ML GenAI application
>
> **Date**: 2026-01-05
> **Version**: 1.0

---

## Table of Contents

1. [Overview](#overview)
2. [Repository Structure](#repository-structure)
3. [Branching Strategy](#branching-strategy)
4. [Workflow Process](#workflow-process)
5. [Release Management](#release-management)
6. [Commit Conventions](#commit-conventions)
7. [Pull Request Process](#pull-request-process)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Version Tagging](#version-tagging)
10. [Change & Release Notes](#change--release-notes)
11. [Repository Setup](#repository-setup)
12. [Team Workflow](#team-workflow)
13. [Best Practices](#best-practices)

---

## Overview

### Objectives

1. **Stability**: Maintain production-ready main branch
2. **Traceability**: Complete audit trail of all changes
3. **Quality**: Automated testing and code review
4. **Compliance**: Enterprise security and governance
5. **Velocity**: Enable rapid feature development
6. **Reliability**: Controlled releases with rollback capability

### Branching Model

We'll use **Git Flow** with enterprise enhancements:

```
main (production)
  ↑
release/v1.x.x (release candidate)
  ↑
develop (integration)
  ↑
feature/* (feature development)
hotfix/* (emergency fixes)
```

---

## Repository Structure

### Initial Repository Setup

```
enterprise-rag-chatbot/
├── .github/
│   ├── workflows/                 # GitHub Actions CI/CD
│   │   ├── ci-develop.yml        # CI for develop branch
│   │   ├── ci-release.yml        # CI for release branches
│   │   ├── deploy-staging.yml    # Deploy to staging
│   │   ├── deploy-production.yml # Deploy to production
│   │   └── security-scan.yml     # Security scanning
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── security_issue.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── CODEOWNERS               # Code ownership
│
├── docs/
│   ├── architecture/            # Architecture documentation
│   ├── setup/                   # Installation guides
│   ├── api/                     # API documentation
│   ├── deployment/              # Deployment guides
│   ├── changelog/               # Version changelogs
│   │   ├── CHANGELOG.md        # Master changelog
│   │   ├── v1.0.0.md
│   │   └── v1.1.0.md
│   └── releases/               # Release notes
│       ├── v1.0.0-RELEASE.md
│       └── v1.1.0-RELEASE.md
│
├── .git/                       # Git metadata
├── .gitignore                  # Git ignore rules
├── .gitattributes              # Git attributes
├── README.md                   # Project overview
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # License file
├── SECURITY.md                 # Security policy
├── CODE_OF_CONDUCT.md         # Code of conduct
└── VERSION                     # Current version file
```

---

## Branching Strategy

### Branch Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    main (production)                         │
│  - Always production-ready                                   │
│  - Tagged with version numbers (v1.0.0, v1.1.0)             │
│  - Only accepts merges from release/* and hotfix/*          │
└─────────────────────────────────────────────────────────────┘
                            ↑
                            │ (merge via PR)
                            │
┌─────────────────────────────────────────────────────────────┐
│               release/v1.x.x (release candidate)             │
│  - Release preparation                                       │
│  - Bug fixes only, no new features                          │
│  - Deployed to staging environment                          │
│  - Merges to main when approved                             │
└─────────────────────────────────────────────────────────────┘
                            ↑
                            │ (branch from develop)
                            │
┌─────────────────────────────────────────────────────────────┐
│                    develop (integration)                     │
│  - Integration branch for features                           │
│  - Always stable, all tests passing                         │
│  - Deployed to QA environment                               │
│  - Features merge here first                                │
└─────────────────────────────────────────────────────────────┘
                            ↑
                            │ (merge via PR)
                            │
    ┌───────────────────────┴──────────────────────┐
    │                                               │
┌───────────────────┐                  ┌───────────────────┐
│  feature/JIRA-123 │                  │  feature/JIRA-456 │
│  - New features   │                  │  - New features   │
│  - Branch naming  │                  │  - Team isolated  │
└───────────────────┘                  └───────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    hotfix/v1.0.1 (emergency)                │
│  - Critical production fixes                                 │
│  - Branches from main                                        │
│  - Merges to main AND develop                               │
└─────────────────────────────────────────────────────────────┘
```

### Branch Types

#### 1. `main` Branch (Production)

**Purpose**: Production-ready code
**Protected**: Yes
**Deployment**: Production environment
**Merge Source**: `release/*` or `hotfix/*` branches only

**Protection Rules**:
- Require pull request reviews (2+ approvals)
- Require status checks to pass
- Require signed commits
- Require linear history
- Include administrators in restrictions

**Example**:
```bash
# main branch should always be deployable
git checkout main
git pull origin main
# Deploy to production
```

#### 2. `develop` Branch (Integration)

**Purpose**: Integration branch for ongoing development
**Protected**: Yes (limited)
**Deployment**: QA environment
**Merge Source**: `feature/*` branches

**Protection Rules**:
- Require pull request reviews (1+ approval)
- Require status checks to pass
- All CI tests must pass

**Example**:
```bash
# develop is the base for all features
git checkout develop
git pull origin develop
git checkout -b feature/new-feature
```

#### 3. `feature/*` Branches (Feature Development)

**Purpose**: Individual feature development
**Protected**: No
**Naming**: `feature/JIRA-123-short-description`
**Lifespan**: Temporary (deleted after merge)
**Merge Target**: `develop`

**Naming Conventions**:
```bash
feature/JIRA-123-add-multimodal-rag
feature/JIRA-456-improve-vector-search
feature/JIRA-789-add-user-analytics
feature/no-ticket-update-dependencies  # Non-JIRA work
```

**Workflow**:
```bash
# Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/JIRA-123-add-multimodal-rag

# Work on feature
git add .
git commit -m "feat(rag): add multimodal document processing"
git push origin feature/JIRA-123-add-multimodal-rag

# Create PR to develop
# After merge, delete branch
git branch -d feature/JIRA-123-add-multimodal-rag
```

#### 4. `release/*` Branches (Release Preparation)

**Purpose**: Prepare for production release
**Protected**: Yes
**Naming**: `release/v1.2.0`
**Lifespan**: Temporary (deleted after merge to main)
**Merge Target**: `main` and `develop`

**Workflow**:
```bash
# Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0

# Update version numbers
echo "1.2.0" > VERSION
git add VERSION
git commit -m "chore: bump version to 1.2.0"

# Fix bugs only (no new features)
git commit -m "fix: resolve authentication issue"

# Deploy to staging for testing
# When approved, merge to main
# Then merge back to develop
```

#### 5. `hotfix/*` Branches (Emergency Fixes)

**Purpose**: Critical production fixes
**Protected**: No
**Naming**: `hotfix/v1.0.1-critical-bug`
**Lifespan**: Temporary (deleted after merge)
**Merge Target**: `main` AND `develop`

**Workflow**:
```bash
# Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/v1.0.1-security-patch

# Fix the critical issue
git commit -m "fix(security): patch SQL injection vulnerability"

# Update version
echo "1.0.1" > VERSION
git commit -m "chore: bump version to 1.0.1"

# Merge to main
# Merge to develop
# Delete branch
```

---

## Workflow Process

### Development Workflow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Plan Feature                                          │
│    - Create JIRA ticket                                  │
│    - Define acceptance criteria                          │
│    - Assign to developer                                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Create Feature Branch                                 │
│    git checkout develop                                  │
│    git checkout -b feature/JIRA-123-description          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Develop & Commit                                      │
│    - Write code                                          │
│    - Write tests (TDD)                                   │
│    - Local testing                                       │
│    - Commit with conventional commits                    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Push & Create PR                                      │
│    git push origin feature/JIRA-123                      │
│    - Create PR to develop                                │
│    - Fill PR template                                    │
│    - Request reviews                                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Code Review                                           │
│    - Automated CI checks                                 │
│    - Peer review (1-2 approvals)                        │
│    - Address feedback                                    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 6. Merge to Develop                                      │
│    - Squash and merge (or rebase)                       │
│    - Delete feature branch                               │
│    - Auto-deploy to QA                                   │
└─────────────────────────────────────────────────────────┘
```

### Release Workflow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Create Release Branch                                 │
│    git checkout -b release/v1.2.0 develop                │
│    - Update VERSION file                                 │
│    - Update CHANGELOG.md                                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Deploy to Staging                                     │
│    - Automated deployment                                │
│    - Smoke tests                                         │
│    - QA team testing                                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Bug Fixes (if needed)                                 │
│    - Fix bugs in release branch                          │
│    - No new features                                     │
│    - Re-deploy and test                                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Release Approval                                      │
│    - QA sign-off                                         │
│    - Product owner approval                              │
│    - Security review                                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Merge to Main                                         │
│    - Create PR: release/v1.2.0 → main                    │
│    - Require 2+ approvals                                │
│    - Merge (no squash)                                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 6. Tag & Deploy                                          │
│    git tag -a v1.2.0 -m "Release v1.2.0"                │
│    - Auto-deploy to production                           │
│    - Create GitHub release                               │
│    - Publish release notes                               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 7. Merge Back to Develop                                 │
│    - Create PR: release/v1.2.0 → develop                 │
│    - Include bug fixes                                   │
│    - Delete release branch                               │
└─────────────────────────────────────────────────────────┘
```

### Hotfix Workflow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Emergency Detected                                    │
│    - Production issue identified                         │
│    - Severity assessment                                 │
│    - Create hotfix ticket                                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Create Hotfix Branch                                  │
│    git checkout -b hotfix/v1.0.1-critical main           │
│    - Branch from main (current production)               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Fix & Test                                            │
│    - Implement fix                                       │
│    - Write regression test                               │
│    - Local testing                                       │
│    - Update VERSION (1.0.0 → 1.0.1)                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Emergency Approval                                    │
│    - Tech lead review                                    │
│    - Fast-track approval                                 │
│    - Security review (if needed)                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Merge to Main                                         │
│    - Create PR: hotfix/v1.0.1 → main                     │
│    - Tag: v1.0.1                                         │
│    - Deploy to production                                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 6. Merge to Develop                                      │
│    - Create PR: hotfix/v1.0.1 → develop                  │
│    - Ensure fix is in next release                       │
│    - Delete hotfix branch                                │
└─────────────────────────────────────────────────────────┘
```

---

## Release Management

### Semantic Versioning

We use **Semantic Versioning 2.0.0**: `MAJOR.MINOR.PATCH`

```
v1.2.3
│ │ │
│ │ └─ PATCH: Bug fixes, patches (backwards compatible)
│ └─── MINOR: New features (backwards compatible)
└───── MAJOR: Breaking changes (not backwards compatible)
```

**Examples**:
- `v1.0.0` → `v1.0.1`: Bug fix (hotfix)
- `v1.0.1` → `v1.1.0`: New feature (minor release)
- `v1.1.0` → `v2.0.0`: Breaking changes (major release)

### Version File

Maintain a `VERSION` file in repository root:

```bash
# VERSION file
1.2.0
```

### Release Schedule

| Type | Frequency | Example |
|------|-----------|---------|
| **Major Release** | 6-12 months | v2.0.0 (breaking changes) |
| **Minor Release** | 2-4 weeks | v1.1.0 (new features) |
| **Patch Release** | As needed | v1.0.1 (bug fixes) |
| **Hotfix** | Emergency | v1.0.1 (critical issues) |

### Pre-Release Versions

For beta/RC versions:

```
v1.2.0-beta.1
v1.2.0-beta.2
v1.2.0-rc.1
v1.2.0-rc.2
v1.2.0  (final release)
```

---

## Commit Conventions

### Conventional Commits

We follow **Conventional Commits** specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Commit Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(rag): add multimodal document support` |
| `fix` | Bug fix | `fix(auth): resolve token expiration issue` |
| `docs` | Documentation | `docs(api): update API endpoint documentation` |
| `style` | Code style (formatting) | `style: apply black formatting to backend` |
| `refactor` | Code refactoring | `refactor(db): optimize query performance` |
| `perf` | Performance improvement | `perf(vector): improve embedding speed` |
| `test` | Add/update tests | `test(rag): add integration tests` |
| `chore` | Maintenance tasks | `chore: update dependencies` |
| `ci` | CI/CD changes | `ci: add automated deployment` |
| `build` | Build system changes | `build: update Docker configuration` |
| `revert` | Revert previous commit | `revert: revert commit abc123` |

### Commit Scope

Common scopes for our application:

```
rag         - RAG system
auth        - Authentication
db          - Database
api         - API endpoints
frontend    - Frontend code
backend     - Backend code
vector      - Vector search
llm         - LLM integration
docs        - Documentation
deployment  - Deployment configs
security    - Security features
```

### Commit Examples

**Good Commits**:
```bash
feat(rag): add support for multimodal documents

- Implement image processing pipeline
- Add vision model integration
- Update document chunking for images
- Add tests for image processing

Closes JIRA-123
```

```bash
fix(auth): resolve token refresh race condition

The token refresh was failing under high concurrency.
This commit adds a mutex lock to prevent race conditions.

Fixes #456
```

```bash
perf(vector): optimize IVFFlat index parameters

- Increase lists from 100 to 1000 for 1M+ vectors
- Add query caching for frequently searched vectors
- Benchmark shows 40% speed improvement

BREAKING CHANGE: Requires index rebuild for existing deployments
```

**Bad Commits** (avoid):
```bash
# Too vague
git commit -m "fix bug"

# No type
git commit -m "update code"

# All caps
git commit -m "FIX: AUTHENTICATION BUG"
```

### Commit Message Template

Create `.gitmessage` template:

```bash
# <type>(<scope>): <subject> (max 72 chars)
# |<----  Using a Maximum Of 72 Characters  ---->|

# Explain why this change is being made
# |<----   Try To Limit Each Line to a Maximum Of 72 Characters   ---->|

# Provide links or keys to any relevant tickets, articles or other resources
# Example: Closes JIRA-123, Fixes #456

# --- COMMIT END ---
# Type can be
#    feat     (new feature)
#    fix      (bug fix)
#    refactor (refactoring code)
#    style    (formatting, missing semicolons, etc)
#    docs     (changes to documentation)
#    test     (adding or refactoring tests)
#    chore    (maintain)
# --------------------
# Remember to
#    Capitalize the subject line
#    Use the imperative mood in the subject line
#    Do not end the subject line with a period
#    Separate subject from body with a blank line
#    Use the body to explain what and why vs. how
#    Can use multiple lines with "-" for bullet points in body
# --------------------
```

Configure Git to use template:
```bash
git config --local commit.template .gitmessage
```

---

## Pull Request Process

### PR Template

Create `.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## Description
<!-- Describe your changes in detail -->

## Type of Change
<!-- Mark the relevant option with an "x" -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] Dependencies update

## Related Issues
<!-- Link to JIRA ticket or GitHub issue -->

Closes JIRA-123
Fixes #456

## Changes Made
<!-- List the specific changes -->

- Added multimodal document processing
- Updated RAG pipeline to handle images
- Added integration tests for image processing

## Testing
<!-- Describe the tests you ran -->

- [ ] Unit tests pass (`pytest tests/unit`)
- [ ] Integration tests pass (`pytest tests/integration`)
- [ ] E2E tests pass (`pytest tests/e2e`)
- [ ] Manual testing completed

### Test Results
```
All tests passed
Coverage: 85%
```

## Screenshots (if applicable)
<!-- Add screenshots for UI changes -->

## Checklist
<!-- Mark completed items with an "x" -->

- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Code is commented (particularly in complex areas)
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added for new features
- [ ] All tests passing
- [ ] CHANGELOG.md updated
- [ ] VERSION updated (if applicable)

## Deployment Notes
<!-- Any special deployment considerations -->

- Requires database migration
- Needs environment variable: `NEW_FEATURE_ENABLED=true`
- Backwards compatible: Yes/No

## Reviewer Notes
<!-- Any specific areas you want reviewers to focus on -->

Please pay special attention to the error handling in `src/rag/multimodal.py`
```

### PR Review Checklist

**Reviewer Responsibilities**:

1. **Code Quality**
   - [ ] Code is clean and readable
   - [ ] No code smells or anti-patterns
   - [ ] Follows project conventions
   - [ ] No unnecessary complexity

2. **Functionality**
   - [ ] Meets acceptance criteria
   - [ ] Edge cases handled
   - [ ] Error handling appropriate
   - [ ] No obvious bugs

3. **Testing**
   - [ ] Adequate test coverage
   - [ ] Tests are meaningful
   - [ ] All tests passing
   - [ ] No flaky tests

4. **Security**
   - [ ] No security vulnerabilities
   - [ ] Input validation present
   - [ ] No secrets in code
   - [ ] Authentication/authorization correct

5. **Performance**
   - [ ] No performance regressions
   - [ ] Database queries optimized
   - [ ] Caching appropriate
   - [ ] Resource usage reasonable

6. **Documentation**
   - [ ] Code is self-documenting
   - [ ] Complex logic explained
   - [ ] API documentation updated
   - [ ] README updated if needed

### PR Size Guidelines

| Size | Lines Changed | Review Time | Recommendation |
|------|---------------|-------------|----------------|
| **XS** | < 10 | < 5 min | Ideal |
| **S** | 10-100 | < 15 min | Good |
| **M** | 100-500 | < 30 min | Acceptable |
| **L** | 500-1000 | 1-2 hours | Consider splitting |
| **XL** | > 1000 | > 2 hours | Must split |

**Large PRs should be split into smaller, logical chunks**

---

## CI/CD Pipeline

### GitHub Actions Workflows

#### 1. **CI for Develop Branch** (`.github/workflows/ci-develop.yml`)

```yaml
name: CI - Develop

on:
  push:
    branches: [develop]
  pull_request:
    branches: [develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov black flake8

      - name: Lint with flake8
        run: flake8 backend/app --max-line-length=120

      - name: Format check with black
        run: black --check backend/app

      - name: Run tests
        run: pytest backend/tests --cov=backend/app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker images
        run: |
          docker-compose build backend frontend

      - name: Run integration tests
        run: |
          docker-compose up -d
          sleep 30
          pytest tests/integration
          docker-compose down

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Trivy security scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  deploy-qa:
    runs-on: ubuntu-latest
    needs: [test, build]
    if: github.ref == 'refs/heads/develop'
    steps:
      - name: Deploy to QA
        run: |
          # Deploy to QA environment
          echo "Deploying to QA..."
```

#### 2. **CI for Release Branch** (`.github/workflows/ci-release.yml`)

```yaml
name: CI - Release

on:
  push:
    branches:
      - 'release/**'
  pull_request:
    branches:
      - 'release/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      # Same as develop CI

  deploy-staging:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - name: Deploy to Staging
        run: |
          # Deploy to staging environment
          echo "Deploying to Staging..."

      - name: Run smoke tests
        run: |
          # Run smoke tests on staging
          pytest tests/smoke
```

#### 3. **Production Deployment** (`.github/workflows/deploy-production.yml`)

```yaml
name: Deploy - Production

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v3

      - name: Verify tag format
        run: |
          if [[ ! "${{ github.ref_name }}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "Invalid tag format"
            exit 1
          fi

      - name: Build production images
        run: |
          docker build -t app:${{ github.ref_name }} .

      - name: Run security scan
        run: |
          trivy image app:${{ github.ref_name }}

      - name: Deploy to production
        run: |
          # Deploy to production
          echo "Deploying v${{ github.ref_name }} to production..."

      - name: Create GitHub Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref_name }}
          release_name: Release ${{ github.ref_name }}
          body_path: docs/releases/${{ github.ref_name }}-RELEASE.md
          draft: false
          prerelease: false

      - name: Notify team
        run: |
          # Send Slack/email notification
          echo "Production deployment complete!"
```

### Environment Strategy

| Environment | Branch | Auto-Deploy | Purpose |
|-------------|--------|-------------|---------|
| **Development** | `feature/*` | No | Local development |
| **QA** | `develop` | Yes | Integration testing |
| **Staging** | `release/*` | Yes | Pre-production testing |
| **Production** | `main` (tagged) | Manual approval | Live system |

---

## Version Tagging

### Creating Tags

```bash
# After merging release branch to main
git checkout main
git pull origin main

# Create annotated tag
git tag -a v1.2.0 -m "Release version 1.2.0

Features:
- Multimodal RAG support
- Improved vector search
- Enhanced security

Bug Fixes:
- Fixed authentication timeout
- Resolved memory leak in document processing
"

# Push tag to remote
git push origin v1.2.0
```

### Tag Naming Convention

```
v<MAJOR>.<MINOR>.<PATCH>[-<PRE-RELEASE>][+<BUILD>]

Examples:
v1.0.0              # Production release
v1.2.0-beta.1       # Beta release
v1.2.0-rc.1         # Release candidate
v1.2.0+20260105     # Build metadata
```

### Listing Tags

```bash
# List all tags
git tag

# List tags matching pattern
git tag -l "v1.*"

# Show tag details
git show v1.2.0

# Delete local tag
git tag -d v1.2.0

# Delete remote tag
git push origin :refs/tags/v1.2.0
```

---

## Change & Release Notes

### CHANGELOG.md Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features in development

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Now removed features

### Fixed
- Bug fixes

### Security
- Security patches

## [1.2.0] - 2026-01-15

### Added
- Multimodal RAG support for images and videos ([#123](link))
- Advanced vector search with hybrid retrieval ([#124](link))
- User analytics dashboard ([#125](link))
- Export wizard for POC-to-production deployment ([#126](link))

### Changed
- Improved LLM response time by 40% ([#127](link))
- Updated embedding model to all-MiniLM-L6-v2 ([#128](link))
- Refactored authentication system ([#129](link))

### Fixed
- Resolved token expiration edge case ([#130](link))
- Fixed memory leak in document processing ([#131](link))
- Corrected vector index parameters for large datasets ([#132](link))

### Security
- Patched SQL injection vulnerability (CVE-2026-001) ([#133](link))
- Updated dependencies with security fixes ([#134](link))

## [1.1.0] - 2025-12-15

### Added
- Fine-tuning system for custom models
- RBAC with organizational hierarchy
- Audit logging for compliance

[Rest of changelog...]

[Unreleased]: https://github.com/org/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/org/repo/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/org/repo/compare/v1.0.0...v1.1.0
```

### Release Notes Template

Create `docs/releases/v1.2.0-RELEASE.md`:

```markdown
# Release v1.2.0 - Multimodal RAG & Advanced Search

**Release Date**: 2026-01-15
**Release Type**: Minor Release
**Status**: Stable

---

## 🎯 Overview

This release introduces multimodal RAG capabilities, allowing processing of images and videos alongside text documents. We've also significantly improved vector search performance and added comprehensive user analytics.

---

## ✨ New Features

### Multimodal Document Processing
- **Image Support**: Process PNG, JPEG, WebP images
- **Vision Models**: Integration with GPT-4 Vision and Claude 3
- **Video Processing**: Extract frames and transcripts from videos
- **Unified Pipeline**: Single RAG pipeline for all modalities

### Advanced Vector Search
- **Hybrid Retrieval**: Combines dense and sparse retrieval
- **Reranking**: Cross-encoder reranking for better results
- **Query Expansion**: Automatic query reformulation
- **Performance**: 40% faster searches on large datasets

### User Analytics Dashboard
- Real-time usage metrics
- Query analytics and insights
- Model performance tracking
- Cost analysis

---

## 🔧 Improvements

- **Performance**: LLM response time reduced by 40%
- **Embeddings**: Upgraded to all-MiniLM-L6-v2 (384-dim)
- **Caching**: Improved Redis caching strategy
- **UI/UX**: Redesigned document upload interface

---

## 🐛 Bug Fixes

- Fixed token refresh race condition under high concurrency
- Resolved memory leak in document processing pipeline
- Corrected IVFFlat index parameters for 1M+ vectors
- Fixed edge case in session timeout logic

---

## 🔒 Security

- **CVE-2026-001**: Patched SQL injection vulnerability in search
- Updated 15 dependencies with security fixes
- Enhanced input validation across all API endpoints
- Improved RBAC permission checks

---

## 📊 Performance Benchmarks

| Metric | v1.1.0 | v1.2.0 | Improvement |
|--------|--------|--------|-------------|
| Query Response Time | 2.5s | 1.5s | 40% faster |
| Vector Search (1M docs) | 800ms | 450ms | 44% faster |
| Document Processing | 12s/doc | 10s/doc | 17% faster |
| Memory Usage | 4.2GB | 3.8GB | 10% reduction |

---

## 📋 Upgrade Guide

### Breaking Changes
None - this release is fully backwards compatible

### Migration Steps

1. **Backup Database**
   ```bash
   docker exec rag-postgres pg_dump -U postgres ragchatbot > backup.sql
   ```

2. **Pull Latest Code**
   ```bash
   git checkout main
   git pull origin main
   git checkout v1.2.0
   ```

3. **Update Dependencies**
   ```bash
   pip install -r backend/requirements.txt --upgrade
   npm install
   ```

4. **Run Migrations**
   ```bash
   alembic upgrade head
   ```

5. **Rebuild Embeddings** (Optional but recommended)
   ```bash
   python scripts/rebuild_embeddings.py
   ```

6. **Restart Services**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

## 🎓 New Documentation

- [Multimodal RAG Guide](../guides/MULTIMODAL_RAG.md)
- [Advanced Search Tutorial](../tutorials/ADVANCED_SEARCH.md)
- [Analytics Dashboard Guide](../guides/ANALYTICS_DASHBOARD.md)

---

## 🙏 Contributors

- @developer1 - Multimodal RAG implementation
- @developer2 - Advanced search features
- @developer3 - Analytics dashboard
- @developer4 - Bug fixes and optimizations

---

## 📝 Full Changelog

See [CHANGELOG.md](../../docs/changelog/CHANGELOG.md#120---2026-01-15) for complete list of changes.

---

## 🐛 Known Issues

- Video processing requires GPU for optimal performance
- Large images (>10MB) may timeout - will be fixed in v1.2.1

---

## 🔜 What's Next (v1.3.0)

- Real-time collaborative editing
- Advanced workflow automation
- Multi-language support expansion
- Custom model training UI

---

**Questions or Issues?**
- GitHub Issues: https://github.com/org/repo/issues
- Documentation: https://docs.example.com
- Support: support@example.com
```

---

## Repository Setup

### Initial Setup Commands

```bash
# 1. Create new repository on GitHub
# Repository name: enterprise-rag-chatbot
# Visibility: Private
# Initialize: No README (we have our own)

# 2. Clone your existing code
cd /path/to/existing/code

# 3. Initialize git (if not already)
git init

# 4. Set up remote
git remote add origin git@github.com:your-org/enterprise-rag-chatbot.git

# 5. Create and commit to main branch
git checkout -b main
git add .
git commit -m "chore: initial commit - baseline codebase

- Complete Enterprise RAG Chatbot codebase
- Backend (FastAPI, Python 3.11)
- Frontend (Next.js 14, TypeScript)
- Database setup with 90+ tables
- Documentation and setup scripts

This represents the stable baseline for all future development.
"

# 6. Push to main
git push -u origin main

# 7. Create develop branch
git checkout -b develop
git push -u origin develop

# 8. Set default branch on GitHub to main
# Go to Settings > Branches > Default branch > main
```

### Branch Protection Rules

#### For `main` branch:

```yaml
Branch protection rules for main:
  Require pull request reviews before merging:
    ✓ Enabled
    Required approvals: 2
    ✓ Dismiss stale reviews
    ✓ Require review from Code Owners
    ✓ Require approval of most recent push

  Require status checks before merging:
    ✓ Enabled
    Required checks:
      - ci/test
      - ci/build
      - ci/security-scan
      - ci/lint
    ✓ Require branches to be up to date

  Require conversation resolution before merging:
    ✓ Enabled

  Require signed commits:
    ✓ Enabled

  Require linear history:
    ✓ Enabled

  Include administrators:
    ✓ Enabled

  Restrict who can push:
    - Release managers only

  Allow force pushes:
    ✗ Disabled

  Allow deletions:
    ✗ Disabled
```

#### For `develop` branch:

```yaml
Branch protection rules for develop:
  Require pull request reviews before merging:
    ✓ Enabled
    Required approvals: 1
    ✓ Dismiss stale reviews

  Require status checks before merging:
    ✓ Enabled
    Required checks:
      - ci/test
      - ci/lint
    ✓ Require branches to be up to date

  Allow force pushes:
    ✗ Disabled
```

### CODEOWNERS File

Create `.github/CODEOWNERS`:

```
# CODEOWNERS file for code review assignment

# Default owners for everything
* @org/engineering-leads

# Backend code
/backend/ @org/backend-team @org/engineering-leads

# Frontend code
/frontend/ @org/frontend-team @org/engineering-leads

# Database migrations
/backend/migrations/ @org/backend-team @org/database-admins

# Infrastructure
/infrastructure/ @org/devops-team
/docker-compose.yml @org/devops-team
/.github/ @org/devops-team

# Documentation
/docs/ @org/technical-writers @org/engineering-leads

# Security
SECURITY.md @org/security-team
/backend/app/services/auth/ @org/security-team

# Configuration files
*.yml @org/devops-team
*.yaml @org/devops-team
Dockerfile* @org/devops-team

# Dependencies
requirements.txt @org/backend-team
package.json @org/frontend-team
```

---

## Team Workflow

### Daily Workflow for Developers

```bash
# Morning: Sync with latest
git checkout develop
git pull origin develop

# Start new feature
git checkout -b feature/JIRA-123-new-feature

# Work and commit
git add .
git commit -m "feat(module): add new capability"

# Push and create PR
git push origin feature/JIRA-123-new-feature
# Create PR on GitHub: feature/JIRA-123 → develop

# After PR approved and merged
git checkout develop
git pull origin develop
git branch -d feature/JIRA-123-new-feature
```

### Weekly Workflow for Release Manager

```bash
# Monday: Plan release
# - Review completed features in develop
# - Create release plan
# - Communicate to team

# Wednesday: Create release branch
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0

# Update version
echo "1.2.0" > VERSION
git add VERSION
git commit -m "chore: bump version to 1.2.0"

# Push and deploy to staging
git push origin release/v1.2.0
# CI/CD auto-deploys to staging

# Thursday-Friday: QA testing
# - QA team tests on staging
# - Fix bugs in release branch
# - Re-deploy and re-test

# Friday afternoon: Release
# If QA approves:
git checkout main
git pull origin main
git merge --no-ff release/v1.2.0
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin main --tags

# Merge back to develop
git checkout develop
git merge --no-ff release/v1.2.0
git push origin develop

# Delete release branch
git branch -d release/v1.2.0
git push origin --delete release/v1.2.0
```

### Hotfix Workflow

```bash
# Production issue detected!
git checkout main
git pull origin main
git checkout -b hotfix/v1.0.1-critical-bug

# Fix the issue
git commit -m "fix(critical): resolve security vulnerability"

# Update version
echo "1.0.1" > VERSION
git commit -m "chore: bump version to 1.0.1"

# Fast-track review and merge to main
git checkout main
git merge --no-ff hotfix/v1.0.1-critical-bug
git tag -a v1.0.1 -m "Hotfix v1.0.1"
git push origin main --tags

# Merge to develop
git checkout develop
git merge --no-ff hotfix/v1.0.1-critical-bug
git push origin develop

# Cleanup
git branch -d hotfix/v1.0.1-critical-bug
git push origin --delete hotfix/v1.0.1-critical-bug
```

---

## Best Practices

### 1. Commit Frequency

- **Commit often**: Small, logical commits
- **Meaningful messages**: Clear description of what and why
- **Atomic commits**: One logical change per commit

### 2. Branch Management

- **Short-lived branches**: Merge features within 1-2 days
- **Keep updated**: Rebase from develop regularly
- **Clean up**: Delete merged branches immediately

### 3. Code Review

- **Timely reviews**: Review within 24 hours
- **Constructive feedback**: Focus on code, not developer
- **Learning opportunity**: Share knowledge

### 4. Testing

- **Write tests first**: TDD approach
- **High coverage**: Maintain >80% code coverage
- **Integration tests**: Test realistic scenarios

### 5. Documentation

- **Update docs**: Documentation changes with code
- **Clear examples**: Provide usage examples
- **Keep current**: Regular doc reviews

### 6. Security

- **No secrets in code**: Use environment variables
- **Scan regularly**: Automated security scans
- **Update dependencies**: Regular dependency updates

### 7. Communication

- **Clear PR descriptions**: Explain what and why
- **Link tickets**: Reference JIRA/issues
- **Team notifications**: Communicate breaking changes

---

## Appendix

### Git Aliases

Add to `~/.gitconfig`:

```ini
[alias]
    # Shortcuts
    co = checkout
    br = branch
    ci = commit
    st = status

    # Logging
    lg = log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit

    # Branch management
    cleanup = "!git branch --merged | grep -v '\\*\\|main\\|develop' | xargs -n 1 git branch -d"

    # Release helpers
    release-start = "!f() { git checkout develop && git pull && git checkout -b release/v$1; }; f"
    release-finish = "!f() { git checkout main && git merge --no-ff release/v$1 && git tag -a v$1 -m \"Release v$1\" && git checkout develop && git merge --no-ff release/v$1 && git branch -d release/v$1; }; f"
```

### Useful Commands

```bash
# Find commits by message
git log --all --grep="fix(auth)"

# See changes between branches
git diff develop...main

# Interactive rebase (clean up commits)
git rebase -i develop

# Cherry-pick a commit
git cherry-pick abc123

# Undo last commit (keep changes)
git reset --soft HEAD~1

# View file history
git log --follow -p -- path/to/file

# Find who changed a line
git blame path/to/file

# Stash changes temporarily
git stash save "work in progress"
git stash pop
```

---

**Document Version**: 1.0
**Last Updated**: 2026-01-05
**Maintained By**: Engineering Leadership
**Next Review**: 2026-04-05
