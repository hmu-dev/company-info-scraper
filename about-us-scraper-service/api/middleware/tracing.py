from fastapi import Request, Response
from typing import Optional, Dict, Any
import uuid
import time
import contextvars
import json
from ..utils.logging import log_event

# Context variables for tracing
request_id = contextvars.ContextVar("request_id", default=None)
parent_id = contextvars.ContextVar("parent_id", default=None)
trace_id = contextvars.ContextVar("trace_id", default=None)


class TracingMiddleware:
    def __init__(self, app):
        """Initialize tracing middleware"""
        self.app = app

    def get_trace_headers(self, request: Request) -> Dict[str, str]:
        """Extract trace headers from request"""
        headers = request.headers
        return {
            "x-request-id": headers.get("x-request-id"),
            "x-b3-traceid": headers.get("x-b3-traceid"),
            "x-b3-spanid": headers.get("x-b3-spanid"),
            "x-b3-parentspanid": headers.get("x-b3-parentspanid"),
        }

    def generate_ids(self, trace_headers: Dict[str, str]) -> Dict[str, str]:
        """Generate trace IDs"""
        # Generate request ID if not provided
        req_id = trace_headers.get("x-request-id") or str(uuid.uuid4())

        # Generate trace ID if not provided
        trace_id_str = trace_headers.get("x-b3-traceid")
        if not trace_id_str:
            trace_id_str = format(uuid.uuid4().int, "032x")[:16]

        # Generate span ID
        span_id = format(uuid.uuid4().int, "016x")[:16]

        # Get parent span ID
        parent_span_id = trace_headers.get("x-b3-spanid")

        return {
            "request_id": req_id,
            "trace_id": trace_id_str,
            "span_id": span_id,
            "parent_id": parent_span_id,
        }

    def set_trace_context(self, ids: Dict[str, str]):
        """Set trace context variables"""
        request_id.set(ids["request_id"])
        trace_id.set(ids["trace_id"])
        parent_id.set(ids["parent_id"])

    def get_trace_response_headers(self, ids: Dict[str, str]) -> Dict[str, str]:
        """Get trace response headers"""
        headers = {
            "x-request-id": ids["request_id"],
            "x-b3-traceid": ids["trace_id"],
            "x-b3-spanid": ids["span_id"],
        }

        if ids["parent_id"]:
            headers["x-b3-parentspanid"] = ids["parent_id"]

        return headers

    async def __call__(self, scope, receive, send):
        """Process request with tracing"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        # Extract trace headers
        trace_headers = self.get_trace_headers(request)

        # Generate trace IDs
        ids = self.generate_ids(trace_headers)

        # Set trace context
        self.set_trace_context(ids)

        # Start timing
        start_time = time.time()

        # Log request start
        log_event(
            "request_start",
            {
                "method": request.method,
                "path": request.url.path,
                "query": dict(request.query_params),
                "client_host": request.client.host,
                "trace_context": {
                    "request_id": ids["request_id"],
                    "trace_id": ids["trace_id"],
                    "span_id": ids["span_id"],
                    "parent_id": ids["parent_id"],
                },
            },
        )

        response_started = False
        response_status = None
        response_headers = []

        async def send_wrapper(message):
            nonlocal response_started, response_status, response_headers

            if message["type"] == "http.response.start":
                response_started = True
                response_status = message["status"]
                response_headers = message.get("headers", [])

                # Add trace headers
                trace_headers = self.get_trace_response_headers(ids)
                for key, value in trace_headers.items():
                    response_headers.append((key.encode(), value.encode()))

                await send(
                    {
                        "type": "http.response.start",
                        "status": response_status,
                        "headers": response_headers,
                    }
                )

            elif message["type"] == "http.response.body":
                if not response_started:
                    raise RuntimeError("Response body sent before response start.")

                await send(message)

                # Calculate duration and log request end
                duration = time.time() - start_time
                log_event(
                    "request_end",
                    {
                        "status_code": response_status,
                        "duration": duration,
                        "success": 200 <= response_status < 300,
                        "trace_context": {
                            "request_id": ids["request_id"],
                            "trace_id": ids["trace_id"],
                            "span_id": ids["span_id"],
                            "parent_id": ids["parent_id"],
                        },
                    },
                )

            else:
                await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            log_event(
                "request_error",
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration": duration,
                    "trace_context": {
                        "request_id": ids["request_id"],
                        "trace_id": ids["trace_id"],
                        "span_id": ids["span_id"],
                        "parent_id": ids["parent_id"],
                    },
                },
            )
            raise


def get_current_trace_context() -> Dict[str, Optional[str]]:
    """Get current trace context"""
    return {
        "request_id": request_id.get(),
        "trace_id": trace_id.get(),
        "parent_id": parent_id.get(),
    }


def setup_tracing(app):
    """Set up request tracing"""
    app.add_middleware(TracingMiddleware)
