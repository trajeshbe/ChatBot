"""
Comprehensive Audit Logging Middleware

Automatically logs all API requests with OpenTelemetry tracing and Prometheus metrics.
Integrates with existing observability stack (Grafana, Tempo, Loki).
"""

from typing import Callable, Optional, Dict, Any
import time
import logging
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI
import json

logger = logging.getLogger(__name__)

# Prometheus metrics
try:
    from prometheus_client import Counter, Histogram, Gauge

    # Request counters
    audit_requests_total = Counter(
        'audit_requests_total',
        'Total number of audited API requests',
        ['method', 'endpoint', 'status', 'user_role']
    )

    audit_user_actions = Counter(
        'audit_user_actions_total',
        'Total user actions by type',
        ['action_type', 'user_id', 'module']
    )

    # Latency histogram
    audit_request_duration_seconds = Histogram(
        'audit_request_duration_seconds',
        'Request duration in seconds',
        ['method', 'endpoint'],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
    )

    # Active users gauge
    audit_active_sessions = Gauge(
        'audit_active_sessions',
        'Number of active user sessions'
    )

    # Failed requests counter
    audit_failed_requests_total = Counter(
        'audit_failed_requests_total',
        'Total failed API requests',
        ['method', 'endpoint', 'error_type']
    )

    PROMETHEUS_AVAILABLE = True
    logger.info("Prometheus metrics initialized for audit middleware")
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus not available, metrics disabled")

# OpenTelemetry tracing
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    tracer = trace.get_tracer(__name__)
    OTEL_AVAILABLE = True
    logger.info("OpenTelemetry tracing initialized for audit middleware")
