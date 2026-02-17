"""
Distributed Tracing for API Calls
Provides end-to-end request tracing across services
"""
import uuid
import time
from typing import Dict, Any, Optional, List
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from . import TRACE_ID_HEADER, TRACE_SAMPLE_RATE
import logging

logger = logging.getLogger(__name__)


class Span:
    """Represents a single span in a trace"""
    
    def __init__(self, trace_id: str, span_id: str, parent_span_id: Optional[str], operation: str):
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.operation = operation
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.tags: Dict[str, Any] = {}
        self.logs: List[Dict[str, Any]] = []
        
    def finish(self):
        """Mark span as finished"""
        self.end_time = time.time()
        
    def set_tag(self, key: str, value: Any):
        """Add a tag to the span"""
        self.tags[key] = value
        
    def log(self, message: str, **kwargs):
        """Add a log entry to the span"""
        self.logs.append({
            "timestamp": time.time(),
            "message": message,
            **kwargs
        })
        
    def duration_ms(self) -> float:
        """Get span duration in milliseconds"""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return (time.time() - self.start_time) * 1000
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary"""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "operation": self.operation,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms(),
            "tags": self.tags,
            "logs": self.logs,
        }


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds distributed tracing to all requests
    """
    
    def __init__(self, app, sample_rate: float = TRACE_SAMPLE_RATE):
        super().__init__(app)
        self.sample_rate = sample_rate
        self.traces: Dict[str, List[Span]] = {}  # In-memory storage (use Redis in production)
        
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate or extract trace ID
        trace_id = request.headers.get(TRACE_ID_HEADER) or str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        parent_span_id = request.headers.get("X-Parent-Span-ID")
        
        # Create span
        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation=f"{request.method} {request.url.path}"
        )
        
        # Add tags
        span.set_tag("http.method", request.method)
        span.set_tag("http.url", str(request.url))
        span.set_tag("http.path", request.url.path)
        if request.client:
            span.set_tag("http.client_ip", request.client.host)
        
        # Store span in request state
        request.state.trace_id = trace_id
        request.state.span = span
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add response tags
            span.set_tag("http.status_code", response.status_code)
            span.set_tag("success", 200 <= response.status_code < 400)
            
            # Finish span
            span.finish()
            
            # Store trace
            if trace_id not in self.traces:
                self.traces[trace_id] = []
            self.traces[trace_id].append(span)
            
            # Add trace headers to response
            response.headers[TRACE_ID_HEADER] = trace_id
            response.headers["X-Span-ID"] = span_id
            
            return response
            
        except Exception as e:
            # Log error in span
            span.log("error", error=str(e), error_type=type(e).__name__)
            span.set_tag("error", True)
            span.set_tag("error.message", str(e))
            span.finish()
            
            # Store trace
            if trace_id not in self.traces:
                self.traces[trace_id] = []
            self.traces[trace_id].append(span)
            
            raise
    
    def get_trace(self, trace_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get all spans for a trace"""
        if trace_id in self.traces:
            return [span.to_dict() for span in self.traces[trace_id]]
        return None
    
    def get_all_traces(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all traces"""
        return {
            trace_id: [span.to_dict() for span in spans]
            for trace_id, spans in self.traces.items()
        }


def get_current_span(request: Request) -> Optional[Span]:
    """Get current span from request state"""
    return getattr(request.state, "span", None)


def get_trace_id(request: Request) -> Optional[str]:
    """Get trace ID from request state"""
    return getattr(request.state, "trace_id", None)
