# User Guide

## Introduction

Welcome to the CRU POC User Guide. This document provides step-by-step instructions for using the CRU Retrieval-Augmented Generation (RAG) system to extract mining information and cost data from PDF documents.

## Table of Contents

1. [Getting Started](#getting-started)
2. [System Access](#system-access)
3. [User Interface Overview](#user-interface-overview)
4. [Pipeline Selection Guide](#pipeline-selection-guide)
5. [Using the System](#using-the-system)
6. [Interpreting Results](#interpreting-results)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [Frequently Asked Questions](#frequently-asked-questions)

## Getting Started

### Prerequisites

Before using the CRU POC, ensure you have:

1. **Access**: SSH access to server 172.27.137.173 or network access to the Streamlit web interface
2. **Documents**: PDF documents containing mining reports (annual reports, technical reports, etc.)
3. **Browser**: Modern web browser (Chrome, Firefox, Safari, or Edge)

### Document Requirements

**Supported Formats**:
- PDF files only
- Text-based PDFs (not scanned images without OCR)
- Any size (though processing time increases with page count)

**Optimal Document Characteristics**:
- Clear text layer (not image-only scans)
- Structured sections with headings
- Mine names mentioned in first few pages
- Cost data in tables or dedicated sections
- Standard financial reporting format

**Not Recommended**:
- Purely scanned documents without OCR
- Image-heavy presentations
- Handwritten documents
- Heavily redacted documents

## System Access

### Option 1: Direct Server Access (for administrators)

1. **SSH into the server**:
   ```bash
   ssh user@172.27.137.173
   ```

2. **Activate the conda environment**:
   ```bash
   conda activate cru_env
   ```

3. **Navigate to the working directory**:
   ```bash
   cd /home/merit/Madhan/CRU/Code
   ```

4. **Start the appropriate pipeline**:

   **LangChain Pipeline**:
   ```bash
   cd langchain_pipeline
   streamlit run home.py
   ```

   **Manual Pipeline**:
   ```bash
   cd manual_pipeline
   streamlit run home_ui.py
   ```

   **Re-Ranker Pipeline**:
   ```bash
   cd re_ranker_pipeline
   streamlit run home.py
   ```

5. **Access the interface**: Open browser to `http://172.27.137.173:8501`

### Option 2: Web Browser Access (for end users)

If the system is already running, simply navigate to:
```
http://172.27.137.173:8501
```

## User Interface Overview

### LangChain Pipeline Interface

```
┌─────────────────────────────────────────┐
│         CRU - POC                       │
├─────────────────────────────────────────┤
│  Choose a PDF file...                   │
│  [Browse Files] [No file chosen]        │
│                                         │
│  [Submit]                               │
└─────────────────────────────────────────┘
```

**Components**:
- **Title**: "CRU - POC"
- **File Uploader**: Click to browse and select PDF file
- **Submit Button**: Initiates processing after file selection

### Re-Ranker Pipeline Interface

```
┌─────────────────────────────────────────┐
│         CRU - POC                       │
├─────────────────────────────────────────┤
│  Choose a PDF file...                   │
│  [Browse Files] [No file chosen]        │
│                                         │
│  Do you want to add re-ranker?          │
│  ○ Yes  ○ No                            │
│                                         │
│  [Submit]                               │
└─────────────────────────────────────────┘
```

**Additional Component**:
- **Re-ranker Toggle**: Choose whether to enable neural re-ranking
  - **Yes**: Better accuracy, slower processing (~+3 seconds)
  - **No**: Faster processing, keyword-based relevance

### Processing Status Indicators

The system provides real-time feedback through status messages:

```
⏳ Splitting and indexing started...
✅ Indexed Successfully...
⏳ Performing retriever and QA...
⏳ Identifying mine name...
✅ Identified mine name(s) - [Mine ABC, Mine XYZ]
⏳ Getting cost information...
✅ Final Answer...
```

## Pipeline Selection Guide

### When to Use Each Pipeline

#### LangChain Pipeline

**Use When**:
- Documents have complex, context-dependent information
- Mine names are mentioned throughout the document
- Queries require semantic understanding (synonyms, paraphrases)
- Accuracy is more important than speed
- Documents are very long (100+ pages)

**Characteristics**:
- **Speed**: Moderate (10-20 seconds)
- **Accuracy**: High (semantic understanding)
- **Complexity**: High (vector search + re-ranking)
- **Best For**: Complex semantic queries

#### Manual Pipeline

**Use When**:
- Documents follow standard formats
- Mine names clearly stated on page 1
- Cost keywords are consistent
- Speed is priority
- Documents are straightforward

**Characteristics**:
- **Speed**: Fast (5-10 seconds)
- **Accuracy**: Good (keyword-based)
- **Complexity**: Low (direct Elasticsearch)
- **Best For**: Standard reports, quick analysis

#### Re-Ranker Pipeline (Recommended)

**Use When**:
- Balance of speed and accuracy needed
- Production use cases
- User wants control over accuracy/speed trade-off
- Standard to moderately complex documents

**Characteristics**:
- **Speed**: Configurable (with/without re-ranker)
- **Accuracy**: High with re-ranker, good without
- **Complexity**: Moderate (hybrid approach)
- **Best For**: General purpose, production use

**Recommendation**: Start with Re-Ranker pipeline with re-ranking enabled for best results.

## Using the System

### Workflow 1: Single Mine Query

**Scenario**: Analyzing a document focused on one primary mine property

#### Step 1: Upload Document

1. Click the file upload area
2. Select your PDF file from the file browser
3. Confirm file is loaded (filename appears)

#### Step 2: Configure Settings (Re-Ranker Pipeline Only)

1. Select "Yes" for re-ranker (recommended for accuracy)
2. Or select "No" for faster processing

#### Step 3: Submit for Processing

1. Click the "Submit" button
2. Wait for processing status messages

#### Step 4: Review Results

The system will:
1. Index the document (~1-2 seconds per page)
2. Search page 1 for mine name
3. Verify the mine name (self-check)
4. Search for cost data related to the mine
5. Display results in table format

**Example Output**:

```
┌─────────────────────────────────────────┐
│ IDENTIFIED MINE NAME                    │
│ Silver Peak Mine                        │
├─────────────────────────────────────────┤
│ RETRIEVED PAGES                         │
│ 45, 67                                  │
├─────────────────────────────────────────┤
│ QA RESPONSE                             │
│ ┌─────────────────────┬──────────────┐ │
│ │ Total Capital       │ $450M USD    │ │
│ │ Development         │ $300M        │ │
│ │ Sustaining Capital  │ $150M        │ │
│ │ Denomination        │ Million      │ │
│ └─────────────────────┴──────────────┘ │
└─────────────────────────────────────────┘
```

### Workflow 2: Multi-Mine Query

**Scenario**: Analyzing a portfolio company with multiple mining properties

#### Triggering Multi-Mine Mode

Multi-mine mode activates automatically when:
- No mine name found on page 1, OR
- The system detects multiple mine references

#### Processing Flow

1. System searches for mine-related keywords across top pages
2. LLM extracts all mine names mentioned
3. For each mine:
   - Searches cost-related pages
   - Extracts cost breakdowns
   - Compiles results
4. Displays aggregated table

**Example Output**:

```
┌──────────────────────────────────────────────────────────────┐
│                    IDENTIFIED MINE NAME                      │
├──────────────────────────────────────────────────────────────┤
│ Silver Peak Mine                                             │
├──────────────────────────────────────────────────────────────┤
│ RETRIEVED PAGES: [12, 34]                                    │
├──────────────────────────────────────────────────────────────┤
│ QA RESPONSE                                                  │
│ Total Capital Expenditure: $450M USD                         │
│ Development: $300M, Sustaining: $150M                        │
├──────────────────────────────────────────────────────────────┤
│                    IDENTIFIED MINE NAME                      │
├──────────────────────────────────────────────────────────────┤
│ Gold Mountain Property                                       │
├──────────────────────────────────────────────────────────────┤
│ RETRIEVED PAGES: [45, 78]                                    │
├──────────────────────────────────────────────────────────────┤
│ QA RESPONSE                                                  │
│ Capital Costs: $280M CAD                                     │
│ Initial: $200M, Expansion: $80M                              │
└──────────────────────────────────────────────────────────────┘
```

### Workflow 3: Processing Multiple Documents (Sequential)

**Note**: Current POC version processes one document at a time

#### Process

1. Upload and process first document
2. Review and save/copy results
3. Refresh browser or restart application
4. Upload next document
5. Repeat

**Future Enhancement**: Batch processing mode to handle multiple files simultaneously

## Interpreting Results

### Understanding the Output Structure

#### Field: Identified Mine Name

**What It Shows**: Name(s) of mine(s) or property(ies) found in the document

**Examples**:
- "Silver Peak Mine"
- "Copper Valley Project"
- "Mt. Milligan Mine"

**Note**: Names are extracted as written in the source document

#### Field: Retrieved Pages

**What It Shows**: Page numbers where cost information was found

**Format**: Comma-separated list (e.g., "45, 67, 89")

**Purpose**:
- Enables verification against source PDF
- Supports audit requirements
- Helps users understand context

**Usage**: Open the original PDF and navigate to these pages to verify extracted data

#### Field: QA Response

**What It Shows**: Structured cost information extracted by the LLM

**Common Elements**:
- **Total Capital**: Overall capital cost/expenditure
- **Development Cost**: Initial mine development expenses
- **Sustaining Capital**: Ongoing capital for maintenance
- **Operating Cash Flow**: Operational cash metrics
- **Closure Costs**: Mine closure and reclamation expenses
- **Denomination**: Scale (thousands, millions, billions)
- **Currency**: USD, CAD, AUD, etc.

**Example Formats**:

**Structured Breakdown**:
```json
{
    "Total Capital Expenditure": "$450M USD",
    "Development": "$300M",
    "Sustaining": "$150M",
    "Denomination": "Million",
    "Currency": "USD"
}
```

**Narrative Format** (when structure unclear):
```
"Total LOM Capital Expenditure is estimated at $1.2B USD
including $800M for development and $400M sustaining capital"
```

### Status Indicators

#### Success Messages

✅ **"Indexed Successfully"**: Document pages loaded into search system

✅ **"Identified mine name(s)"**: Mine extraction successful

✅ **"Final Answer"**: Complete processing, results ready

#### Warning/Error Messages

❌ **"Mine name not found"**: No mine identified on page 1 (triggers multi-mine search)

❌ **"Indexing Failed"**: Problem with PDF processing
- **Cause**: Corrupted PDF, unsupported format, or file read error
- **Action**: Verify PDF is valid, try re-uploading

❌ **"QA failed, try again"**: LLM processing error
- **Cause**: API timeout, malformed response, or context too large
- **Action**: Retry processing, check document size/complexity

⚠️ **"Unable to find cost data"**: Cost information not extracted
- **Cause**: Cost not mentioned in document or unusual terminology
- **Action**: Manually verify document has cost information

### Validating Results

#### Recommended Validation Steps

1. **Check Retrieved Pages**:
   - Open source PDF
   - Navigate to listed page numbers
   - Verify context matches extracted data

2. **Verify Mine Names**:
   - Confirm names are spelled correctly
   - Check if all mines mentioned in document are captured (for multi-mine)

3. **Validate Cost Figures**:
   - Confirm numbers match source
   - Verify denomination (thousands vs. millions)
   - Check currency matches

4. **Review Breakdowns**:
   - Ensure cost categories are correctly attributed
   - Verify totals sum correctly

#### Discrepancy Handling

If results don't match expectations:

1. **Check Source Pages**: Verify pages contain relevant information
2. **Review Original Context**: Check if information is in tables, footnotes, or unusual formats
3. **Try Alternative Pipeline**: Different retrieval strategy may work better
4. **Adjust Configuration**: Modify retrieval sizes or prompts (see Configuration section)

## Configuration

### Configuration Files

Each pipeline has a `config.ini` file controlling behavior:

**Locations**:
- LangChain: `langchain_pipeline/config.ini`
- Manual: `manual_pipeline/config.ini`
- Re-Ranker: `re_ranker_pipeline/config.ini`

### Common Configuration Parameters

#### Retrieval Parameters

**retriever_size** / **single_retriever_size**:
- **What**: Number of pages retrieved from search
- **Default**: 10-15
- **Range**: 5-20
- **Impact**: Higher = more context but slower processing

**reranker_size** / **single_reranker_size**:
- **What**: Number of pages after re-ranking
- **Default**: 1-2
- **Range**: 1-5
- **Impact**: Higher = more context for LLM but may include noise

#### Query Customization

**mine_query** / **single_mine_query**:
- **What**: Question asked to find mine names
- **Default**: "Is there any specific mine plant or property mentioned in the report?"
- **Customization**: Adjust for industry-specific terminology

**cost_query** / **single_cost_query**:
- **What**: Question asked to extract costs
- **Default**: "What are the capital cost or capital expenditure and its breakdown?"
- **Customization**: Add specific cost categories if needed

#### Prompt Templates

**mine_prompt** / **single_mine_header**:
- **What**: Instructions for mine extraction
- **Format**: Template with {context} and {question} placeholders
- **Customization**: Adjust JSON output format or instructions

**cost_prompt** / **single_cost_header**:
- **What**: Instructions for cost extraction
- **Format**: Template with {context} and {question} placeholders
- **Customization**: Emphasize specific cost categories

### Modifying Configuration

#### Step 1: Locate Configuration File

```bash
cd /path/to/pipeline
nano config.ini  # or use your preferred editor
```

#### Step 2: Edit Parameters

Example - Increase retrieval for better recall:
```ini
[query_params]
single_retriever_size = 15  # Increased from 10
single_reranker_size = 3    # Increased from 2
```

#### Step 3: Save and Restart

1. Save the config file
2. Restart the Streamlit application
3. Re-upload document to apply new settings

### Advanced Configuration

#### Elasticsearch Query Customization

**single_cost_qnt** / **cost_qnt**:
- **What**: Keywords for cost page retrieval
- **Format**: Boolean OR query
- **Example**:
  ```ini
  cost_qnt = (capital costs) OR (Total cash cost) OR
             (LOM Capital Expenditure) OR (sustaining capital)
  ```
- **Customization**: Add industry-specific cost terms

#### Chunk Settings (LangChain Only)

**chunk_size**:
- **What**: Characters per document chunk
- **Default**: 1200
- **Range**: 500-2000
- **Impact**: Smaller = more granular, larger = more context

**overlap_size**:
- **What**: Character overlap between chunks
- **Default**: 20
- **Range**: 0-100
- **Impact**: Prevents splitting concepts across boundaries

## Troubleshooting

### Common Issues and Solutions

#### Issue: No Results Returned

**Symptoms**: System completes but shows "Mine name not found" or empty results

**Possible Causes**:
1. Document is scanned image without text layer
2. Mine names use non-standard terminology
3. Cost data in unusual formats (charts, images)

**Solutions**:
1. Verify PDF has selectable text (not just images)
2. Customize mine_query to use document-specific terms
3. Try alternative pipeline
4. Manually verify document contains expected information

#### Issue: Slow Processing

**Symptoms**: Processing takes >30 seconds

**Possible Causes**:
1. Large document (100+ pages)
2. Re-ranker enabled with high retrieval size
3. Server resource constraints

**Solutions**:
1. Reduce retriever_size in config
2. Disable re-ranker for faster processing
3. Process smaller documents or document sections
4. Check server load

#### Issue: Incorrect Mine Names

**Symptoms**: Wrong mine name extracted or partial names

**Possible Causes**:
1. Multiple mines mentioned on page 1
2. Ambiguous language
3. Project names vs. mine names confusion

**Solutions**:
1. Review page 1 of source PDF
2. Adjust mine extraction prompt to be more specific
3. Use multi-mine mode to capture all mentions
4. Manually verify and select correct mine

#### Issue: Missing Cost Breakdowns

**Symptoms**: Total cost found but no breakdown, or vice versa

**Possible Causes**:
1. Breakdown in different section/page than total
2. Breakdown in table format (hard to parse)
3. Insufficient pages retrieved

**Solutions**:
1. Increase retriever_size to capture more pages
2. Check if breakdown is in footnotes or appendix
3. Manually extract breakdown from retrieved pages
4. Customize cost_query to specifically request breakdowns

#### Issue: Malformed JSON Response

**Symptoms**: Raw text instead of structured data, or parsing errors

**Possible Causes**:
1. LLM generated non-JSON response
2. Complex cost structure exceeds LLM capacity
3. Ambiguous information in source

**Solutions**:
1. Retry processing (LLM may succeed on second attempt)
2. Simplify cost_prompt to request simpler structure
3. Review retrieved pages for clarity
4. Use raw text response and manually structure

### Error Messages Reference

| Error Message | Meaning | Action |
|---------------|---------|--------|
| "Indexing Failed" | PDF processing error | Verify PDF validity, check file permissions |
| "Config Error" | Configuration file issue | Review config.ini syntax |
| "Mine name not found" | No mine on page 1 | Normal - triggers multi-mine mode |
| "QA failed try again" | LLM processing error | Retry upload, check API connectivity |
| "Unable to find cost data" | Cost pages not retrieved | Increase retriever_size or verify document has cost info |

## Best Practices

### Document Preparation

1. **Use Text-Based PDFs**: Ensure PDFs have selectable text layers
2. **Standard Formats**: Documents following industry standards work best
3. **Clear Naming**: Save files with descriptive names for tracking
4. **Size Optimization**: <50MB files process faster

### Query Strategy

1. **Start with Re-Ranker**: Use Re-Ranker pipeline with re-ranking enabled as default
2. **Verify Results**: Always check retrieved pages against source
3. **Iterative Refinement**: If results unclear, adjust config and retry
4. **Document Findings**: Keep notes on which settings work for different document types

### Performance Optimization

1. **Disable Re-Ranker for Speed**: When quick estimates needed
2. **Process During Off-Peak**: Large documents during low-usage times
3. **Batch Planning**: Queue multiple documents for sequential processing
4. **Save Results Immediately**: Copy/export results before processing next document

### Accuracy Maximization

1. **Use Re-Ranking**: Enable neural re-ranking for best precision
2. **Verify Ambiguous Results**: Manual check when LLM expresses uncertainty
3. **Cross-Reference**: Compare results across pipelines for validation
4. **Prompt Tuning**: Customize prompts for specific document sets

## Frequently Asked Questions

### General Questions

**Q: What types of mining documents does the system support?**

A: Annual reports, technical reports (NI 43-101, JORC), feasibility studies, quarterly filings, and investor presentations. Any PDF with text-based content about mines and costs.

**Q: Can I process multiple PDFs at once?**

A: Current POC version processes one document at a time. Sequential processing is required.

**Q: How long does processing take?**

A: Single mine: 5-15 seconds. Multi-mine: 15-60 seconds depending on number of mines and document size.

**Q: Is my data secure?**

A: Documents are processed locally. Only prompts and retrieved content are sent to OpenAI API. Original PDFs are stored temporarily and can be deleted after processing.

### Technical Questions

**Q: Which pipeline should I use?**

A: Start with Re-Ranker pipeline (re-ranking enabled) for best balance. Use Manual for speed, LangChain for complex semantic queries.

**Q: Can I customize the questions asked?**

A: Yes, edit the config.ini file's query section. Restart the application after changes.

**Q: Why does the system sometimes return page 1 only?**

A: For single mine mode, the system searches page 1 first as mine names are typically introduced early in reports.

**Q: What if my document has mine names in different languages?**

A: GPT-3.5-turbo supports multiple languages. Results may be returned in the source language. Prompts can be customized for specific languages.

### Results Questions

**Q: Why are some cost breakdowns incomplete?**

A: Possible causes: (1) Information spread across multiple pages not all retrieved, (2) Data in image/chart format, (3) Non-standard terminology. Try increasing retriever_size.

**Q: How accurate are the results?**

A: Typically 90%+ for mine names, 85%+ for cost extraction in standard reports. Always verify against source pages.

**Q: Can I export results?**

A: Currently, results are displayed in the browser. Copy/paste into Excel or use screenshot for export. Future versions may include direct export.

**Q: What does the "flag" field mean in JSON responses?**

A: "True" = information found and extracted. "False" = information not found in retrieved pages.

## Getting Help

### Support Resources

**Documentation**: Refer to technical architecture and functional architecture docs for deeper understanding

**Configuration Examples**: Review sample config files in each pipeline directory

**Logs**: Check console output for detailed error messages and debugging info

### Reporting Issues

When reporting problems, include:
1. Pipeline used (LangChain, Manual, or Re-Ranker)
2. Document characteristics (pages, type, format)
3. Error message or unexpected behavior
4. Configuration settings if modified
5. Steps to reproduce

## Conclusion

The CRU POC system provides a powerful, flexible tool for extracting mining information from complex PDF documents. By following this guide and applying best practices, users can efficiently analyze mining reports, extract critical financial data, and make informed decisions based on accurate, verifiable information.

For optimal results:
- Use the Re-Ranker pipeline with re-ranking enabled
- Always verify results against source pages
- Customize configuration for your specific document types
- Leverage multi-mine mode for portfolio analysis

Happy mining data extraction!
