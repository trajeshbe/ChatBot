# Planning Document Classifier - User Guide

## Introduction

Welcome to the Planning Document Classifier user guide. This document will help you understand how to use the application effectively to classify planning and construction documents automatically using AI.

### What This Tool Does

The Planning Document Classifier analyzes PDF planning documents and automatically categorizes them into standardized construction types. It provides:
- Main classification category (e.g., Residential, Commercial)
- Detailed sub-classification (e.g., Multi-Family Housing, Office Buildings)
- Justification explaining why the document was classified that way

### Who Should Use This Guide

- Urban planners and planning officers
- Construction project managers
- Document management staff
- Regulatory compliance officers
- Anyone working with planning documentation

---

## Getting Started

### System Requirements

#### Browser Requirements
- **Supported Browsers**:
  - Google Chrome (recommended)
  - Mozilla Firefox
  - Microsoft Edge
  - Safari

- **Browser Settings**:
  - JavaScript enabled
  - Cookies enabled (for session management)
  - Minimum screen resolution: 1024x768

#### Internet Connection
- Active internet connection required
- Minimum speed: 1 Mbps
- Recommended: 5+ Mbps for optimal performance

#### Document Requirements
- **File Format**: PDF only
- **Text Requirement**: PDF must contain extractable text (not scanned images)
- **File Size**: Up to 100MB (recommended under 20MB)
- **Language**: English language documents
- **Content Type**: Planning statements, design & access statements, impact assessments

### Accessing the Application

1. **Open Your Browser**
   - Launch your preferred web browser

2. **Navigate to Application URL**
   - Enter the URL provided by your administrator
   - Example: `https://your-deployment-url.com`

3. **Verify Application Loaded**
   - You should see the title "📋 Document Classifier"
   - Instructions should be visible
   - Upload panel should appear on the left

---

## Understanding the Interface

### Screen Layout

