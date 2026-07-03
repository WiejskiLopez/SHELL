"""gRPC client interceptor that injects x-correlation-id into outgoing metadata.

TODO: Full implementation once gRPC communication between services is required.
The current stub provides the structural skeleton.
"""

from __future__ import annotations

from typing import Any

from shell.application.platform.context.correlation_id import get_correlation_id


class CorrelationIdInterceptor:
    """Injects the current correlation_id into outgoing gRPC metadata.

    Usage:
        interceptor = CorrelationIdInterceptor()
        channel = grpc.aio.insecure_channel("host:port", interceptors=[interceptor])
    """

    async def intercept_unary_unary(
        self,
        continuation: Any,
        client_call_details: Any,
        request: Any,
    ) -> Any:
        corr_id = get_correlation_id()
        if not corr_id:
            return await continuation(client_call_details, request)

        metadata = list(getattr(client_call_details, "metadata", None) or [])

        # TODO: use open-telemetry propagation format (traceparent / W3C)
        #       when migrating to distributed tracing
        metadata.append(("x-correlation-id", corr_id))

        # Reconstruct client_call_details with updated metadata
        if dataclasses.is_dataclass(client_call_details):
            updated_details = dataclasses.replace(
                client_call_details,
                metadata=metadata,  # type: ignore[type-var]
            )
        else:
            updated_details = client_call_details

        return await continuation(updated_details, request)
