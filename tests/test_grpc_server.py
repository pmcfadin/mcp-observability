import types

import pytest

import app.grpc_server as gs


@pytest.mark.asyncio
async def test_observability_servicer_uppercase(monkeypatch):
    # Create fake pb2 and pb2_grpc modules compatible with grpc_server expectations
    class _FakeRequest:
        def __init__(self, prompt: str):
            self.prompt = prompt

    class _FakeResponse:
        def __init__(self, reply: str):
            self.reply = reply

    fake_pb2 = types.SimpleNamespace(SampleRequest=_FakeRequest, SampleResponse=_FakeResponse)
    fake_pb2_grpc = types.SimpleNamespace(ObservabilityServiceServicer=object)

    monkeypatch.setattr(gs, "pb2", fake_pb2, raising=False)
    monkeypatch.setattr(gs, "pb2_grpc", fake_pb2_grpc, raising=False)

    servicer = gs.ObservabilityServicer()
    request = _FakeRequest("hello")
    # Context not used; pass None
    response = await servicer.Sample(request, None)

    assert response.reply == "HELLO" 