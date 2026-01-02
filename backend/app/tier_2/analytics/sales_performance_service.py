"""Sales Performance Analytics - Business Logic Service"""

import logging
from typing import List, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .sales_performance_schemas import *

logger = logging.getLogger(__name__)


class SalesPerformanceService:
    """Service for sales performance analysis"""

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.llm_service = LLMService(db, settings)

    async def analyze_sales(self, request: AnalyzeSalesRequest) -> AnalyzeSalesResponse:
        """Analyze sales performance with AI-powered insights"""
        try:
            logger.info(f"Analyzing {len(request.sales_reps)} reps with {len(request.opportunities)} opportunities")

            # Score sales reps
            rep_scores = []
            if request.include_rep_scoring:
                for rep in request.sales_reps:
                    rep_opps = [o for o in request.opportunities if o.sales_rep_id == rep.rep_id]
                    score = self._score_sales_rep(rep, rep_opps, request.period_start, request.period_end)
                    rep_scores.append(score)

            # Predict opportunity outcomes
            opp_predictions = []
            if request.include_win_probability:
                for opp in request.opportunities:
                    if opp.stage not in [OpportunityStage.CLOSED_WON, OpportunityStage.CLOSED_LOST]:
                        pred = self._predict_opportunity_outcome(opp)
                        opp_predictions.append(pred)

            # Calculate pipeline health
            pipeline = self._calculate_pipeline_health(request.opportunities)

            # Calculate period summary
            period_summary = self._calculate_period_summary(request.opportunities, request.sales_reps)

            # Generate AI insights
            ai_insights = await self._generate_ai_insights(rep_scores, pipeline, period_summary)

            # Generate strategic recommendations
            strategic_recs = self._generate_strategic_recommendations(rep_scores, pipeline)

            return AnalyzeSalesResponse(
                success=True,
                rep_scores=rep_scores,
                opportunity_predictions=opp_predictions,
                pipeline_health=pipeline,
                period_summary=period_summary,
                ai_insights=ai_insights,
                strategic_recommendations=strategic_recs
            )

        except Exception as e:
            logger.error(f"Error analyzing sales: {e}", exc_info=True)
            raise

    def _score_sales_rep(
        self, rep: SalesRepData, opportunities: List[OpportunityData],
        period_start: datetime, period_end: datetime
    ) -> RepPerformanceScore:
        """Score individual sales rep performance"""
        # Calculate metrics
        closed_won = [o for o in opportunities if o.stage == OpportunityStage.CLOSED_WON]
        closed_lost = [o for o in opportunities if o.stage == OpportunityStage.CLOSED_LOST]
        total_closed = len(closed_won) + len(closed_lost)

        total_revenue = sum(o.value for o in closed_won)
        deals_closed = len(closed_won)
        win_rate = (deals_closed / total_closed * 100) if total_closed > 0 else 0.0
        average_deal_size = (total_revenue / deals_closed) if deals_closed > 0 else 0.0
        pipeline_value = sum(o.value for o in opportunities if o.stage not in [OpportunityStage.CLOSED_WON, OpportunityStage.CLOSED_LOST])
        quota_attainment = (total_revenue / rep.quota * 100) if rep.quota > 0 else 0.0

        # Calculate performance score (0-100)
        score = 50.0  # Base score

        # Quota attainment impact (0-30 points)
        if quota_attainment >= 100:
            score += 30
        elif quota_attainment >= 80:
            score += 20
        elif quota_attainment >= 60:
            score += 10

        # Win rate impact (0-25 points)
        if win_rate >= 50:
            score += 25
        elif win_rate >= 40:
            score += 20
        elif win_rate >= 30:
            score += 15
        elif win_rate >= 20:
            score += 10

        # Deals closed impact (0-15 points)
        if deals_closed >= 10:
            score += 15
        elif deals_closed >= 5:
            score += 10
        elif deals_closed >= 3:
            score += 5

        # Pipeline health impact (0-10 points)
        if pipeline_value > rep.quota:
            score += 10
        elif pipeline_value > rep.quota * 0.5:
            score += 5

        performance_score = max(0.0, min(100.0, score))

        # Determine performance tier
        if performance_score >= 85:
            tier = PerformanceTier.TOP_PERFORMER
        elif performance_score >= 70:
            tier = PerformanceTier.ABOVE_AVERAGE
        elif performance_score >= 50:
            tier = PerformanceTier.AVERAGE
        elif performance_score >= 35:
            tier = PerformanceTier.BELOW_AVERAGE
        else:
            tier = PerformanceTier.NEEDS_IMPROVEMENT

        # Identify strengths and improvement areas
        strengths = []
        improvements = []

        if win_rate >= 40:
            strengths.append(f"High win rate ({win_rate:.1f}%)")
        elif win_rate < 25:
            improvements.append(f"Low win rate ({win_rate:.1f}%) - improve qualification")

        if quota_attainment >= 100:
            strengths.append(f"Exceeded quota ({quota_attainment:.1f}%)")
        elif quota_attainment < 70:
            improvements.append(f"Below quota ({quota_attainment:.1f}%) - increase activity")

        if average_deal_size > 50000:
            strengths.append("Strong average deal size")

        if pipeline_value > rep.quota:
            strengths.append("Healthy pipeline coverage")
        elif pipeline_value < rep.quota * 0.5:
            improvements.append("Insufficient pipeline - increase prospecting")

        return RepPerformanceScore(
            rep_id=rep.rep_id,
            rep_name=rep.rep_name,
            performance_score=round(performance_score, 2),
            performance_tier=tier,
            total_revenue=round(total_revenue, 2),
            deals_closed=deals_closed,
            win_rate=round(win_rate, 2),
            average_deal_size=round(average_deal_size, 2),
            pipeline_value=round(pipeline_value, 2),
            quota_attainment=round(quota_attainment, 2),
            key_strengths=strengths[:3],
            improvement_areas=improvements[:3]
        )

    def _predict_opportunity_outcome(self, opp: OpportunityData) -> OpportunityPrediction:
        """Predict opportunity win probability and close date"""
        # Base win probability from opportunity data
        win_prob = opp.probability

        # Adjust based on stage
        stage_factors = {
            OpportunityStage.PROSPECTING: 0.7,
            OpportunityStage.QUALIFICATION: 0.85,
            OpportunityStage.PROPOSAL: 1.0,
            OpportunityStage.NEGOTIATION: 1.15,
        }
        win_prob *= stage_factors.get(opp.stage, 1.0)

        # Adjust based on deal age
        days_open = (datetime.now() - opp.created_date).days
        if days_open > 180:
            win_prob *= 0.7  # Old deals less likely to close
        elif days_open < 30:
            win_prob *= 0.85  # Very new deals uncertain

        # Adjust based on time to expected close
        days_to_close = (opp.expected_close_date - datetime.now()).days
        if days_to_close < 0:
            win_prob *= 0.5  # Overdue deals at risk
        elif days_to_close > 90:
            win_prob *= 0.9  # Far out deals less certain

        win_prob = max(0.0, min(100.0, win_prob))

        # Predict close date
        if opp.stage == OpportunityStage.NEGOTIATION:
            predicted_close = datetime.now() + timedelta(days=15)
        elif opp.stage == OpportunityStage.PROPOSAL:
            predicted_close = datetime.now() + timedelta(days=30)
        else:
            predicted_close = opp.expected_close_date

        # Identify risk and success factors
        risk_factors = []
        success_factors = []

        if days_open > 180:
            risk_factors.append("Deal has been open for over 6 months")
        if days_to_close < 0:
            risk_factors.append("Expected close date has passed")
        if opp.value > 100000:
            risk_factors.append("Large deal size requires additional scrutiny")

        if opp.stage == OpportunityStage.NEGOTIATION:
            success_factors.append("In negotiation stage - close to closing")
        if opp.probability >= 70:
            success_factors.append("High probability assigned by sales rep")

        # Generate recommendations
        recommendations = []
        if days_to_close < 14:
            recommendations.append("Urgent: Close date approaching - schedule executive review")
        if win_prob < 50:
            recommendations.append("Low win probability - consider re-qualification or disqualification")
        if days_open > 90 and opp.stage == OpportunityStage.PROSPECTING:
            recommendations.append("Long sales cycle - accelerate qualification process")

        return OpportunityPrediction(
            opportunity_id=opp.opportunity_id,
            win_probability=round(win_prob, 2),
            predicted_close_date=predicted_close,
            risk_factors=risk_factors[:5],
            success_factors=success_factors[:5],
            recommended_actions=recommendations[:5]
        )

    def _calculate_pipeline_health(self, opportunities: List[OpportunityData]) -> PipelineHealth:
        """Calculate overall pipeline health metrics"""
        # Filter to open opportunities
        open_opps = [o for o in opportunities if o.stage not in [OpportunityStage.CLOSED_WON, OpportunityStage.CLOSED_LOST]]

        total_value = sum(o.value for o in open_opps)
        weighted_value = sum(o.value * (o.probability / 100) for o in open_opps)

        # Stage distribution
        stage_dist = {}
        for opp in open_opps:
            stage = opp.stage.value
            stage_dist[stage] = stage_dist.get(stage, 0) + 1

        # Average deal size
        avg_deal_size = (total_value / len(open_opps)) if open_opps else 0.0

        # Conversion rate (closed won / total closed)
        closed_won = len([o for o in opportunities if o.stage == OpportunityStage.CLOSED_WON])
        closed_lost = len([o for o in opportunities if o.stage == OpportunityStage.CLOSED_LOST])
        total_closed = closed_won + closed_lost
        conversion_rate = (closed_won / total_closed * 100) if total_closed > 0 else 0.0

        # Health score (0-100)
        health_score = 50.0

        if weighted_value > 500000:
            health_score += 20
        elif weighted_value > 250000:
            health_score += 10

        if conversion_rate >= 40:
            health_score += 20
        elif conversion_rate >= 30:
            health_score += 15
        elif conversion_rate >= 20:
            health_score += 10

        if len(open_opps) >= 20:
            health_score += 10

        health_score = max(0.0, min(100.0, health_score))

        # Identify bottleneck stages
        bottlenecks = []
        if stage_dist.get("prospecting", 0) > len(open_opps) * 0.4:
            bottlenecks.append("Prospecting - too many early-stage deals")
        if stage_dist.get("negotiation", 0) < len(open_opps) * 0.1:
            bottlenecks.append("Negotiation - not enough deals in final stage")

        return PipelineHealth(
            total_value=round(total_value, 2),
            weighted_value=round(weighted_value, 2),
            stage_distribution=stage_dist,
            average_deal_size=round(avg_deal_size, 2),
            conversion_rate=round(conversion_rate, 2),
            health_score=round(health_score, 2),
            bottleneck_stages=bottlenecks
        )

    def _calculate_period_summary(
        self, opportunities: List[OpportunityData], reps: List[SalesRepData]
    ) -> Dict[str, float]:
        """Calculate summary metrics for the period"""
        closed_won = [o for o in opportunities if o.stage == OpportunityStage.CLOSED_WON]

        total_revenue = sum(o.value for o in closed_won)
        total_deals = len(closed_won)
        avg_deal_size = (total_revenue / total_deals) if total_deals > 0 else 0.0
        total_quota = sum(r.quota for r in reps)
        quota_attainment = (total_revenue / total_quota * 100) if total_quota > 0 else 0.0

        return {
            "total_revenue": round(total_revenue, 2),
            "total_deals_closed": float(total_deals),
            "average_deal_size": round(avg_deal_size, 2),
            "team_quota_attainment": round(quota_attainment, 2),
            "total_reps": float(len(reps))
        }

    async def _generate_ai_insights(
        self, rep_scores: List[RepPerformanceScore],
        pipeline: PipelineHealth, period_summary: Dict[str, float]
    ) -> str:
        """Generate AI-powered insights using LLM"""
        try:
            top_performers = len([r for r in rep_scores if r.performance_tier == PerformanceTier.TOP_PERFORMER])
            avg_score = sum(r.performance_score for r in rep_scores) / len(rep_scores) if rep_scores else 0

            prompt = f"""Analyze this sales team performance:

Team Size: {len(rep_scores)} reps
Top Performers: {top_performers}
Average Performance Score: {avg_score:.1f}
Total Revenue: ${period_summary.get('total_revenue', 0):,.0f}
Quota Attainment: {period_summary.get('team_quota_attainment', 0):.1f}%
Pipeline Health: {pipeline.health_score:.1f}/100
Conversion Rate: {pipeline.conversion_rate:.1f}%

Provide 2-3 sentences of expert insights on team performance, key opportunities, and coaching priorities."""

            response = await self.llm_service.generate_response(
                prompt=prompt, model="gpt-4o-mini", temperature=0.3
            )
            return response.strip()

        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return "Sales analysis complete. Focus on pipeline health and rep coaching for continued success."

    def _generate_strategic_recommendations(
        self, rep_scores: List[RepPerformanceScore], pipeline: PipelineHealth
    ) -> List[str]:
        """Generate strategic recommendations"""
        recs = []

        # Rep performance recommendations
        needs_improvement = len([r for r in rep_scores if r.performance_tier == PerformanceTier.NEEDS_IMPROVEMENT])
        if needs_improvement > 0:
            recs.append(f"{needs_improvement} reps need immediate coaching and performance improvement plans")

        below_avg = len([r for r in rep_scores if r.performance_tier in [PerformanceTier.BELOW_AVERAGE, PerformanceTier.NEEDS_IMPROVEMENT]])
        if below_avg > len(rep_scores) * 0.3:
            recs.append("Over 30% of team underperforming - review hiring, training, and enablement processes")

        # Pipeline recommendations
        if pipeline.health_score < 60:
            recs.append(f"Pipeline health score {pipeline.health_score:.0f}/100 - increase prospecting and deal velocity")

        if pipeline.conversion_rate < 25:
            recs.append(f"Low conversion rate ({pipeline.conversion_rate:.1f}%) - improve qualification and sales process")

        if pipeline.bottleneck_stages:
            recs.append(f"Pipeline bottlenecks identified: {', '.join(pipeline.bottleneck_stages)}")

        return recs[:5]

    async def search_performance(self, request: SearchPerformanceRequest) -> SearchPerformanceResponse:
        """Search historical performance data"""
        return SearchPerformanceResponse(
            success=True,
            records=[],
            total_count=0,
            summary_stats={"message": "Historical performance search - database integration pending"}
        )

    async def export_performance(self, request: ExportPerformanceRequest) -> ExportPerformanceResponse:
        """Export performance data"""
        return ExportPerformanceResponse(
            success=True,
            export_data={"message": "Performance export", "format": request.format},
            format=request.format,
            record_count=0
        )

    async def get_stats(self) -> PerformanceStatsResponse:
        """Get sales performance statistics"""
        return PerformanceStatsResponse(
            success=True,
            total_reps_analyzed=0,
            total_opportunities=0,
            average_win_rate=0.0,
            average_deal_size=0.0,
            top_performers_count=0,
            total_pipeline_value=0.0,
            quarter_over_quarter_growth=0.0
        )

    async def get_status(self) -> StatusResponse:
        """Get service status"""
        return StatusResponse(
            success=True,
            status="operational",
            capabilities=[
                "Sales Rep Performance Scoring",
                "Opportunity Win Probability Prediction",
                "Pipeline Health Analysis",
                "Conversion Rate Tracking",
                "Quota Attainment Monitoring",
                "AI-Powered Sales Insights",
                "Strategic Coaching Recommendations"
            ]
        )
