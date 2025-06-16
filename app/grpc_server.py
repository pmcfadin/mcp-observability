from __future__ import annotations

import asyncio
from logging import getLogger
from typing import AsyncIterator
import types

import grpc

try:
    from app import observability_pb2 as pb2  # generated file path
    from app import observability_pb2_grpc as pb2_grpc
except ImportError:  # pragma: no cover
    # Stubs not generated; server cannot start. This is acceptable in CI until
    # compile step runs. A warning is logged instead of crashing import time.
    pb2 = None  # type: ignore

    # Create a minimal stand-in with attribute used for inheritance so that imports
    # in environments without generated stubs (e.g. CI) still succeed.
    class _FallbackServicerBase:  # pylint: disable=too-few-public-methods
        pass

    pb2_grpc = types.SimpleNamespace(
        ObservabilityServiceServicer=_FallbackServicerBase,
    )  # type: ignore

logger = getLogger(__name__)


class ObservabilityServicer(pb2_grpc.ObservabilityServiceServicer):  # type: ignore[misc]
    async def Sample(self, request: pb2.SampleRequest, context: grpc.aio.ServicerContext) -> pb2.SampleResponse:  # type: ignore[name-defined]
        reply = request.prompt.upper()
        return pb2.SampleResponse(reply=reply)

    async def SampleStream(
        self, request: pb2.SampleRequest, context: grpc.aio.ServicerContext
    ) -> AsyncIterator[pb2.SampleResponse]:  # type: ignore[name-defined]
        for ch in request.prompt:
            yield pb2.SampleResponse(reply=ch)
            await asyncio.sleep(0.01)


def serve(port: int = 50051) -> None:  # pragma: no cover
    if pb2 is None:
        logger.warning("gRPC stubs not available; generate them with grpc_tools.protoc")
        return

    server = grpc.aio.server()
    pb2_grpc.add_ObservabilityServiceServicer_to_server(ObservabilityServicer(), server)
    server.add_insecure_port(f"0.0.0.0:{port}")

    async def _start() -> None:
        await server.start()
        logger.info("gRPC server started on port %d", port)
        await server.wait_for_termination()

    asyncio.run(_start())


if __name__ == "__main__":  # pragma: no cover
    serve() 