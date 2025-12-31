"""
Enhanced Agent Tools - Month 1 & 2 Implementation

Includes:
- Tier 2: Data Processing (pandas, visualization)
- Tier 3: Document Extraction (PDF, Excel, Word with docling)
- Tier 4: Vision & OCR
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class EnhancedAgentTools:
    """Enhanced tools for data processing, document extraction, and vision"""

    def __init__(self, workspace: Path, artifacts_dir: Path, session_state: Dict):
        self.workspace = workspace
        self.artifacts_dir = artifacts_dir
        self.session_state = session_state

        # Lazy imports for heavy dependencies
        self._pandas = None
        self._matplotlib = None
        self._seaborn = None
        self._plotly = None

    @property
    def pandas(self):
        if self._pandas is None:
            import pandas as pd
            self._pandas = pd
        return self._pandas

    @property
    def matplotlib(self):
        if self._matplotlib is None:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            self._matplotlib = plt
        return self._matplotlib

    @property
    def seaborn(self):
        if self._seaborn is None:
            import seaborn as sns
            self._seaborn = sns
        return self._seaborn

    @property
    def plotly(self):
        if self._plotly is None:
            import plotly.express as px
            import plotly.graph_objects as go
            self._plotly = {'px': px, 'go': go}
        return self._plotly

    # ========================================================================
    # TIER 2: DATA PROCESSING TOOLS
    # ========================================================================

    async def analyze_dataframe(
        self,
        file_path: str,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Comprehensive EDA on CSV/Excel data

        Args:
            file_path: Path to CSV/Excel file (relative to workspace)
            analysis_type: 'quick' | 'comprehensive' | 'custom'

        Returns:
            Dictionary with summary stats, correlations, insights, visualizations
        """
        try:
            # Validate file path
            full_path = self.workspace / file_path
            if not full_path.exists():
                return {"success": False, "error": "File not found"}

            if not full_path.suffix in ['.csv', '.xlsx', '.xls']:
                return {"success": False, "error": "Unsupported file type. Use CSV or Excel."}

            # Load data
            pd = self.pandas
            if file_path.endswith('.csv'):
                df = pd.read_csv(full_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(full_path)

            # Basic analysis
            result = {
                "success": True,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "data_types": df.dtypes.astype(str).to_dict(),
                "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024
            }

            # Summary statistics
            result["summary_stats"] = df.describe().to_dict()

            # Missing values analysis
            missing = df.isnull().sum()
            result["missing_values"] = {
                "count": missing.to_dict(),
                "percentage": (missing / len(df) * 100).to_dict()
            }

            # Data type breakdown
            result["dtype_counts"] = df.dtypes.value_counts().to_dict()

            # Comprehensive analysis
            if analysis_type in ['comprehensive', 'custom']:
                # Correlation analysis (numeric columns only)
                numeric_df = df.select_dtypes(include=['number'])
                if not numeric_df.empty and len(numeric_df.columns) > 1:
                    result["correlations"] = numeric_df.corr().to_dict()

                    # Generate correlation heatmap
                    plt = self.matplotlib
                    sns = self.seaborn

                    plt.figure(figsize=(12, 8))
                    sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', center=0)
                    plt.title('Correlation Heatmap')

                    viz_path = self.artifacts_dir / f"correlation_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    plt.savefig(viz_path, bbox_inches='tight', dpi=150)
                    plt.close()

                    result["visualizations"] = result.get("visualizations", [])
                    result["visualizations"].append(str(viz_path.relative_to(self.workspace)))

                    # Track artifact
                    self.session_state["artifacts"].append({
                        "path": str(viz_path.relative_to(self.workspace)),
                        "type": "visualization",
                        "created_at": datetime.utcnow().isoformat()
                    })

                # Distribution analysis
                if not numeric_df.empty:
                    plt = self.matplotlib

                    # Create distribution plots for numeric columns (max 6)
                    cols_to_plot = numeric_df.columns[:6]
                    n_cols = len(cols_to_plot)

                    if n_cols > 0:
                        fig, axes = plt.subplots(
                            nrows=(n_cols + 2) // 3,
                            ncols=min(n_cols, 3),
                            figsize=(15, 5 * ((n_cols + 2) // 3))
                        )
                        if n_cols == 1:
                            axes = [axes]
                        else:
                            axes = axes.flatten()

                        for idx, col in enumerate(cols_to_plot):
                            axes[idx].hist(numeric_df[col].dropna(), bins=30, edgecolor='black')
                            axes[idx].set_title(f'Distribution: {col}')
                            axes[idx].set_xlabel(col)
                            axes[idx].set_ylabel('Frequency')

                        # Hide empty subplots
                        for idx in range(n_cols, len(axes)):
                            axes[idx].axis('off')

                        plt.tight_layout()

                        viz_path = self.artifacts_dir / f"distributions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        plt.savefig(viz_path, bbox_inches='tight', dpi=150)
                        plt.close()

                        result["visualizations"].append(str(viz_path.relative_to(self.workspace)))

                        self.session_state["artifacts"].append({
                            "path": str(viz_path.relative_to(self.workspace)),
                            "type": "visualization",
                            "created_at": datetime.utcnow().isoformat()
                        })

            # Generate insights
            insights = []

            # Missing values insights
            high_missing = {k: v for k, v in result["missing_values"]["percentage"].items() if v > 10}
            if high_missing:
                insights.append(f"Columns with >10% missing values: {list(high_missing.keys())}")

            # High correlations
            if "correlations" in result:
                corr_df = pd.DataFrame(result["correlations"])
                high_corr = []
                for i in range(len(corr_df.columns)):
                    for j in range(i+1, len(corr_df.columns)):
                        corr_val = corr_df.iloc[i, j]
                        if abs(corr_val) > 0.7:
                            high_corr.append(
                                f"{corr_df.columns[i]} ↔ {corr_df.columns[j]}: {corr_val:.2f}"
                            )
                if high_corr:
                    insights.append(f"Strong correlations found: {'; '.join(high_corr[:5])}")

            # Data quality
            duplicate_rows = df.duplicated().sum()
            if duplicate_rows > 0:
                insights.append(f"Found {duplicate_rows} duplicate rows")

            result["insights"] = insights

            logger.info(f"✅ DataFrame analysis complete: {len(df)} rows, {len(df.columns)} columns")
            return result

        except Exception as e:
            logger.error(f"DataFrame analysis error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    async def visualize_data(
        self,
        file_path: str,
        chart_type: str = "auto",
        x_column: str = None,
        y_column: str = None,
        title: str = None
    ) -> Dict[str, Any]:
        """
        Create visualizations from data

        Args:
            file_path: Path to CSV/Excel file
            chart_type: 'auto' | 'scatter' | 'line' | 'bar' | 'box' | 'histogram'
            x_column: Column for X-axis
            y_column: Column for Y-axis
            title: Chart title

        Returns:
            Dictionary with visualization path
        """
        try:
            # Load data
            full_path = self.workspace / file_path
            pd = self.pandas

            if file_path.endswith('.csv'):
                df = pd.read_csv(full_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(full_path)
            else:
                return {"success": False, "error": "Unsupported file type"}

            plt = self.matplotlib

            # Auto-detect columns if not specified
            if chart_type == "auto":
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) >= 2:
                    x_column = x_column or numeric_cols[0]
                    y_column = y_column or numeric_cols[1]
                    chart_type = "scatter"
                elif len(numeric_cols) == 1:
                    y_column = y_column or numeric_cols[0]
                    chart_type = "histogram"
                else:
                    return {"success": False, "error": "No numeric columns found for visualization"}

            # Create visualization
            plt.figure(figsize=(12, 6))

            if chart_type == "scatter":
                plt.scatter(df[x_column], df[y_column], alpha=0.6)
                plt.xlabel(x_column)
                plt.ylabel(y_column)

            elif chart_type == "line":
                plt.plot(df[x_column], df[y_column])
                plt.xlabel(x_column)
                plt.ylabel(y_column)

            elif chart_type == "bar":
                df.groupby(x_column)[y_column].mean().plot(kind='bar')
                plt.xlabel(x_column)
                plt.ylabel(f'Average {y_column}')

            elif chart_type == "box":
                df.boxplot(column=y_column, by=x_column)

            elif chart_type == "histogram":
                plt.hist(df[y_column].dropna(), bins=30, edgecolor='black')
                plt.xlabel(y_column)
                plt.ylabel('Frequency')

            plt.title(title or f"{chart_type.title()} Plot")
            plt.tight_layout()

            # Save
            viz_path = self.artifacts_dir / f"{chart_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(viz_path, bbox_inches='tight', dpi=150)
            plt.close()

            # Track artifact
            self.session_state["artifacts"].append({
                "path": str(viz_path.relative_to(self.workspace)),
                "type": "visualization",
                "created_at": datetime.utcnow().isoformat()
            })

            return {
                "success": True,
                "visualization": str(viz_path.relative_to(self.workspace)),
                "chart_type": chart_type
            }

        except Exception as e:
            logger.error(f"Visualization error: {str(e)}")
            return {"success": False, "error": str(e)}

    # ========================================================================
    # TIER 3: DOCUMENT EXTRACTION TOOLS
    # ========================================================================

    async def extract_pdf_content(
        self,
        file_path: str,
        strategy: str = "auto",
        extract_tables: bool = True,
        use_ocr: bool = False
    ) -> Dict[str, Any]:
        """
        Multi-strategy PDF extraction with docling, pdfplumber, and OCR

        Args:
            file_path: Path to PDF file
            strategy: 'auto' | 'text' | 'tables' | 'ocr' | 'docling'
            extract_tables: Whether to extract tables
            use_ocr: Force OCR even if text exists

        Returns:
            Extracted content (text, tables, metadata)
        """
        try:
            full_path = self.workspace / file_path
            if not full_path.exists():
                return {"success": False, "error": "File not found"}

            result = {
                "success": True,
                "file": file_path,
                "strategy_used": strategy,
                "text": "",
                "tables": [],
                "metadata": {}
            }

            # Strategy: docling (best for structured documents)
            if strategy in ["auto", "docling"]:
                try:
                    from docling.document_converter import DocumentConverter

                    converter = DocumentConverter()
                    doc = converter.convert(str(full_path))

                    result["text"] = doc.export_to_markdown()
                    result["strategy_used"] = "docling"
                    result["metadata"]["pages"] = len(doc.pages) if hasattr(doc, 'pages') else None

                    logger.info(f"✅ PDF extracted with docling: {len(result['text'])} characters")

                except Exception as e:
                    logger.warning(f"Docling extraction failed: {str(e)}, trying pdfplumber...")
                    strategy = "text"  # Fallback

            # Strategy: pdfplumber (good for tables)
            if strategy in ["auto", "text", "tables"] and not result["text"]:
                try:
                    import pdfplumber

                    text_parts = []
                    tables_extracted = []

                    with pdfplumber.open(full_path) as pdf:
                        result["metadata"]["pages"] = len(pdf.pages)

                        for page_num, page in enumerate(pdf.pages, 1):
                            # Extract text
                            page_text = page.extract_text()
                            if page_text:
                                text_parts.append(f"--- Page {page_num} ---\n{page_text}\n")

                            # Extract tables
                            if extract_tables:
                                tables = page.extract_tables()
                                for table_idx, table in enumerate(tables, 1):
                                    if table:
                                        # Convert to CSV
                                        table_csv_path = self.artifacts_dir / f"pdf_table_p{page_num}_t{table_idx}.csv"

                                        import csv
                                        with open(table_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                                            writer = csv.writer(csvfile)
                                            writer.writerows(table)

                                        tables_extracted.append({
                                            "page": page_num,
                                            "table_index": table_idx,
                                            "csv_path": str(table_csv_path.relative_to(self.workspace)),
                                            "rows": len(table),
                                            "cols": len(table[0]) if table else 0
                                        })

                                        self.session_state["artifacts"].append({
                                            "path": str(table_csv_path.relative_to(self.workspace)),
                                            "type": "table",
                                            "created_at": datetime.utcnow().isoformat()
                                        })

                    result["text"] = "\n".join(text_parts)
                    result["tables"] = tables_extracted
                    result["strategy_used"] = "pdfplumber"

                    logger.info(f"✅ PDF extracted with pdfplumber: {len(result['text'])} characters, {len(tables_extracted)} tables")

                except Exception as e:
                    logger.warning(f"pdfplumber extraction failed: {str(e)}")

            # Strategy: OCR (for scanned PDFs or if forced)
            if (use_ocr or not result["text"]) and strategy in ["auto", "ocr"]:
                try:
                    from pdf2image import convert_from_path
                    import pytesseract

                    # Convert PDF to images
                    images = convert_from_path(str(full_path), dpi=300)

                    text_parts = []
                    for page_num, image in enumerate(images, 1):
                        # OCR each page
                        page_text = pytesseract.image_to_string(image)
                        text_parts.append(f"--- Page {page_num} (OCR) ---\n{page_text}\n")

                    result["text"] = "\n".join(text_parts)
                    result["strategy_used"] = "ocr"
                    result["metadata"]["pages"] = len(images)

                    logger.info(f"✅ PDF extracted with OCR: {len(result['text'])} characters")

                except Exception as e:
                    logger.error(f"OCR extraction failed: {str(e)}")
                    return {"success": False, "error": f"All extraction strategies failed. Last error: {str(e)}"}

            # Save extracted text
            if result["text"]:
                text_path = self.artifacts_dir / f"pdf_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(result["text"])

                result["text_file"] = str(text_path.relative_to(self.workspace))

                self.session_state["artifacts"].append({
                    "path": str(text_path.relative_to(self.workspace)),
                    "type": "extracted_text",
                    "created_at": datetime.utcnow().isoformat()
                })

            return result

        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    async def analyze_excel_workbook(
        self,
        file_path: str,
        analyze_formulas: bool = True
    ) -> Dict[str, Any]:
        """
        Deep Excel analysis with multi-sheet support

        Args:
            file_path: Path to Excel file
            analyze_formulas: Whether to extract and analyze formulas

        Returns:
            Sheet summaries, formulas, data ranges
        """
        try:
            full_path = self.workspace / file_path
            if not full_path.exists():
                return {"success": False, "error": "File not found"}

            pd = self.pandas
            import openpyxl

            # Load with openpyxl for formula analysis
            wb = openpyxl.load_workbook(str(full_path), data_only=False)

            result = {
                "success": True,
                "file": file_path,
                "sheets": {},
                "formulas": [] if analyze_formulas else None,
                "total_sheets": len(wb.sheetnames)
            }

            # Analyze each sheet
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]

                # Load as DataFrame for data analysis
                df = pd.read_excel(full_path, sheet_name=sheet_name)

                sheet_info = {
                    "name": sheet_name,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": list(df.columns),
                    "data_types": df.dtypes.astype(str).to_dict(),
                    "summary_stats": df.describe().to_dict() if not df.empty else {}
                }

                # Extract formulas
                if analyze_formulas:
                    for row in ws.iter_rows():
                        for cell in row:
                            if cell.value and isinstance(cell.value, str) and cell.value.startswith('='):
                                result["formulas"].append({
                                    "sheet": sheet_name,
                                    "cell": cell.coordinate,
                                    "formula": cell.value
                                })

                # Export sheet as CSV
                csv_path = self.artifacts_dir / f"excel_{sheet_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df.to_csv(csv_path, index=False)

                sheet_info["csv_export"] = str(csv_path.relative_to(self.workspace))

                self.session_state["artifacts"].append({
                    "path": str(csv_path.relative_to(self.workspace)),
                    "type": "csv_export",
                    "created_at": datetime.utcnow().isoformat()
                })

                result["sheets"][sheet_name] = sheet_info

            logger.info(f"✅ Excel analysis complete: {len(wb.sheetnames)} sheets")

            return result

        except Exception as e:
            logger.error(f"Excel analysis error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def extract_word_document(
        self,
        file_path: str,
        extract_images: bool = False
    ) -> Dict[str, Any]:
        """
        Extract content from Word documents

        Args:
            file_path: Path to .docx file
            extract_images: Whether to extract images

        Returns:
            Text, tables, metadata
        """
        try:
            full_path = self.workspace / file_path
            if not full_path.exists():
                return {"success": False, "error": "File not found"}

            from docx import Document

            doc = Document(str(full_path))

            result = {
                "success": True,
                "file": file_path,
                "text": "",
                "tables": [],
                "paragraphs_count": len(doc.paragraphs),
                "tables_count": len(doc.tables)
            }

            # Extract text
            text_parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)

            result["text"] = "\n\n".join(text_parts)

            # Extract tables
            for table_idx, table in enumerate(doc.tables, 1):
                table_data = []
                for row in table.rows:
                    row_data = [cell.text for cell in row.cells]
                    table_data.append(row_data)

                # Save table as CSV
                table_csv_path = self.artifacts_dir / f"word_table_{table_idx}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

                import csv
                with open(table_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(table_data)

                result["tables"].append({
                    "table_index": table_idx,
                    "csv_path": str(table_csv_path.relative_to(self.workspace)),
                    "rows": len(table_data),
                    "cols": len(table_data[0]) if table_data else 0
                })

                self.session_state["artifacts"].append({
                    "path": str(table_csv_path.relative_to(self.workspace)),
                    "type": "table",
                    "created_at": datetime.utcnow().isoformat()
                })

            # Save extracted text
            text_path = self.artifacts_dir / f"word_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(result["text"])

            result["text_file"] = str(text_path.relative_to(self.workspace))

            self.session_state["artifacts"].append({
                "path": str(text_path.relative_to(self.workspace)),
                "type": "extracted_text",
                "created_at": datetime.utcnow().isoformat()
            })

            logger.info(f"✅ Word document extracted: {len(result['text'])} characters, {len(result['tables'])} tables")

            return result

        except Exception as e:
            logger.error(f"Word extraction error: {str(e)}")
            return {"success": False, "error": str(e)}

    # ========================================================================
    # TIER 4: VISION & OCR TOOLS
    # ========================================================================

    async def analyze_image_with_vision(
        self,
        image_path: str,
        prompt: str = "Describe this image in detail, including any text, charts, diagrams, or data you can see.",
        model: str = "llama3.2-vision:11b"
    ) -> Dict[str, Any]:
        """
        Use vision model (llama3.2-vision via Ollama) to analyze images

        Args:
            image_path: Path to image file
            prompt: What to ask the vision model
            model: Vision model to use

        Returns:
            Vision model response
        """
        try:
            full_path = self.workspace / image_path
            if not full_path.exists():
                return {"success": False, "error": "Image not found"}

            # Read image as base64
            import base64
            with open(full_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # Call Ollama vision model
            import ollama

            response = ollama.chat(
                model=model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [image_data]
                }]
            )

            result = {
                "success": True,
                "image": image_path,
                "model": model,
                "prompt": prompt,
                "description": response['message']['content']
            }

            logger.info(f"✅ Vision analysis complete for {image_path}")

            return result

        except Exception as e:
            logger.error(f"Vision analysis error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def extract_text_from_image(
        self,
        image_path: str,
        engine: str = "tesseract",
        language: str = "eng"
    ) -> Dict[str, Any]:
        """
        OCR text extraction from images

        Args:
            image_path: Path to image file
            engine: 'tesseract' | 'easyocr'
            language: Language code (eng, fra, deu, spa, etc.)

        Returns:
            Extracted text
        """
        try:
            full_path = self.workspace / image_path
            if not full_path.exists():
                return {"success": False, "error": "Image not found"}

            from PIL import Image

            image = Image.open(full_path)

            text = ""

            if engine == "tesseract":
                import pytesseract
                text = pytesseract.image_to_string(image, lang=language)

            elif engine == "easyocr":
                import easyocr
                reader = easyocr.Reader([language])
                results = reader.readtext(str(full_path))
                text = "\n".join([result[1] for result in results])

            # Save extracted text
            text_path = self.artifacts_dir / f"ocr_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text)

            result = {
                "success": True,
                "image": image_path,
                "engine": engine,
                "language": language,
                "text": text,
                "text_file": str(text_path.relative_to(self.workspace)),
                "character_count": len(text)
            }

            self.session_state["artifacts"].append({
                "path": str(text_path.relative_to(self.workspace)),
                "type": "ocr_text",
                "created_at": datetime.utcnow().isoformat()
            })

            logger.info(f"✅ OCR extraction complete: {len(text)} characters")

            return result

        except Exception as e:
            logger.error(f"OCR extraction error: {str(e)}")
            return {"success": False, "error": str(e)}
