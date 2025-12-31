# Vendor Recommendation System - User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [User Interface Overview](#user-interface-overview)
4. [Vendor-Tender Matching](#vendor-tender-matching)
5. [Understanding Results](#understanding-results)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

## Introduction

The Vendor Recommendation System helps procurement professionals and business development teams quickly match vendor capabilities with tender requirements using AI-powered analysis.

### Who Should Use This Guide
- Procurement officers
- Business development managers
- Contract analysts
- Tender managers
- Vendor relationship managers

### What You'll Learn
- How to upload and process documents
- How to interpret matching results
- Best practices for optimal results
- Common issues and solutions

## Getting Started

### Launching the Application

1. Open your terminal or command prompt
2. Navigate to the project directory
3. Activate your virtual environment (if applicable)
4. Run the command:
   ```bash
   streamlit run app.py
   ```
5. Your default web browser will open automatically
6. If not, navigate to: http://localhost:8501

### First-Time Setup Checklist

- [ ] Application launches successfully
- [ ] No error messages in the terminal
- [ ] Web interface loads properly
- [ ] Sample data files are available in `data/` folder
- [ ] API credentials are configured

## User Interface Overview

### Main Interface Components

The application features a clean, intuitive interface with the following elements:

#### 1. Page Header
- **Title**: "Recommendation - Tender2Vendor"
- Indicates the current functionality

#### 2. File Upload Section
Contains two file uploaders:
- **Tender Documents Uploader**: Accepts PDF files
- **Vendor Profile Uploader**: Accepts TXT files

#### 3. Submit Button
- Processes uploaded files
- Triggers the matching analysis

#### 4. Progress Indicator
- Shows processing status
- Displays "Please wait..." during analysis
- Progress bar for multiple tender files

#### 5. Results Display
- Tabular view of matching results
- Sortable by confidence score
- Full-width display for easy reading

## Vendor-Tender Matching

### Step-by-Step Process

#### Step 1: Prepare Your Documents

**Tender Documents (PDF)**:
- Ensure PDFs are text-based (not scanned images)
- Multiple tender files can be uploaded simultaneously
- Recommended maximum file size: 10MB per file
- Include complete tender specifications

**Vendor Profile (TXT)**:
- Create a plain text file with vendor information
- Include relevant details (see format below)
- Use clear, structured formatting
- Save with UTF-8 encoding

#### Step 2: Upload Tender Documents

1. Click on "Please upload tender documents(s)"
2. Browse and select one or more PDF files
3. Supported format: PDF only
4. Multiple files: Hold Ctrl/Cmd to select multiple files
5. Verify files appear in the upload area

**Accepted Tender Information**:
- Project requirements
- Technical specifications
- Scope of work
- Deliverables
- Industry/sector information
- Geographic location
- Timeline and milestones

#### Step 3: Upload Vendor Profile

1. Click on "Please upload the vendor profile"
2. Browse and select a TXT file
3. Supported format: TXT only
4. Single file only
5. Verify file appears in the upload area

**Recommended Vendor Profile Format**:
```
Vendor Name: [Company Name]

Industries: [Industry 1], [Industry 2], [Industry 3]

Capabilities:
- [Capability 1]
- [Capability 2]
- [Capability 3]

Locations Served: [Country/Region 1], [Country/Region 2]

Certifications: [Cert 1], [Cert 2]

Company Size: [Employee count or size category]

Past Projects:
- [Project 1 description]
- [Project 2 description]

Vendor Search History (optional):
"[search query 1]"
"[search query 2]"
```

**Example Vendor Profile**:
```
Vendor Name: TechSolutions Ltd

Industries: Healthcare, IT Services, Cloud Computing

Capabilities:
- Cloud infrastructure deployment
- Healthcare data management systems
- HIPAA-compliant solutions
- 24/7 technical support

Locations Served: United Kingdom, Europe, North America

Certifications: ISO 27001, ISO 9001, HIPAA Certified

Company Size: 200-300 employees

Past Projects:
- Deployed cloud EHR system for hospital network
- Implemented secure data backup for healthcare provider
- Migration of legacy systems to cloud platform
```

#### Step 4: Submit for Analysis

1. Review uploaded files
2. Click the "Submit" button
3. Wait for processing to complete
4. Monitor the progress bar

**Processing Time**:
- Single tender: 10-30 seconds
- Multiple tenders: 30 seconds - 2 minutes
- Depends on document length and complexity

#### Step 5: Review Results

Results appear in a sortable table with the following columns:
- **Vendor_Name**: Name of the vendor being evaluated
- **Tender_Title**: Title or identifier of the tender
- **Confidence_Score**: Match score between 0.1 and 1.0
- **Justification**: Detailed explanation of the match

## Understanding Results

### Confidence Score Interpretation

The system generates a confidence score between 0.1 and 1.0:

| Score Range | Interpretation | Recommendation |
|------------|----------------|----------------|
| 0.9 - 1.0 | Excellent Match | Highly recommended - Strong alignment |
| 0.7 - 0.89 | Good Match | Recommended - Substantial alignment |
| 0.5 - 0.69 | Moderate Match | Consider - Partial alignment |
| 0.3 - 0.49 | Weak Match | Review carefully - Limited alignment |
| 0.1 - 0.29 | Poor Match | Not recommended - Minimal alignment |

### Scoring Criteria

The AI evaluates alignment based on:

1. **Capabilities Alignment**
   - Technical skills match
   - Service offerings relevance
   - Solution types compatibility

2. **Industry Experience**
   - Sector expertise
   - Domain knowledge
   - Similar project history

3. **Geographic Coverage**
   - Service locations
   - Regional presence
   - Market knowledge

4. **Certifications & Compliance**
   - Required certifications
   - Industry standards
   - Regulatory compliance

5. **Technical Requirements**
   - Technology stack
   - Tools and platforms
   - Integration capabilities

### Justification Analysis

The justification field provides:
- **Strengths**: Areas of strong alignment
- **Matches**: Specific matching criteria
- **Capabilities**: Relevant vendor capabilities
- **Experience**: Related past projects

**Example Justification**:
```
Strong match due to:
- Vendor has extensive healthcare IT experience
- Certified in required compliance standards (HIPAA, ISO 27001)
- Successfully delivered similar cloud-based EHR systems
- Serves the same geographic region
- Possesses required technical capabilities in cloud infrastructure
```

### Sorting and Filtering Results

#### Sort by Confidence Score
- Results are automatically sorted by confidence score (highest first)
- Click column header to re-sort
- Helps prioritize vendor outreach

#### Analyze Multiple Tenders
- Each tender is evaluated separately
- Compare scores across different tenders
- Identify vendors suitable for multiple opportunities

## Best Practices

### Document Preparation

#### For Tender Documents

1. **Use Complete Documents**
   - Include full tender specifications
   - Don't use abbreviated versions
   - Ensure all requirements are listed

2. **Text-Based PDFs**
   - Avoid scanned images
   - Use native PDF format
   - Ensure text is selectable

3. **Clear Structure**
   - Well-organized sections
   - Clear headings
   - Logical flow

4. **Comprehensive Information**
   - Technical requirements
   - Functional specifications
   - Industry/sector details
   - Geographic scope

#### For Vendor Profiles

1. **Be Specific**
   - List concrete capabilities
   - Mention specific technologies
   - Include measurable achievements

2. **Stay Relevant**
   - Focus on core competencies
   - Highlight differentiators
   - Emphasize recent experience

3. **Use Standard Terminology**
   - Industry-standard terms
   - Common certifications
   - Recognized technologies

4. **Update Regularly**
   - Keep information current
   - Add new capabilities
   - Update certifications

### Optimization Tips

#### Improve Matching Accuracy

1. **Use Detailed Descriptions**
   - More context improves analysis
   - Include specific examples
   - Provide comprehensive information

2. **Maintain Consistent Format**
   - Use structured vendor profiles
   - Follow recommended template
   - Standardize information presentation

3. **Include Keywords**
   - Industry-specific terms
   - Technical keywords
   - Certification names
   - Geographic identifiers

4. **Quality Over Quantity**
   - Relevant information is key
   - Avoid generic statements
   - Focus on differentiating factors

#### Batch Processing

For multiple tenders:
1. Upload all tender PDFs at once
2. Use a comprehensive vendor profile
3. Process in single batch for efficiency
4. Review results collectively
5. Sort by confidence score for prioritization

### Interpreting Edge Cases

#### High Score, Unclear Justification
- Review vendor profile for completeness
- Check if tender has specific requirements
- May indicate generic match

#### Low Score, Despite Apparent Match
- Check for missing keywords in vendor profile
- Verify all capabilities are explicitly stated
- Consider updating vendor profile

#### Inconsistent Scores Across Similar Tenders
- Review tender documents for differences
- Check for specific requirements variations
- Analyze justifications for insights

## Troubleshooting

### Common Issues

#### Issue: File Upload Fails

**Symptoms**: Error message or file doesn't upload

**Solutions**:
1. Check file format (PDF for tenders, TXT for vendors)
2. Verify file size (< 10MB recommended)
3. Ensure file is not corrupted
4. Try renaming file (avoid special characters)
5. Check file permissions

#### Issue: "Server busy" Message

**Symptoms**: Warning message after submission

**Solutions**:
1. Wait a few moments and try again
2. Check internet connection
3. Verify API key is valid
4. Check OpenAI service status
5. Review error logs for details

#### Issue: No Results Displayed

**Symptoms**: Submit completes but no table appears

**Solutions**:
1. Refresh the page
2. Re-upload files
3. Check console for errors
4. Verify files contain valid content
5. Review application logs

#### Issue: PDF Reading Error

**Symptoms**: Warning about PDF reading failure

**Solutions**:
1. Ensure PDF is not password-protected
2. Verify PDF contains selectable text
3. Try converting scanned PDFs using OCR
4. Use different PDF file
5. Check PDF is not corrupted

#### Issue: Low Confidence Scores

**Symptoms**: All matches show low scores

**Solutions**:
1. Review vendor profile completeness
2. Ensure capabilities are explicitly stated
3. Add more specific details
4. Include relevant keywords
5. Match terminology with tender

### Error Messages

| Error Message | Meaning | Solution |
|--------------|---------|----------|
| "Config file not found" | Missing config.yaml | Ensure config.yaml exists in root |
| "Failed to read txt file" | Vendor profile unreadable | Check file encoding (use UTF-8) |
| "Failed to read pdf file" | Tender PDF unreadable | Verify PDF is valid and text-based |
| "Server busy" | API or processing issue | Wait and retry |

## FAQ

### General Questions

**Q: How many tender documents can I upload at once?**
A: The system supports multiple PDF uploads. For optimal performance, upload 5-10 tenders at a time.

**Q: Can I upload multiple vendor profiles?**
A: Currently, the system processes one vendor profile at a time. To evaluate multiple vendors, run separate analyses.

**Q: How long does processing take?**
A: Typically 10-30 seconds per tender. Multiple tenders may take 1-2 minutes total.

**Q: Is my data stored or shared?**
A: Documents are temporarily stored locally during processing. Data sent to OpenAI API follows their privacy policy.

**Q: Can I export results?**
A: Currently, results are displayed on-screen. You can copy the table data or take screenshots. Future versions may include export functionality.

### Technical Questions

**Q: What makes a good vendor profile?**
A: Detailed, specific information about capabilities, experience, certifications, and past projects relevant to the tender types you're analyzing.

**Q: Why do similar vendors get different scores for the same tender?**
A: Scores reflect the specific capabilities and details in each vendor profile. Even similar vendors may have different documented strengths.

**Q: Can the system handle non-English documents?**
A: The system is optimized for English. Other languages may work but results may vary.

**Q: How is the confidence score calculated?**
A: The AI model analyzes semantic similarity between tender requirements and vendor capabilities, considering multiple factors like experience, certifications, and technical fit.

**Q: Can I customize the scoring criteria?**
A: Currently, the criteria are predefined. Customization would require code modifications to the prompt templates.

### Best Practice Questions

**Q: Should I include pricing information in vendor profiles?**
A: No. The system focuses on technical/functional alignment, not commercial terms. Pricing is not evaluated.

**Q: How often should I update vendor profiles?**
A: Update whenever there are significant changes to capabilities, certifications, or major project completions.

**Q: What's the ideal length for a vendor profile?**
A: Include all relevant information without redundancy. Typically 300-800 words is effective.

**Q: Should I use the actual tender title in the PDF?**
A: Yes, clear tender titles help with organization and identification in the results.

**Q: Can I use this for pre-qualification screening?**
A: Yes, it's an excellent tool for initial vendor screening and shortlisting for tenders.

## Tips for Success

### For Procurement Teams

1. **Standardize Vendor Profiles**
   - Create templates for vendor data collection
   - Maintain a library of vendor profiles
   - Regular updates from vendors

2. **Build a Tender Library**
   - Categorize past tenders
   - Document outcomes
   - Learn from patterns

3. **Combine with Manual Review**
   - Use as first-pass screening tool
   - Supplement with expert judgment
   - Consider additional factors beyond capabilities

### For Business Development

1. **Monitor Opportunities**
   - Regularly test your profile against new tenders
   - Identify match patterns
   - Adjust capabilities presentation

2. **Competitive Analysis**
   - Understand what makes high-scoring matches
   - Identify capability gaps
   - Focus on differentiators

3. **Profile Optimization**
   - A/B test different profile formats
   - Include specific case studies
   - Use industry-standard terminology

## Getting Help

### Support Resources

1. **Documentation**
   - Review other documentation files
   - Check API reference for technical details
   - Consult installation guide for setup issues

2. **Log Files**
   - Check `logs/error_logs.json` for errors
   - Review `logs/info_logs.json` for processing info
   - Logs provide detailed troubleshooting information

3. **Community**
   - Streamlit community forums
   - LangChain documentation
   - OpenAI support resources

## Next Steps

After mastering the basics:
1. Experiment with different vendor profile formats
2. Analyze patterns in high-scoring matches
3. Build a library of optimized vendor profiles
4. Review Technical Architecture for system understanding
5. Explore API Reference for advanced usage

---

**Remember**: This tool is designed to assist decision-making, not replace professional judgment. Always review results in the context of your specific requirements and organizational needs.
