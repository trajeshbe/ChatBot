"""
Matcher Service
Tier 2 Module: Procurement

PO-to-invoice matching and reconciliation using tier_1 services.
100% tier_1 service reuse - zero new dependencies.
"""

import uuid
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from app.tier_1.document_processing.document_service import DocumentService

from .matcher_schemas import (
    POMatchRequest,
    POMatchResponse,
    BulkMatchRequest,
    BulkMatchResponse,
    PurchaseOrder,
    Invoice,
    LineItem,
    MatchResult,
    MatchStatus,
    Discrepancy,
    DiscrepancyType
)

logger = logging.getLogger(__name__)


class MatcherService:
    """
    PO-to-invoice matching service.

    Matching Process:
    1. Document Extraction → Extract PO and invoice data using LLM
    2. Data Normalization → Standardize formats, currencies
    3. Fuzzy Matching → Match by PO number, vendor, date ranges
    4. Line Item Matching → Match individual line items
    5. Variance Calculation → Calculate price, quantity, total variances
    6. Discrepancy Identification → Flag exceptions and anomalies
    7. Approval Routing → Determine if manual approval required
    8. Confidence Scoring → Calculate overall match confidence
    """

    def __init__(self, db: Session, settings: Settings, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.settings = settings
        self.config = config or {}

        # Tier 1 service dependencies
        self.llm_service = LLMService()
        self.document_service = DocumentService(db, settings)

        logger.info("✓ MatcherService initialized with tier_1 services")
        if config:
            logger.info(f"✓ Using module config with model: {config.get(\'llm\', {}).get(\'default\', {}).get(\'model\', \'default\')}")

    async def match_po_to_invoice(
        self,
        request: POMatchRequest
    ) -> POMatchResponse:
        """Match PO to invoice with variance analysis."""
        start_time = datetime.utcnow()
        match_id = str(uuid.uuid4())

        logger.info(f"💼 Starting PO-to-invoice matching")

        try:
            # Step 1: Get PO data (from document or manual)
            if request.use_document_extraction and request.po_document_id:
                po_data = await self._extract_po_data(request.po_document_id)
            elif request.po_data:
                po_data = request.po_data
            else:
                raise ValueError("Either po_document_id or po_data must be provided")

            # Step 2: Get invoice data (from document or manual)
            if request.use_document_extraction and request.invoice_document_id:
                invoice_data = await self._extract_invoice_data(request.invoice_document_id)
            elif request.invoice_data:
                invoice_data = request.invoice_data
            else:
                raise ValueError("Either invoice_document_id or invoice_data must be provided")

            # Step 3: Perform matching
            match_result = await self._perform_matching(
                po_data,
                invoice_data,
                request.variance_tolerance_percent,
                request.auto_approve_threshold_percent
            )

            # Step 4: Store match result
            await self._store_match_result(request, match_result)

            # Step 5: Build response
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            response = POMatchResponse(
                match_id=match_id,
                po_number=po_data.po_number,
                invoice_number=invoice_data.invoice_number,
                match_status=match_result.match_status,
                match_confidence=match_result.match_confidence,
                po_summary={
                    "po_number": po_data.po_number,
                    "vendor": po_data.vendor_name,
                    "total_amount": po_data.total_amount,
                    "currency": po_data.currency,
                    "line_items": len(po_data.line_items)
                },
                invoice_summary={
                    "invoice_number": invoice_data.invoice_number,
                    "vendor": invoice_data.vendor_name,
                    "total_amount": invoice_data.total_amount,
                    "currency": invoice_data.currency,
                    "line_items": len(invoice_data.line_items)
                },
                match_result=match_result,
                processing_time_seconds=processing_time,
                tier_1_services_used=["LLMService", "DocumentService"] if request.use_document_extraction else ["LLMService"]
            )

            logger.info(f"✓ Match complete: {match_result.match_status.value} (confidence: {match_result.match_confidence:.2f})")
            return response

        except Exception as e:
            logger.error(f"❌ Matching failed: {str(e)}", exc_info=True)
            raise

    async def _extract_po_data(self, document_id: str) -> PurchaseOrder:
        """Extract PO data from document using LLM."""
        try:
            from app.models.database import Document
            doc = self.db.query(Document).filter(Document.id == document_id).first()

            if not doc:
                raise ValueError(f"Document {document_id} not found")

            chunks = await self.document_service.get_document_chunks(document_id)
            text = "\n".join([chunk.content for chunk in chunks[:5]])

            prompt = f"""Extract purchase order details from this document:

{text}

Extract the following fields:
- PO number
- Vendor name
- PO date
- Total amount
- Tax amount
- Currency
- Line items (description, quantity, unit price, total)
- Department
- Requester
- Delivery date

Return JSON:
{{
    "po_number": "PO-12345",
    "vendor_name": "Acme Corp",
    "po_date": "2024-01-15",
    "total_amount": 15000.00,
    "tax_amount": 1500.00,
    "currency": "USD",
    "line_items": [
        {{
            "description": "Widget A",
            "quantity": 100,
            "unit_price": 50.00,
            "total": 5000.00
        }}
    ],
    "department": "IT",
    "requester": "John Doe"
}}

Return ONLY valid JSON."""

            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o-mini')
            temperature = llm_config.get('temperature', 0.0)
            max_tokens = llm_config.get('max_tokens', 1000)

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            data = json.loads(response.strip())

            # Convert to PurchaseOrder model
            line_items = [
                LineItem(
                    description=item["description"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total=item["total"]
                )
                for item in data.get("line_items", [])
            ]

            return PurchaseOrder(
                po_number=data["po_number"],
                vendor_name=data["vendor_name"],
                po_date=datetime.fromisoformat(data["po_date"]) if data.get("po_date") else None,
                total_amount=data["total_amount"],
                tax_amount=data.get("tax_amount"),
                currency=data.get("currency", "USD"),
                line_items=line_items,
                department=data.get("department"),
                requester=data.get("requester")
            )

        except Exception as e:
            logger.error(f"Failed to extract PO data: {str(e)}")
            raise

    async def _extract_invoice_data(self, document_id: str) -> Invoice:
        """Extract invoice data from document using LLM."""
        try:
            from app.models.database import Document
            doc = self.db.query(Document).filter(Document.id == document_id).first()

            if not doc:
                raise ValueError(f"Document {document_id} not found")

            chunks = await self.document_service.get_document_chunks(document_id)
            text = "\n".join([chunk.content for chunk in chunks[:5]])

            prompt = f"""Extract invoice details from this document:

{text}

Extract the following fields:
- Invoice number
- Vendor name
- Invoice date
- Due date
- Total amount
- Tax amount
- Currency
- Line items (description, quantity, unit price, total)
- Payment terms
- PO number reference (if mentioned)

Return JSON:
{{
    "invoice_number": "INV-67890",
    "vendor_name": "Acme Corp",
    "invoice_date": "2024-01-20",
    "due_date": "2024-02-20",
    "total_amount": 16500.00,
    "tax_amount": 1500.00,
    "currency": "USD",
    "line_items": [
        {{
            "description": "Widget A",
            "quantity": 100,
            "unit_price": 55.00,
            "total": 5500.00
        }}
    ],
    "payment_terms": "Net 30",
    "po_number_reference": "PO-12345"
}}

Return ONLY valid JSON."""

            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o-mini')
            temperature = llm_config.get('temperature', 0.0)
            max_tokens = llm_config.get('max_tokens', 1000)

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            data = json.loads(response.strip())

            # Convert to Invoice model
            line_items = [
                LineItem(
                    description=item["description"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total=item["total"]
                )
                for item in data.get("line_items", [])
            ]

            return Invoice(
                invoice_number=data["invoice_number"],
                vendor_name=data["vendor_name"],
                invoice_date=datetime.fromisoformat(data["invoice_date"]) if data.get("invoice_date") else None,
                due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
                total_amount=data["total_amount"],
                tax_amount=data.get("tax_amount"),
                currency=data.get("currency", "USD"),
                line_items=line_items,
                payment_terms=data.get("payment_terms"),
                po_number_reference=data.get("po_number_reference")
            )

        except Exception as e:
            logger.error(f"Failed to extract invoice data: {str(e)}")
            raise

    async def _perform_matching(
        self,
        po: PurchaseOrder,
        invoice: Invoice,
        variance_tolerance: float,
        auto_approve_threshold: float
    ) -> MatchResult:
        """Perform PO-to-invoice matching with variance analysis."""
        discrepancies = []
        match_confidence = 100.0  # Start at 100%

        # Check vendor match
        if po.vendor_name.lower() != invoice.vendor_name.lower():
            discrepancies.append(Discrepancy(
                discrepancy_type=DiscrepancyType.VENDOR_MISMATCH,
                description=f"Vendor mismatch: PO '{po.vendor_name}' vs Invoice '{invoice.vendor_name}'",
                po_value=po.vendor_name,
                invoice_value=invoice.vendor_name,
                severity="critical",
                recommended_action="Verify vendor details before processing"
            ))
            match_confidence -= 30.0

        # Check PO number reference
        if invoice.po_number_reference and invoice.po_number_reference != po.po_number:
            discrepancies.append(Discrepancy(
                discrepancy_type=DiscrepancyType.MISSING_PO,
                description=f"PO number mismatch: Expected '{po.po_number}', Invoice references '{invoice.po_number_reference}'",
                po_value=po.po_number,
                invoice_value=invoice.po_number_reference,
                severity="high",
                recommended_action="Verify PO number reference"
            ))
            match_confidence -= 20.0

        # Check total amount variance
        total_variance = abs(invoice.total_amount - po.total_amount)
        total_variance_percent = (total_variance / po.total_amount * 100) if po.total_amount > 0 else 0

        if total_variance_percent > variance_tolerance:
            discrepancies.append(Discrepancy(
                discrepancy_type=DiscrepancyType.TOTAL_AMOUNT_VARIANCE,
                description=f"Total amount variance of {total_variance_percent:.2f}% exceeds tolerance",
                po_value=po.total_amount,
                invoice_value=invoice.total_amount,
                variance_amount=total_variance,
                variance_percent=total_variance_percent,
                severity="high" if total_variance_percent > 10 else "medium",
                recommended_action="Review pricing and quantities"
            ))
            match_confidence -= min(total_variance_percent * 2, 40.0)

        # Check tax variance
        if po.tax_amount and invoice.tax_amount:
            tax_variance = abs(invoice.tax_amount - po.tax_amount)
            tax_variance_percent = (tax_variance / po.tax_amount * 100) if po.tax_amount > 0 else 0

            if tax_variance_percent > variance_tolerance:
                discrepancies.append(Discrepancy(
                    discrepancy_type=DiscrepancyType.TAX_VARIANCE,
                    description=f"Tax variance of {tax_variance_percent:.2f}%",
                    po_value=po.tax_amount,
                    invoice_value=invoice.tax_amount,
                    variance_amount=tax_variance,
                    variance_percent=tax_variance_percent,
                    severity="medium",
                    recommended_action="Verify tax calculation"
                ))
                match_confidence -= 10.0

        # Match line items
        matched_items = 0
        total_items = max(len(po.line_items), len(invoice.line_items))

        for po_item in po.line_items:
            # Find matching invoice line item (simplified - match by description)
            matched = False
            for inv_item in invoice.line_items:
                if po_item.description.lower() in inv_item.description.lower() or \
                   inv_item.description.lower() in po_item.description.lower():
                    matched = True
                    matched_items += 1

                    # Check quantity variance
                    if abs(inv_item.quantity - po_item.quantity) > 0.01:
                        discrepancies.append(Discrepancy(
                            discrepancy_type=DiscrepancyType.QUANTITY_VARIANCE,
                            description=f"Quantity variance for '{po_item.description}'",
                            po_value=po_item.quantity,
                            invoice_value=inv_item.quantity,
                            variance_amount=abs(inv_item.quantity - po_item.quantity),
                            severity="medium",
                            recommended_action="Verify quantity received"
                        ))

                    # Check price variance
                    price_variance_percent = abs(inv_item.unit_price - po_item.unit_price) / po_item.unit_price * 100 if po_item.unit_price > 0 else 0
                    if price_variance_percent > variance_tolerance:
                        discrepancies.append(Discrepancy(
                            discrepancy_type=DiscrepancyType.PRICE_VARIANCE,
                            description=f"Price variance for '{po_item.description}': {price_variance_percent:.2f}%",
                            po_value=po_item.unit_price,
                            invoice_value=inv_item.unit_price,
                            variance_percent=price_variance_percent,
                            severity="medium",
                            recommended_action="Verify pricing agreement"
                        ))
                    break

            if not matched:
                discrepancies.append(Discrepancy(
                    discrepancy_type=DiscrepancyType.LINE_ITEM_MISMATCH,
                    description=f"Line item '{po_item.description}' in PO not found in invoice",
                    severity="medium",
                    recommended_action="Check if item was removed or description changed"
                ))

        # Determine match status
        match_confidence = max(0.0, min(100.0, match_confidence))

        if len(discrepancies) == 0:
            match_status = MatchStatus.EXACT_MATCH
        elif total_variance_percent <= auto_approve_threshold:
            match_status = MatchStatus.EXACT_MATCH
        elif total_variance_percent <= variance_tolerance:
            match_status = MatchStatus.PARTIAL_MATCH
        else:
            match_status = MatchStatus.UNDER_REVIEW

        requires_approval = total_variance_percent > auto_approve_threshold
        approval_threshold_exceeded = total_variance_percent > variance_tolerance

        return MatchResult(
            po_number=po.po_number,
            invoice_number=invoice.invoice_number,
            match_status=match_status,
            match_confidence=match_confidence / 100.0,
            total_variance_amount=total_variance,
            total_variance_percent=total_variance_percent,
            discrepancies=discrepancies,
            matched_line_items=matched_items,
            total_line_items=total_items,
            requires_approval=requires_approval,
            approval_threshold_exceeded=approval_threshold_exceeded
        )

    async def _store_match_result(
        self,
        request: POMatchRequest,
        match_result: MatchResult
    ):
        """Store match result in database."""
        try:
            from app.models.database_enhanced import POMatchResults

            match_record = POMatchResults(
                id=uuid.uuid4(),
                match_id=uuid.UUID(match_result.match_id),
                module_id="matcher",
                po_document_id=uuid.UUID(request.po_document_id) if request.po_document_id else None,
                invoice_document_id=uuid.UUID(request.invoice_document_id) if request.invoice_document_id else None,
                session_id=request.session_id,
                project_id=uuid.UUID(request.project_id) if request.project_id else None,
                match_data={
                    "match_status": match_result.match_status.value,
                    "match_confidence": match_result.match_confidence,
                    "total_variance_amount": match_result.total_variance_amount,
                    "total_variance_percent": match_result.total_variance_percent,
                    "discrepancies": [d.dict() for d in match_result.discrepancies],
                    "requires_approval": match_result.requires_approval
                },
                created_at=datetime.utcnow()
            )

            self.db.add(match_record)
            self.db.commit()

            logger.info(f"✓ Stored match result")

        except Exception as e:
            logger.error(f"Failed to store match result: {str(e)}")
