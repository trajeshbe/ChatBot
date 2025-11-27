# Phase 3: Agent 1.1 EDA Integration - Implementation Plan

**Date**: 2025-11-26
**Status**: ⏳ READY TO IMPLEMENT

---

## 🎯 Objective

Enhance Agent 1.1 (Sample Complexity Analyzer) to use the new EDA Analyzer Service and include AI/ML tech stack recommendations in the complexity analysis output.

---

## 📋 Prerequisites (COMPLETE)

✅ Phase 1: EDA Analyzer Service created (`backend/app/services/eda_analyzer.py`)
✅ Phase 2: Tech Stack Knowledge Base created (`backend/app/config/tech_stack_patterns.yaml`)
✅ ChatBot LLM tools mapped in tech stack YAML

---

## 🔧 Implementation Steps

### Step 1: Modify Agent 1.1 in workflow.py

**File**: `backend/app/agents/project_estimator/workflow.py`
**Method**: `sample_complexity_analyzer` (lines 540-604)

**Current Behavior**:
- Calls `ComplexityAnalyzerService`
- Returns basic complexity analysis with multipliers

**New Behavior**:
- Import and use `EDAAnalyzer` service
- Analyze uploaded sample files with EDA
- Generate comprehensive EDA report
- Load tech stack recommendations from YAML
- Map detected data types to AI/ML tools
- Include EDA report AND tech stack in `complexity_analysis` state

### Step 2: Enhanced State Output Structure

**Current `complexity_analysis` structure**:
```python
{
    "overall_rating": "High",
    "confidence_score": 0.85,
    "impact_on_estimation": {
        "effort_multiplier": 1.8,
        "rate_multiplier": 1.30,
        "skill_requirements": {...},
        "recommended_teams": [...]
    },
    "reasoning": "..."
}
```

**NEW Enhanced `complexity_analysis` structure**:
```python
{
    "overall_rating": "High",
    "confidence_score": 0.85,
    "impact_on_estimation": {
        "effort_multiplier": 1.8,
        "rate_multiplier": 1.30,
        "skill_requirements": {...},
        "recommended_teams": [...]
    },
    "reasoning": "...",

    # NEW: EDA Report
    "eda_report": {
        "total_files_analyzed": 3,
        "domain": "Data Analytics",
        "detected_data_types": ["tabular_excel", "pdf_text"],
        "overall_data_quality": 0.87,
        "total_data_volume_mb": 8.5,
        "files_analysis": [
            {
                "file_type": "excel",
                "file_size_mb": 5.2,
                "sheets": 3,
                "overall_data_quality": 0.92,
                "insights": [...]
            }
        ],
        "insights": [
            "High-quality structured data suitable for ML models",
            "Recommended tools: pandas, scikit-learn, XGBoost"
        ]
    },

    # NEW: Recommended AI/ML Tech Stack
    "recommended_tech_stack": {
        "primary_tools": {
            "data_processing": [
                "pandas - Data manipulation and analysis",
                "scikit-learn - Classical ML (regression, classification)"
            ],
            "visualization": [
                "Plotly / Dash - Interactive Python viz",
                "Grafana - Real-time dashboards"
            ]
        },
        "chatbot_tools": {
            "document_intelligence": [
                {
                    "name": "DocumentService (with Docling)",
                    "description": "Enterprise PDF processing",
                    "service": "app.services.document_service.DocumentService",
                    "applicable": true,
                    "reason": "Complex PDFs detected in sample files"
                },
                {
                    "name": "RAG Pipeline (Multi-Strategy)",
                    "description": "Hybrid retrieval for Q&A",
                    "service": "app.services.rag_service.RAGService",
                    "applicable": true,
                    "reason": "Document Q&A system recommended for project"
                }
            ]
        },
        "use_cases": [
            "Document Q&A systems (RAG)",
            "Data analysis and visualization",
            "ML model training on structured data"
        ]
    }
}
```

### Step 3: Code Implementation Snippet

