# 📄 Document Tracking: sample_entity_relationship.docx

**Uploaded**: 2026-01-04 11:53:49 UTC
**Document ID**: `ec9a245a-f3af-4330-9f60-8d738d9a6432`
**Purpose**: Entity Relationship Extraction Testing

---

## 📊 Document Details

| Property | Value |
|----------|-------|
| **Filename** | `sample_entity_relationship.docx` |
| **Document ID** | `ec9a245a-f3af-4330-9f60-8d738d9a6432` |
| **File Type** | Microsoft Word Document (`.docx`) |
| **File Size** | 17,056 bytes (17 KB) |
| **Upload Time** | 2026-01-04 11:53:49 UTC |
| **Processing Status** | ✅ Successfully processed |
| **Chunks Created** | 5 chunks |
| **Embeddings** | ✅ Generated |

---

## 🎯 Intended Use

**Module**: Relation Extractor (Document Intelligence)

**Test Scenario**: Extract entities and relationships from the document to validate:
- Entity extraction (people, organizations, locations, etc.)
- Relationship extraction (employed_by, located_in, acquired, etc.)
- Confidence scoring
- Graph generation

---

## 📋 Quick Reference Commands

### Extract Relations from This Document

```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/modules/relation-extractor/extract \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "ec9a245a-f3af-4330-9f60-8d738d9a6432",
    "extraction_mode": "text",
    "min_confidence": 0.6
  }'
```

### Check Document Chunks

```bash
# Query database
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT chunk_index, LEFT(content, 100) as content_preview
   FROM document_chunks
   WHERE document_id = 'ec9a245a-f3af-4330-9f60-8d738d9a6432'
   ORDER BY chunk_index;"
```

### View Document Metadata

```bash
# Query database
docker-compose exec postgres psql -U postgres -d ragchatbot -c \
  "SELECT filename, file_type, processing_status, created_at
   FROM documents
   WHERE id = 'ec9a245a-f3af-4330-9f60-8d738d9a6432';"
```

---

## 🧪 Test Results

### Document Processing
- ✅ **Upload**: Successful
- ✅ **File Detection**: DOCX format recognized
- ✅ **Text Extraction**: Completed
- ✅ **Chunking**: 5 chunks created
- ✅ **Embedding Generation**: All chunks embedded
- ✅ **Session Association**: Linked to session

### Relation Extraction

**Status**: Ready for extraction

**To Test**:
1. Open Relation Extractor UI panel
2. Document should be pre-selected (uploaded in current session)
3. Click "Extract Relations"
4. Review extracted entities and relationships

**Expected Output**:
- List of entities with types (person, organization, location, etc.)
- List of relationships with subject-predicate-object structure
- Confidence scores for each extraction
- Graph visualization with nodes and edges
- Total extraction time and statistics

---

## 📝 Notes

- Document is tracked in session: All extractions will use this document context
- Embeddings available: Can be used for semantic search within the document
- 5 chunks: Document was split into 5 semantic chunks for processing
- Ready for testing: All preprocessing complete, ready for relation extraction

---

## 🔗 Related Documents

**Previous Test Document**: `test_relations.txt`
- Document ID: `b748e015-8b9b-4681-b8a9-515c632ae094`
- Successfully extracted 5 relations
- Used for initial testing and validation

---

## ✅ Verification Checklist

- [x] Document uploaded successfully
- [x] File type recognized (DOCX)
- [x] Text extracted from Word document
- [x] Chunks created (5 total)
- [x] Embeddings generated
- [x] Session association established
- [ ] Relation extraction performed (pending user action)
- [ ] Results reviewed
- [ ] Confidence scores validated

---

**Document Tracked**: 2026-01-04 12:15:00
**Status**: ✅ **READY FOR RELATION EXTRACTION**
