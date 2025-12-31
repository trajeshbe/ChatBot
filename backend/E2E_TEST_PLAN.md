# End-to-End Testing Plan - Project-Based Chat Sessions

## Objective
Ensure all existing functionality continues to work while new project-based features work correctly.

## Test Scenarios

### Scenario 1: Regular Chat (Non-Project) - EXISTING FUNCTIONALITY
**Purpose**: Ensure existing chat functionality still works without projects

1. Navigate to Chat tab
2. Upload a document without specifying project
3. Ask a question
4. Verify:
   - ✅ Document uploads successfully
   - ✅ Document appears in list
   - ✅ Query returns answer with sources
   - ✅ Session is created
   - ✅ Conversation history persists

### Scenario 2: Project-Based Document Upload
**Purpose**: Verify documents are correctly associated with projects

1. Navigate to Projects tab
2. Select "Construction Intelligence" project
3. Click "New chat in Construction Intelligence"
4. Upload a construction-related document
5. Verify:
   - ✅ Document has project_id in database
   - ✅ Document appears only in this project's file list
   - ✅ Document does NOT appear in other projects
   - ✅ Session has project_id in database

### Scenario 3: Project-Scoped RAG Queries
**Purpose**: Ensure queries only search project documents

1. Create Project A with Document A (about AI)
2. Create Project B with Document B (about Construction)
3. In Project A, ask "What is machine learning?"
4. Verify:
   - ✅ Answer comes from Document A
   - ✅ Sources only include Document A
   - ✅ Document B is NOT in sources
5. In Project B, ask "What are construction phases?"
6. Verify:
   - ✅ Answer comes from Document B
   - ✅ Sources only include Document B
   - ✅ Document A is NOT in sources

### Scenario 4: Global/Non-Project Documents
**Purpose**: Verify documents without project are accessible globally

1. Upload document to "Global" project (or no project)
2. Query from Project A
3. Query from Project B
4. Verify:
   - ✅ Global document appears in both contexts (if designed that way)
   - OR ✅ Global document only in Global project context

### Scenario 5: Project Navigation
**Purpose**: Verify navigation between projects works correctly

1. From dashboard, click Projects tab
2. Click on "Construction Intelligence"
3. Verify:
   - ✅ Shows project details page
   - ✅ Shows only Construction Intelligence files
   - ✅ File count matches project documents only
4. Click "New chat in Construction Intelligence"
5. Verify:
   - ✅ Chat interface appears within project context
   - ✅ Project name shown in header
   - ✅ Document list shows only project files
6. Click "Back to Construction Intelligence"
7. Verify:
   - ✅ Returns to project detail view
   - ✅ No data loss

### Scenario 6: Project Selector in Chat Tab
**Purpose**: Verify project switching in main chat works

1. Navigate to Chat tab
2. Select Project A from dropdown
3. Verify:
   - ✅ Document list updates to show Project A files
   - ✅ Queries scope to Project A
4. Switch to Project B
5. Verify:
   - ✅ Document list updates to show Project B files
   - ✅ Previous chat history preserved
   - ✅ New queries scope to Project B

### Scenario 7: Multi-Model Support
**Purpose**: Ensure model selection still works with projects

1. In a project, select different models (GPT-4, Claude, Ollama)
2. Ask same question with each model
3. Verify:
   - ✅ All models work
   - ✅ Project scoping works with all models
   - ✅ Responses differ by model

### Scenario 8: Session Persistence
**Purpose**: Verify sessions persist correctly with projects

1. Start chat in Project A
2. Ask 3 questions
3. Refresh browser
4. Return to same project
5. Verify:
   - ✅ Session restored
   - ✅ Chat history visible
   - ✅ Can continue conversation
   - ✅ Project context maintained

### Scenario 9: File Upload Edge Cases
**Purpose**: Test various file types and scenarios

1. Upload PDF to Project A
2. Upload DOCX to Project A
3. Upload TXT to Project B
4. Upload large file (>10MB) if supported
5. Verify:
   - ✅ All file types process correctly
   - ✅ Each file associated with correct project
   - ✅ Embeddings generated for all
   - ✅ Searchable within correct project only

### Scenario 10: RBAC and Permissions
**Purpose**: Ensure project permissions work

1. As Admin, create Project A
2. As User, try to access Project A
3. Verify:
   - ✅ Permissions enforced
   - ✅ Users see only their projects or shared projects
   - ✅ Audit logs capture actions

## Success Criteria

### Core Functionality (Must Pass)
- [ ] Regular chat without projects works
- [ ] File upload without projects works
- [ ] Queries return correct answers
- [ ] All LLM models work
- [ ] Session management works

### Project Features (Must Pass)
- [ ] project_id saved to documents table
- [ ] project_id saved to chat_sessions table
- [ ] Document list filtered by project
- [ ] RAG queries scoped to project documents
- [ ] Project navigation clear and intuitive

### User Experience (Should Pass)
- [ ] No duplicate/confusing buttons
- [ ] Clear indication of current project context
- [ ] Project selector easy to find and use
- [ ] File counts accurate per project
- [ ] Performance acceptable (<2s for queries)

### Data Integrity (Must Pass)
- [ ] No document leakage between projects
- [ ] No session mixing between projects
- [ ] Database constraints enforced
- [ ] No orphaned records

## Regression Testing
After all fixes, re-run existing test suites:
- `pytest tests/test_document_service.py`
- `pytest tests/test_rag_service.py`
- `pytest tests/test_embedding_service.py`
- Manual UI testing checklist

## Performance Benchmarks
- Document upload: < 3s for 1MB file
- RAG query: < 5s with project scoping
- Project list load: < 1s
- Document list (100 files): < 2s with filtering
