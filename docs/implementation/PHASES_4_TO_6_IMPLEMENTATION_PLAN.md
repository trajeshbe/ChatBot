# Phases 4-6: EDA Report & Tech Stack in BRD - Implementation Plan

**Date**: 2025-11-26
**Status**: ⏳ READY TO IMPLEMENT
**Estimated Time**: 2-3 hours

---

## 📋 Overview

Complete the EDA + Tech Stack integration by adding detailed EDA report and AI/ML tech stack recommendations to the generated BRD document.

**Note**: Phase 4 (Debate Coordinator) is being deferred as an advanced feature. We're focusing on immediate value delivery by adding EDA content to the BRD.

---

## ✅ What's Already Complete (Phase 3)

- ✅ Agent 1.1 enhanced with EDA capabilities
- ✅ EDA Analyzer Service operational
- ✅ Tech Stack Knowledge Base (YAML) created
- ✅ ChatBot tools mapped in tech stack
- ✅ Helper methods for complexity analysis
- ✅ Section 2.5 "Sample Complexity Analysis" in BRD (basic version)

---

## 🎯 Phase 5: Update Agent 6 - Add EDA Report & Tech Stack to BRD

### File to Modify
`backend/app/agents/project_estimator/workflow.py` - Agent 6 (document_generator_agent method)

### Location to Insert
**After line 1678** (after the reasoning paragraph), **before line 1683** (Technical Scope section)

### Code to Add

Insert these two new sections after the existing complexity analysis:

