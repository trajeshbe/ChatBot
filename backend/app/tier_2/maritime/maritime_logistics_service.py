"""
Maritime Logistics Optimizer - Business Logic Service
AI-powered maritime logistics optimization with route planning, port scheduling, and cargo management.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import math
import uuid

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .maritime_logistics_schemas import (
    OptimizeRouteRequest,
    OptimizeRouteResponse,
    OptimizedRoute,
    RouteSegment,
    PortSchedule,
    CargoLoadingPlan,
    SearchRoutesRequest,
    SearchRoutesResponse,
    RouteRecord,
    ExportRoutesRequest,
    ExportRoutesResponse,
    MaritimeStatsResponse,
    StatusResponse,
    VesselType,
    RouteOptimizationGoal,
    WeatherCondition,
    Port,
)

logger = logging.getLogger(__name__)


class MaritimeLogisticsService:
    """Service for maritime logistics optimization using AI"""

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.llm_service = LLMService(db, settings)

    async def optimize_route(
        self, request: OptimizeRouteRequest
    ) -> OptimizeRouteResponse:
        """
        Optimize maritime route with AI-powered analysis.

        Args:
            request: Route optimization parameters

        Returns:
            OptimizeRouteResponse with optimized route, schedule, and cargo plan
        """
        try:
            logger.info(
                f"Optimizing route from {request.origin_port.name} to {request.destination_port.name} "
                f"for vessel {request.vessel.name} with {len(request.cargo)} cargo items"
            )

            # Calculate route segments
            route_segments = self._calculate_route_segments(request)

            # Calculate port schedule
            port_schedule = self._calculate_port_schedule(request, route_segments)

            # Generate cargo loading plan
            cargo_loading_plan = self._generate_cargo_loading_plan(request)

            # Calculate vessel performance metrics
            vessel_metrics = self._calculate_vessel_metrics(
                request, route_segments, port_schedule
            )

            # Build optimized route
            optimized_route = self._build_optimized_route(
                request, route_segments, vessel_metrics
            )

            # Generate AI insights using LLM
            ai_insights = await self._generate_ai_insights(
                request, optimized_route, vessel_metrics
            )

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                request, optimized_route, vessel_metrics
            )

            # Generate alternative routes
            alternative_routes = self._generate_alternative_routes(
                request, route_segments
            )

            return OptimizeRouteResponse(
                success=True,
                optimized_route=optimized_route,
                port_schedule=port_schedule,
                cargo_loading_plan=cargo_loading_plan,
                vessel_performance_metrics=vessel_metrics,
                ai_insights=ai_insights,
                recommendations=recommendations,
                alternative_routes=alternative_routes,
            )

        except Exception as e:
            logger.error(f"Error optimizing route: {e}", exc_info=True)
            raise

    def _calculate_route_segments(
        self, request: OptimizeRouteRequest
    ) -> List[RouteSegment]:
        """Calculate route segments based on optimization goal"""
        segments = []

        # Build port sequence based on optimization goal
        ports = [request.origin_port] + request.intermediate_ports + [request.destination_port]

        for i in range(len(ports) - 1):
            from_port = ports[i]
            to_port = ports[i + 1]

            # Calculate distance using Haversine formula
            distance_nm = self._calculate_distance_nautical_miles(
                from_port.location, to_port.location
            )

            # Estimate duration based on vessel speed
            duration_hours = distance_nm / request.vessel.speed_knots

            # Adjust for weather if enabled
            weather_condition = WeatherCondition.MODERATE
            if request.consider_weather:
                weather_condition = self._assess_weather_condition(
                    from_port.location, to_port.location
                )
                if weather_condition in [WeatherCondition.ROUGH, WeatherCondition.SEVERE]:
                    duration_hours *= 1.2  # 20% slower in rough weather
                elif weather_condition == WeatherCondition.STORM:
                    duration_hours *= 1.5  # 50% slower in storm

            # Calculate fuel cost
            fuel_cost = (
                duration_hours * request.vessel.fuel_consumption_rate * 500  # $500/ton average
            )

            # Apply optimization goal adjustments
            if request.optimization_goal == RouteOptimizationGoal.MINIMIZE_FUEL:
                # Slower speed = better fuel efficiency
                duration_hours *= 1.15
                fuel_cost *= 0.85
            elif request.optimization_goal == RouteOptimizationGoal.MINIMIZE_TIME:
                # Faster speed = more fuel
                duration_hours *= 0.9
                fuel_cost *= 1.15

            segment = RouteSegment(
                from_port=from_port,
                to_port=to_port,
                distance_nautical_miles=distance_nm,
                estimated_duration_hours=duration_hours,
                fuel_cost_usd=fuel_cost,
                weather_condition=weather_condition,
            )
            segments.append(segment)

        return segments

    def _calculate_distance_nautical_miles(
        self, loc1: Dict[str, float], loc2: Dict[str, float]
    ) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        lat1 = math.radians(loc1["lat"])
        lon1 = math.radians(loc1["lon"])
        lat2 = math.radians(loc2["lat"])
        lon2 = math.radians(loc2["lon"])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        # Earth radius in nautical miles
        radius_nm = 3440.065

        return radius_nm * c

    def _assess_weather_condition(
        self, loc1: Dict[str, float], loc2: Dict[str, float]
    ) -> WeatherCondition:
        """Assess weather condition for route segment (simplified simulation)"""
        # In production, integrate with weather API
        # For now, use location-based heuristics
        avg_lat = (loc1["lat"] + loc2["lat"]) / 2

        if abs(avg_lat) > 60:  # High latitudes
            return WeatherCondition.ROUGH
        elif abs(avg_lat) > 45:
            return WeatherCondition.MODERATE
        else:
            return WeatherCondition.CLEAR

    def _calculate_port_schedule(
        self, request: OptimizeRouteRequest, segments: List[RouteSegment]
    ) -> List[PortSchedule]:
        """Calculate port arrival/departure schedule"""
        schedule = []
        current_time = request.departure_time or datetime.now()

        # Origin port
        all_ports = [request.origin_port] + request.intermediate_ports + [request.destination_port]

        for i, port in enumerate(all_ports):
            if i > 0:
                # Add sailing time from previous segment
                current_time += timedelta(hours=segments[i - 1].estimated_duration_hours)

            arrival_time = current_time

            # Estimate handling operations based on cargo
            handling_ops = self._determine_handling_operations(request.cargo, port)
            handling_hours = len(handling_ops) * 2  # 2 hours per operation average

            departure_time = arrival_time + timedelta(hours=handling_hours)

            # Calculate port fees
            port_cost = (
                port.handling_cost_per_hour * handling_hours
                + (port.average_wait_time_hours or 0) * 100  # Wait time penalty
            )

            schedule.append(
                PortSchedule(
                    port=port,
                    arrival_time=arrival_time,
                    departure_time=departure_time,
                    berth_number=(i % port.berth_capacity) + 1,
                    handling_operations=handling_ops,
                    estimated_cost_usd=port_cost,
                )
            )

            current_time = departure_time

        return schedule

    def _determine_handling_operations(self, cargo: List, port: Port) -> List[str]:
        """Determine cargo handling operations at port"""
        ops = []
        for cargo_item in cargo:
            ops.append(f"Load/Unload {cargo_item.cargo_type.value}")
            if cargo_item.special_handling:
                ops.append(f"Special: {cargo_item.special_handling}")
        return list(set(ops))[:5]  # Limit to 5 unique operations

    def _generate_cargo_loading_plan(
        self, request: OptimizeRouteRequest
    ) -> List[CargoLoadingPlan]:
        """Generate optimal cargo loading plan"""
        # Sort cargo by priority and weight
        sorted_cargo = sorted(
            request.cargo, key=lambda x: (x.priority, x.weight_tons), reverse=True
        )

        loading_plan = []
        for idx, cargo_item in enumerate(sorted_cargo):
            # Heavier items at bottom, high priority accessible
            if cargo_item.weight_tons > 100:
                position = "Lower deck - Center"
                stability_impact = "High stability contribution"
            elif cargo_item.priority >= 8:
                position = "Upper deck - Forward"
                stability_impact = "Quick access for priority cargo"
            else:
                position = f"Mid deck - Bay {idx % 10}"
                stability_impact = "Balanced distribution"

            # Weight distribution score (simplified)
            weight_score = min(100.0, (cargo_item.weight_tons / 500) * 100)

            loading_plan.append(
                CargoLoadingPlan(
                    cargo_item=cargo_item,
                    position=position,
                    load_sequence=idx + 1,
                    weight_distribution_score=weight_score,
                    stability_impact=stability_impact,
                )
            )

        return loading_plan

    def _calculate_vessel_metrics(
        self,
        request: OptimizeRouteRequest,
        segments: List[RouteSegment],
        schedule: List[PortSchedule],
    ) -> Dict[str, Any]:
        """Calculate vessel performance metrics"""
        total_distance = sum(s.distance_nautical_miles for s in segments)
        total_fuel_cost = sum(s.fuel_cost_usd for s in segments)
        total_port_fees = sum(s.estimated_cost_usd for s in schedule)
        total_sailing_hours = sum(s.estimated_duration_hours for s in segments)
        total_port_hours = sum(
            (s.departure_time - s.arrival_time).total_seconds() / 3600 for s in schedule
        )

        return {
            "total_distance_nm": round(total_distance, 2),
            "total_fuel_cost_usd": round(total_fuel_cost, 2),
            "total_port_fees_usd": round(total_port_fees, 2),
            "total_cost_usd": round(total_fuel_cost + total_port_fees, 2),
            "total_sailing_hours": round(total_sailing_hours, 2),
            "total_port_hours": round(total_port_hours, 2),
            "total_duration_hours": round(total_sailing_hours + total_port_hours, 2),
            "average_speed_knots": round(total_distance / total_sailing_hours, 2)
            if total_sailing_hours > 0
            else 0,
            "fuel_efficiency_rating": self._calculate_fuel_efficiency_rating(
                total_fuel_cost, total_distance
            ),
        }

    def _calculate_fuel_efficiency_rating(
        self, fuel_cost: float, distance: float
    ) -> str:
        """Calculate fuel efficiency rating"""
        cost_per_nm = fuel_cost / distance if distance > 0 else 0

        if cost_per_nm < 50:
            return "Excellent"
        elif cost_per_nm < 100:
            return "Good"
        elif cost_per_nm < 150:
            return "Average"
        else:
            return "Needs Improvement"

    def _build_optimized_route(
        self, request: OptimizeRouteRequest, segments: List[RouteSegment], metrics: Dict[str, Any]
    ) -> OptimizedRoute:
        """Build optimized route object"""
        # Calculate estimated arrival
        departure = request.departure_time or datetime.now()
        arrival = departure + timedelta(hours=metrics["total_duration_hours"])

        # Calculate optimization score (0-100)
        optimization_score = self._calculate_optimization_score(request, metrics)

        # Assess weather risk
        weather_conditions = [s.weather_condition for s in segments]
        weather_risk = self._assess_weather_risk(weather_conditions)

        return OptimizedRoute(
            route_id=str(uuid.uuid4()),
            segments=segments,
            total_distance_nm=metrics["total_distance_nm"],
            total_duration_hours=metrics["total_duration_hours"],
            total_fuel_cost_usd=metrics["total_fuel_cost_usd"],
            total_port_fees_usd=metrics["total_port_fees_usd"],
            total_cost_usd=metrics["total_cost_usd"],
            estimated_arrival=arrival,
            optimization_score=optimization_score,
            weather_risk_level=weather_risk,
            fuel_efficiency_rating=metrics["fuel_efficiency_rating"],
        )

    def _calculate_optimization_score(
        self, request: OptimizeRouteRequest, metrics: Dict[str, Any]
    ) -> float:
        """Calculate optimization score based on goal"""
        # Baseline score
        score = 70.0

        if request.optimization_goal == RouteOptimizationGoal.MINIMIZE_COST:
            # Lower cost = higher score
            if metrics["total_cost_usd"] < 50000:
                score = 95.0
            elif metrics["total_cost_usd"] < 100000:
                score = 85.0
            else:
                score = 70.0
        elif request.optimization_goal == RouteOptimizationGoal.MINIMIZE_TIME:
            # Faster = higher score
            avg_speed = metrics["average_speed_knots"]
            if avg_speed > 20:
                score = 95.0
            elif avg_speed > 15:
                score = 85.0
        elif request.optimization_goal == RouteOptimizationGoal.MINIMIZE_FUEL:
            # Better fuel efficiency = higher score
            if metrics["fuel_efficiency_rating"] == "Excellent":
                score = 95.0
            elif metrics["fuel_efficiency_rating"] == "Good":
                score = 85.0

        # Bonus for balanced approach
        if request.optimization_goal == RouteOptimizationGoal.BALANCE_ALL:
            score = 80.0

        return round(score, 1)

    def _assess_weather_risk(self, conditions: List[WeatherCondition]) -> str:
        """Assess overall weather risk level"""
        if any(c == WeatherCondition.STORM for c in conditions):
            return "High Risk"
        elif any(c == WeatherCondition.SEVERE for c in conditions):
            return "Moderate-High Risk"
        elif any(c == WeatherCondition.ROUGH for c in conditions):
            return "Moderate Risk"
        else:
            return "Low Risk"

    async def _generate_ai_insights(
        self, request: OptimizeRouteRequest, route: OptimizedRoute, metrics: Dict[str, Any]
    ) -> str:
        """Generate AI-powered insights using LLM"""
        try:
            prompt = f"""You are a maritime logistics optimization expert. Analyze this route and provide insights.

