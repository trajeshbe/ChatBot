# Generic RAG Prototype - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Uploading Documents](#uploading-documents)
3. [Selecting LLM Models](#selecting-llm-models)
4. [Asking Questions](#asking-questions)
5. [Understanding Responses](#understanding-responses)
6. [Advanced Features](#advanced-features)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Use Case Examples](#use-case-examples)
10. [FAQ](#faq)

---

## Getting Started

### Step 1: Launch the Application

Open your terminal and navigate to the generic_rag directory:

```bash
cd /path/to/generic_rag
streamlit run rag_table.py
```

The application will automatically open in your default web browser at `http://localhost:8501`.

### Step 2: Understand the Interface

The application has two main tabs:

- **Upload Tab**: Where you upload and index PDF documents
- **Chat Tab**: Where you interact with the AI and ask questions

### Step 3: Workflow Overview

```
Upload PDF → Select Table Option → Upload → Select LLM → Ask Questions → View Answers with Sources
```

---

## Uploading Documents

### Basic Upload Process

1. **Navigate to the Upload Tab**
   - Click on the "Upload" tab at the top of the page

2. **Choose Your PDF File**
   - Click "Browse files" or drag and drop a PDF file
   - Only PDF files are supported
   - File size recommendations:
     - Small (< 10 MB): Fast processing
     - Medium (10-50 MB): Moderate processing time
     - Large (> 50 MB): May take several minutes

3. **Configure Upload Settings**

   **Table Processing Option**:
   - Unchecked (Default): Standard text extraction
     - Faster processing
     - Suitable for text-heavy documents
   - Checked: Advanced table extraction
     - Slower processing (uses LlamaParse API)
     - Better for documents with complex tables
     - Preserves table structure

   **Chunk Size** (configured in config.ini):
   - Default: 250 characters
   - Smaller chunks: More precise retrieval, may lose context
   - Larger chunks: More context, may reduce precision

4. **Click Upload Button**
   - Wait for progress indicators:
     - "Uploading file" toast notification
     - "Indexing file" toast notification
     - "Done" success message

5. **Processing Times** (approximate):
   - 10-page document (standard): ~5-10 seconds
   - 10-page document (with tables): ~15-30 seconds
   - 100-page document (standard): ~30-60 seconds
   - 100-page document (with tables): ~2-5 minutes

### Document Requirements

**Supported Formats**:
- PDF (.pdf) - only format supported

**Document Characteristics**:
- Searchable PDFs (text-based): Best results
- Scanned PDFs (image-based): May not work without OCR
- Password-protected PDFs: Not supported
- Corrupted PDFs: Will show error message

**Language Support**:
- English: Optimal performance
- Other languages: Depends on model support
  - Most models support major European languages
  - Performance may vary for non-Latin scripts

### Replacing Documents

To upload a new document:
1. Simply upload a new file in the Upload tab
2. The system will clear the previous index
3. The new document will be indexed
4. Your conversation history will be cleared

---

## Selecting LLM Models

### Available Models

The application supports multiple LLM providers:

#### Groq Models (Recommended for Speed)
1. **llama-3.1-70b-versatile**
   - Best overall performance
   - Fast inference
   - Large context window
   - Best for: Complex questions, detailed answers

2. **llama-3.2-11b-vision-preview**
   - Vision capabilities (experimental)
   - Good for multimodal tasks
   - Best for: General questions

3. **mixtral-8x7b-32768**
   - Very large context window (32k tokens)
   - Good for long documents
   - Best for: Documents with extensive context

#### HuggingFace Models
4. **mistralai/Mistral-7B-Instruct-v0.2**
   - Balanced performance
   - Moderate speed
   - Best for: General purpose use

5. **mistralai/Mixtral-8x7B-Instruct-v0.1**
   - Higher capacity than Mistral-7B
   - Slower inference
   - Best for: Complex reasoning tasks

6. **mistralai/Mistral-7B-Instruct-v0.1**
   - Earlier version of Mistral
   - Stable performance
   - Best for: General questions

### Model Selection Process

1. **Navigate to Chat Tab**
2. **Use the Model Dropdown**
   - Click "Choose the LLM Model" dropdown
   - Select your preferred model
3. **Wait for Initialization**
   - Model loads (usually instant due to caching)
   - You'll see the chat interface activate

### Model Comparison

| Model | Speed | Quality | Context | Best For |
|-------|-------|---------|---------|----------|
| llama-3.1-70b-versatile | Fast | Excellent | Large | Complex Q&A |
| mixtral-8x7b-32768 | Fast | Very Good | Very Large | Long documents |
| llama-3.2-11b-vision | Fast | Good | Medium | General use |
| Mixtral-8x7B (HF) | Moderate | Very Good | Medium | Detailed analysis |
| Mistral-7B-v0.2 (HF) | Moderate | Good | Medium | General Q&A |
| Mistral-7B-v0.1 (HF) | Moderate | Good | Medium | Simple queries |

### Switching Models

You can switch models at any time:
1. Select a different model from the dropdown
2. The conversation history is preserved
3. Subsequent questions use the new model

---

## Asking Questions

### Chat Interface

Once a model is selected:
1. **Chat Container**: Displays conversation history (400px height)
2. **Chat Input Box**: Type your questions at the bottom
3. **Send Button**: Press Enter or click to send

### Question Types

#### 1. Factual Questions
Ask for specific information from the document:

**Examples**:
- "What is the total revenue mentioned in the report?"
- "Who is the author of this paper?"
- "What are the key findings in section 3?"

**Tips**:
- Be specific about what you're looking for
- Mention section numbers or headings if known
- Use quotation marks for exact phrases

#### 2. Summary Questions
Request summaries or overviews:

**Examples**:
- "Summarize the main points of this document"
- "What are the key takeaways from chapter 2?"
- "Provide an overview of the methodology"

**Tips**:
- Specify the scope (whole document, specific section)
- Request bullet points for clarity
- Ask for summaries at different detail levels

#### 3. Comparative Questions
Compare information within the document:

**Examples**:
- "What are the differences between Model A and Model B?"
- "Compare the results in Table 1 and Table 2"
- "How does this year's performance compare to last year?"

**Tips**:
- Be clear about what you're comparing
- Specify criteria if needed
- Ask for structured comparisons (tables, lists)

#### 4. Analytical Questions
Request analysis or interpretation:

**Examples**:
- "What are the implications of these findings?"
- "Why did the revenue decrease in Q3?"
- "What patterns can be observed in the data?"

**Tips**:
- These may go beyond document content
- Model will base analysis on document information
- Results depend on model capabilities

#### 5. Clarification Questions
Follow up on previous answers:

**Examples**:
- "Can you elaborate on that?"
- "What does that term mean?"
- "Please provide more details about X"

**Tips**:
- Reference previous context
- Conversation memory helps with context
- Build on previous answers

### Question Best Practices

#### DO:
- Ask clear, specific questions
- Use proper grammar and punctuation
- Reference page numbers or sections when possible
- Break complex questions into simpler parts
- Verify critical information manually

#### DON'T:
- Ask questions unrelated to the document (without upload)
- Use extremely vague questions
- Expect information not in the document
- Assume the model remembers unlimited history
- Rely solely on AI for critical decisions

### Query Optimization

**For Better Results**:

1. **Be Specific**
   - Bad: "Tell me about revenue"
   - Good: "What was the total revenue for Q3 2023?"

2. **Provide Context**
   - Bad: "What about the other method?"
   - Good: "Compared to Method A, what are the advantages of Method B?"

3. **Use Keywords**
   - Include important terms from the document
   - Reference specific sections or tables

4. **Structured Requests**
   - "List the top 5 risks mentioned"
   - "Create a bullet-point summary of recommendations"

---

## Understanding Responses

### Response Structure

Each AI response contains:

1. **Answer Text**: The generated response
2. **View References**: Expandable section with sources

### Answer Display

- **Streaming**: Answers appear word-by-word
- **Formatting**: Markdown formatting supported
- **Length**: Varies based on question and model (max ~1200 tokens)

### Source Citations

Click "View References" to see source information:

```python
[
    {
        'Page': 5,
        'Content': 'The revenue for Q3 2023 was $1.2M...'
    },
    {
        'Page': 5,
        'Content': 'This represents a 15% increase...'
    },
    {
        'Page': 12,
        'Content': 'Compared to Q2, the growth rate...'
    }
]
```

**Information Provided**:
- **Page**: Source page number in the original PDF
- **Content**: Relevant text excerpt from the document

### Verifying Answers

Always verify critical information:

1. **Check Source Pages**: Review the cited page numbers
2. **Cross-Reference**: Compare with original document
3. **Multiple Questions**: Ask the same question differently
4. **Context Awareness**: Ensure answer makes sense

### Answer Quality Indicators

**High-Quality Answers**:
- Specific to your question
- Backed by multiple source citations
- Consistent with document content
- Clear and well-structured

**Low-Quality Answers**:
- Vague or generic
- Few or no source citations
- Contradictory information
- Off-topic responses

**If Answer Quality is Poor**:
1. Rephrase your question
2. Try a different model
3. Break complex questions into parts
4. Check if information exists in document
5. Verify document was indexed correctly

---

## Advanced Features

### 1. Table Processing

For documents with complex tables:

**How to Enable**:
1. Upload Tab → Check "With tables" checkbox
2. Upload your PDF
3. Wait for processing (slower than standard)

**Benefits**:
- Better table structure preservation
- More accurate extraction of tabular data
- Improved question answering about tables

**Example Questions for Tables**:
- "What is the value in row 3, column 2 of Table 1?"
- "Compare the performance metrics across all regions"
- "List all the products with revenue > $1M"

### 2. Conversation Memory

The system maintains conversation history:

**How It Works**:
- Previous questions and answers are remembered
- Context is maintained within the session
- Follow-up questions benefit from this memory

**Example Conversation**:
```
User: "What is the main topic of this document?"
AI: "The main topic is climate change mitigation strategies."

User: "What specific strategies are mentioned?"
AI: "Based on the previous context about climate change, the document
     mentions renewable energy, carbon capture, and reforestation."
```

**Limitations**:
- Memory clears when you refresh the page
- Limited to current session
- Very long conversations may exceed context window

### 3. Non-RAG Mode

Use LLM without uploading a document:

**How to Use**:
1. Don't upload any document
2. Select an LLM model in Chat tab
3. Ask general questions

**Use Cases**:
- General knowledge questions
- Testing different models
- Getting help with non-document queries

**Example**:
```
User: "Explain the concept of RAG in AI"
AI: "RAG (Retrieval-Augmented Generation) is a technique..."
```

### 4. Model Switching

Compare models on the same question:

**Process**:
1. Ask a question with Model A
2. Switch to Model B using dropdown
3. Ask the same question
4. Compare responses

**Benefits**:
- Find best model for your use case
- Cross-validate answers
- Optimize for speed vs. quality

---

## Best Practices

### Document Preparation

1. **Ensure Quality PDFs**
   - Use text-based PDFs when possible
   - Avoid scanned documents without OCR
   - Check PDF isn't corrupted

2. **Organize Large Documents**
   - Consider splitting very large PDFs (> 500 pages)
   - Use bookmarks or table of contents
   - Clear section headings improve retrieval

3. **Table-Heavy Documents**
   - Always use "With tables" option
   - Ensure tables are well-formatted in source
   - Test with sample questions

### Querying Strategy

1. **Start Broad, Then Narrow**
   ```
   Step 1: "What is this document about?"
   Step 2: "What are the main findings in section 3?"
   Step 3: "What specific data supports finding #2?"
   ```

2. **Use Iterative Refinement**
   - Ask initial question
   - Review answer and sources
   - Refine question based on response
   - Repeat until satisfied

3. **Leverage Source Citations**
   - Always check "View References"
   - Verify page numbers in original PDF
   - Use citations to ask follow-up questions

### Performance Optimization

1. **Choose Appropriate Models**
   - Simple queries: Mistral-7B
   - Complex analysis: Llama-3.1-70b
   - Speed priority: Groq models
   - Quality priority: Mixtral-8x7B

2. **Optimize Document Size**
   - Chunk size affects retrieval
   - Default (250) works for most cases
   - Adjust in config.ini if needed

3. **Manage Expectations**
   - AI may not find information if poorly worded
   - Very specific details may require exact keywords
   - Complex reasoning has limitations

### Security & Privacy

1. **Sensitive Documents**
   - Application runs locally
   - Documents sent to embedding API (sentence-transformers is local if run locally)
   - LLM queries sent to external APIs (HuggingFace, Groq)
   - Consider privacy implications

2. **API Key Protection**
   - Never share your config.ini
   - Keep API keys confidential
   - Rotate keys periodically

3. **Document Cleanup**
   - Uploaded files stored in `input/` folder
   - Manually delete after use if sensitive
   - Clear ChromaDB for full cleanup

---

## Troubleshooting

### Common Issues

#### Issue 1: "Config file not found" Error

**Cause**: config.ini missing or in wrong directory

**Solution**:
```bash
# Check if file exists
ls config.ini

# Ensure you're in the right directory
pwd

# Create config.ini from template if needed
```

#### Issue 2: Upload Fails

**Possible Causes & Solutions**:

1. **Invalid PDF**
   - Verify file is a valid PDF
   - Try opening in PDF reader
   - Re-download if corrupted

2. **Permission Issues**
   - Check write permissions on `input/` folder
   - Run with appropriate user permissions

3. **Large File**
   - Files > 100 MB may timeout
   - Consider splitting document
   - Increase timeout if needed

#### Issue 3: No Answer Generated

**Possible Causes & Solutions**:

1. **No Document Uploaded**
   - Upload a document first
   - Or use non-RAG mode

2. **API Key Issues**
   - Verify API keys in config.ini
   - Check key validity with provider
   - Ensure sufficient API credits

3. **Network Issues**
   - Check internet connection
   - Verify API endpoints are accessible
   - Check firewall settings

#### Issue 4: Poor Answer Quality

**Solutions**:

1. **Rephrase Question**
   - Use different keywords
   - Be more specific
   - Break into simpler questions

2. **Try Different Model**
   - Switch to larger model
   - Compare multiple models

3. **Check Document**
   - Verify information exists in document
   - Check if document indexed correctly
   - Re-upload if necessary

#### Issue 5: Slow Response

**Solutions**:

1. **Switch to Faster Model**
   - Use Groq models (llama-3.1-70b-versatile)
   - Avoid HuggingFace models during peak hours

2. **Optimize Questions**
   - Shorter, more focused questions
   - Avoid requesting lengthy summaries

3. **Check Network**
   - Verify internet speed
   - Close other applications using bandwidth

#### Issue 6: Table Data Not Extracted

**Solutions**:

1. **Enable Table Processing**
   - Re-upload with "With tables" checked
   - Verify LlamaParse API key is valid

2. **Check Table Format**
   - Complex tables may still fail
   - Ensure table is in PDF as text, not image

### Getting Help

**Check Logs**:
```bash
# View today's logs
ls logs/$(date +%d-%m-%y)/

# View current hour log
tail -f logs/$(date +%d-%m-%y)/$(date +%H).log
```

**Debug Mode**:
- Review console output in terminal
- Check Streamlit logs for errors
- Note exact error messages

---

## Use Case Examples

### Use Case 1: Financial Report Analysis

**Scenario**: Analyze quarterly financial report

**Steps**:
1. Upload quarterly_report_q3_2024.pdf
2. Don't check "With tables" (unless heavy tables)
3. Select: llama-3.1-70b-versatile

**Example Questions**:
```
Q: "What was the total revenue for Q3 2024?"
A: "According to page 3, the total revenue for Q3 2024 was $12.5M..."

Q: "How does this compare to Q2 2024?"
A: "Based on page 3 and page 15, Q3 revenue of $12.5M represents a
    8.7% increase from Q2's $11.5M..."

Q: "What were the main drivers of revenue growth?"
A: "The document identifies three main drivers on page 7:
    1. New customer acquisition (35% increase)
    2. Product line expansion (28% increase)
    3. International markets (22% increase)"
```

### Use Case 2: Research Paper Review

**Scenario**: Extract methodology from academic paper

**Steps**:
1. Upload research_paper.pdf
2. Don't check tables (unless methodology has tables)
3. Select: mistralai/Mixtral-8x7B-Instruct-v0.1

**Example Questions**:
```
Q: "Summarize the methodology used in this study"
A: "According to Section 3 (pages 5-8), the study employed a mixed-methods
    approach combining quantitative surveys (n=500) with qualitative
    interviews (n=25)..."

Q: "What were the inclusion criteria for participants?"
A: "Page 6 lists the following inclusion criteria:
    - Age 18-65
    - Diagnosed with condition X
    - No prior treatment
    - Willing to provide informed consent"

Q: "What statistical methods were used?"
A: "The paper describes multiple statistical approaches on page 9:
    - Descriptive statistics for demographics
    - T-tests for group comparisons
    - Regression analysis for predictive modeling
    - P-value threshold of 0.05"
```

### Use Case 3: Legal Contract Review

**Scenario**: Review terms in service agreement

**Steps**:
1. Upload service_agreement.pdf
2. Check "With tables" (contracts often have tables)
3. Select: llama-3.1-70b-versatile

**Example Questions**:
```
Q: "What is the termination clause?"
A: "Section 8 on page 12 outlines the termination provisions:
    Either party may terminate with 30 days written notice.
    Immediate termination allowed for material breach..."

Q: "What are the payment terms?"
A: "According to Section 4 (page 5):
    - Payment due within 30 days of invoice
    - Late fees of 1.5% per month
    - Payment methods: wire transfer, check"

Q: "Are there any liability limitations?"
A: "Yes, Section 9 (page 14) limits liability to the amount paid
    in the 12 months preceding the claim, excluding cases of
    gross negligence or willful misconduct."
```

### Use Case 4: Technical Documentation

**Scenario**: Find specific API endpoints

**Steps**:
1. Upload api_documentation.pdf
2. Don't check tables
3. Select: llama-3.2-11b-vision-preview

**Example Questions**:
```
Q: "List all authentication endpoints"
A: "The documentation lists these authentication endpoints:
    1. POST /api/v1/auth/login (page 23)
    2. POST /api/v1/auth/logout (page 24)
    3. POST /api/v1/auth/refresh (page 25)
    4. GET /api/v1/auth/verify (page 26)"

Q: "What parameters are required for the login endpoint?"
A: "According to page 23, the /api/v1/auth/login endpoint requires:
    Required parameters:
    - username (string)
    - password (string)
    Optional parameters:
    - remember_me (boolean)
    - device_id (string)"

Q: "What error codes can be returned?"
A: "Page 23 documents these possible error responses:
    - 400: Invalid credentials
    - 401: Unauthorized
    - 429: Too many attempts
    - 500: Server error"
```

---

## FAQ

### General Questions

**Q: Can I upload multiple documents at once?**
A: No, the current version supports one document at a time. Upload a new document to replace the current one.

**Q: How long are documents stored?**
A: Documents remain stored until you upload a new document or manually delete them from the `input/` folder.

**Q: Can I use scanned PDFs?**
A: Only if they have been OCR-processed. Pure image PDFs won't work.

**Q: What languages are supported?**
A: Primarily English. Other languages may work but performance varies.

**Q: Is my data secure?**
A: Documents and queries are sent to external APIs (HuggingFace, Groq, LlamaParse). Review their privacy policies for details.

### Technical Questions

**Q: How does the RAG system work?**
A: Documents are split into chunks, embedded as vectors, stored in ChromaDB. Queries retrieve relevant chunks which are sent to the LLM for answer generation.

**Q: What is the chunk size and why does it matter?**
A: Default is 250 characters. Smaller chunks give precise retrieval but may lose context. Larger chunks provide more context but may reduce precision.

**Q: Can I run this offline?**
A: No, the application requires internet access for LLM APIs and some embedding models.

**Q: How do I clear the vector database?**
A: Upload a new document (automatically clears) or manually delete the `DB/` folder.

**Q: Can I customize the LLM parameters?**
A: Yes, edit config.ini to change temperature, max_tokens, etc.

### Performance Questions

**Q: Why is LlamaParse processing so slow?**
A: LlamaParse provides advanced parsing including tables, which requires more processing time.

**Q: Which model is fastest?**
A: Groq models (llama-3.1-70b-versatile, mixtral-8x7b-32768) are generally fastest.

**Q: How can I improve answer quality?**
A: Use larger models (llama-3.1-70b, Mixtral-8x7B), ask specific questions, and enable table processing when needed.

**Q: What's the maximum document size?**
A: No hard limit, but documents > 500 pages may take very long to process. Performance depends on your system resources.

### Troubleshooting Questions

**Q: Why am I getting empty responses?**
A: Check API keys, verify document was indexed, ensure question relates to document content.

**Q: The application won't start. What should I do?**
A: Verify all dependencies are installed (`pip install -r requirements.txt`), check Python version (3.8+), ensure config.ini exists.

**Q: How do I update my API keys?**
A: Edit config.ini and update the key values. Restart the application.

**Q: Embedding model download failed. What now?**
A: Check internet connection, verify HuggingFace is accessible, try manually downloading the model, or wait and retry.

---

## Tips & Tricks

### Tip 1: Effective Question Formulation
- Use "What", "How", "Why" questions for detailed answers
- Use "List" or "Summarize" for structured responses
- Reference page numbers when you know them

### Tip 2: Handling Long Documents
- Upload document with table processing for better structure
- Ask for summaries by section
- Use specific page or section references

### Tip 3: Verifying Critical Information
- Always check source citations
- Ask the same question to different models
- Cross-reference with original document
- Don't rely solely on AI for important decisions

### Tip 4: Maximizing Model Performance
- Groq models for speed
- Mixtral models for quality
- Llama-3.1-70b for balance
- Experiment to find best fit

### Tip 5: Managing Conversations
- Start with overview questions
- Progress to specific details
- Use follow-up questions to dig deeper
- Reference previous answers in new questions

---

**Document Version**: 1.0
**Last Updated**: December 2024
**Maintained By**: Merit Software Services

**Need More Help?**
- Review the [Architecture & Design](03_architecture_design.md) document
- Check the [API Reference](04_api_reference.md) for technical details
- Consult the [Installation & Setup](02_installation_setup.md) guide
