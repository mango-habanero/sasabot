"""Internal DTO for LLM intent recognition."""

from typing import Any

from pydantic import BaseModel, Field

from src.data.enums import IntentType


class Intent(BaseModel):
    type: IntentType = Field(
        description="The recognized intent type",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1",
    )
    entities: dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted entities from user message",
    )
    reasoning: str | None = Field(
        default=None,
        description="LLM's reasoning for the intent classification",
    )
