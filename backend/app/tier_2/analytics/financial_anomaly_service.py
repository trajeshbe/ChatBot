"""Financial Anomaly Detector - Business Logic Service"""

import logging
import statistics
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .financial_anomaly_schemas import *

logger = logging.getLogger(__name__)


class FinancialAnomalyService:
    """Service for financial anomaly detection"""

    def __init__(self, db: Session, settings: Settings, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.settings = settings
        self.config = config or {}
        self.llm_service = LLMService()
        if config:
            logger.info(f"✓ Using module config with model: {config.get('llm', {}).get('default', {}).get('model', 'default')}")

    async def detect_anomalies(self, request: DetectAnomaliesRequest) -> DetectAnomaliesResponse:
        """Detect financial anomalies with AI analysis"""
        try:
            logger.info(f"Analyzing {len(request.transactions)} transactions for anomalies")

            # Build account profiles
            account_profiles = {acc.account_id: acc for acc in request.accounts}

            # Detect anomalies
            anomalies = []
            for txn in request.transactions:
                account = account_profiles.get(txn.account_id)
                if account:
                    detected = self._detect_transaction_anomalies(txn, account, request.detection_sensitivity)
                    anomalies.extend(detected)

            # Score fraud risk
            fraud_scores = []
            if request.include_fraud_scoring:
                for txn in request.transactions:
                    account = account_profiles.get(txn.account_id)
                    if account:
                        score = self._score_fraud_risk(txn, account, anomalies)
                        fraud_scores.append(score)

            # Detect patterns
            patterns = self._detect_anomaly_patterns(anomalies, request.transactions)

            # Calculate summary stats
            summary_stats = self._calculate_summary_stats(anomalies, request.transactions)

            # Generate AI insights
            ai_insights = await self._generate_ai_insights(anomalies, patterns, summary_stats)

            # Generate risk mitigation recommendations
            risk_recs = self._generate_risk_mitigation(anomalies, patterns, fraud_scores)

            return DetectAnomaliesResponse(
                success=True,
                anomalies=anomalies,
                fraud_scores=fraud_scores,
                patterns=patterns,
                summary_stats=summary_stats,
                ai_insights=ai_insights,
                risk_mitigation_recommendations=risk_recs
            )

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}", exc_info=True)
            raise

    def _detect_transaction_anomalies(
        self, txn: TransactionData, account: AccountData, sensitivity: float
    ) -> List[AnomalyDetection]:
        """Detect anomalies in a single transaction"""
        anomalies = []

        # Amount-based anomaly detection
        amount_deviation = abs(txn.amount - account.typical_transaction_amount) / account.typical_transaction_amount if account.typical_transaction_amount > 0 else 0

        if amount_deviation > (2.0 / sensitivity):  # 2x typical = anomaly at default sensitivity
            anomaly_type = AnomalyType.SPENDING_SPIKE if txn.amount > account.typical_transaction_amount else AnomalyType.REVENUE_DROP
            anomaly_score = min(100.0, amount_deviation * 20 * sensitivity)

            if anomaly_score >= 80:
                risk_level = RiskLevel.CRITICAL
            elif anomaly_score >= 60:
                risk_level = RiskLevel.HIGH
            elif anomaly_score >= 40:
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW

            factors = [
                f"Transaction amount ${txn.amount:,.2f} is {amount_deviation:.1f}x typical amount",
                f"Typical transaction: ${account.typical_transaction_amount:,.2f}"
            ]

            actions = []
            if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                actions.append("Flag for immediate manual review")
                actions.append("Contact account holder for verification")
            else:
                actions.append("Monitor account for additional unusual activity")

            anomalies.append(AnomalyDetection(
                transaction_id=txn.transaction_id,
                account_id=txn.account_id,
                anomaly_type=anomaly_type,
                risk_level=risk_level,
                anomaly_score=round(anomaly_score, 2),
                deviation_percentage=round(amount_deviation * 100, 2),
                description=f"Unusual transaction amount detected - {amount_deviation:.1f}x deviation from typical",
                contributing_factors=factors,
                recommended_actions=actions
            ))

        # Refund abuse detection
        if txn.category == TransactionCategory.REFUND and txn.amount > account.typical_transaction_amount * 1.5:
            anomaly_score = min(100.0, 70 * sensitivity)
            risk_level = RiskLevel.HIGH if anomaly_score >= 60 else RiskLevel.MEDIUM

            anomalies.append(AnomalyDetection(
                transaction_id=txn.transaction_id,
                account_id=txn.account_id,
                anomaly_type=AnomalyType.REFUND_ABUSE,
                risk_level=risk_level,
                anomaly_score=round(anomaly_score, 2),
                deviation_percentage=round((txn.amount / account.typical_transaction_amount - 1) * 100, 2),
                description="Unusually large refund transaction - potential refund abuse",
                contributing_factors=["Large refund amount", "Exceeds typical transaction size"],
                recommended_actions=["Verify refund legitimacy", "Review refund policy compliance"]
            ))

        return anomalies

    def _score_fraud_risk(
        self, txn: TransactionData, account: AccountData, anomalies: List[AnomalyDetection]
    ) -> FraudRiskScore:
        """Score fraud risk for a transaction"""
        fraud_score = 20.0  # Base score

        fraud_indicators = []
        behavioral_patterns = []

        # Check if transaction has anomalies
        txn_anomalies = [a for a in anomalies if a.transaction_id == txn.transaction_id]
        if txn_anomalies:
            fraud_score += min(40, len(txn_anomalies) * 20)
            fraud_indicators.append(f"{len(txn_anomalies)} anomaly/anomalies detected")

        # Large transaction indicator
        if txn.amount > account.typical_transaction_amount * 5:
            fraud_score += 20
            fraud_indicators.append("Significantly larger than typical transaction")

        # Time-based patterns
        hour = txn.timestamp.hour
        if hour < 6 or hour > 22:  # Late night/early morning
            fraud_score += 10
            behavioral_patterns.append("Transaction during unusual hours")

        # Determine risk level
        if fraud_score >= 80:
            risk_level = RiskLevel.CRITICAL
        elif fraud_score >= 60:
            risk_level = RiskLevel.HIGH
        elif fraud_score >= 40:
            risk_level = RiskLevel.MEDIUM
        elif fraud_score >= 20:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.INFORMATIONAL

        # Verification recommendations
        verifications = []
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            verifications.extend([
                "Require multi-factor authentication",
                "Contact customer via verified phone number",
                "Temporarily hold transaction pending verification"
            ])
        elif risk_level == RiskLevel.MEDIUM:
            verifications.extend([
                "Send verification email to registered address",
                "Monitor for additional suspicious activity"
            ])

        return FraudRiskScore(
            transaction_id=txn.transaction_id,
            fraud_probability=round(min(100.0, fraud_score), 2),
            risk_level=risk_level,
            fraud_indicators=fraud_indicators[:5],
            behavioral_patterns=behavioral_patterns[:5],
            recommended_verification=verifications[:3]
        )

    def _detect_anomaly_patterns(
        self, anomalies: List[AnomalyDetection], transactions: List[TransactionData]
    ) -> List[AnomalyPattern]:
        """Detect patterns across multiple anomalies"""
        patterns = []

        # Group anomalies by type
        by_type = defaultdict(list)
        for anomaly in anomalies:
            by_type[anomaly.anomaly_type].append(anomaly)

        # Analyze each type
        for anomaly_type, type_anomalies in by_type.items():
            if len(type_anomalies) >= 3:  # Pattern requires at least 3 instances
                affected_accounts = len(set(a.account_id for a in type_anomalies))
                total_amount = sum(
                    txn.amount for txn in transactions
                    if txn.transaction_id in [a.transaction_id for a in type_anomalies]
                )

                # Get time range
                txn_times = [
                    txn.timestamp for txn in transactions
                    if txn.transaction_id in [a.transaction_id for a in type_anomalies]
                ]
                first_occurrence = min(txn_times) if txn_times else datetime.now()
                last_occurrence = max(txn_times) if txn_times else datetime.now()

                # Determine severity
                avg_score = statistics.mean(a.anomaly_score for a in type_anomalies)
                if avg_score >= 70:
                    severity = RiskLevel.CRITICAL
                elif avg_score >= 50:
                    severity = RiskLevel.HIGH
                elif avg_score >= 30:
                    severity = RiskLevel.MEDIUM
                else:
                    severity = RiskLevel.LOW

                patterns.append(AnomalyPattern(
                    pattern_id=f"pattern_{anomaly_type.value}_{len(patterns)}",
                    pattern_type=anomaly_type.value.replace('_', ' ').title(),
                    affected_accounts=affected_accounts,
                    total_transactions=len(type_anomalies),
                    total_amount=round(total_amount, 2),
                    first_occurrence=first_occurrence,
                    last_occurrence=last_occurrence,
                    severity=severity
                ))

        return patterns

    def _calculate_summary_stats(
        self, anomalies: List[AnomalyDetection], transactions: List[TransactionData]
    ) -> Dict[str, float]:
        """Calculate summary statistics"""
        total_anomalies = len(anomalies)
        total_transactions = len(transactions)
        anomaly_rate = (total_anomalies / total_transactions * 100) if total_transactions > 0 else 0.0

        critical_count = len([a for a in anomalies if a.risk_level == RiskLevel.CRITICAL])
        high_count = len([a for a in anomalies if a.risk_level == RiskLevel.HIGH])

        avg_anomaly_score = statistics.mean(a.anomaly_score for a in anomalies) if anomalies else 0.0

        flagged_txn_ids = set(a.transaction_id for a in anomalies)
        total_amount_flagged = sum(txn.amount for txn in transactions if txn.transaction_id in flagged_txn_ids)

        return {
            "total_anomalies": float(total_anomalies),
            "total_transactions": float(total_transactions),
            "anomaly_rate": round(anomaly_rate, 2),
            "critical_anomalies": float(critical_count),
            "high_risk_anomalies": float(high_count),
            "average_anomaly_score": round(avg_anomaly_score, 2),
            "total_amount_flagged": round(total_amount_flagged, 2)
        }

    async def _generate_ai_insights(
        self, anomalies: List[AnomalyDetection], patterns: List[AnomalyPattern],
        summary_stats: Dict[str, float]
    ) -> str:
        """Generate AI-powered insights using LLM"""
        try:
            critical_count = int(summary_stats.get("critical_anomalies", 0))
            anomaly_rate = summary_stats.get("anomaly_rate", 0)

            prompt = f"""Analyze this financial anomaly detection report:

Total Transactions: {int(summary_stats.get('total_transactions', 0))}
Anomalies Detected: {int(summary_stats.get('total_anomalies', 0))}
Anomaly Rate: {anomaly_rate:.1f}%
Critical Anomalies: {critical_count}
Patterns Identified: {len(patterns)}
Total Amount Flagged: ${summary_stats.get('total_amount_flagged', 0):,.2f}

Provide 2-3 sentences of expert insights on the anomaly patterns, fraud risk, and priority actions."""

            # Get LLM parameters from module config
            llm_config = self.config.get('llm', {}).get('default', {})
            model = llm_config.get('model', 'gpt-4o-mini')
            temperature = llm_config.get('temperature', 0.3)

            response = await self.llm_service.generate_response(
                prompt=prompt, model=model, temperature=temperature
            )
            return response.strip()

        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return "Anomaly detection complete. Focus on critical and high-risk transactions for immediate review."

    def _generate_risk_mitigation(
        self, anomalies: List[AnomalyDetection], patterns: List[AnomalyPattern],
        fraud_scores: List[FraudRiskScore]
    ) -> List[str]:
        """Generate risk mitigation recommendations"""
        recs = []

        # Critical anomaly recommendations
        critical_anomalies = [a for a in anomalies if a.risk_level == RiskLevel.CRITICAL]
        if critical_anomalies:
            recs.append(f"URGENT: {len(critical_anomalies)} critical anomalies require immediate investigation")

        # High fraud risk recommendations
        high_fraud = [f for f in fraud_scores if f.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]]
        if high_fraud:
            recs.append(f"{len(high_fraud)} transactions flagged as high fraud risk - implement additional verification")

        # Pattern-based recommendations
        critical_patterns = [p for p in patterns if p.severity == RiskLevel.CRITICAL]
        if critical_patterns:
            recs.append(f"{len(critical_patterns)} critical anomaly patterns detected - potential coordinated fraud")

        # General recommendations
        if len(anomalies) > 10:
            recs.append("High anomaly volume detected - review detection sensitivity and account security measures")

        return recs[:5]

    async def search_anomalies(self, request: SearchAnomaliesRequest) -> SearchAnomaliesResponse:
        """Search historical anomalies"""
        return SearchAnomaliesResponse(
            success=True,
            anomalies=[],
            total_count=0,
            summary_stats={"message": "Historical anomaly search - database integration pending"}
        )

    async def export_anomalies(self, request: ExportAnomaliesRequest) -> ExportAnomaliesResponse:
        """Export anomaly data"""
        return ExportAnomaliesResponse(
            success=True,
            export_data={"message": "Anomaly export", "format": request.format},
            format=request.format,
            record_count=0
        )

    async def get_stats(self) -> AnomalyStatsResponse:
        """Get anomaly detection statistics"""
        return AnomalyStatsResponse(
            success=True,
            total_anomalies_detected=0,
            total_transactions_analyzed=0,
            anomaly_rate=0.0,
            fraud_rate=0.0,
            most_common_anomaly_type="unusual_transaction",
            average_anomaly_score=0.0,
            total_amount_flagged=0.0
        )

    async def get_status(self) -> StatusResponse:
        """Get service status"""
        return StatusResponse(
            success=True,
            status="operational",
            capabilities=[
                "Real-time Transaction Anomaly Detection",
                "Fraud Risk Scoring",
                "Pattern Recognition",
                "Behavioral Analysis",
                "Risk Level Classification",
                "AI-Powered Insights",
                "Automated Alert Generation"
            ]
        )
