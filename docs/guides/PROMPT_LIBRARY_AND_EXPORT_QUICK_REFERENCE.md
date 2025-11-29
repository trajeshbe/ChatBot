# 📚 Prompt Library & Export - Quick Reference

**Last Updated**: 2025-11-29
**Status**: ✅ COMPLETE AND READY

---

## 🎯 COMPLETE SYSTEM OVERVIEW

You now have **3 powerful features** fully integrated:

### 1. ⚡ Slash Command (Prompt Palette)
- **Access**: Type `/` in chat input
- **Function**: Quick access to reusable prompts
- **Navigation**: Keyboard arrows, Enter, Escape
- **Features**: Search, preview, variable detection

### 2. 📖 Prompt Library Manager
- **Access**: Click "Prompt Library" tab in sidebar (📖 BookOpen icon)
- **Function**: Full CRUD for prompts and templates
- **Features**: Create, edit, delete, search, filter, rate

### 3. 📥 Output Export
- **Access**: Click "Export Response" on any AI message
- **Function**: Export chat responses to files
- **Formats**: Excel, Word, Markdown, JSON
- **Features**: Quick export, template selection

---

## 🚀 QUICK START (3 STEPS)

### Step 1: Use a Prompt
1. Open http://localhost:3001
2. Type `/` in chat
3. Select a prompt (e.g., "Document Summarization")
4. Fill in variables and send

### Step 2: Manage Prompts
1. Click 📖 **Prompt Library** in sidebar
2. Browse existing prompts
3. Click **Create New Prompt** to add your own
4. Edit or delete prompts as needed

### Step 3: Export Results
1. Get an AI response
2. Click **Export Response** button
3. Select format (Excel, Word, Markdown, JSON)
4. Click **Quick Export**
5. File downloads automatically!

---

## 📍 WHERE TO FIND EVERYTHING

### In the UI:

```
Sidebar Navigation:
├── 💬 Chats
├── 📁 Files
├── ⬆️ Upload Files
├── 🌐 Web Scraping
├── 🧮 Project Estimator
└── 📖 Prompt Library ← NEW! (Manage prompts)

Chat Interface:
├── Type / ← Slash command palette opens
├── AI Response
│   ├── 👍👎 Feedback
│   └── 📥 Export Response ← NEW! (Export to files)
└── Input area

Prompt Library Manager:
├── [Prompts] [Templates] ← Tabs
├── Search & Filters
├── [Create New Prompt] ← Button
└── Prompt Cards
    ├── Edit icon (✏️)
    └── Delete icon (🗑️)
```

---

## 🎨 VISUAL GUIDE

### Slash Command Palette
```
┌─────────────────────────────────────────────┐
│ /entity                           [Prompts] │
├─────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────┐ │
│ │ ✓ Entity Relationship Extraction       │ │
│ │   Extract entities and relationships   │ │
│ │   📋 json  🏷️ chat                     │ │
│ ├─────────────────────────────────────────┤ │
│ │   Document Summarization               │ │
│ │   Create structured summaries          │ │
│ │   📋 markdown  🏷️ chat                 │ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ Details                                 │ │
│ │ Analyze the input text and extract...  │ │
│ │ Variables: {input_text}                 │ │
│ └─────────────────────────────────────────┘ │
│ Press ↑↓ to navigate, Enter to select,     │
│ Esc to close, Tab for details              │
└─────────────────────────────────────────────┘
```

### Prompt Library Manager
```
┌──────────────────────────────────────────────┐
│ 📚 Prompt Library Manager  [Create Prompt]  │
├──────────────────────────────────────────────┤
│ [🔍 Search] [Module▾] [Category▾] [👁Public]│
├──────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐             │
│ │Entity       │ │Document     │             │
│ │Extraction ✓ │ │Summary    ✓ │             │
│ │Extract...   │ │Create...    │             │
│ │🏷️ chat      │ │🏷️ chat      │             │
│ │📋 json      │ │📋 markdown  │             │
│ │⭐0.0 (0)    │ │⭐0.0 (0)    │             │
│ │[✏️][🗑️]     │ │[✏️][🗑️]     │             │
│ └─────────────┘ └─────────────┘             │
└──────────────────────────────────────────────┘
```