```python
            # NEW SECTION 2.6: EDA Report Summary
            eda_report = complexity_analysis.get("eda_report")
            if eda_report:
                doc.add_page_break()
                doc.add_heading('2.6 Exploratory Data Analysis (EDA) Report', 1)

                # Files Analyzed
                total_files = eda_report.get("total_files_analyzed", 0)
                p_files = doc.add_paragraph()
                p_files.add_run("Files Analyzed: ").bold = True
                p_files.add_run(f"{total_files}")

                # Domain Detected
                domain = eda_report.get("domain", "Unknown")
                p_domain = doc.add_paragraph()
                p_domain.add_run("Domain Detected: ").bold = True
                p_domain.add_run(domain)

                # Data Quality
                data_quality = eda_report.get("overall_data_quality", 0)
                p_quality = doc.add_paragraph()
                p_quality.add_run("Overall Data Quality: ").bold = True
                p_quality.add_run(f"{data_quality:.1%}")

                # Data Volume
                data_volume = eda_report.get("total_data_volume_mb", 0)
                p_volume = doc.add_paragraph()
                p_volume.add_run("Total Data Volume: ").bold = True
                p_volume.add_run(f"{data_volume:.2f} MB")

                doc.add_paragraph()  # Spacing

                # Detected Data Types
                data_types = eda_report.get("detected_data_types", [])
                if data_types:
                    doc.add_paragraph("Detected Data Types:", style='Heading 2')
                    for data_type in data_types:
                        doc.add_paragraph(data_type.replace("_", " ").title(), style='List Bullet')

                doc.add_paragraph()  # Spacing

                # Key Insights
                insights = eda_report.get("insights", [])
                if insights:
                    doc.add_paragraph("Key Insights:", style='Heading 2')
                    for insight in insights:
                        doc.add_paragraph(insight, style='List Bullet')

                # Files Analysis (Detailed breakdown)
                files_analysis = eda_report.get("files_analysis", [])
                if files_analysis:
                    doc.add_paragraph()  # Spacing
                    doc.add_paragraph("Detailed File Analysis:", style='Heading 2')

                    for file_data in files_analysis:
                        file_type = file_data.get("file_type", "Unknown")
                        file_size_mb = file_data.get("file_size_mb", 0)

                        p_file = doc.add_paragraph()
                        p_file.add_run(f"{file_type.upper()} File ({file_size_mb:.2f} MB)").bold = True

                        # Excel-specific details
                        if file_type in ["excel", "xlsx", "xls"]:
                            sheets = file_data.get("sheets", 0)
                            rows = file_data.get("total_rows", 0)
                            cols = file_data.get("total_columns", 0)
                            file_quality = file_data.get("overall_data_quality", 0)

                            doc.add_paragraph(f"  • Sheets: {sheets}", style='List Bullet 2')
                            doc.add_paragraph(f"  • Rows: {rows}, Columns: {cols}", style='List Bullet 2')
                            doc.add_paragraph(f"  • Data Quality: {file_quality:.1%}", style='List Bullet 2')

                        # PDF-specific details
                        elif file_type == "pdf":
                            pages = file_data.get("pages", 0)
                            doc_type = file_data.get("document_type", "Unknown")
                            has_images = file_data.get("has_images", False)

                            doc.add_paragraph(f"  • Pages: {pages}", style='List Bullet 2')
                            doc.add_paragraph(f"  • Type: {doc_type}", style='List Bullet 2')
                            doc.add_paragraph(f"  • Contains Images: {'Yes' if has_images else 'No'}", style='List Bullet 2')

                        # Image-specific details
                        elif file_type in ["image", "jpg", "jpeg", "png"]:
                            width = file_data.get("width", 0)
                            height = file_data.get("height", 0)

                            doc.add_paragraph(f"  • Dimensions: {width}x{height}px", style='List Bullet 2')

                        doc.add_paragraph()  # Spacing between files

            # NEW SECTION 2.7: Recommended AI/ML Tech Stack
            tech_stack = complexity_analysis.get("recommended_tech_stack")
            if tech_stack:
                doc.add_page_break()
                doc.add_heading('2.7 Recommended AI/ML Tech Stack', 1)

                # Primary Tools
                primary_tools = tech_stack.get("primary_tools", {})
                if primary_tools:
                    doc.add_paragraph("Recommended AI/ML Tools by Data Type:", style='Heading 2')

                    for data_type, tools_info in primary_tools.items():
                        p_dt = doc.add_paragraph()
                        p_dt.add_run(f"{data_type.replace('_', ' ').title()}:").bold = True

                        # Data Processing Tools
                        data_processing = tools_info.get("data_processing", [])
                        if data_processing:
                            doc.add_paragraph("Data Processing & Analytics:", style='List Bullet')
                            for tool in data_processing[:5]:  # Top 5
                                doc.add_paragraph(f"• {tool}", style='List Bullet 2')

                        # PDF Processing
                        pdf_processing = tools_info.get("pdf_processing", [])
                        if pdf_processing:
                            doc.add_paragraph("PDF Processing:", style='List Bullet')
                            for tool in pdf_processing[:5]:
                                doc.add_paragraph(f"• {tool}", style='List Bullet 2')

                        # OCR
                        ocr_tools = tools_info.get("ocr", [])
                        if ocr_tools:
                            doc.add_paragraph("OCR Engines:", style='List Bullet')
                            for tool in ocr_tools[:5]:
                                doc.add_paragraph(f"• {tool}", style='List Bullet 2')

                        # Vision Models
                        vision_models = tools_info.get("vision_models", [])
                        if vision_models:
                            doc.add_paragraph("Vision Models:", style='List Bullet')
                            for tool in vision_models[:5]:
                                doc.add_paragraph(f"• {tool}", style='List Bullet 2')

                        # Web Scraping
                        web_scraping = tools_info.get("web_scraping", [])
                        if web_scraping:
                            doc.add_paragraph("Web Scraping:", style='List Bullet')
                            for tool in web_scraping[:5]:
                                doc.add_paragraph(f"• {tool}", style='List Bullet 2')

                        doc.add_paragraph()  # Spacing between data types

                # ChatBot's Own Tools
                chatbot_tools = tech_stack.get("chatbot_tools", {})
                if chatbot_tools:
                    doc.add_paragraph()  # Spacing
                    doc.add_paragraph("ChatBot Platform Capabilities (Recommended for This Project):", style='Heading 2')

                    # Document Intelligence
                    doc_intelligence = chatbot_tools.get("document_intelligence", [])
                    if doc_intelligence:
                        doc.add_paragraph("Document Intelligence:", style='List Bullet')
                        for tool_info in doc_intelligence:
                            tool_name = tool_info.get("name", "Unknown")
                            description = tool_info.get("description", "")
                            reason = tool_info.get("reason", "")
                            service_path = tool_info.get("service", "")

                            p_tool = doc.add_paragraph()
                            p_tool.add_run(f"• {tool_name}").bold = True
                            p_tool.add_run(f": {description}")

                            doc.add_paragraph(f"  Reason: {reason}", style='List Bullet 2')
                            doc.add_paragraph(f"  Service: {service_path}", style='List Bullet 2')

                    # Vision Analysis
                    vision_analysis = chatbot_tools.get("vision_analysis", [])
                    if vision_analysis:
                        doc.add_paragraph()  # Spacing
                        doc.add_paragraph("Vision Analysis:", style='List Bullet')
                        for tool_info in vision_analysis:
                            tool_name = tool_info.get("name", "Unknown")
                            description = tool_info.get("description", "")
                            reason = tool_info.get("reason", "")
                            service_path = tool_info.get("service", "")

                            p_tool = doc.add_paragraph()
                            p_tool.add_run(f"• {tool_name}").bold = True
                            p_tool.add_run(f": {description}")

                            doc.add_paragraph(f"  Reason: {reason}", style='List Bullet 2')
                            doc.add_paragraph(f"  Service: {service_path}", style='List Bullet 2')

                    # RAG Pipeline
                    rag_pipeline = chatbot_tools.get("rag_pipeline", [])
                    if rag_pipeline:
                        doc.add_paragraph()  # Spacing
                        doc.add_paragraph("Knowledge Base & Search:", style='List Bullet')
                        for tool_info in rag_pipeline:
                            tool_name = tool_info.get("name", "Unknown")
                            description = tool_info.get("description", "")
                            reason = tool_info.get("reason", "")
                            service_path = tool_info.get("service", "")

                            p_tool = doc.add_paragraph()
                            p_tool.add_run(f"• {tool_name}").bold = True
                            p_tool.add_run(f": {description}")

                            doc.add_paragraph(f"  Reason: {reason}", style='List Bullet 2')
                            doc.add_paragraph(f"  Service: {service_path}", style='List Bullet 2')

                # Use Cases
                use_cases = tech_stack.get("use_cases", [])
                if use_cases:
                    doc.add_paragraph()  # Spacing
                    doc.add_paragraph("Recommended Use Cases for This Project:", style='Heading 2')
                    for use_case in use_cases[:10]:  # Top 10 use cases
                        doc.add_paragraph(use_case, style='List Bullet')
```

