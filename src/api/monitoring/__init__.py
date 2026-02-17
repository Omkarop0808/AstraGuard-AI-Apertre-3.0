# API Monitoring and Observability
# Configuration constants

# Metrics collection intervals
METRICS_COLLECTION_INTERVAL = 60  # seconds
METRICS_RETENTION_PERIOD = 86400  # 24 hours

# Performance thresholds
LATENCY_P50_THRESHOLD_MS = 50
LATENCY_P95_THRESHOLD_MS = 100
LATENCY_P99_THRESHOLD_MS = 200
ERROR_RATE_THRESHOLD = 0.001  # 0.1%
SLA_UPTIME_TARGET = 0.999  # 99.9%

# Tracing configuration
TRACE_SAMPLE_RATE = 1.0  # 100% sampling
TRACE_ID_HEADER = "X-Trace-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"