### Export Modal
```
┌──────────────────────────────────────────┐
│ 📥 Export Response               [X]     │
├──────────────────────────────────────────┤
│ Select Format                            │
│ ┌─────────┐ ┌─────────┐                 │
│ │📊 Excel │ │📄 Word  │                 │
│ │.xlsx    │ │.docx    │                 │
│ └─────────┘ └─────────┘                 │
│ ┌─────────┐ ┌─────────┐                 │
│ │📋 MD    │ │💻 JSON  │                 │
│ │.md      │ │.json    │                 │
│ └─────────┘ └─────────┘                 │
│                                          │
│ Content Preview                          │
│ ┌──────────────────────────────────────┐ │
│ │ Here's a summary...                  │ │
│ └──────────────────────────────────────┘ │
│                                          │
│ [Quick Export] [With Template]          │
└──────────────────────────────────────────┘
```

---

## ⚡ COMMON WORKFLOWS

### Workflow 1: Use Existing Prompt
```
1. Type /
2. Search "summary"
3. Select "Document Summarization"
4. Paste your text
5. Send → Get formatted summary
6. Click "Export Response"
7. Select Word
8. Click "Quick Export"
9. Done! ✅
```

### Workflow 2: Create Custom Prompt
```
1. Click 📖 Prompt Library in sidebar
2. Click "Create New Prompt"
3. Fill in:
   - Name: "Code Review"
   - Prompt: "Review {code} for {language}"
   - Module: chat
   - Format: markdown
4. Click "Create Prompt"
5. Type /code in chat
6. Your prompt appears!
7. Done! ✅
```

### Workflow 3: Export with Template
```
1. Get AI response
2. Click "Export Response"
3. Select Excel
4. Click "With Template"
5. Choose "Entity Relationship Excel"
6. Click "Export Excel"
7. Excel downloads with custom formatting
8. Done! ✅
```

---

## 🔑 KEY FEATURES

### Slash Command ⚡
- **Trigger**: `/` in chat input
- **Speed**: Instant popup
- **Search**: Real-time fuzzy search
- **Preview**: See prompt before using
- **Variables**: Auto-detected and highlighted
- **Keyboard**: Full keyboard navigation

### Prompt Library Manager 📖
- **Create**: Add new prompts with full metadata
- **Edit**: Modify existing prompts
- **Delete**: Remove unused prompts
- **Search**: Filter by name, tags, description
- **Filter**: By module, category, public/private
- **Rate**: 5-star rating system
- **Verify**: Mark quality prompts

### Output Export 📥
- **4 Formats**: Excel, Word, Markdown, JSON
- **2 Modes**: Quick export or template-based
- **Templates**: Choose from 4 seed templates
- **Preview**: See content before export
- **Download**: Automatic file download
- **Naming**: Auto-timestamped filenames

---

## 📊 CURRENT DATA

### Prompts Available (5)
1. **Entity Relationship Extraction** - Extract entities as JSON
2. **Document Summarization** - Create structured summaries
3. **Comparative Analysis** - Compare items in table format
4. **Meeting Minutes Extraction** - Extract meeting data as JSON
5. **Data Table Generation** - Generate formatted tables

### Templates Available (4)
1. **Entity Relationship Excel** - For entity extractions
2. **Summary Report (Word)** - For document summaries
3. **Formatted Notes (Markdown)** - For meeting notes
4. **Structured Data (JSON)** - For data extractions

---

## 💡 PRO TIPS

### Tip 1: Use Variables for Reusability
```
❌ Bad: "Summarize this document"
✅ Good: "Summarize {document_type} focusing on {key_aspects}"
```

### Tip 2: Tag Your Prompts
```
❌ Bad: No tags
✅ Good: Tags: "nlp, extraction, entities, json"
```

