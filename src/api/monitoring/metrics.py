"""
Performance Metrics Collection
Tracks latency, throughput, error rates, and other performance metrics
"""
import time
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, field
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
import statistics


@dataclass
class EndpointMetrics:
    """Metrics for a single endpoint"""
    request_count: int = 0
    error_count: int = 0
    latencies: deque = field(default_factory=lambda: deque(maxlen=1000))  # Keep last 1000
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    
    def add_request(self, latency_ms: float, status_code: int):
        """Record a request"""
        self.request_count += 1
        self.latencies.append(latency_ms)
        self.status_codes[status_code] += 1
        if status_code >= 400:
            self.error_count += 1
    
    def get_percentile(self, percentile: float) -> float:
        """Calculate latency percentile"""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * percentile / 100)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]
    
    def get_error_rate(self) -> float:
        """Calculate error rate"""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count
    
    def get_avg_latency(self) -> float:
        """Calculate average latency"""
        if not self.latencies:
            return 0.0
        return statistics.mean(self.latencies)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.get_error_rate(),
            "latency": {
                "avg_ms": self.get_avg_latency(),
                "p50_ms": self.get_percentile(50),
                "p95_ms": self.get_percentile(95),
                "p99_ms": self.get_percentile(99),
            },
            "status_codes": dict(self.status_codes),
        }


class MetricsCollector:
    """Collects and stores performance metrics"""
    
    def __init__(self):
        self.endpoints: Dict[str, EndpointMetrics] = defaultdict(EndpointMetrics)
        self.start_time = time.time()
        self.total_requests = 0
        self.total_errors = 0
        
    def record_request(self, endpoint: str, latency_ms: float, status_code: int):
        """Record a request"""
        self.endpoints[endpoint].add_request(latency_ms, status_code)
        self.total_requests += 1
        if status_code >= 400:
            self.total_errors += 1
    
    def get_endpoint_metrics(self, endpoint: str) -> Dict[str, Any]:
        """Get metrics for a specific endpoint"""
        if endpoint in self.endpoints:
            return self.endpoints[endpoint].to_dict()
        return {}
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        uptime_seconds = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime_seconds,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "overall_error_rate": self.total_errors / self.total_requests if self.total_requests > 0 else 0.0,
            "requests_per_second": self.total_requests / uptime_seconds if uptime_seconds > 0 else 0.0,
            "endpoints": {
                endpoint: metrics.to_dict()
                for endpoint, metrics in self.endpoints.items()
            }
        }
    
    def get_sla_status(self) -> Dict[str, Any]:
        """Get SLA compliance status"""
        uptime_seconds = time.time() - self.start_time
        uptime_percentage = 1.0  # Simplified - in production, track actual downtime
        
        # Calculate overall metrics
        all_latencies = []
        for metrics in self.endpoints.values():
            all_latencies.extend(metrics.latencies)
        
        p95_latency = 0.0
        if all_latencies:
            sorted_latencies = sorted(all_latencies)
            index = int(len(sorted_latencies) * 0.95)
            p95_latency = sorted_latencies[min(index, len(sorted_latencies) - 1)]
        
        overall_error_rate = self.total_errors / self.total_requests if self.total_requests > 0 else 0.0
        
        return {
            "uptime_percentage": uptime_percentage,
            "uptime_target": 0.999,  # 99.9%
            "uptime_met": uptime_percentage >= 0.999,
            "p95_latency_ms": p95_latency,
            "p95_target_ms": 100,
            "p95_met": p95_latency < 100,
            "error_rate": overall_error_rate,
            "error_rate_target": 0.001,  # 0.1%
            "error_rate_met": overall_error_rate < 0.001,
            "overall_sla_met": (
                uptime_percentage >= 0.999 and
                p95_latency < 100 and
                overall_error_rate < 0.001
            )
        }


# Global metrics collector instance
metrics_collector = MetricsCollector()


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware that collects performance metrics for all requests
    """
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Record start time
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            endpoint = f"{request.method} {request.url.path}"
            metrics_collector.record_request(endpoint, latency_ms, response.status_code)
            
            # Add performance headers
            response.headers["X-Response-Time-Ms"] = f"{latency_ms:.2f}"
            
            return response
            
        except Exception as e:
            # Record error
            latency_ms = (time.time() - start_time) * 1000
            endpoint = f"{request.method} {request.url.path}"
            metrics_collector.record_request(endpoint, latency_ms, 500)
            raise


def get_metrics() -> Dict[str, Any]:
    """Get all collected metrics"""
    return metrics_collector.get_all_metrics()


def get_endpoint_metrics(endpoint: str) -> Dict[str, Any]:
    """Get metrics for a specific endpoint"""
    return metrics_collector.get_endpoint_metrics(endpoint)


def get_sla_status() -> Dict[str, Any]:
    """Get SLA compliance status"""
    return metrics_collector.get_sla_status()
