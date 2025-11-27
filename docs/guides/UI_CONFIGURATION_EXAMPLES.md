# UI Configuration Examples - Practical Guide

**Date**: 2025-11-27
**Purpose**: Real-world examples of how to configure Weights UI for optimal responses
**Audience**: End users, administrators, power users

---

## 📋 Table of Contents

1. [Quick Reference Matrix](#quick-reference-matrix)
2. [Beginner Scenarios](#beginner-scenarios)
3. [Intermediate Scenarios](#intermediate-scenarios)
4. [Advanced Scenarios](#advanced-scenarios)
5. [Troubleshooting Configurations](#troubleshooting-configurations)
6. [Performance Optimization](#performance-optimization)

---

## Quick Reference Matrix

| Scenario | Primary Strategy | Key Settings | Expected Response Time |
|----------|-----------------|--------------|----------------------|
| General chat | `direct_llm: 0.95` | No RAG | < 2 seconds |
| Current document Q&A | `rag_short_term: 0.90` | `top_k: 5` | 3-5 seconds |
| Historical search | `rag_long_term: 0.90` | `top_k: 10-15` | 5-8 seconds |
| Web scraping | `tool_web_scraping: 0.85` | N/A | 10-30 seconds |
| PDF/Image analysis | `tool_ocr: 0.85` | N/A | 8-15 seconds |
| Smart balanced | `rag_hybrid: 0.80` | `top_k: 5-7` | 4-6 seconds |

---

## Beginner Scenarios

### Scenario 1: "I Just Want to Chat with AI"

**Use Case**: You want to use the chatbot like ChatGPT without any document retrieval.

**Configuration Steps**:

1. Open **Weights Configuration** → **Strategy** tab
2. Set sliders:
   ```
   direct_llm: 0.95  ⬆️ (slide to max)
   rag_short_term: 0.01  ⬇️ (slide to min)
   rag_long_term: 0.01  ⬇️ (slide to min)
   rag_hybrid: 0.01  ⬇️ (slide to min)
   All tool strategies: 0.01  ⬇️ (slide to min)
   ```
3. Click **"Apply to My Session"**

**What This Does**:
- ✅ Fast responses (1-2 seconds)
- ✅ No document retrieval overhead
- ✅ Pure LLM knowledge (up to training cutoff)
- ❌ Won't reference your uploaded documents
- ❌ Won't search past conversations

**Best For**:
- General knowledge questions
- Creative writing
- Coding help
- Math problems
- Explanations of concepts

**Example Queries**:
```
✅ "Explain quantum computing in simple terms"
✅ "Write a Python function to sort a list"
✅ "What are the capitals of European countries?"
❌ "What did my contract say about termination?" (needs documents)
```

---

### Scenario 2: "I Just Uploaded a Document and Want to Ask Questions"

**Use Case**: You uploaded a PDF/DOCX and want to ask questions about it immediately.

**Configuration Steps**:

1. **First, upload your document**:
   - Go to **File Upload** section
   - Drag & drop or click to upload
   - Wait for "Processing complete" message

2. Open **Weights Configuration** → **Strategy** tab
3. Set sliders:
   ```
   rag_short_term: 0.90  ⬆️ (high priority for session docs)
   direct_llm: 0.05  ⬇️
   rag_long_term: 0.02  ⬇️
   rag_hybrid: 0.01  ⬇️
   All tool strategies: 0.01  ⬇️
   ```

4. Go to **RAG Settings** tab:
   ```
   top_k: 5  (default is fine for single document)
   min_similarity_threshold: 0.3  (lower = more results)
   ```

5. Click **"Apply to My Session"**

**What This Does**:
- ✅ Searches ONLY documents uploaded in current session
- ✅ Fast and focused results
- ✅ Ignores old documents you're not working with
- ❌ Won't find info from documents uploaded yesterday

**Best For**:
- Analyzing contracts, reports, research papers
- Extracting specific information
- Summarizing documents
- Fact-checking within document

**Example Queries**:
```
✅ "What is the total budget mentioned in this document?"
✅ "Summarize the key findings from section 3"
✅ "List all the names of people mentioned"
✅ "What are the main risks identified?"
```

**Pro Tip**: If document is very large (100+ pages), increase `top_k` to 10-15 in RAG Settings.

---

### Scenario 3: "I Want to Search Across All My Documents"

**Use Case**: You have uploaded many documents over time and want to search across everything.

**Configuration Steps**:

1. Open **Weights Configuration** → **Strategy** tab
2. Set sliders:
   ```
   rag_long_term: 0.90  ⬆️ (search all documents)
   rag_short_term: 0.03  ⬇️
   direct_llm: 0.03  ⬇️
   rag_hybrid: 0.01  ⬇️
   All tool strategies: 0.01  ⬇️
   ```

3. Go to **RAG Settings** tab:
   ```
   top_k: 15  ⬆️ (retrieve more chunks across many docs)
   min_similarity_threshold: 0.4  (stricter to avoid noise)
   ```

4. Click **"Apply to My Session"**

**What This Does**:
- ✅ Searches across ALL uploaded documents (current + historical)
- ✅ Finds information even if uploaded weeks ago
- ✅ Cross-references multiple documents
- ⚠️ Slower responses (5-8 seconds)
- ⚠️ May return results from unrelated old documents

**Best For**:
- Knowledge base queries
- Research across multiple papers
- Finding precedents
- Historical analysis

**Example Queries**:
```
✅ "Find all mentions of 'project Alpha' across all documents"
✅ "Compare the budgets from Q1, Q2, and Q3 reports"
✅ "What did we say about security in past contracts?"
✅ "Show me all customer feedback about feature X"
```

---

## Intermediate Scenarios

### Scenario 4: "Smart Hybrid - Let the System Decide"

**Use Case**: You want the system to intelligently choose between session docs and all docs.

**Configuration Steps**:

1. Open **Weights Configuration** → **Strategy** tab
2. Set sliders:
   ```
   rag_hybrid: 0.80  ⬆️ (hybrid mode)
   rag_short_term: 0.08
   rag_long_term: 0.08
   direct_llm: 0.02  ⬇️
   All tool strategies: 0.01  ⬇️
   ```

3. Go to **RAG Settings** tab:
   ```
   top_k: 7  (balanced)
   min_similarity_threshold: 0.35
   ```

4. Click **"Apply to My Session"**

**What This Does**:
- ✅ Searches session documents FIRST (fast)
- ✅ Falls back to all documents if needed
- ✅ Balanced speed vs. coverage
- ✅ **Recommended default for most users**

**Decision Logic**:
```
Query arrives
    ↓
Search session documents first
    ↓
Found 3+ relevant chunks? → Use them (fast path)
    ↓
Found < 3 chunks? → Search all documents (fallback)
```

**Best For**:
- General daily use
- Mixed workloads (some current docs, some historical)
- When you're not sure what you need
- New users learning the system

**Example Queries**:
```
✅ "What is the deadline?" (checks current docs first, falls back if needed)
✅ "Compare this with last quarter" (automatically searches historical)
✅ "Summarize today's meeting notes" (uses session docs)
✅ "What was our policy on X?" (falls back to all docs)
```

---

### Scenario 5: "I Need to Scrape Data from Websites"

**Use Case**: You want to extract information from web pages or fill forms.

**Configuration Steps**:

1. Open **Weights Configuration** → **Strategy** tab
2. Set sliders:
   ```
   tool_web_scraping: 0.85  ⬆️ (web scraping mode)
   tool_navigation: 0.10
   direct_llm: 0.02
   All RAG strategies: 0.01  ⬇️
   ```

3. Click **"Apply to My Session"**

4. **Alternative Method**: Use dedicated **Web Scraper** UI component
   - Navigate to Web Scraper section
   - Enter URL
   - Optionally provide scraping prompt
   - Click "Scrape"

**What This Does**:
- ✅ Uses Playwright browser automation
- ✅ Handles JavaScript-rendered pages
- ✅ Can navigate, click, fill forms
- ✅ Extracts structured or unstructured data
- ⚠️ Slower (10-30 seconds depending on page)

**Best For**:
- Extracting product listings
- Monitoring competitor pricing
- Gathering research data
- Scraping documentation

**Example Queries (via Chat)**:
```
✅ "Scrape https://example.com/products and extract prices"
✅ "Navigate to https://docs.site.com and extract API endpoints"
✅ "Get the latest news from https://news.com/tech"
```

**Example Using Web Scraper UI**:
```
URL: https://books.toscrape.com
Scraping Prompt: "Extract book titles, prices, and ratings from all pages"
→ System navigates, extracts data, saves to session documents
→ Then you can query: "What are the top 5 highest-rated books?"
```

---

### Scenario 6: "I Have Scanned PDFs with Images/Tables"

**Use Case**: Your documents contain scanned images, charts, or complex tables.

**Configuration Steps**:

1. Open **Weights Configuration** → **Strategy** tab
2. Set sliders:
   ```
   tool_ocr: 0.85  ⬆️ (OCR/vision mode)
   tool_docling: 0.10  (fallback for structured docs)
   rag_short_term: 0.02
   direct_llm: 0.01  ⬇️
   ```

3. Click **"Apply to My Session"**

4. **Upload your scanned PDF**:
   - File Upload section
   - System automatically detects images
   - OCR processing runs

**What This Does**:
- ✅ Extracts text from images using OCR
- ✅ Analyzes charts, graphs, diagrams
- ✅ Preserves table structures
- ✅ Handles handwritten text (with limitations)
- ⚠️ Processing takes longer (8-15 seconds)

**Best For**:
- Scanned contracts/invoices
- Historical documents
- Handwritten notes
- Image-heavy reports
- Screenshots

**Example Queries**:
```
✅ "What is the invoice number in the scanned document?"
✅ "Extract the table from page 3"
✅ "What does the handwritten note say?"
✅ "Describe the chart on page 5"
```

**Pro Tip**: For best results with complex tables, use `tool_docling: 0.85` instead of OCR.

---

### Scenario 7: "I Want Fast Answers with Citation Sources"

**Use Case**: You need quick answers but also want to verify sources.

**Configuration Steps**:

1. Open **Weights Configuration** → **Strategy** tab
2. Set sliders:
   ```
   rag_hybrid: 0.80  ⬆️ (for source attribution)
   ```

3. Go to **RAG Settings** tab:
   ```
   top_k: 3  ⬇️ (fewer chunks = faster)
   min_similarity_threshold: 0.5  ⬆️ (strict = high relevance)
   ```

4. Go to **Reranking** tab:
   ```
   semantic_weight: 0.70  ⬆️ (prioritize relevance)
   keyword_weight: 0.20
   recency_weight: 0.10
   ```

5. Click **"Apply to My Session"**

**What This Does**:
- ✅ Fast responses (3-5 seconds)
- ✅ High-quality source citations
- ✅ Only shows most relevant chunks
- ❌ May miss broader context

**Best For**:
- Fact-checking
- Academic research
- Compliance verification
- Audit trails

**Example Output**:
```
Query: "What is the termination notice period?"

Answer: "The termination notice period is 30 days as stated in Section 5.3."

Sources:
📄 employment_contract.pdf (Score: 0.92)
   "Either party may terminate this agreement with 30 days written notice..."

📄 company_policy.pdf (Score: 0.85)
   "Standard termination notice: 30 calendar days..."
```

---

## Advanced Scenarios

### Scenario 8: "Multi-Document Comparative Analysis"

**Use Case**: Compare information across multiple documents and synthesize insights.

**Configuration Steps**:

1. Open **Weights Configuration** → **Strategy** tab
2. Set sliders:
   ```
   rag_long_term: 0.85  ⬆️ (access all documents)
   rag_hybrid: 0.10
   ```

3. Go to **RAG Settings** tab:
   ```
   top_k: 20  ⬆️⬆️ (retrieve many chunks)
   min_similarity_threshold: 0.25  ⬇️ (broader search)
   ```

4. Go to **Answer Fusion** tab:
   ```
   best_answer_weight: 0.5
   second_best_weight: 0.3
   third_best_weight: 0.2
   ```
   *(This weights multiple answer candidates)*

5. Go to **Source Quality** tab:
   ```
   long_term: 0.40  ⬆️ (prioritize older docs)
   short_term: 0.30
   general: 0.20
   ```

6. Click **"Apply to My Session"**

**What This Does**:
- ✅ Retrieves information from many documents
- ✅ Compares and contrasts findings
- ✅ Synthesizes cross-document insights
- ⚠️ Slower responses (8-12 seconds)
- ⚠️ Higher LLM token usage

**Best For**:
- Market research reports
- Competitive analysis
- Trend analysis over time
- Policy comparison

**Example Queries**:
```
✅ "Compare our Q1, Q2, and Q3 revenue growth"
✅ "How have customer satisfaction scores changed over the year?"
✅ "What are the common themes across all employee feedback?"
✅ "Compare our pricing strategy with competitors A, B, and C"
```

**Expected Response**:
```
The system will:
1. Retrieve 20 relevant chunks from multiple documents
2. Identify patterns and differences
3. Synthesize a comparative analysis
4. Cite specific sources for each claim
```

---

### Scenario 9: "Real-Time Web Research + Document Context"

**Use Case**: Combine live web data with your existing documents.

**Configuration Steps**:

1. Open **Weights Configuration** → **Strategy** tab
2. Set sliders:
   ```
   tool_navigation: 0.50  ⬆️ (web research)
   rag_hybrid: 0.40  ⬆️ (document context)
   tool_web_scraping: 0.05
   direct_llm: 0.03
   ```

3. Go to **Multi-Tool Weights** tab:
   ```
   navigation_agent: 0.50  ⬆️
   document_rag: 0.40  ⬆️
   web_scraping: 0.05
   ocr_tool: 0.03
   docling: 0.02
   ```

4. Click **"Apply to My Session"**

**What This Does**:
- ✅ Fetches live data from web
- ✅ Combines with your document knowledge
- ✅ Cross-references online + offline sources
- ⚠️ Slower (15-25 seconds)

**Best For**:
- Market intelligence
- Competitive monitoring
- Fact-checking with current data
- Due diligence research

**Example Queries**:
```
✅ "Compare our pricing (from internal_pricing.pdf) with current competitor prices at https://competitor.com/pricing"

✅ "Check if the statistics in our report match the latest data at https://stats.gov"

✅ "Navigate to https://news.site.com and find articles related to topics in my uploaded report"
```

**How It Works**:
```
Query: "Compare our pricing with competitor.com"
    ↓
1. Extracts "our pricing" from uploaded documents (RAG)
2. Navigates to competitor.com and scrapes pricing (Navigation Agent)
3. Compares both datasets (LLM synthesis)
4. Returns comparative analysis with sources from both
```

---

### Scenario 10: "Complex Document Processing Pipeline"

**Use Case**: Handle mixed document types (PDFs, images, Excel, websites) in one workflow.

**Configuration Steps**:

1. Open **Weights Configuration** → **Strategy** tab
2. Set sliders to **balanced multi-tool**:
   ```
   rag_hybrid: 0.40
   tool_docling: 0.25  (for Excel, structured docs)
   tool_ocr: 0.20  (for images, scanned PDFs)
   tool_web_scraping: 0.10  (for web content)
   direct_llm: 0.03
   ```

3. Go to **Multi-Tool Weights** tab:
   ```
   document_rag: 0.40
   docling: 0.25
   ocr_tool: 0.20
   web_scraping: 0.10
   navigation_agent: 0.05
   ```

4. Go to **RAG Settings** tab:
   ```
   top_k: 10
   chunk_size: 1024  ⬆️ (larger chunks for complex docs)
   chunk_overlap: 200
   ```

5. Click **"Apply to My Session"**

**What This Does**:
- ✅ Automatically selects right tool for each document type
- ✅ Handles mixed content seamlessly
- ✅ Preserves structure from Excel/tables
- ✅ Extracts text from images
- ⚠️ Processing time varies by document type

**Best For**:
- Due diligence packages
- Research collections
- Compliance audits
- Multi-source intelligence gathering

**Example Workflow**:
```
1. Upload files:
   - financial_report.pdf (text PDF)
   - scanned_contract.pdf (scanned images)
   - budget.xlsx (Excel spreadsheet)
   - logo.png (image file)

2. System automatically:
   - Uses standard RAG for financial_report.pdf
   - Uses OCR for scanned_contract.pdf
   - Uses Docling for budget.xlsx (preserves table structure)
   - Uses vision model for logo.png

3. Query: "What is the total budget and does it match the contract terms?"

4. System:
   - Extracts budget from Excel (Docling)
   - Extracts contract terms from scanned PDF (OCR)
   - Cross-references both
   - Returns synthesized answer
```

---

### Scenario 11: "Ultra-Fast Responses (Optimize for Speed)"

**Use Case**: You need the absolute fastest responses, willing to sacrifice some accuracy.

**Configuration Steps**:

1. Open **Weights Configuration** → **Strategy** tab
2. Set sliders:
   ```
   rag_short_term: 0.90  ⬆️ (session docs only)
   ```

3. Go to **RAG Settings** tab:
   ```
   top_k: 2  ⬇️⬇️ (minimal retrieval)
   min_similarity_threshold: 0.6  ⬆️ (strict matching)
   chunk_size: 512  ⬇️ (smaller chunks)
   ```

4. Go to **Reranking** tab:
   ```
   semantic_weight: 0.80  ⬆️ (skip keyword/recency)
   keyword_weight: 0.10  ⬇️
   recency_weight: 0.10  ⬇️
   ```

5. Go to **Cache** tab:
   ```
   similarity_threshold: 0.95  ⬆️ (aggressive caching)
   ttl_seconds: 3600  (1 hour cache)
   ```

6. Click **"Apply to My Session"**

**What This Does**:
- ✅ Responses in 1-3 seconds
- ✅ Caches similar queries aggressively
- ✅ Minimal retrieval overhead
- ❌ May miss relevant context
- ❌ Less comprehensive answers

**Best For**:
- Quick lookups
- FAQ answering
- Simple fact retrieval
- High-volume query scenarios

**Performance Comparison**:
```
Standard Config:  Query → 5-7 seconds → Answer
Speed-Optimized:  Query → 1-3 seconds → Answer

Trade-off: 60% faster, but answers may be less comprehensive
```

---

### Scenario 12: "Maximum Accuracy (Research Mode)"

**Use Case**: You need the most accurate, comprehensive answers regardless of speed.

**Configuration Steps**:

1. Open **Weights Configuration** → **Strategy** tab
2. Set sliders:
   ```
   rag_long_term: 0.85  ⬆️ (search everything)
   ```

3. Go to **RAG Settings** tab:
   ```
   top_k: 25  ⬆️⬆️⬆️ (maximum retrieval)
   min_similarity_threshold: 0.15  ⬇️⬇️ (very broad)
   chunk_size: 1024  ⬆️ (larger context)
   chunk_overlap: 256  ⬆️ (more overlap)
   ```

4. Go to **Reranking** tab:
   ```
   semantic_weight: 0.50
   keyword_weight: 0.30  (consider keywords)
   recency_weight: 0.20  (consider freshness)
   ```

5. Go to **Scoring Formula** tab:
   ```
   relevance_score: 0.40  ⬆️
   completeness_score: 0.30  ⬆️
   confidence: 0.20
   diversity_bonus: 0.10
   ```

6. Go to **Answer Fusion** tab:
   ```
   best_answer_weight: 0.4  ⬇️
   second_best_weight: 0.35  ⬆️
   third_best_weight: 0.25  ⬆️
   ```
   *(Consider multiple answer candidates)*

7. Click **"Apply to My Session"**

**What This Does**:
- ✅ Retrieves maximum context (25 chunks)
- ✅ Considers multiple answer perspectives
- ✅ Comprehensive, well-sourced answers
- ✅ High recall (finds everything relevant)
- ⚠️ Slower responses (10-15 seconds)
- ⚠️ Higher LLM costs (more tokens)

**Best For**:
- Academic research
- Legal analysis
- Medical literature review
- Critical decision-making
- Audit and compliance

**Example Query Comparison**:

**Standard Config** (top_k=5):
```
Query: "What are the side effects of medication X?"
Answer: "Common side effects include nausea, headache, and dizziness."
Sources: 2 documents, 5 chunks
```

**Research Mode** (top_k=25):
```
Query: "What are the side effects of medication X?"
Answer: "Common side effects include nausea (reported in 23% of cases),
headache (15%), and dizziness (12%). Less common but serious side effects
include liver dysfunction (0.5%), allergic reactions (0.3%), and cardiac
arrhythmias (0.1%). Long-term use has been associated with vitamin B12
deficiency in some patients. Pediatric patients show different safety
profiles with..."

Sources: 8 documents, 25 chunks with detailed citations
```

---

## Troubleshooting Configurations

### Problem 1: "I'm Getting Irrelevant Results"

**Symptoms**:
- AI returns information not related to your query
- Sources are from wrong documents
- Answers seem generic

**Solution**:

1. **Increase similarity threshold**:
   ```
   RAG Settings → min_similarity_threshold: 0.5 to 0.7
   ```

2. **Reduce top_k**:
   ```
   RAG Settings → top_k: 15 to 5
   ```

3. **Check your strategy**:
   ```
   If using rag_long_term, switch to rag_short_term or rag_hybrid
   ```

4. **Increase semantic reranking**:
   ```
   Reranking → semantic_weight: 0.8
   Reranking → keyword_weight: 0.15
   ```

---

### Problem 2: "I'm Not Getting Any Results"

**Symptoms**:
- "No relevant documents found"
- Empty source list
- Generic LLM answers without citations

**Solution**:

1. **Lower similarity threshold**:
   ```
   RAG Settings → min_similarity_threshold: 0.7 to 0.2
   ```

2. **Increase top_k**:
   ```
   RAG Settings → top_k: 5 to 15
   ```

3. **Check document processing**:
   ```
   Uploaded Files List → Verify "Processed: Yes"
   ```

4. **Try broader search**:
   ```
   Switch from rag_short_term to rag_long_term
   ```

---

### Problem 3: "Responses Are Too Slow"

**Symptoms**:
- Queries take 10+ seconds
- UI feels sluggish

**Solution**:

1. **Reduce top_k**:
   ```
   RAG Settings → top_k: 15 to 3
   ```

2. **Switch to faster strategy**:
   ```
   Strategy → rag_short_term: 0.90 (instead of rag_long_term)
   ```

3. **Enable aggressive caching**:
   ```
   Cache → similarity_threshold: 0.95
   Cache → ttl_seconds: 3600
   ```

4. **Use smaller chunks**:
   ```
   RAG Settings → chunk_size: 1024 to 512
   ```

5. **For general queries, use Direct LLM**:
   ```
   Strategy → direct_llm: 0.95
   ```

---

### Problem 4: "AI Isn't Using My Documents"

**Symptoms**:
- Answers don't reference uploaded files
- No sources shown
- Generic knowledge-based responses

**Solution**:

1. **Check direct_llm weight**:
   ```
   If direct_llm > 0.8, reduce to 0.05
   ```

2. **Increase RAG strategy weights**:
   ```
   Strategy → rag_short_term: 0.90
   or
   Strategy → rag_hybrid: 0.80
   ```

3. **Verify documents processed**:
   ```
   Check "Uploaded Files" list for "Processed: Yes"
   ```

4. **Check session association**:
   ```
   Ensure you're in the same session where you uploaded files
   ```

---

### Problem 5: "Getting Errors with Web Scraping"

**Symptoms**:
- "Failed to scrape URL"
- Timeout errors
- Incomplete data extraction

**Solution**:

1. **Check URL accessibility**:
   ```
   Test URL in regular browser first
   ```

2. **Increase tool weight**:
   ```
   Strategy → tool_web_scraping: 0.85
   Multi-Tool Weights → web_scraping: 0.80
   ```

3. **Try alternative method**:
   ```
   Use dedicated "Web Scraper" UI instead of chat
   Provide specific scraping prompt
   ```

4. **Handle JavaScript-heavy sites**:
   ```
   Use tool_navigation: 0.85 instead
   (Navigation agent waits for JS to render)
   ```

---

## Performance Optimization

### Optimization 1: Reduce Token Usage (Lower Costs)

**Goal**: Minimize LLM API costs while maintaining quality.

**Configuration**:

1. **RAG Settings**:
   ```
   top_k: 3 to 5 (fewer chunks = fewer tokens)
   chunk_size: 512 (smaller chunks)
   ```

2. **Answer Fusion**:
   ```
   best_answer_weight: 0.8
   second_best_weight: 0.15
   third_best_weight: 0.05
   (Rely more on single best answer)
   ```

3. **Enable caching**:
   ```
   Cache → similarity_threshold: 0.9
   Cache → ttl_seconds: 7200 (2 hours)
   ```

**Expected Savings**: 40-60% reduction in token usage

---

### Optimization 2: Maximize Recall (Don't Miss Anything)

**Goal**: Ensure all relevant information is found.

**Configuration**:

1. **RAG Settings**:
   ```
   top_k: 20 to 25
   min_similarity_threshold: 0.15 to 0.25
   ```

2. **Strategy**:
   ```
   rag_long_term: 0.90 (search everything)
   ```

3. **Scoring**:
   ```
   Scoring Formula → completeness_score: 0.40
   ```

**Trade-off**: Slower, higher cost, but comprehensive results

---

### Optimization 3: Balanced Production Settings (Recommended)

**Goal**: Good balance of speed, accuracy, and cost for production use.

**Configuration**:

1. **Strategy**:
   ```
   rag_hybrid: 0.80
   rag_short_term: 0.08
   rag_long_term: 0.08
   direct_llm: 0.02
   ```

2. **RAG Settings**:
   ```
   top_k: 7
   min_similarity_threshold: 0.35
   chunk_size: 768
   chunk_overlap: 128
   ```

3. **Reranking**:
   ```
   semantic_weight: 0.65
   keyword_weight: 0.25
   recency_weight: 0.10
   ```

4. **Cache**:
   ```
   similarity_threshold: 0.90
   ttl_seconds: 1800 (30 minutes)
   ```

5. **Scoring**:
   ```
   relevance_score: 0.35
   completeness_score: 0.25
   confidence: 0.25
   diversity_bonus: 0.15
   ```

**Expected Performance**:
- Response time: 3-6 seconds
- Good accuracy: 85-90%
- Moderate token usage
- Cache hit rate: 30-40%

---

## Quick Configuration Templates

Copy and paste these configurations for common scenarios:

### Template 1: General Chatbot
```yaml
Strategy:
  direct_llm: 0.95
  all_others: 0.01

RAG Settings:
  (not applicable)
```

### Template 2: Document Q&A
```yaml
Strategy:
  rag_short_term: 0.90

RAG Settings:
  top_k: 5
  min_similarity_threshold: 0.35
```

### Template 3: Knowledge Base Search
```yaml
Strategy:
  rag_long_term: 0.90

RAG Settings:
  top_k: 15
  min_similarity_threshold: 0.40
```

### Template 4: Smart Hybrid (Recommended Default)
```yaml
Strategy:
  rag_hybrid: 0.80
  rag_short_term: 0.08
  rag_long_term: 0.08

RAG Settings:
  top_k: 7
  min_similarity_threshold: 0.35

Reranking:
  semantic_weight: 0.65
  keyword_weight: 0.25
  recency_weight: 0.10
```

### Template 5: Web Scraping
```yaml
Strategy:
  tool_web_scraping: 0.85
  tool_navigation: 0.10

Multi-Tool Weights:
  web_scraping: 0.80
  navigation_agent: 0.15
```

### Template 6: OCR/Vision
```yaml
Strategy:
  tool_ocr: 0.85
  tool_docling: 0.10

Multi-Tool Weights:
  ocr_tool: 0.80
  docling: 0.15
```

---

## Best Practices

### ✅ Do's:

1. **Start with defaults** (Hybrid mode) and adjust based on results
2. **Test configurations** with representative queries before production
3. **Use Direct LLM** for general knowledge questions (faster, cheaper)
4. **Enable caching** to improve performance for repeated queries
5. **Monitor response times** and adjust `top_k` accordingly
6. **Document your configurations** for different use cases
7. **Lower similarity threshold** if getting "no results"
8. **Raise similarity threshold** if getting irrelevant results

### ❌ Don'ts:

1. **Don't set multiple strategies to high values** (> 0.8) - they conflict
2. **Don't use tool strategies for simple queries** - unnecessary overhead
3. **Don't set top_k too high** (> 25) - diminishing returns, slower responses
4. **Don't ignore processing status** - ensure documents are processed before querying
5. **Don't use rag_long_term** if you only need current session docs
6. **Don't disable caching** in production - significant performance gain
7. **Don't set min_similarity_threshold too low** (< 0.1) - noise in results
8. **Don't forget to click "Apply to My Session"** after changing settings

---

## Session-Specific Tips

### For New Sessions:
- Start with **rag_short_term: 0.90** to focus on uploaded docs
- Upload documents first, configure second
- Verify "Processed: Yes" before querying

### For Established Sessions:
- Consider **rag_hybrid: 0.80** to leverage both session and historical docs
- Enable caching to speed up repeated queries
- Periodically review and clean up old documents

### For Shared/Admin Sessions:
- Use **rag_long_term: 0.85** to search across all users' documents
- Increase `top_k` to 15-20 for comprehensive search
- Be aware of longer response times

---

## Monitoring Your Configuration

### Check Current Settings:
1. Open **Weights Configuration**
2. Review all tabs to see active values
3. Click "Reset to Defaults" if needed

### Verify Configuration Is Applied:
1. Submit a test query
2. Click "Show Metrics & Sources"
3. Check metadata for:
   - `routing_strategy` (e.g., "rag_hybrid")
   - `chunks_retrieved` (should match your top_k expectation)
   - `use_documents` (true/false)

### Backend Logs (Admin):
```bash
docker-compose logs backend --tail=50 | grep "Strategy routing weights"
```
Should show your configured weights.

---

## FAQ

**Q: What's the best default configuration?**
A: **Smart Hybrid** (Template 4) - `rag_hybrid: 0.80` with `top_k: 7`

**Q: Why are my responses empty?**
A: Check `docs/fixes/EMPTY_RESPONSE_FIX_COMPLETE.md` - likely a configuration issue with Direct LLM strategy.

**Q: How do I speed up responses?**
A: Reduce `top_k`, use `rag_short_term`, enable caching, or use `direct_llm` for general queries.

**Q: Can I save multiple configurations?**
A: Currently, configurations are per-session. You can manually copy slider values and reapply them.

**Q: What happens if I set all strategies to 0.50?**
A: System will normalize weights and choose based on query characteristics. Not recommended - be explicit.

**Q: Do configurations persist across sessions?**
A: Yes, configurations are saved to localStorage per session. New sessions use defaults.

---

## Additional Resources

- **Technical Deep Dive**: `docs/rag_features/RAG_STRATEGY_ROUTING_GUIDE.md`
- **Fix Documentation**: `docs/fixes/EMPTY_RESPONSE_FIX_COMPLETE.md`
- **Parameter Validation**: `docs/fixes/ALL_WEIGHTS_CONFIG_VALIDATION.md`
- **Architecture Guide**: `docs/architecture/MEMORY_HIERARCHY_GUIDE.md`

---

**End of UI Configuration Examples Guide**