### Implementation Steps

1. **Open workflow.py** at line 1678
2. **Find** the complexity analysis reasoning section:
   ```python
   reasoning = complexity_analysis.get("reasoning", "")
   if reasoning:
       doc.add_paragraph("Analysis Reasoning:", style='Heading 2')
       doc.add_paragraph(reasoning)
   ```
3. **Insert** the two new sections (2.6 and 2.7) **immediately after** the reasoning paragraph
4. **Save** the file
5. **Validate** Python syntax:
   ```bash
   docker-compose exec -T backend python3 -m py_compile /app/app/agents/project_estimator/workflow.py
   ```

---

## 🎯 Phase 6: Create Downloadable EDA Report Endpoint

### File to Create/Modify
`backend/app/api/routes/project_estimator_routes.py` (or similar)

### New Endpoint

```python
@router.get("/api/v1/project-estimator/{job_id}/eda-report")
async def get_eda_report(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Download EDA report for a project estimator job.

    Returns:
        JSON with EDA report data, or 404 if not found
    """
    # Retrieve job from database
    job = db.query(ProjectEstimatorJob).filter(
        ProjectEstimatorJob.id == job_id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Extract EDA report from job state
    state = job.state_json  # Assuming state is stored as JSON
    complexity_analysis = state.get("complexity_analysis", {})
    eda_report = complexity_analysis.get("eda_report")
    tech_stack = complexity_analysis.get("recommended_tech_stack")

    if not eda_report:
        raise HTTPException(status_code=404, detail="EDA report not available for this job")

    return {
        "job_id": job_id,
        "eda_report": eda_report,
        "recommended_tech_stack": tech_stack,
        "generated_at": job.created_at.isoformat() if job.created_at else None
    }


@router.get("/api/v1/project-estimator/{job_id}/eda-report/excel")
async def download_eda_report_excel(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Download EDA report as Excel file.

    Returns:
        Excel file with EDA data
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    from fastapi.responses import StreamingResponse
    import io

    # Retrieve EDA report
    job = db.query(ProjectEstimatorJob).filter(
        ProjectEstimatorJob.id == job_id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    state = job.state_json
    complexity_analysis = state.get("complexity_analysis", {})
    eda_report = complexity_analysis.get("eda_report")

    if not eda_report:
        raise HTTPException(status_code=404, detail="EDA report not available")

    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "EDA Summary"

    # Header
    ws['A1'] = "EDA Report Summary"
    ws['A1'].font = Font(bold=True, size=16)

    # Summary data
    row = 3
    ws[f'A{row}'] = "Total Files Analyzed"
    ws[f'B{row}'] = eda_report.get("total_files_analyzed", 0)
    row += 1

    ws[f'A{row}'] = "Domain"
    ws[f'B{row}'] = eda_report.get("domain", "Unknown")
    row += 1

    ws[f'A{row}'] = "Overall Data Quality"
    ws[f'B{row}'] = f"{eda_report.get('overall_data_quality', 0):.1%}"
    row += 1

    ws[f'A{row}'] = "Total Data Volume (MB)"
    ws[f'B{row}'] = eda_report.get("total_data_volume_mb", 0)
    row += 2

    # Data types
    ws[f'A{row}'] = "Detected Data Types"
    ws[f'A{row}'].font = Font(bold=True)
    row += 1

    for data_type in eda_report.get("detected_data_types", []):
        ws[f'A{row}'] = data_type.replace("_", " ").title()
        row += 1

    row += 1

    # Insights
    ws[f'A{row}'] = "Key Insights"
    ws[f'A{row}'].font = Font(bold=True)
    row += 1

    for insight in eda_report.get("insights", []):
        ws[f'A{row}'] = insight
        row += 1

    # Save to bytes
    excel_bytes = io.BytesIO()
    wb.save(excel_bytes)
    excel_bytes.seek(0)

    return StreamingResponse(
        excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=EDA_Report_{job_id}.xlsx"}
    )
```

