"""
Exploratory Data Analysis (EDA) Analyzer Service

Analyzes uploaded sample files to understand:
- Data nature, quality, and type
- Document characteristics (images, CAD drawings, engineering plans, etc.)
- Generates comprehensive EDA reports (5-10MB data limit)

Used by Agent 1.1 (Sample Complexity Analyzer) to provide deep insights.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image
import openpyxl
from openpyxl.utils import get_column_letter
import PyPDF2
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Data size limits (5-10MB range)
MAX_FILE_SIZE_MB = 10
MAX_EXCEL_ROWS = 50000  # Limit Excel analysis to prevent memory issues
MAX_EXCEL_COLS = 500


class EDAAnalyzer:
    """
    Performs exploratory data analysis on uploaded sample files.

    Supports:
    - Excel files (.xlsx, .xls) - Statistical analysis
    - PDF files - Document structure analysis
    - Images (.png, .jpg, .jpeg) - Visual characteristics
    - CAD drawings - Technical drawing analysis (via vision LLM)
    """

    def __init__(self):
        self.vision_service = None  # Will be initialized when needed

    async def _get_vision_service(self):
        """Lazy load vision service to avoid import issues."""
        if self.vision_service is None:
            from app.services.vision_service import get_vision_service
            self.vision_service = await get_vision_service()
        return self.vision_service

    def check_file_size(self, file_path: str) -> tuple[bool, float]:
        """
        Check if file is within acceptable size limits.

        Returns:
            (is_valid, size_mb): Boolean and size in MB
        """
        try:
            size_bytes = Path(file_path).stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            is_valid = size_mb <= MAX_FILE_SIZE_MB
            return is_valid, size_mb
        except Exception as e:
            logger.error(f"Error checking file size: {e}")
            return False, 0.0

    async def analyze_excel_file(self, file_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive EDA on Excel file.

        Returns statistical summary, data quality metrics, and structure analysis.
        """
        logger.info(f"Starting Excel EDA for: {file_path}")

        try:
            # Check file size first
            is_valid, size_mb = self.check_file_size(file_path)
            if not is_valid:
                logger.warning(f"Excel file too large: {size_mb:.2f}MB (max {MAX_FILE_SIZE_MB}MB)")
                return {
                    "error": f"File too large ({size_mb:.2f}MB). Maximum: {MAX_FILE_SIZE_MB}MB",
                    "file_size_mb": size_mb
                }

            # Load workbook
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)

            sheets_analysis = []
            total_rows = 0
            total_cols = 0

            for sheet_name in wb.sheetnames:
                logger.info(f"Analyzing sheet: {sheet_name}")
                ws = wb[sheet_name]

                # Get sheet dimensions
                max_row = ws.max_row
                max_col = ws.max_column

                # Fix Bug #4: Handle None values for max_row/max_col
                if max_row is None:
                    max_row = MAX_EXCEL_ROWS
                    logger.warning(f"Sheet '{sheet_name}' has no max_row, using default {MAX_EXCEL_ROWS}")

                if max_col is None:
                    max_col = MAX_EXCEL_COLS
                    logger.warning(f"Sheet '{sheet_name}' has no max_col, using default {MAX_EXCEL_COLS}")

                # Limit analysis to prevent memory issues
                analyze_rows = min(max_row, MAX_EXCEL_ROWS)
                analyze_cols = min(max_col, MAX_EXCEL_COLS)

                if max_row > MAX_EXCEL_ROWS:
                    logger.warning(f"Sheet '{sheet_name}' has {max_row} rows. Analyzing first {MAX_EXCEL_ROWS} only.")

                # Convert to DataFrame for statistical analysis
                data = []
                headers = []

                # Read headers
                for col in range(1, analyze_cols + 1):
                    cell_value = ws.cell(1, col).value
                    headers.append(cell_value if cell_value else f"Column_{col}")

                # Read data (skip header row)
                for row in range(2, min(analyze_rows + 1, 1001)):  # Sample first 1000 rows
                    row_data = []
                    for col in range(1, analyze_cols + 1):
                        row_data.append(ws.cell(row, col).value)
                    data.append(row_data)

                # Create DataFrame
                df = pd.DataFrame(data, columns=headers)

                # Statistical Analysis
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                categorical_cols = df.select_dtypes(include=['object']).columns.tolist()

                # Data quality metrics
                missing_values = df.isnull().sum().to_dict()
                missing_percentages = (df.isnull().sum() / len(df) * 100).to_dict()

                # Numeric statistics
                numeric_stats = {}
                if numeric_cols:
                    for col in numeric_cols:
                        try:
                            numeric_stats[col] = {
                                "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                                "median": float(df[col].median()) if not pd.isna(df[col].median()) else None,
                                "std": float(df[col].std()) if not pd.isna(df[col].std()) else None,
                                "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                                "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                                "quartiles": {
                                    "25%": float(df[col].quantile(0.25)) if not pd.isna(df[col].quantile(0.25)) else None,
                                    "50%": float(df[col].quantile(0.50)) if not pd.isna(df[col].quantile(0.50)) else None,
                                    "75%": float(df[col].quantile(0.75)) if not pd.isna(df[col].quantile(0.75)) else None
                                },
                                "outliers_count": int(((df[col] < (df[col].quantile(0.25) - 1.5 * (df[col].quantile(0.75) - df[col].quantile(0.25)))) |
                                                        (df[col] > (df[col].quantile(0.75) + 1.5 * (df[col].quantile(0.75) - df[col].quantile(0.25))))).sum())
                            }
                        except Exception as e:
                            logger.warning(f"Error calculating stats for column {col}: {e}")
                            numeric_stats[col] = {"error": str(e)}

                # Categorical statistics
                categorical_stats = {}
                if categorical_cols:
                    for col in categorical_cols[:10]:  # Limit to first 10 categorical columns
                        try:
                            value_counts = df[col].value_counts().head(10).to_dict()
                            categorical_stats[col] = {
                                "unique_values": int(df[col].nunique()),
                                "top_values": {str(k): int(v) for k, v in value_counts.items()},
                                "most_common": str(df[col].mode()[0]) if not df[col].mode().empty else None
                            }
                        except Exception as e:
                            logger.warning(f"Error calculating stats for column {col}: {e}")
                            categorical_stats[col] = {"error": str(e)}

                # Data quality score (0-1)
                completeness = 1 - (df.isnull().sum().sum() / (df.shape[0] * df.shape[1]))

                # Detect time series data
                is_time_series = any('date' in str(col).lower() or 'time' in str(col).lower() for col in df.columns)

                sheet_analysis = {
                    "sheet_name": sheet_name,
                    "dimensions": {
                        "rows": max_row,
                        "columns": max_col,
                        "analyzed_rows": analyze_rows,
                        "analyzed_columns": analyze_cols
                    },
                    "data_quality": {
                        "completeness": float(completeness),
                        "missing_values_total": int(df.isnull().sum().sum()),
                        "missing_percentages": {k: float(v) for k, v in missing_percentages.items() if v > 0}
                    },
                    "column_types": {
                        "numeric_count": len(numeric_cols),
                        "categorical_count": len(categorical_cols),
                        "numeric_columns": numeric_cols[:20],  # Limit output
                        "categorical_columns": categorical_cols[:20]
                    },
                    "numeric_statistics": numeric_stats,
                    "categorical_statistics": categorical_stats,
                    "data_characteristics": {
                        "is_time_series": is_time_series,
                        "has_outliers": any(stats.get("outliers_count", 0) > 0 for stats in numeric_stats.values() if isinstance(stats, dict)),
                        "data_density": float(1 - df.isnull().sum().sum() / (df.shape[0] * df.shape[1]))
                    }
                }

                sheets_analysis.append(sheet_analysis)
                total_rows += max_row
                total_cols += max_col

            wb.close()

            # Overall Excel file summary
            overall_quality = np.mean([sheet["data_quality"]["completeness"] for sheet in sheets_analysis])

            return {
                "file_type": "excel",
                "file_size_mb": size_mb,
                "total_sheets": len(sheets_analysis),
                "total_rows": total_rows,
                "total_columns": total_cols,
                "overall_data_quality": float(overall_quality),
                "sheets": sheets_analysis,
                "analysis_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing Excel file: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": f"Failed to analyze Excel file: {str(e)}",
                "file_type": "excel"
            }

    async def analyze_pdf_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze PDF structure and content.

        Returns page count, text density, embedded objects, etc.
        """
        logger.info(f"Starting PDF EDA for: {file_path}")

        try:
            # Check file size
            is_valid, size_mb = self.check_file_size(file_path)
            if not is_valid:
                return {
                    "error": f"File too large ({size_mb:.2f}MB). Maximum: {MAX_FILE_SIZE_MB}MB",
                    "file_size_mb": size_mb
                }

            # Open PDF
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)

                page_count = len(pdf_reader.pages)

                # Analyze first 10 pages for text density
                pages_analyzed = min(page_count, 10)
                total_text_length = 0
                has_images = False

                for i in range(pages_analyzed):
                    page = pdf_reader.pages[i]
                    text = page.extract_text()
                    total_text_length += len(text)

                    # Check for images
                    if '/XObject' in page.get('/Resources', {}):
                        has_images = True

                avg_text_per_page = total_text_length / pages_analyzed if pages_analyzed > 0 else 0

                # Determine document type based on text density
                if avg_text_per_page > 1000:
                    doc_type = "text-heavy"
                elif avg_text_per_page > 200:
                    doc_type = "mixed"
                elif has_images:
                    doc_type = "image-heavy (possibly technical drawings)"
                else:
                    doc_type = "minimal-text"

                return {
                    "file_type": "pdf",
                    "file_size_mb": size_mb,
                    "page_count": page_count,
                    "pages_analyzed": pages_analyzed,
                    "avg_text_per_page": int(avg_text_per_page),
                    "has_embedded_images": has_images,
                    "document_type": doc_type,
                    "text_density": "high" if avg_text_per_page > 1000 else "medium" if avg_text_per_page > 200 else "low",
                    "analysis_timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error analyzing PDF file: {e}")
            return {
                "error": f"Failed to analyze PDF file: {str(e)}",
                "file_type": "pdf"
            }

    async def analyze_image_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze image file characteristics and use vision LLM for content understanding.

        Returns image properties and vision analysis.
        """
        logger.info(f"Starting Image EDA for: {file_path}")

        try:
            # Check file size
            is_valid, size_mb = self.check_file_size(file_path)
            if not is_valid:
                return {
                    "error": f"File too large ({size_mb:.2f}MB). Maximum: {MAX_FILE_SIZE_MB}MB",
                    "file_size_mb": size_mb
                }

            # Open image
            img = Image.open(file_path)

            # Basic image properties
            width, height = img.size
            mode = img.mode
            format_name = img.format

            # Calculate aspect ratio
            aspect_ratio = width / height if height > 0 else 0

            # Determine if it's likely a technical drawing
            is_likely_technical = (
                (width > 1500 or height > 1500) and  # Large dimensions
                mode in ['L', '1', 'RGB'] and  # Grayscale or RGB
                aspect_ratio > 0.5 and aspect_ratio < 2.0  # Reasonable aspect ratio
            )

            # Use vision LLM to understand content
            vision_analysis = None
            try:
                vision_service = await self._get_vision_service()
                vision_prompt = """Analyze this image and describe:
1. What type of document/drawing is this? (e.g., architectural plan, engineering diagram, chart, photograph, etc.)
2. What is the complexity level? (simple, moderate, complex)
3. What technical details are visible?
4. Are there any specialized elements (CAD drawings, schematics, blueprints, etc.)?

Provide a concise analysis in 3-5 sentences."""

                vision_result = await vision_service.describe_image(file_path, question=vision_prompt)
                vision_analysis = vision_result

            except Exception as e:
                logger.warning(f"Vision analysis failed: {e}")
                vision_analysis = f"Vision analysis unavailable: {str(e)}"

            return {
                "file_type": "image",
                "file_size_mb": size_mb,
                "dimensions": {
                    "width": width,
                    "height": height,
                    "aspect_ratio": float(aspect_ratio)
                },
                "format": format_name,
                "color_mode": mode,
                "megapixels": float((width * height) / 1_000_000),
                "is_likely_technical_drawing": is_likely_technical,
                "vision_analysis": vision_analysis,
                "analysis_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing image file: {e}")
            return {
                "error": f"Failed to analyze image file: {str(e)}",
                "file_type": "image"
            }

    async def generate_eda_report(self, files_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive EDA report from multiple file analyses.

        Args:
            files_analysis: List of individual file analysis results

        Returns:
            Comprehensive EDA report with summary, insights, and recommendations
        """
        logger.info(f"Generating comprehensive EDA report for {len(files_analysis)} files")

        try:
            # Categorize files by type
            excel_files = [f for f in files_analysis if f.get("file_type") == "excel"]
            pdf_files = [f for f in files_analysis if f.get("file_type") == "pdf"]
            image_files = [f for f in files_analysis if f.get("file_type") == "image"]

            # Calculate overall data quality
            excel_quality_scores = [f.get("overall_data_quality", 0) for f in excel_files if "error" not in f]
            avg_data_quality = np.mean(excel_quality_scores) if excel_quality_scores else None

            # Detect data characteristics
            has_time_series = any(
                any(sheet.get("data_characteristics", {}).get("is_time_series", False)
                    for sheet in f.get("sheets", []))
                for f in excel_files if "error" not in f
            )

            has_technical_drawings = any(
                f.get("is_likely_technical_drawing", False) for f in image_files
            ) or any(
                f.get("document_type", "").find("drawing") >= 0 for f in pdf_files
            )

            has_large_data = any(
                f.get("total_rows", 0) > 10000 for f in excel_files
            )

            # Determine domain based on file characteristics
            domain = "Unknown"
            if has_technical_drawings:
                domain = "Engineering/CAD"
            elif has_time_series and has_large_data:
                domain = "Data Analytics/BI"
            elif has_large_data:
                domain = "Data Processing"
            elif len(pdf_files) > len(excel_files):
                domain = "Document-heavy"

            # Summary
            report = {
                "summary": {
                    "total_files_analyzed": len(files_analysis),
                    "file_types": {
                        "excel": len(excel_files),
                        "pdf": len(pdf_files),
                        "images": len(image_files)
                    },
                    "total_size_mb": sum(f.get("file_size_mb", 0) for f in files_analysis),
                    "domain_detected": domain
                },
                "data_characteristics": {
                    "has_time_series_data": has_time_series,
                    "has_technical_drawings": has_technical_drawings,
                    "has_large_data": has_large_data,
                    "average_data_quality": float(avg_data_quality) if avg_data_quality else None
                },
                "detailed_analysis": {
                    "excel_files": excel_files,
                    "pdf_files": pdf_files,
                    "image_files": image_files
                },
                "insights": self._generate_insights(files_analysis, domain, has_technical_drawings, has_large_data, has_time_series),
                "report_timestamp": datetime.now().isoformat()
            }

            return report

        except Exception as e:
            logger.error(f"Error generating EDA report: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": f"Failed to generate EDA report: {str(e)}"
            }

    def _generate_insights(self, files_analysis: List[Dict[str, Any]], domain: str,
                          has_technical: bool, has_large_data: bool, has_time_series: bool) -> List[str]:
        """Generate human-readable insights from analysis."""
        insights = []

        if domain == "Engineering/CAD":
            insights.append("Technical drawings detected - project likely involves CAD/engineering workflows")
            insights.append("Recommend specialized tools: AutoCAD API, GIS systems, or technical drawing parsers")

        if has_large_data:
            insights.append("Large datasets detected (>10,000 rows) - data processing infrastructure required")
            insights.append("Consider Apache Spark, Dask, or distributed processing frameworks")

        if has_time_series:
            insights.append("Time-series data detected - temporal analysis and forecasting capabilities needed")
            insights.append("Recommend: InfluxDB, Grafana, or specialized time-series libraries")

        excel_files = [f for f in files_analysis if f.get("file_type") == "excel" and "error" not in f]
        if excel_files:
            avg_quality = np.mean([f.get("overall_data_quality", 0) for f in excel_files])
            if avg_quality < 0.7:
                insights.append(f"Data quality concerns detected (completeness: {avg_quality:.1%}) - data cleaning required")
            elif avg_quality > 0.95:
                insights.append(f"High-quality data detected (completeness: {avg_quality:.1%}) - minimal preprocessing needed")

        if len(files_analysis) > 10:
            insights.append("Large number of sample files - complex multi-faceted project")

        return insights


# Singleton instance
_eda_analyzer_instance = None


async def get_eda_analyzer() -> EDAAnalyzer:
    """Get EDA Analyzer singleton instance."""
    global _eda_analyzer_instance
    if _eda_analyzer_instance is None:
        _eda_analyzer_instance = EDAAnalyzer()
    return _eda_analyzer_instance