### Tip 3: Choose the Right Export Format
- **Excel**: For data you'll analyze (filter, sort, chart)
- **Word**: For reports you'll format and share
- **Markdown**: For docs you'll commit to GitHub
- **JSON**: For data you'll import into other systems

### Tip 4: Create Prompts for Your Workflow
Don't use generic prompts! Create custom ones for:
- Your industry (healthcare, finance, legal, etc.)
- Your role (analyst, developer, manager, etc.)
- Your tasks (reports, code reviews, data extraction, etc.)

### Tip 5: Rate Prompts to Build Quality Library
- Rate prompts after using them
- 5 stars = Perfect, use regularly
- 4 stars = Good, minor tweaks needed
- 3 stars = OK, needs improvement
- 1-2 stars = Delete or rewrite

---

## 🐛 TROUBLESHOOTING QUICK FIXES

### Problem: Slash command not appearing
```bash
# Solution:
1. Hard refresh: Ctrl+Shift+R
2. Check frontend: docker-compose ps frontend
3. Rebuild if needed: docker-compose build frontend --no-cache
```

### Problem: Export button not visible
```bash
# Solution:
1. Hard refresh: Ctrl+Shift+R
2. Ensure message is from assistant (not your own)
3. Check browser console (F12) for errors
```

### Problem: Prompts not loading
```bash
# Solution:
1. Check backend: docker-compose ps backend
2. Test API: curl http://localhost:8000/api/v1/prompts
3. Check browser console for errors
```

### Problem: Export download fails
```bash
# Solution:
1. Check backend logs: docker-compose logs backend | tail -50
2. Test export API:
   curl -X POST http://localhost:8000/api/v1/export \
     -H "Content-Type: application/json" \
     -d '{"content":"test","template_type":"markdown","filename":"test.md"}' \
     --output test.md
3. Check browser download settings
```

---

## 📚 COMPLETE DOCUMENTATION

For detailed information, see:

1. **Slash Command**: `SLASH_COMMAND_READY_TO_TEST.md`
2. **Prompt Library Manager**: `PROMPT_LIBRARY_MANAGEMENT_GUIDE.md`
3. **Output Export**: `OUTPUT_EXPORT_COMPLETE.md`
4. **Full Implementation**: `PROMPT_LIBRARY_UI_COMPLETE.md`

---

## 🎯 SUMMARY

### What's Available:
✅ **Slash command** - Type `/` for instant prompt access
✅ **Prompt Library Manager** - Full CRUD for prompts (📖 tab in sidebar)
✅ **Output Export** - Export AI responses to 4 file formats
✅ **5 seed prompts** - Ready to use
✅ **4 seed templates** - Ready for exports

### How to Access:
1. **Slash Command**: Type `/` in chat input
2. **Library Manager**: Click 📖 Prompt Library in sidebar
3. **Export**: Click "Export Response" on any AI message

### File Locations:
- **Frontend Components**:
  - `frontend/src/components/PromptCommandPalette.tsx`
  - `frontend/src/components/PromptLibraryManager.tsx`
  - `frontend/src/components/OutputExport.tsx`
  - `frontend/src/components/ChatInterfaceEnhanced.tsx` (integrated)
  - `frontend/src/components/SidebarModern.tsx` (navigation)

- **Backend Services**:
  - `backend/app/api/routes/prompt_library_routes.py`
  - `backend/app/services/export_service.py`
  - `backend/migrations/012_add_prompt_library_and_templates.sql`

### URL:
**http://localhost:3001**

---

## 🚀 NEXT STEPS

1. ✅ **Try slash command**: Type `/` in chat
2. ✅ **Explore prompts**: Click 📖 Prompt Library tab
3. ✅ **Create custom prompt**: Click "Create New Prompt"
4. ✅ **Export a response**: Get AI answer → Click "Export Response"
5. ✅ **Rate prompts**: Use star ratings to build quality library

---

**Everything is ready! Start using your prompt library now! 🎉**
