"""
Usage Analytics by Endpoint and User
Tracks API usage patterns and user behavior
"""
import time
from typing import Dict, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from fastapi import Request


@dataclass
class UserAnalytics:
    """Analytics for a single user"""
    request_count: int = 0
    endpoints_used: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    error_count: int = 0
    
    def record_request(self, endpoint: str, status_code: int):
        """Record a request"""
        self.request_count += 1
        self.endpoints_used[endpoint] += 1
        self.last_seen = time.time()
        if status_code >= 400:
            self.error_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "request_count": self.request_count,
            "endpoints_used": dict(self.endpoints_used),
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0.0,
        }


@dataclass
class EndpointAnalytics:
    """Analytics for a single endpoint"""
    request_count: int = 0
    unique_users: set = field(default_factory=set)
    methods_used: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    hourly_requests: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    
    def record_request(self, user_id: Optional[str], method: str):
        """Record a request"""
        self.request_count += 1
        if user_id:
            self.unique_users.add(user_id)
        self.methods_used[method] += 1
        
        # Track hourly usage
        hour = int(time.time() // 3600)
        self.hourly_requests[hour] += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "request_count": self.request_count,
            "unique_users": len(self.unique_users),
            "methods_used": dict(self.methods_used),
            "hourly_requests": dict(self.hourly_requests),
        }


class AnalyticsCollector:
    """Collects and stores usage analytics"""
    
    def __init__(self):
        self.users: Dict[str, UserAnalytics] = defaultdict(UserAnalytics)
        self.endpoints: Dict[str, EndpointAnalytics] = defaultdict(EndpointAnalytics)
        self.anonymous_requests = 0
        
    def record_request(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str],
        status_code: int
    ):
        """Record a request"""
        # Record user analytics
        if user_id:
            self.users[user_id].record_request(endpoint, status_code)
        else:
            self.anonymous_requests += 1
        
        # Record endpoint analytics
        self.endpoints[endpoint].record_request(user_id, method)
    
    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics for a specific user"""
        if user_id in self.users:
            return self.users[user_id].to_dict()
        return {}
    
    def get_endpoint_analytics(self, endpoint: str) -> Dict[str, Any]:
        """Get analytics for a specific endpoint"""
        if endpoint in self.endpoints:
            return self.endpoints[endpoint].to_dict()
        return {}
    
    def get_all_analytics(self) -> Dict[str, Any]:
        """Get all analytics"""
        return {
            "total_users": len(self.users),
            "anonymous_requests": self.anonymous_requests,
            "users": {
                user_id: analytics.to_dict()
                for user_id, analytics in self.users.items()
            },
            "endpoints": {
                endpoint: analytics.to_dict()
                for endpoint, analytics in self.endpoints.items()
            }
        }
    
    def get_top_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top endpoints by request count"""
        sorted_endpoints = sorted(
            self.endpoints.items(),
            key=lambda x: x[1].request_count,
            reverse=True
        )
        
        return [
            {
                "endpoint": endpoint,
                **analytics.to_dict()
            }
            for endpoint, analytics in sorted_endpoints[:limit]
        ]
    
    def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by request count"""
        sorted_users = sorted(
            self.users.items(),
            key=lambda x: x[1].request_count,
            reverse=True
        )
        
        return [
            {
                "user_id": user_id,
                **analytics.to_dict()
            }
            for user_id, analytics in sorted_users[:limit]
        ]


# Global analytics collector instance
analytics_collector = AnalyticsCollector()


def record_request(
    request: Request,
    status_code: int,
    user_id: Optional[str] = None
):
    """Record a request for analytics"""
    endpoint = request.url.path
    method = request.method
    analytics_collector.record_request(endpoint, method, user_id, status_code)


def get_analytics() -> Dict[str, Any]:
    """Get all analytics"""
    return analytics_collector.get_all_analytics()


def get_user_analytics(user_id: str) -> Dict[str, Any]:
    """Get analytics for a specific user"""
    return analytics_collector.get_user_analytics(user_id)


def get_endpoint_analytics(endpoint: str) -> Dict[str, Any]:
    """Get analytics for a specific endpoint"""
    return analytics_collector.get_endpoint_analytics(endpoint)


def get_top_endpoints(limit: int = 10) -> List[Dict[str, Any]]:
    """Get top endpoints by request count"""
    return analytics_collector.get_top_endpoints(limit)


def get_top_users(limit: int = 10) -> List[Dict[str, Any]]:
    """Get top users by request count"""
    return analytics_collector.get_top_users(limit)