Vessel: {request.vessel.name} ({request.vessel.vessel_type.value})
Route: {request.origin_port.name} → {request.destination_port.name}
Optimization Goal: {request.optimization_goal.value}

Metrics:
- Total Distance: {metrics['total_distance_nm']} nautical miles
- Total Duration: {metrics['total_duration_hours']} hours
- Total Cost: ${metrics['total_cost_usd']:,.2f}
- Fuel Efficiency: {metrics['fuel_efficiency_rating']}
- Weather Risk: {route.weather_risk_level}
- Optimization Score: {route.optimization_score}/100

Provide 3-4 sentences of expert insights about this route optimization, including strengths and potential concerns."""

            response = await self.llm_service.generate_response(
                prompt=prompt, model="gpt-4o-mini", temperature=0.3
            )

            return response.strip()

        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return "AI insights temporarily unavailable. Route optimization completed successfully."

    async def _generate_recommendations(
        self, request: OptimizeRouteRequest, route: OptimizedRoute, metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        # Weather-based recommendations
        if route.weather_risk_level in ["High Risk", "Moderate-High Risk"]:
            recommendations.append("Consider delaying departure by 24-48 hours for better weather conditions")

        # Cost optimization
        if metrics["total_cost_usd"] > 100000:
            recommendations.append("Explore consolidation opportunities to reduce per-unit shipping costs")

        # Speed optimization
        if metrics["average_speed_knots"] < 12:
            recommendations.append("Current speed is below optimal - consider route alternatives or vessel upgrade")

        # Fuel efficiency
        if metrics["fuel_efficiency_rating"] in ["Needs Improvement", "Average"]:
            recommendations.append("Implement slow steaming to improve fuel efficiency by 15-20%")

        # Port optimization
        if len(request.intermediate_ports) > 3:
            recommendations.append("Multiple port stops increase costs - evaluate necessity of each stop")

        return recommendations[:5]  # Limit to top 5

    def _generate_alternative_routes(
        self, request: OptimizeRouteRequest, base_segments: List[RouteSegment]
    ) -> List[OptimizedRoute]:
        """Generate alternative route options (simplified)"""
        # In production, this would explore different port combinations
        # For now, return empty list
        return []

    async def search_routes(self, request: SearchRoutesRequest) -> SearchRoutesResponse:
        """Search historical routes (placeholder for database integration)"""
        # Placeholder implementation
        return SearchRoutesResponse(
            success=True,
            routes=[],
            total_count=0,
            summary_stats={"message": "Historical route search - database integration pending"},
        )

    async def export_routes(self, request: ExportRoutesRequest) -> ExportRoutesResponse:
        """Export routes to various formats"""
        # Placeholder implementation
        export_data = {
            "message": "Route export functionality",
            "format": request.format,
            "routes": [],
        }

        return ExportRoutesResponse(
            success=True, export_data=export_data, format=request.format, record_count=0
        )

    async def get_stats(self) -> MaritimeStatsResponse:
        """Get maritime logistics statistics"""
        return MaritimeStatsResponse(
            success=True,
            total_routes_optimized=0,
            total_distance_traveled_nm=0.0,
            total_fuel_saved_usd=0.0,
            average_optimization_score=0.0,
            most_efficient_vessel_type="container",
            busiest_ports=[],
            weather_impact_stats={
                "message": "Statistics tracking - database integration pending"
            },
        )

    async def get_status(self) -> StatusResponse:
        """Get service status"""
        return StatusResponse(
            success=True,
            service_name="Maritime Logistics Optimizer",
            version="1.0.0",
            status="operational",
            capabilities=[
                "Route Optimization",
                "Port Scheduling",
                "Cargo Loading Plans",
                "Weather Impact Assessment",
                "Cost Optimization",
                "AI-Powered Insights",
            ],
        )