---

## 🧪 Testing Plan

### Test 1: Basic BRD Generation with EDA
1. Upload sample files (Excel, PDF, images)
2. Generate estimate
3. Download BRD
4. **Verify**:
   - Section 2.5 has complexity analysis
   - Section 2.6 has EDA report
   - Section 2.7 has tech stack recommendations
   - ChatBot tools are listed when applicable

### Test 2: No Sample Files
1. Generate estimate WITHOUT uploading sample files
2. Download BRD
3. **Verify**:
   - Section 2.5 shows "No sample files" message
   - Sections 2.6 and 2.7 are NOT added (graceful degradation)

### Test 3: EDA Report Endpoint
```bash
# Get EDA report JSON
curl http://localhost:8000/api/v1/project-estimator/{job_id}/eda-report

# Download EDA report as Excel
curl -O http://localhost:8000/api/v1/project-estimator/{job_id}/eda-report/excel
```

---

## ✅ Success Criteria

- [ ] Section 2.6 "EDA Report" added to BRD
- [ ] Section 2.7 "Recommended Tech Stack" added to BRD
- [ ] EDA metrics displayed correctly (files, domain, quality, volume)
- [ ] Data types listed
- [ ] Insights displayed
- [ ] ChatBot tools highlighted when applicable
- [ ] Primary AI/ML tools shown by data type
- [ ] Use cases listed
- [ ] API endpoint returns EDA report JSON
- [ ] Excel download works
- [ ] Graceful degradation when no EDA report exists
- [ ] Python syntax validates
- [ ] No breaking changes to existing workflow

