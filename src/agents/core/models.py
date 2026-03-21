"""Core Pydantic models shared across all pipeline stages."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class Parameter(BaseModel):
    """HTTP request parameter."""

    name: str
    location: Literal["query", "header", "cookie", "body", "path"]
    type: str = "string"
    sample_value: str | None = None


class Endpoint(BaseModel):
    """API endpoint descriptor."""

    url: str
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
    parameters: list[Parameter] = Field(default_factory=list)
    auth_required: bool = False
    content_type: str = "application/json"


class CryptoContext(BaseModel):
    """Encryption context detected on target."""

    detected: bool = False
    algorithm: str | None = None
    key: str | None = None
    iv: str | None = None
    padding: str | None = None
    encryption_scope: str | None = None
    encrypted_endpoints: list[str] = Field(default_factory=list)


class AuthStep(BaseModel):
    """Single step in an authentication flow."""

    order: int = Field(..., ge=1)
    action: str
    description: str = ""


class AuthFlow(BaseModel):
    """Authentication flow descriptor."""

    steps: list[AuthStep] = Field(default_factory=list)
    session_mechanism: Literal["cookie", "jwt", "bearer", "custom"]
    two_factor: bool = False
    sso: bool = False


class WafProfile(BaseModel):
    """WAF detection profile."""

    detected: bool = False
    vendor: str | None = None
    ruleset: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Technology(BaseModel):
    """Detected technology on target."""

    name: str
    version: str | None = None
    category: str | None = None


class SessionConfig(BaseModel):
    """Session configuration for a pentest workspace."""

    session_name: str
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))
    target_url: str = Field(..., min_length=1)
    scope: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)
    tool_enabled: bool = True
    auto_approve_low: bool = False
    max_retries: int = Field(default=3, ge=1, le=10)
    reflexion_memory_size: int = Field(default=5, ge=1, le=20)
    llm_model: str = "gpt-4o"
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
