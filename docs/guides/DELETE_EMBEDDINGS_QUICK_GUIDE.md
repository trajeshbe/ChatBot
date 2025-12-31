# Quick Guide: Delete Documents & Embeddings

**Date**: 2025-12-02
**Feature**: Document Deletion from Admin Dashboard

---

## 📍 Where to Find It

**Location**: Admin Dashboard → Database Tab → Documents & Embeddings

**URL**: `http://localhost:3001/admin`

---

## 🎯 Step-by-Step Guide

### Step 1: Access Admin Dashboard

1. Navigate to: `http://localhost:3001/admin`
2. Click on the **"Database"** tab (at the top)
3. You'll see the **"Documents & Embeddings"** section

### Step 2: Find the Document

You have two options:

**Option A: Search**
- Type filename in the search box
- Click "Search" button
- Matching documents appear below

**Option B: Browse**
- Scroll through the document list
- Each document shows:
  - Filename
  - File type and size
  - Processing status
  - Chunks count
  - Embeddings count and percentage

### Step 3: Click Delete Button

1. **Hover** over the document you want to delete
2. A **trash icon (🗑️)** appears on the right side
3. **Click** the trash icon

### Step 4: Confirm Deletion

A confirmation dialog appears:

```
⚠️ Delete document and all embeddings?

Document: your-file.pdf
This will permanently delete:
• The document record
• All chunks
• All embeddings

This action cannot be undone.
```

**Choose**:
- Click **"OK"** to proceed with deletion
- Click **"Cancel"** to abort

### Step 5: Deletion Complete

Success message appears:

```
✅ Document deleted successfully!

Filename: your-file.pdf
Chunks deleted: 26
Embeddings removed: 26
```

The document list **automatically refreshes** and the deleted document disappears.

---

## 🎨 Visual Guide

### What You'll See

**Before Deletion**:
```
┌─────────────────────────────────────────────────────────────┐
│  Documents & Embeddings                                      │
│  [Search box]  [Search]                                      │
├─────────────────────────────────────────────────────────────┤
│  📄 example.pdf                              [100%] [🗑️]    │
│     application/pdf • 1.6 MB • Processed                     │
│     Chunks: 26 • Embeddings: 26 (100.0%)                     │
│     In 1 session(s)                                          │
├─────────────────────────────────────────────────────────────┤
│  📄 another-file.pdf                          [85%] [🗑️]    │
│     ...                                                       │
└─────────────────────────────────────────────────────────────┘
```

**After Clicking Delete**:
- Confirmation dialog pops up
- Document is highlighted

**After Confirming**:
- Success alert shows deletion details
- Document removed from list
- If you had that document selected, the chunks panel clears

---

## ⚙️ What Gets Deleted

### ✅ Deleted

| Item | Description |
|------|-------------|
| **Document Record** | Entry in `documents` table |
| **All Chunks** | All text chunks from the document |
| **All Embeddings** | All vector embeddings (384-dim, 512-dim, 768-dim) |
| **Session Links** | Associations with chat sessions |

### ❌ Not Deleted

| Item | Reason |
|------|--------|
| **MinIO Files** | Physical files may be referenced elsewhere |
| **Chat Messages** | Preserves conversation history |

---

## 💡 Use Cases

### When to Delete Documents

1. **Wrong Document Uploaded**
   - User uploaded incorrect file
   - Delete and re-upload correct version

2. **Sensitive Information**
   - Document contains data that shouldn't be searchable
   - Remove to prevent accidental exposure

3. **Outdated Information**
   - Old version of document
   - Delete old, keep only latest version

4. **Test Documents**
   - Testing uploads
   - Clean up test data

5. **Storage Management**
   - Free up database space
   - Remove unused embeddings

---

## 🔒 Safety Features

### Built-in Protections

1. **Confirmation Dialog**
   - Prevents accidental deletion
   - Shows exactly what will be deleted

2. **Detailed Summary**
   - Success message shows what was deleted
   - Chunk and embedding counts

3. **Transaction Safety**
   - All deletions in a single transaction
   - Rollback on error (nothing deleted if error occurs)

4. **Auto-Refresh**
   - Document list updates immediately
   - See results right away

---

## 🚨 Common Issues

### Issue 1: Delete Button Not Visible

**Problem**: Can't see the trash icon

**Solution**:
- **Hover** your mouse over the document row
- The delete button appears on hover
- Make sure you're in the Database tab

### Issue 2: "Document Not Found" Error

**Problem**: Error when trying to delete

**Possible Causes**:
- Document already deleted by another user
- Document ID is invalid

**Solution**:
- Click "Search" to refresh the list
- Try again with a different document

### Issue 3: Deletion Takes Long Time

**Problem**: Deletion seems stuck

**Possible Causes**:
- Large number of chunks (>1000)
- Database is busy

**Solution**:
- Wait for confirmation message
- Check backend logs: `docker-compose logs backend -f`
- If stuck >30 seconds, refresh page and try again

---

## 📊 Monitoring Deletions

### Check Backend Logs

```bash
# Watch for deletion events
docker-compose logs backend -f | grep "🗑️"

# Example output:
🗑️  Document deleted successfully:
   Document: example.pdf
   ID: 12345678-1234-1234-1234-123456789abc
   Chunks deleted: 26
   Embeddings removed: 26
```

### Verify in Database

```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d ragchatbot

# Check if document exists
SELECT filename, processing_status
FROM documents
WHERE filename = 'example.pdf';

# Should return 0 rows if deleted
```

---

## 🎯 Best Practices

### Before Deleting

1. **Verify Document**
   - Click on the document to view chunks
   - Make sure it's the right one

2. **Check Sessions**
   - Note how many sessions use this document
   - Consider impact on existing conversations

3. **Backup (Optional)**
   - If important, export chunks first
   - Use Admin Dashboard → Database → Export

### After Deleting

1. **Verify Deletion**
   - Check success message
   - Confirm document is gone from list

2. **Re-upload if Needed**
   - If you deleted by mistake
   - Upload the document again
   - Embeddings will be regenerated

---

## 📝 Quick Reference

### Keyboard Shortcuts
- **No shortcuts** - Must use mouse to click delete button

### API Endpoint (For Developers)
```bash
DELETE /api/v1/documents/{document_id}
```

### Response Time
- Small documents (<10 chunks): <1 second
- Medium documents (10-100 chunks): 1-3 seconds
- Large documents (>100 chunks): 3-10 seconds

---

## ❓ FAQ

**Q: Can I undo a deletion?**
A: No, deletion is permanent. You'll need to re-upload the document.

**Q: Will this affect my chat history?**
A: No, your conversations remain. Sources will show "Document not found".

**Q: Can I delete multiple documents at once?**
A: Not yet. You must delete one at a time. Bulk delete is a future enhancement.

**Q: Do I need special permissions?**
A: Currently no. Any user with admin dashboard access can delete documents.

**Q: What happens to MinIO files?**
A: Physical files remain in MinIO. Only database records and embeddings are deleted.

---

## 🔗 Related Documentation

- **Feature Documentation**: `docs/features/DOCUMENT_DELETION_FEATURE.md`
- **Admin Guide**: `docs/guides/ADMIN_GUIDE.md`
- **API Reference**: `docs/api/README.md`

---

**Status**: ✅ **READY TO USE**

**Access**: Admin Dashboard → Database Tab → Documents & Embeddings

**Quick Start**:
1. Go to `/admin`
2. Click "Database" tab
3. Hover over document
4. Click 🗑️ icon
5. Confirm

---

**End of Quick Guide**