```python
async def sample_complexity_analyzer(self, state: ProjectEstimatorState) -> Dict[str, Any]:
    """
    Agent 1.1: Analyze uploaded sample files to determine project complexity.

    NOW WITH:
    - Comprehensive EDA analysis
    - AI/ML tech stack recommendations
    - ChatBot tool mapping
    """
    logger.info("Agent 1.1: Sample Complexity Analyzer (with EDA) - Analyzing uploaded samples")

    try:
        # Import EDA Analyzer
        from app.services.eda_analyzer import EDAAnalyzer
        import yaml
        from pathlib import Path

        eda_analyzer = EDAAnalyzer()

        # Step 1: Perform EDA on all uploaded sample files
        sample_files_paths = []

        # Collect BRD files
        for brd_file in state.get("uploaded_brd_files", []):
            sample_files_paths.append(brd_file)

        # Collect cost files
        for cost_file in state.get("uploaded_cost_files", []):
            sample_files_paths.append(cost_file)

        # Collect sample data files
        for sample_file in state.get("uploaded_sample_data", []):
            sample_files_paths.append(sample_file)

        if not sample_files_paths:
            logger.warning("No sample files provided for EDA")
            return self._generate_fallback_analysis(state, "No sample files")

        # Step 2: Analyze each file with EDA
        files_analysis = []
        for file_path in sample_files_paths:
            try:
                file_ext = Path(file_path).suffix.lower()

                if file_ext in ['.xlsx', '.xls']:
                    analysis = await eda_analyzer.analyze_excel_file(file_path)
                elif file_ext == '.pdf':
                    analysis = await eda_analyzer.analyze_pdf_file(file_path)
                elif file_ext in ['.jpg', '.jpeg', '.png']:
                    analysis = await eda_analyzer.analyze_image_file(file_path)
                else:
                    logger.warning(f"Unsupported file type: {file_ext}")
                    continue

                files_analysis.append(analysis)
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                continue

        if not files_analysis:
            logger.error("No files successfully analyzed")
            return self._generate_fallback_analysis(state, "EDA analysis failed")

        # Step 3: Generate comprehensive EDA report
        eda_report = await eda_analyzer.generate_eda_report(files_analysis)

        logger.info(f"EDA Complete: Domain={eda_report.get('domain')}, "
                   f"Data Quality={eda_report.get('overall_data_quality'):.2f}")

        # Step 4: Load tech stack knowledge base
        tech_stack_yaml_path = Path(__file__).parent.parent.parent / "config" / "tech_stack_patterns.yaml"
        with open(tech_stack_yaml_path, 'r') as f:
            tech_stack_kb = yaml.safe_load(f)

        # Step 5: Map detected data types to AI/ML tools
        detected_data_types = eda_report.get("detected_data_types", [])
        recommended_tools = self._map_data_types_to_tools(detected_data_types, tech_stack_kb)

        # Step 6: Determine complexity based on EDA insights
        complexity_rating, effort_mult, rate_mult = self._determine_complexity_from_eda(eda_report)

        logger.info(f"Complexity: {complexity_rating}, Effort: {effort_mult}x, Rate: {rate_mult}x")

        # Step 7: Build enhanced complexity analysis
        enhanced_analysis = {
            "overall_rating": complexity_rating,
            "confidence_score": eda_report.get("confidence_score", 0.8),
            "impact_on_estimation": {
                "effort_multiplier": effort_mult,
                "rate_multiplier": rate_mult,
                "skill_requirements": {
                    "minimum_level": "Senior" if complexity_rating == "High" else "Mid-level",
                    "specialized_skills": self._extract_required_skills(eda_report, recommended_tools)
                },
                "recommended_teams": self._recommend_teams_from_eda(eda_report)
            },
            "reasoning": self._generate_reasoning(eda_report, recommended_tools),

            # NEW: Include full EDA report
            "eda_report": eda_report,

            # NEW: Include recommended tech stack
            "recommended_tech_stack": recommended_tools
        }

        return {
            **state,
            "complexity_analysis": enhanced_analysis
        }

    except Exception as e:
        logger.error(f"Sample Complexity Analyzer with EDA failed: {str(e)}", exc_info=True)
        return self._generate_fallback_analysis(state, str(e))


def _map_data_types_to_tools(self, data_types: List[str], tech_stack_kb: Dict) -> Dict:
    """Map detected data types to AI/ML tool recommendations"""
    recommended_tools = {
        "primary_tools": {},
        "chatbot_tools": {},
        "use_cases": []
    }

    data_type_mapping = tech_stack_kb.get("data_type_ai_tools", {})
    chatbot_tools = tech_stack_kb.get("chatbot_llm_tools", {})

    for data_type in data_types:
        if data_type in data_type_mapping:
            tools_info = data_type_mapping[data_type]
            recommended_tools["primary_tools"][data_type] = tools_info.get("recommended_ai_tools", {})
            recommended_tools["use_cases"].extend(tools_info.get("use_cases", []))

    # Map applicable ChatBot tools
    if "complex_pdfs" in data_types or "pdf_text" in data_types:
        recommended_tools["chatbot_tools"]["document_intelligence"] = [
            {
                "name": "DocumentService (with Docling)",
                "description": "Enterprise PDF processing",
                "service": "app.services.document_service.DocumentService",
                "applicable": True,
                "reason": "Complex PDFs detected"
            },
            {
                "name": "OCRService",
                "description": "Hybrid Docling + Tesseract OCR",
                "service": "app.services.ocr_service.OCRService",
                "applicable": True,
                "reason": "PDF text extraction required"
            }
        ]

    if "images" in data_types:
        recommended_tools["chatbot_tools"]["vision_analysis"] = [
            {
                "name": "VisionService",
                "description": "Technical drawing and image analysis",
                "service": "app.services.vision_service.VisionService",
                "applicable": True,
                "reason": "Images/drawings detected"
            }
        ]

    return recommended_tools


def _determine_complexity_from_eda(self, eda_report: Dict) -> Tuple[str, float, float]:
    """Determine complexity rating and multipliers from EDA report"""
    data_quality = eda_report.get("overall_data_quality", 0.5)
    data_volume_mb = eda_report.get("total_data_volume_mb", 0)
    detected_types = eda_report.get("detected_data_types", [])

    # High complexity indicators
    has_images = any("image" in dt for dt in detected_types)
    has_technical_drawings = any("technical" in dt or "cad" in dt for dt in detected_types)
    has_complex_pdfs = "complex_pdfs" in detected_types
    large_volume = data_volume_mb > 5
    low_quality = data_quality < 0.7

    complexity_score = 0
    if has_technical_drawings:
        complexity_score += 3
    if has_images:
        complexity_score += 2
    if has_complex_pdfs:
        complexity_score += 2
    if large_volume:
        complexity_score += 1
    if low_quality:
        complexity_score += 1

    # Determine rating
    if complexity_score >= 5:
        return "High", 1.8, 1.30
    elif complexity_score >= 2:
        return "Medium", 1.3, 1.15
    else:
        return "Low", 1.0, 1.0


def _generate_fallback_analysis(self, state: Dict, reason: str) -> Dict:
    """Generate fallback analysis when EDA fails"""
    fallback_analysis = {
        "overall_rating": "Medium",
        "confidence_score": 0.5,
        "impact_on_estimation": {
            "effort_multiplier": 1.0,
            "rate_multiplier": 1.0,
            "skill_requirements": {
                "minimum_level": "Senior",
                "specialized_skills": []
            },
            "recommended_teams": []
        },
        "reasoning": f"EDA analysis unavailable: {reason}. Using default multipliers.",
        "eda_report": None,
        "recommended_tech_stack": None
    }

    state["errors"].append(f"Sample Complexity Analyzer (EDA): {reason}")
    return {
        **state,
        "complexity_analysis": fallback_analysis
    }
```