```
┌─────────────────────────────────────────────────────────────┐
│  📋 Document Classifier                                      │
├─────────────────────────────────────────────────────────────┤
│  Upload a planning PDF document to classify its             │
│  construction type using AI.                                │
│                                                             │
│  📝 Instructions:                                           │
│  1. Upload a PDF document                                   │
│  2. Click the "Classify Document" button                    │
│  3. View the AI-generated classification results            │
│                                                             │
│  🏗️ Classification Types:                                  │
│  • 🏠 Residential: Single-Family Homes, Multi-Family...     │
│  • 🏢 Commercial: Office Buildings, Retail Stores...        │
│  • 🏛️ Institutional: Healthcare, Educational...            │
│  • 🏗️ Infrastructure: Industrial, Energy, Transport...     │
│  • 🌳 Recreational: Parks, Sports Facilities...             │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│  📂 Upload & │    📊 Classification Results                 │
│    Process   │                                              │
│              │    👈 Please upload a PDF document to begin  │
│  [Choose     │       classification                         │
│   File]      │                                              │
│              │                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

### Interface Elements

#### Top Section - Instructions
- **Purpose**: Provides quick reference for using the application
- **Content**:
  - Step-by-step instructions
  - Classification categories overview
  - Examples of each document type

#### Left Panel - Upload & Process (20% width)
- **File Upload Widget**: Drag-and-drop or click to browse
- **Process Button**: Triggers classification (appears after upload)

#### Right Panel - Classification Results (80% width)
- **Results Display**: Shows classification after processing
- **Status Messages**: Provides feedback during processing

### Classification Categories Reference

The application classifies documents into 5 main categories with 27 sub-categories:

#### 🏠 Residential
Projects involving housing and living spaces.

**Sub-Categories**:
- **Single-Family Homes**: Individual houses for single families
- **Multi-Family Housing**: Apartments, flats, townhomes
- **Affordable Housing**: Cost-accessible housing developments
- **Senior or Assisted Living**: Facilities for elderly care
- **Student Housing**: Purpose-built student accommodation
- **Mixed Use**: Residential combined with commercial space

**Example Documents**:
- Planning applications for housing estates
- Design statements for apartment buildings
- Affordable housing proposals

#### 🏢 Commercial
Business and retail facilities.

**Sub-Categories**:
- **Office Buildings**: Corporate and administrative buildings
- **Retail (High Street or Standalone)**: Shops and stores
- **Supermarket/Foodstore**: Grocery and food retail
- **Shopping Centre/Retail Park**: Multiple retail units
- **Hospitality (Hotels, Hostels)**: Accommodation services
- **Restaurants/Cafes/Drive-thru**: Food service establishments
- **Warehousing/Distribution**: Storage and logistics facilities
- **Mixed Use (Retail/Office)**: Combined retail and office space

**Example Documents**:
- Office development proposals
- Retail park planning statements
- Restaurant change of use applications

#### 🏛️ Institutional
Public service and civic buildings.

**Sub-Categories**:
- **Healthcare**: Hospitals, clinics, medical facilities
- **Education**: Schools, colleges, universities
- **Government/Civic Buildings**: Municipal and government facilities
- **Community Facilities**: Libraries, community halls, cultural centers
- **Religious Institutions**: Churches, mosques, temples, synagogues

**Example Documents**:
- School extension proposals
- Hospital development applications
- Community center planning statements

#### 🏗️ Infrastructure
Industrial and utility installations.

**Sub-Categories**:
- **Industrial**: Manufacturing and processing plants
- **Energy**: Renewable energy, power stations, substations
- **Transportation**: Bus/rail/airport terminals
- **Parking Structures**: Multi-level or surface car parks
- **Logistics Hubs/Depots**: Distribution centers
- **Data Centres/Telecom Infrastructure**: Server farms, telecom facilities

**Example Documents**:
- Solar farm planning applications
- Distribution center proposals
- Data center development statements

#### 🌳 Recreational
Leisure and public spaces.

**Sub-Categories**:
- **Parks/Green Spaces**: Public parks and open spaces
- **Sports Facilities/Arenas**: Stadiums, gyms, sports centers
- **Event Venues/Outdoor Structures**: Concert venues, event spaces
- **Temporary Structures/Permitted Events**: Temporary installations

**Example Documents**:
- Park development proposals
- Sports facility planning applications
- Event venue planning statements

---

## Step-by-Step Instructions

### Basic Workflow

#### Step 1: Prepare Your Document

1. **Locate Your PDF File**
   - Ensure it's a planning-related document
   - Verify it's in PDF format
   - Check that text is selectable (not a scanned image)

2. **Document Quality Check**
   - Open PDF in a PDF reader
   - Try selecting text with your cursor
   - If text can't be selected, you'll need to OCR the document first

**Good Document Examples**:
- Planning statements (PDF with selectable text)
- Design and access statements (native PDF)
- Environmental impact assessments (text-based PDF)

**Documents That Won't Work**:
- Scanned PDFs without OCR
- Image files (JPG, PNG)
- Word documents (convert to PDF first)

#### Step 2: Upload Your Document

1. **Locate the Upload Widget**
   - Look for the left panel labeled "📂 Upload & Process"
   - Find the "Choose a PDF file" button

2. **Select Your File**

   **Option A - Click to Browse**:
   - Click the "Browse files" button
   - Navigate to your document location
   - Select the PDF file
   - Click "Open"

   **Option B - Drag and Drop**:
   - Open your file explorer
   - Locate the PDF file
   - Drag it onto the upload widget
   - Drop it when the widget highlights

3. **Verify Upload**
   - You should see a "🔍 Classify Document" button appear
   - The button should be highlighted in blue

#### Step 3: Classify the Document

1. **Click the "Classify Document" Button**
   - The button is in the left panel
   - It's blue/primary colored for visibility

2. **Wait for Processing**

   **You'll see these stages**:

   a. **Text Extraction** (2-10 seconds)
      - Progress bar shows page-by-page extraction
      - Status text shows "Processing page X of Y"

   b. **AI Classification** (10-20 seconds)
      - Spinner shows "Classifying document using AI..."
      - This is when the AI analyzes your document

   c. **Results Display** (immediate)
      - "✅ Classification completed!" message appears
      - Results populate the right panel

3. **Review the Progress**
   - Don't refresh the page during processing
   - Don't click the button again
   - Wait for the completion message

#### Step 4: Review Results

The results appear in the right panel with three components:

1. **Construction Class**
   - Displayed in the top-left result box
   - Shows the main category (e.g., "Residential")
   - Blue highlighted box

2. **Sub Class**
   - Displayed in the top-right result box
   - Shows the specific sub-category (e.g., "Multi-Family Housing")
   - Blue highlighted box

3. **Justification**
   - Displayed below the class boxes
   - Explains why this classification was chosen
   - References specific content from your document
   - Usually 2-5 sentences

**Example Result**:
```
┌─────────────────────────┬──────────────────────────┐
│ 🏗️ Construction Class:  │ 🏢 Sub Class:            │
│ Commercial              │ Office Buildings         │
└─────────────────────────┴──────────────────────────┘

