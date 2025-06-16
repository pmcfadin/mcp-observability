import json

import pytest

from mcp_observability.schemas import (
    Message,
    MessageContent,
    MessageContentType,
    MessageRole,
    Prompt,
    Resource,
    ResourceType,
    SamplingRequest,
    Tool,
)


def test_resource_roundtrip() -> None:
    resource = Resource(
        id="res-1",
        type=ResourceType.text,
        name="Example",
        description="An example resource",
        content="hello world",
        metadata={"tags": ["example"]},
    )

    json_data = resource.model_dump_json()
    parsed = Resource.model_validate_json(json_data)

    assert parsed == resource


def test_prompt_roundtrip() -> None:
    prompt = Prompt(
        id="p1",
        template="Hello, {{name}}!",
        inputVariables=["name"],
    )
    data = json.loads(prompt.model_dump_json(by_alias=True))
    assert data["inputVariables"] == ["name"]
    assert Prompt.model_validate_json(prompt.model_dump_json(by_alias=True)) == prompt


def test_tool_schema_serialization() -> None:
    tool = Tool(
        name="calc_sum",
        description="Calculate sum of two numbers",
        inputSchema={
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            "required": ["a", "b"],
        },
    )
    dumped = tool.model_dump(by_alias=True)
    assert "inputSchema" in dumped
    assert dumped["inputSchema"]["type"] == "object"


def test_sampling_request_validation() -> None:
    request = SamplingRequest(
        messages=[
            Message(
                role=MessageRole.user,
                content=MessageContent(type=MessageContentType.text, text="Hi"),
            )
        ],
        maxTokens=10,
    )

    assert request.messages[0].role == MessageRole.user
    schema = request.model_json_schema()
    assert "properties" in schema


if __name__ == "__main__":
    pytest.main([__file__]) 