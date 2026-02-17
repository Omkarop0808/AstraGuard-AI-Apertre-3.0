"""
Real-time Monitoring Dashboard
Provides comprehensive monitoring data for visualization
"""
from typing import Dict, Any, List
from . import metrics, analytics


def get_dashboard_data() -> Dict[str, Any]:
    """
    Get comprehensive dashboard data including:
    - Performance metrics
    - Usage analytics
    - SLA status
    - Top endpoints and users
    """
    
    # Get all metrics
    all_metrics = metrics.get_metrics()
    
    # Get SLA status
    sla_status = metrics.get_sla_status()
    
    # Get analytics
    all_analytics = analytics.get_analytics()
    top_endpoints = analytics.get_top_endpoints(10)
    top_users = analytics.get_top_users(10)
    
    return {
        "performance": {
            "uptime_seconds": all_metrics.get("uptime_seconds", 0),
            "total_requests": all_metrics.get("total_requests", 0),
            "total_errors": all_metrics.get("total_errors", 0),
            "overall_error_rate": all_metrics.get("overall_error_rate", 0),
            "requests_per_second": all_metrics.get("requests_per_second", 0),
        },
        "sla": sla_status,
        "endpoints": all_metrics.get("endpoints", {}),
        "usage": {
            "total_users": all_analytics.get("total_users", 0),
            "anonymous_requests": all_analytics.get("anonymous_requests", 0),
            "top_endpoints": top_endpoints,
            "top_users": top_users,
        },
        "alerts": generate_alerts(all_metrics, sla_status),
    }


def generate_alerts(metrics_data: Dict[str, Any], sla_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate alerts based on metrics and SLA thresholds
    """
    alerts = []
    
    # Check error rate
    error_rate = metrics_data.get("overall_error_rate", 0)
    if error_rate > 0.001:  # 0.1% threshold
        alerts.append({
            "severity": "high",
            "type": "error_rate",
            "message": f"Error rate ({error_rate:.2%}) exceeds threshold (0.1%)",
            "value": error_rate,
            "threshold": 0.001,
        })
    
    # Check P95 latency
    if not sla_data.get("p95_met", True):
        p95_latency = sla_data.get("p95_latency_ms", 0)
        alerts.append({
            "severity": "medium",
            "type": "latency",
            "message": f"P95 latency ({p95_latency:.2f}ms) exceeds threshold (100ms)",
            "value": p95_latency,
            "threshold": 100,
        })
    
    # Check SLA compliance
    if not sla_data.get("overall_sla_met", True):
        alerts.append({
            "severity": "high",
            "type": "sla",
            "message": "Overall SLA not met",
            "details": sla_data,
        })
    
    # Check individual endpoint error rates
    for endpoint, endpoint_metrics in metrics_data.get("endpoints", {}).items():
        endpoint_error_rate = endpoint_metrics.get("error_rate", 0)
        if endpoint_error_rate > 0.01:  # 1% threshold for individual endpoints
            alerts.append({
                "severity": "medium",
                "type": "endpoint_error_rate",
                "message": f"Endpoint {endpoint} error rate ({endpoint_error_rate:.2%}) is high",
                "endpoint": endpoint,
                "value": endpoint_error_rate,
                "threshold": 0.01,
            })
    
    return alerts


def get_endpoint_details(endpoint: str) -> Dict[str, Any]:
    """Get detailed metrics and analytics for a specific endpoint"""
    endpoint_metrics = metrics.get_endpoint_metrics(endpoint)
    endpoint_analytics = analytics.get_endpoint_analytics(endpoint)
    
    return {
        "endpoint": endpoint,
        "metrics": endpoint_metrics,
        "analytics": endpoint_analytics,
    }


def get_user_details(user_id: str) -> Dict[str, Any]:
    """Get detailed analytics for a specific user"""
    user_analytics = analytics.get_user_analytics(user_id)
    
    return {
        "user_id": user_id,
        "analytics": user_analytics,
    }