📝 Justification:
The document describes a planning application for a 5-story
office building with 10,000 sq ft of workspace. The planning
statement references 'commercial lease arrangements' and
'business park location', clearly indicating office use.
Additional mentions of 'parking for 50 vehicles' and
'reception area' further support office classification.
```

#### Step 5: Use the Results

**Copying Results**:
- Click and drag to select text
- Right-click and choose "Copy"
- Or use Ctrl+C (Windows) or Cmd+C (Mac)

**Recording Results**:
- Copy to spreadsheet for record-keeping
- Save to document management system
- Include in planning file notes

**Next Document**:
- Upload another PDF to classify more documents
- Previous results will be replaced
- No limit on number of documents

---

## Common Tasks

### Classifying Multiple Documents

**Process**:
1. Upload and classify first document
2. Review and record results
3. Upload next document (previous results will clear)
4. Repeat for all documents

**Tip**: Keep a spreadsheet open to record results as you go.

**Example Workflow**:
```
Document 1 → Upload → Classify → Copy results to spreadsheet
Document 2 → Upload → Classify → Copy results to spreadsheet
Document 3 → Upload → Classify → Copy results to spreadsheet
...
```

### Handling Large Documents

**If your document is very long**:

1. **The system automatically handles this**:
   - Text is truncated to 45,000 characters
   - Truncation happens at sentence boundaries
   - Classification uses the available content

2. **You'll see a note if truncated**:
   - Check the justification
   - AI still provides accurate classification
   - Based on the first ~90-120 pages typically

3. **Best Practices**:
   - Ensure key information is early in document
   - Executive summaries are valuable
   - First 50 pages usually sufficient for classification

### Verifying Classifications

**How to check if classification is accurate**:

1. **Read the Justification**:
   - Does it reference relevant content?
   - Are the quoted sections accurate?
   - Does the reasoning make sense?

2. **Cross-Reference Categories**:
   - Review the category descriptions
   - Check if your document matches
   - Consider if sub-class is appropriate

3. **When to Question Results**:
   - Justification seems generic
   - No specific document references
   - Classification doesn't match document content

4. **What to Do If Incorrect**:
   - Try uploading again (sometimes helps)
   - Check document quality
   - Contact administrator if consistently wrong

### Saving and Sharing Results

**Copy Text Method**:
```
1. Select all result text
2. Copy (Ctrl+C or Cmd+C)
3. Paste into document or email
```

**Screenshot Method**:
```
1. Press Print Screen (Windows) or Cmd+Shift+4 (Mac)
2. Crop to results area
3. Save or paste into document
```

**Spreadsheet Logging**:
```
Create columns:
- Document Name
- Upload Date
- Main Class
- Sub Class
- Justification
- Reviewer Notes
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "OpenAI API key not found" Error

**Symptom**: Red error message at top of page saying API key is missing.

**Cause**: Application not properly configured.

**Solution**: Contact your system administrator. This is a configuration issue that users cannot fix.

---

#### Issue: "No text could be extracted from the PDF"

**Symptom**: Error message after upload saying no text was found.

**Possible Causes**:
1. PDF is a scanned image without OCR
2. PDF is corrupted
3. PDF uses unsupported encoding

**Solutions**:

**For Scanned PDFs**:
1. Use OCR software to make text selectable:
   - Adobe Acrobat Pro (Tools → Enhance Scans → Recognize Text)
   - Free online OCR tools
   - OS built-in OCR

2. Verify text is selectable:
   - Open PDF in a reader
   - Try to select text with cursor
   - If successful, try uploading again

**For Corrupted PDFs**:
1. Try opening in different PDF readers
2. Use PDF repair tools
3. Request new copy from source

---

#### Issue: Classification Seems Incorrect

**Symptom**: Results don't match expected document type.

**Diagnostic Steps**:

1. **Check the Justification**:
   - Read what the AI based its decision on
   - Look for referenced content
   - See if reasoning makes sense

2. **Review Document Content**:
   - Does document clearly state purpose?
   - Is primary use clearly defined?
   - Could it be interpreted differently?

3. **Consider Mixed Use**:
   - Some documents describe mixed-use developments
   - AI may focus on dominant use
   - Check if "Mixed Use" sub-class was assigned

**Solutions**:

1. **Try Again**:
   - Upload the same document again
   - Sometimes slight variations occur
   - Compare both results

2. **Check Document Quality**:
   - Ensure key information is present
   - Verify planning statement is clear
   - Confirm document isn't missing pages

3. **Manual Override**:
   - Use results as guidance only
   - Apply professional judgment
   - Document why you disagree if necessary

---

#### Issue: Processing Takes Too Long