---

## 📊 Expected Results

### Before (Current Agent 1.1)
```json
{
  "overall_rating": "High",
  "effort_multiplier": 1.8,
  "rate_multiplier": 1.30,
  "reasoning": "Complex project requirements detected"
}
```

### After (Enhanced with EDA)
```json
{
  "overall_rating": "High",
  "effort_multiplier": 1.8,
  "rate_multiplier": 1.30,
  "reasoning": "Analysis based on 3 sample files with 87% data quality...",

  "eda_report": {
    "total_files_analyzed": 3,
    "domain": "Data Analytics",
    "overall_data_quality": 0.87,
    "insights": ["High-quality data", "Recommended: pandas, XGBoost"]
  },

  "recommended_tech_stack": {
    "primary_tools": {
      "data_processing": ["pandas", "scikit-learn"],
      "pdf_processing": ["Docling", "pdfplumber"]
    },
    "chatbot_tools": {
      "document_intelligence": [
        {
          "name": "DocumentService (with Docling)",
          "applicable": true,
          "reason": "Complex PDFs detected"
        }
      ]
    }
  }
}
```

---

## ✅ Success Criteria

1. ✅ Agent 1.1 calls EDA Analyzer service
2. ✅ EDA report generated for all sample files
3. ✅ Tech stack recommendations included in state
4. ✅ Complexity multipliers based on EDA insights
5. ✅ ChatBot tools mapped when applicable
6. ✅ Fallback gracefully if EDA fails

---

## 🔄 Next Phases (After Phase 3)

**Phase 4**: Create Agent 1.2 - Debate Coordinator
**Phase 5**: Update Agent 6 to include EDA report in BRD Section 2.6
**Phase 6**: Create downloadable EDA report endpoint
**Phase 7**: Frontend - Display tech stack recommendations

---

## 📁 Files to Modify

| File | Lines | Change |
|------|-------|--------|
| `backend/app/agents/project_estimator/workflow.py` | 540-604 | Replace Agent 1.1 method |
| `backend/app/agents/project_estimator/workflow.py` | Add helpers | `_map_data_types_to_tools()`, `_determine_complexity_from_eda()`, `_generate_fallback_analysis()` |

---

**Phase 3 Status**: ⏳ READY TO IMPLEMENT
**Prerequisites**: ✅ COMPLETE (Phases 1-2)
**Implementation Time**: ~1-2 hours
**Testing Required**: Yes - Upload sample files and verify EDA report + tech stack in logs

---

**Date Prepared**: 2025-11-26