---

## 📊 Expected BRD Structure (After Implementation)

```
Business Requirements Document
├── 1. Executive Summary
├── 2. Project Objectives
├── 2.5 Sample Complexity Analysis ✅ (Already exists)
│   ├── Overall Complexity Rating
│   ├── Confidence Score
│   ├── Impact on Estimation
│   │   ├── Effort Multiplier
│   │   ├── Rate Multiplier
│   │   ├── Skill Requirements
│   │   └── Recommended Teams
│   └── Analysis Reasoning
│
├── 2.6 Exploratory Data Analysis (EDA) Report ⭐ NEW
│   ├── Files Analyzed
│   ├── Domain Detected
│   ├── Overall Data Quality
│   ├── Total Data Volume
│   ├── Detected Data Types
│   ├── Key Insights
│   └── Detailed File Analysis
│       ├── Excel Files (sheets, rows, columns, quality)
│       ├── PDF Files (pages, type, images)
│       └── Image Files (dimensions)
│
├── 2.7 Recommended AI/ML Tech Stack ⭐ NEW
│   ├── Recommended Tools by Data Type
│   │   ├── Data Processing & Analytics
│   │   ├── PDF Processing
│   │   ├── OCR Engines
│   │   ├── Vision Models
│   │   └── Web Scraping
│   ├── ChatBot Platform Capabilities
│   │   ├── Document Intelligence
│   │   │   ├── DocumentService (with Docling)
│   │   │   └── OCRService
│   │   ├── Vision Analysis
│   │   │   └── VisionService
│   │   └── Knowledge Base & Search
│   │       └── RAG Pipeline (Multi-Strategy)
│   └── Recommended Use Cases
│
├── 3. Technical Scope
├── 4. Team Structure
├── 5. Project Workflow & Timeline
└── 6. Cost Estimation
```

---

## 🎓 Key Implementation Notes

### 1. Conditional Rendering
Only show Sections 2.6 and 2.7 if EDA report exists:
```python
eda_report = complexity_analysis.get("eda_report")
if eda_report:
    # Add Section 2.6 and 2.7
```

### 2. Safe Dict Access
Always use `.get()` with defaults to avoid KeyErrors:
```python
total_files = eda_report.get("total_files_analyzed", 0)
domain = eda_report.get("domain", "Unknown")
```

### 3. Formatting
- Use `.bold = True` for field names
- Use `style='List Bullet'` for bulleted lists
- Use `style='List Bullet 2'` for nested bullets
- Use `doc.add_paragraph()` for spacing between sections
- Use `doc.add_page_break()` before major sections

### 4. Data Truncation
Limit lists to avoid overwhelming the document:
```python
for tool in tools[:5]:  # Top 5 only
```

---

## 📁 Files to Modify/Create

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/agents/project_estimator/workflow.py` | Modify (lines 1678-1683) | Add Sections 2.6 and 2.7 to BRD |
| `backend/app/api/routes/project_estimator_routes.py` | Create/Modify | Add EDA report endpoints |
| `PHASES_4_TO_6_COMPLETE.md` | Create | Document completion |

---

## ⏱️ Time Estimate

- **Phase 5** (BRD Enhancement): 1-1.5 hours
- **Phase 6** (EDA Endpoint): 0.5-1 hour
- **Testing**: 0.5 hour
- **Total**: 2-3 hours

---

**Next Action**: Implement Phase 5 by adding the code sections to workflow.py:1678-1683

**Date Prepared**: 2025-11-26