**Symptom**: Classification seems stuck or takes over 60 seconds.

**Expected Times**:
- Text extraction: 2-10 seconds (depending on pages)
- Classification: 10-20 seconds
- Total: Usually under 30 seconds

**If taking longer**:

1. **Check Internet Connection**:
   - Ensure stable connection
   - Try refreshing page if disconnected
   - Re-upload document

2. **Wait Patiently**:
   - Very large documents may take longer
   - API can occasionally be slow
   - Give it 2 minutes before taking action

3. **Refresh and Retry**:
   - If no progress after 2 minutes
   - Refresh the browser page
   - Upload document again

---

#### Issue: Can't Upload File

**Symptom**: Upload widget doesn't accept file.

**Checks**:

1. **File Format**:
   - Must be PDF format
   - Check file extension is `.pdf`
   - Convert other formats to PDF first

2. **File Size**:
   - Very large files (>100MB) may fail
   - Try compressing PDF
   - Use PDF optimization tools

3. **Browser Issues**:
   - Try different browser
   - Clear browser cache
   - Disable browser extensions temporarily

---

#### Issue: Button Doesn't Appear After Upload

**Symptom**: File uploads but no "Classify Document" button.

**Solutions**:
1. Refresh the page
2. Try uploading again
3. Try different browser
4. Check browser console for errors (F12)

---

#### Issue: Results Don't Display

**Symptom**: Processing completes but no results shown.

**Solutions**:
1. Scroll down (results may be below viewport)
2. Refresh page and try again
3. Check browser console for errors
4. Try different browser

---

### Error Messages Reference

| Error Message | Meaning | Action |
|--------------|---------|--------|
| "OpenAI API key not found" | Configuration issue | Contact administrator |
| "No text could be extracted" | PDF has no selectable text | OCR the document first |
| "An error occurred: [details]" | Processing failure | Check details, try again |
| "Failed to parse classification" | API response issue | Try again, contact support if persists |
| Connection errors | Network issue | Check internet, try again |

---

## Best Practices

### Document Preparation

1. **Use High-Quality PDFs**:
   - Native PDFs better than scanned
   - Clear, readable text
   - Complete documents (not excerpts)

2. **Ensure Key Information is Present**:
   - Planning statement should be clear
   - Project description visible
   - Intended use stated explicitly

3. **File Organization**:
   - Name files descriptively
   - Keep originals separate from classified
   - Maintain classification log

### Efficient Workflow

1. **Batch Processing**:
   - Gather all documents first
   - Prepare spreadsheet for results
   - Process systematically
   - Record as you go

2. **Quality Control**:
   - Review justifications
   - Spot-check results
   - Flag uncertain classifications
   - Have expert review edge cases

