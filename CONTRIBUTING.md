# Contributing to Enterprise RAG Chatbot

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/rag-chatbot.git
   cd rag-chatbot
   ```

2. **Set Up Development Environment**
   ```bash
   # Copy environment file
   cp .env.example .env

   # Start services
   make dev

   # Or use the quick start script
   ./scripts/quick-start.sh
   ```

3. **Install Dependencies**
   ```bash
   make install
   ```

## Development Workflow

### Backend Development

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Format code
black app/ tests/

# Lint code
pylint app/
```

### Frontend Development

```bash
# Install dependencies
cd frontend
npm install

# Run development server
npm run dev

# Run tests
npm test

# Lint code
npm run lint
```

## Code Style

### Python (Backend)
- Follow PEP 8 guidelines
- Use Black for code formatting
- Use type hints
- Document functions with docstrings

### TypeScript/React (Frontend)
- Follow Airbnb React/JSX Style Guide
- Use ESLint and Prettier
- Use TypeScript for type safety
- Use functional components with hooks

## Testing

### Unit Tests
- Write unit tests for all new features
- Maintain >80% code coverage
- Use pytest for backend, Jest for frontend

### Integration Tests
- Test API endpoints
- Test database interactions
- Test external service integrations

### Run Tests
```bash
# Backend
make test-backend

# Frontend
make test-frontend

# All tests
make test
```

## Commit Guidelines

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions or changes
- `chore:` Build process or tooling changes

Example:
```
feat: add semantic caching for embeddings
fix: resolve database connection timeout
docs: update API documentation
```

## Pull Request Process

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code
   - Add tests
   - Update documentation

3. **Test Your Changes**
   ```bash
   make test
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```

5. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Go to GitHub
   - Create a pull request from your fork
   - Fill out the PR template
   - Wait for review

## Code Review

All submissions require code review. The review process:
1. Automated tests must pass
2. Code must meet style guidelines
3. Changes must be documented
4. At least one maintainer approval required

## Documentation

- Update README.md for user-facing changes
- Update API documentation for API changes
- Add inline comments for complex logic
- Update architecture diagrams if needed

## Architecture Guidelines

### Backend Architecture
- Use dependency injection
- Follow clean architecture principles
- Separate business logic from infrastructure
- Use async/await for I/O operations

### Frontend Architecture
- Use component composition
- Separate presentational and container components
- Use custom hooks for shared logic
- Implement proper error boundaries

## Performance Guidelines

- Optimize database queries
- Implement caching where appropriate
- Use async operations for I/O
- Profile before optimizing
- Document performance-critical sections

## Security Guidelines

- Never commit secrets or API keys
- Use environment variables for configuration
- Validate and sanitize all inputs
- Follow OWASP security best practices
- Report security issues privately

## Questions or Issues?

- Check existing issues on GitHub
- Ask questions in discussions
- Join our community chat (if available)
- Review documentation thoroughly

Thank you for contributing! 🎉