except ImportError:
    OTEL_AVAILABLE = False
    logger.warning("OpenTelemetry not available, tracing disabled")


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive audit logging of all API requests.

    Features:
    - Automatic logging of all HTTP requests
    - OpenTelemetry distributed tracing
    - Prometheus metrics collection
    - Structured logging for Grafana Loki
    - User action tracking
    - Session correlation
    """

    def __init__(
        self,
        app: FastAPI,
        exclude_paths: Optional[list] = None,
        enable_body_logging: bool = False
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]
        self.enable_body_logging = enable_body_logging

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process each HTTP request with comprehensive audit logging"""

        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Generate request ID for correlation
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Extract context
        context = await self._extract_request_context(request)
        context['request_id'] = request_id

        # Start OpenTelemetry span
        span = None
        if OTEL_AVAILABLE:
            span = self._start_otel_span(request, context)

        try:
            # Process request
            response = await call_next(request)

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            context['latency_ms'] = latency_ms
            context['status_code'] = response.status_code

            # Log audit event
            await self._log_audit_event(
                request=request,
                response=response,
                context=context,
                latency_ms=latency_ms,
                error=None
            )

            # Update metrics
            if PROMETHEUS_AVAILABLE:
                self._update_metrics(request, response, latency_ms, context, error=None)

            # Update span
            if span:
                self._update_span(span, response.status_code, None)

            # Add audit headers to response
            response.headers['X-Request-ID'] = request_id
            response.headers['X-Audit-Logged'] = 'true'

            return response

        except Exception as e:
            # Log error
            latency_ms = (time.time() - start_time) * 1000
            context['latency_ms'] = latency_ms
            context['error'] = str(e)
            context['error_type'] = type(e).__name__

            await self._log_audit_event(
                request=request,
                response=None,
                context=context,
                latency_ms=latency_ms,
                error=e
            )

            # Update metrics
            if PROMETHEUS_AVAILABLE:
                self._update_metrics(request, None, latency_ms, context, error=e)

            # Update span
            if span:
                self._update_span(span, 500, e)

            raise

    async def _extract_request_context(self, request: Request) -> Dict[str, Any]:
        """Extract comprehensive context from request"""

        # Extract user info from token/session
        user_id = None
        username = None
        user_role = None
        session_id = None

        # Try to get user from request state (set by auth middleware)
        if hasattr(request.state, 'user'):
            user = request.state.user
            user_id = str(user.id) if hasattr(user, 'id') else None
            username = user.username if hasattr(user, 'username') else None
            user_role = user.role.value if hasattr(user, 'role') else None

        # Try to get session_id from query params or headers
        session_id = request.query_params.get('session_id') or request.headers.get('X-Session-ID')

        # Extract request details
        context = {
            'method': request.method,
            'path': request.url.path,
            'endpoint': f"{request.method} {request.url.path}",
            'query_params': dict(request.query_params),
            'headers': dict(request.headers),
            'client_host': request.client.host if request.client else None,
            'user_agent': request.headers.get('user-agent'),
            'user_id': user_id,
            'username': username,
            'user_role': user_role,
            'session_id': session_id,
        }

        # Optionally log request body (sanitized)
        if self.enable_body_logging and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                if body:
                    context['request_body_size'] = len(body)
                    # Don't log full body for security
            except Exception as e:
                logger.debug(f"Could not read request body: {e}")

        return context

    def _start_otel_span(self, request: Request, context: Dict[str, Any]):
        """Start OpenTelemetry span for distributed tracing"""
        try:
            span = tracer.start_span(
                name=f"{request.method} {request.url.path}",
                attributes={
                    "http.method": request.method,
                    "http.url": str(request.url),
                    "http.target": request.url.path,
                    "http.user_agent": context.get('user_agent'),
                    "user.id": context.get('user_id'),
                    "user.role": context.get('user_role'),
                    "session.id": context.get('session_id'),
                    "request.id": context.get('request_id'),
                }
            )
            return span
        except Exception as e:
            logger.error(f"Failed to create OpenTelemetry span: {e}")
            return None

    def _update_span(self, span, status_code: int, error: Optional[Exception]):
        """Update OpenTelemetry span with response info"""
        if not span:
            return

        try:
            span.set_attribute("http.status_code", status_code)

            if error:
                span.set_status(Status(StatusCode.ERROR, str(error)))
                span.record_exception(error)
            elif status_code >= 400:
                span.set_status(Status(StatusCode.ERROR, f"HTTP {status_code}"))
            else:
                span.set_status(Status(StatusCode.OK))

            span.end()
        except Exception as e:
            logger.error(f"Failed to update OpenTelemetry span: {e}")

    async def _log_audit_event(
        self,
        request: Request,
        response: Optional[Response],
        context: Dict[str, Any],
        latency_ms: float,
        error: Optional[Exception]
    ):
        """Log structured audit event to database and logs (for Loki)"""

        # Determine action type from endpoint
        action_type = self._determine_action_type(request.url.path, request.method)

        # Create structured log entry (for Grafana Loki)
        log_entry = {
            "event_type": "api_request",
            "request_id": context.get('request_id'),
            "timestamp": time.time(),
            "user_id": context.get('user_id'),
            "username": context.get('username'),
            "user_role": context.get('user_role'),
            "session_id": context.get('session_id'),
            "action_type": action_type,
            "method": context.get('method'),
            "path": context.get('path'),
            "endpoint": context.get('endpoint'),
            "status_code": context.get('status_code'),
            "latency_ms": latency_ms,
            "client_ip": context.get('client_host'),
            "user_agent": context.get('user_agent', '')[:200],  # Truncate
            "error": context.get('error'),
            "error_type": context.get('error_type'),
        }

        # Log to stdout (captured by Loki)
        if error:
            logger.error(f"AUDIT_EVENT: {json.dumps(log_entry)}")
        else:
            logger.info(f"AUDIT_EVENT: {json.dumps(log_entry)}")

        # Store to database (async, don't block)
        try:
            await self._store_audit_to_db(request, context, latency_ms, action_type, error)
        except Exception as e:
            logger.error(f"Failed to store audit log to database: {e}")
            # Don't fail request if audit storage fails

    async def _store_audit_to_db(
        self,
        request: Request,
        context: Dict[str, Any],
        latency_ms: float,
        action_type: str,
        error: Optional[Exception]
    ):
        """Store audit log to PostgreSQL database"""
        try:
            from app.services.audit_service import audit_service
            from app.core.database import get_db

            # Get database session
            async for db in get_db():
                await audit_service.log_action(
                    db=db,
                    action=action_type,
                    user_id=uuid.UUID(context.get('user_id')) if context.get('user_id') else None,
                    session_id=context.get('session_id'),
                    resource_type=self._extract_resource_type(request.url.path),
                    description=f"{context.get('method')} {context.get('path')}",
                    request_data={
                        'query_params': context.get('query_params'),
                        'request_body_size': context.get('request_body_size'),
                    },
                    ip_address=context.get('client_host'),
                    user_agent=context.get('user_agent'),
                    status_code=context.get('status_code'),
                    error_message=str(error) if error else None,
                    latency_ms=latency_ms,
                    meta_info={
                        'request_id': context.get('request_id'),
                        'endpoint': context.get('endpoint'),
                    }
                )
                break  # Only use first session

        except Exception as e:
            logger.error(f"Error storing audit log to database: {e}")

    def _update_metrics(
        self,
        request: Request,
        response: Optional[Response],
        latency_ms: float,
        context: Dict[str, Any],
        error: Optional[Exception]
    ):
        """Update Prometheus metrics"""
        try:
            method = context.get('method', 'UNKNOWN')
            endpoint = context.get('path', 'unknown')
            status = str(context.get('status_code', 500 if error else 200))
            user_role = context.get('user_role', 'anonymous')

            # Increment request counter
            audit_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status,
                user_role=user_role
            ).inc()

            # Record latency
            audit_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(latency_ms / 1000.0)

            # Track user actions
            action_type = self._determine_action_type(request.url.path, method)
            module = self._extract_module(request.url.path)
            audit_user_actions.labels(
                action_type=action_type,
                user_id=context.get('user_id', 'anonymous'),
                module=module
            ).inc()

            # Track failed requests
            if error:
                audit_failed_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    error_type=type(error).__name__
                ).inc()

        except Exception as e:
            logger.error(f"Error updating Prometheus metrics: {e}")

    def _determine_action_type(self, path: str, method: str) -> str:
        """Determine action type from endpoint path and method"""
        path_lower = path.lower()

        if '/upload' in path_lower:
            return 'upload'
        elif '/query' in path_lower or '/chat' in path_lower:
            return 'query'
        elif '/scrape' in path_lower:
            return 'scrape'
        elif '/login' in path_lower or '/auth/login' in path_lower:
            return 'login'
        elif '/logout' in path_lower or '/auth/logout' in path_lower:
            return 'logout'
        elif method == 'DELETE':
            return 'delete'
        elif method == 'POST':
            return 'create'
        elif method in ['PUT', 'PATCH']:
            return 'update'
        elif method == 'GET':
            return 'view'
        else:
            return 'unknown'

    def _extract_module(self, path: str) -> str:
        """Extract module name from path"""
        path_parts = path.strip('/').split('/')

        if len(path_parts) >= 3 and path_parts[0] == 'api':
            # /api/v1/module -> module
            return path_parts[2] if len(path_parts) > 2 else 'unknown'

        return 'unknown'

    def _extract_resource_type(self, path: str) -> Optional[str]:
        """Extract resource type from path"""
        if '/document' in path or '/upload' in path:
            return 'document'
        elif '/query' in path or '/chat' in path:
            return 'query'
        elif '/scrape' in path:
            return 'scrape'
        elif '/user' in path:
            return 'user'
        elif '/session' in path:
            return 'session'
        elif '/project' in path:
            return 'project'
        return None


def setup_audit_middleware(app: FastAPI):
    """Setup audit middleware on FastAPI app"""
    app.add_middleware(
        AuditMiddleware,
        exclude_paths=[
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/static"
        ],
        enable_body_logging=False  # Set to True for debugging (not recommended in prod)
    )
    logger.info("Audit middleware initialized with OpenTelemetry and Prometheus")