3. **Result Management**:
   - Log immediately (results don't persist)
   - Include document metadata
   - Note confidence level
   - Add reviewer comments

### Classification Review

1. **When to Trust Results**:
   - Justification is detailed and specific
   - References actual document content
   - Classification aligns with your reading
   - Sub-class is appropriate

2. **When to Question Results**:
   - Generic justification
   - No specific references
   - Doesn't match document
   - Unusual sub-class choice

3. **Professional Judgment**:
   - Use AI as assistant, not replacement
   - Apply domain expertise
   - Consider local context
   - Override when necessary

---

## Advanced Tips

### Understanding AI Decision-Making

**The AI considers**:
- Explicit statements of purpose
- Terminology used (e.g., "residential units", "office space")
- Building descriptions
- Use case descriptions
- Regulatory references
- Context clues

**The AI prioritizes**:
- Clear, explicit statements
- Primary use (in mixed-use cases)
- Predominant purpose
- Legal/planning definitions

### Interpreting Complex Cases

**Mixed-Use Developments**:
- AI will classify based on dominant use
- Check if "Mixed Use" sub-class assigned
- Justification should explain the mix
- May need manual adjustment for your purposes

**Phased Developments**:
- AI classifies overall project
- May focus on first phase if prominent
- Review justification for phase details

**Changes of Use**:
- AI classifies proposed use (not current)
- Check justification references "change"
- Verify it identified the new purpose

### Quality Assurance

**Random Sampling**:
```
Process 100 documents
↓
Randomly select 10 for expert review
↓
Compare AI vs. expert classifications
↓
Measure accuracy rate
↓
Adjust trust level accordingly
```

**Systematic Review**:
- Review all "edge case" classifications
- Double-check mixed-use categorizations
- Verify unusual sub-class assignments
- Question vague justifications

---

## Frequently Asked Questions

### General Questions

**Q: How accurate is the classifier?**
A: The classifier uses advanced AI (GPT-4o) and is designed for high accuracy. However, always review results using professional judgment. Accuracy typically exceeds 90% for clear, well-written planning documents.

**Q: Can I classify multiple documents at once?**
A: Currently, the system processes one document at a time. Upload and classify each document individually.

**Q: Is there a limit to how many documents I can classify?**
A: There's no built-in limit in the application, but usage may be subject to organizational policies or API rate limits.

**Q: How long are my results stored?**
A: Results are not stored. They only display during your current session. Copy or record results before processing another document.

### Document Questions

**Q: What types of documents work best?**
A: Planning statements, design and access statements, and environmental impact assessments work best. Documents should clearly describe the proposed development.

**Q: Can I upload scanned PDFs?**
A: Only if they've been OCR'd (text is selectable). Pure image scans won't work.

**Q: What if my document is in a language other than English?**
A: The system is optimized for English documents. Other languages may produce unreliable results.

**Q: How large can my document be?**
A: The system can handle documents up to 100MB, but smaller files (under 20MB) work best. Very long documents are automatically truncated to fit processing limits.

### Technical Questions

**Q: What browser should I use?**
A: Chrome, Firefox, Edge, or Safari. Chrome is recommended for best compatibility.

**Q: Do I need to install anything?**
A: No. The application runs entirely in your web browser.

**Q: Is my document data secure?**
A: Documents are processed in memory and not permanently stored. However, they are sent to OpenAI's API for classification. Check with your administrator about data policies.

**Q: Can I use this offline?**
A: No. The application requires an internet connection to access the AI classification service.

### Results Questions

**Q: Can I edit the classification after it's generated?**
A: The application doesn't provide editing. Copy results to another system (spreadsheet, database) where you can modify as needed.

**Q: Why do I get different results for the same document?**
A: AI can have slight variations, but with low temperature settings (0.3), results should be highly consistent. Significant differences may indicate an issue.

**Q: What does the justification tell me?**
A: The justification explains why the AI chose that classification, referencing specific content from your document. It provides transparency and helps you verify accuracy.

**Q: Can I export results?**
A: Copy and paste results into your preferred system. There's no built-in export function currently.

---

## Getting Help

### When to Contact Support

**Contact your administrator or support team if**:
- Application won't load
- Persistent errors occur
- API key errors appear
- Results are consistently incorrect
- Technical issues prevent usage

### Information to Provide

**When reporting issues, include**:
1. **What you were trying to do**
2. **What happened instead**
3. **Error messages** (exact text or screenshot)
4. **Browser and version** (e.g., "Chrome 120")
5. **Document details** (size, number of pages, format)
6. **Steps to reproduce** (if applicable)

### Self-Help Resources

**Before contacting support**:
1. Check this user guide
2. Review troubleshooting section
3. Try different browser
4. Clear browser cache
5. Test with different document

---

## Appendix

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+C / Cmd+C | Copy selected text |
| Ctrl+V / Cmd+V | Paste |
| Ctrl+A / Cmd+A | Select all |
| F5 | Refresh page |
| Ctrl+F / Cmd+F | Find on page |

### Browser Compatibility

| Browser | Minimum Version | Recommended |
|---------|----------------|-------------|
| Chrome | 90+ | Latest |
| Firefox | 88+ | Latest |
| Edge | 90+ | Latest |
| Safari | 14+ | Latest |

### Document Format Support

| Format | Supported | Notes |
|--------|-----------|-------|
| PDF (native) | ✅ Yes | Best results |
| PDF (scanned + OCR) | ✅ Yes | Must have text layer |
| PDF (scanned, no OCR) | ❌ No | OCR first |
| Word (.docx) | ❌ No | Convert to PDF |
| Images (JPG, PNG) | ❌ No | Not supported |

### Classification Quick Reference

| Symbol | Category | Key Words to Look For |
|--------|----------|----------------------|
| 🏠 | Residential | Houses, apartments, flats, dwelling, residential units |
| 🏢 | Commercial | Office, retail, shop, store, commercial, business |
| 🏛️ | Institutional | Hospital, school, university, government, civic, community |
| 🏗️ | Infrastructure | Industrial, factory, warehouse, energy, transport, data center |
| 🌳 | Recreational | Park, sports, recreation, leisure, events, green space |

---

**Document Version**: 1.0
**Last Updated**: December 2025
**For Application Version**: 0.1.0

---

## Document Change Log

| Date | Version | Changes |
|------|---------|---------|
| Dec 2025 | 1.0 | Initial user guide creation |

For additional assistance, please contact your system administrator.
