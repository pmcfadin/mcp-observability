"""Pydantic models implementing a minimal subset of the Model Context Protocol (MCP).

The goal of this module is *not* to re-implement the full
https://modelcontextprotocol.io specification.  Instead, it provides the
specific structures that the *mcp-observability* service needs to expose its
Resources, Prompts, Tools, and to (optionally) initiate Sampling requests from
clients.

Each model includes JSON-schema compliant field naming so that they can be
serialised directly through FastAPI / JSON-RPC without additional translation
layers.

Keeping the file < 500 LoC ensures readability and satisfies the repository
contribution guidelines.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


class ResourceType(str, Enum):
    """High-level resource content types recognised by the MCP spec."""

    file = "file"
    url = "url"
    text = "text"
    image = "image"
    # The spec allows arbitrary MIME types – additional types may be added as
    # needed.


class Resource(BaseModel):
    """Contextual information a server can expose to clients/LLMs.

    The *content* field is intentionally typed as *Any* because a resource may
    contain raw strings, binary blobs (base64-encoded), or nested JSON data.
    Consumers are expected to inspect the *type* field to decide how to handle
    *content*.
    """

    id: str = Field(..., description="Unique identifier for the resource")
    type: ResourceType = Field(..., description="Type hint for the resource")
    name: Optional[str] = Field(None, description="Human-readable name")
    description: Optional[str] = None
    content: Optional[Any] = Field(
        None, description="Resource payload or an external reference/URI"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary caller-defined metadata"
    )

    class Config:
        """Model configuration."""

        populate_by_name = True
        extra = "forbid"


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


class Prompt(BaseModel):
    """Templated prompt definition compatible with the MCP *Prompts* feature."""

    id: str = Field(..., description="Unique identifier for the prompt")
    template: str = Field(..., description="Prompt template string")
    input_variables: List[str] = Field(
        default_factory=list,
        alias="inputVariables",
        description="Variable names expected by the template",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary prompt metadata"
    )

    class Config:
        populate_by_name = True
        extra = "forbid"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


class ToolAnnotations(BaseModel):
    """Optional behaviour hints – see MCP spec §Tool annotations."""

    title: Optional[str] = None
    readOnlyHint: bool = False
    destructiveHint: bool = True
    idempotentHint: bool = False
    openWorldHint: bool = True


class Tool(BaseModel):
    """Executable capability exposed by the server."""

    name: str = Field(..., description="Unique tool identifier")
    description: Optional[str] = None
    input_schema: Dict[str, Any] = Field(
        ..., alias="inputSchema", description="JSON Schema for parameters"
    )
    annotations: Optional[ToolAnnotations] = None

    class Config:
        populate_by_name = True
        extra = "forbid"


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class MessageContentType(str, Enum):
    text = "text"
    image = "image"


class MessageContent(BaseModel):
    type: MessageContentType
    text: Optional[str] = None
    # For images: base64-encoded data and MIME type
    data: Optional[str] = None
    mimeType: Optional[str] = None

    @validator("text", always=True)
    def _validate_content(cls, v, values):  # noqa: N805
        content_type = values.get("type")
        if content_type == MessageContentType.text and v is None:
            raise ValueError("'text' must be provided when type=='text'")
        if content_type == MessageContentType.image and v is not None:
            raise ValueError("'text' must be None when type=='image'")
        return v


class Message(BaseModel):
    role: MessageRole
    content: MessageContent


class ModelHint(BaseModel):
    name: Optional[str] = None  # e.g. "claude-3-sonnet"


class ModelPreferences(BaseModel):
    hints: Optional[List[ModelHint]] = None
    costPriority: Optional[float] = Field(None, ge=0.0, le=1.0)
    speedPriority: Optional[float] = Field(None, ge=0.0, le=1.0)
    intelligencePriority: Optional[float] = Field(None, ge=0.0, le=1.0)


class SamplingRequest(BaseModel):
    messages: List[Message]
    system_prompt: Optional[str] = Field(None, alias="systemPrompt")
    include_context: Optional[str] = Field(
        None, alias="includeContext", description="Context inclusion policy"
    )
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: int = Field(..., alias="maxTokens", gt=0)
    stop_sequences: Optional[List[str]] = Field(None, alias="stopSequences")
    model_preferences: Optional[ModelPreferences] = Field(
        None, alias="modelPreferences"
    )
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True
        extra = "forbid"


class SamplingResponse(BaseModel):
    model: str
    stop_reason: Optional[str] = Field(None, alias="stopReason")
    role: MessageRole
    content: MessageContent

    class Config:
        populate_by_name = True
        extra = "forbid"


# ---------------------------------------------------------------------------
# Initialize Handshake (Lifecycle)
# ---------------------------------------------------------------------------

class ClientInfo(BaseModel):
    name: str
    version: Optional[str] = None
    informationUri: Optional[str] = None


class ServerInfo(BaseModel):
    name: str
    version: str
    informationUri: Optional[str] = None


class Capabilities(BaseModel):
    """Subset of MCP capabilities we expose.

    For now we only advertise resources, prompts, tools, and sampling availability.
    Additional nested capability fields can be added later if/when implemented.
    """

    resources: bool = False
    prompts: bool = False
    tools: bool = False
    sampling: bool = False


class InitializeRequest(BaseModel):
    version: str = Field(..., description="MCP protocol version requested by the client")
    client: ClientInfo
    capabilities: Optional[Capabilities] = None


class InitializeResponse(BaseModel):
    version: str = Field(..., description="Protocol version selected by the server")
    server: ServerInfo
    capabilities: Capabilities

    class Config:
        populate_by_name = True
        extra = "forbid" 