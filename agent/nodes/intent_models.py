from pydantic import BaseModel, Field, field_validator
from typing import Optional

class IntentClassification(BaseModel):
    intent: str = Field(
        description=(
            "The classified intent of the user message. Must be exactly one of: "
            "business_query, followup_business_query, chat, schema_request, "
            "metadata_request, unsafe_request, out_of_scope"
        )
    )
    confidence: float = Field(
        description="Confidence score of the classification, ranging strictly between 0.0 and 1.0"
    )
    requires_clarification: bool = Field(
        description="True if the user query is too ambiguous or vague, requiring further clarification"
    )
    clarification_message: Optional[str] = Field(
        default=None,
        description="Specific question or message asking the user to clarify their request when requires_clarification is True"
    )
    conversational_response: Optional[str] = Field(
        default=None,
        description="Direct conversational answer if the intent is not a business_query or followup_business_query"
    )

    @field_validator("intent")
    @classmethod
    def validate_intent_name(cls, value: str) -> str:
        allowed_intents = {
            "business_query",
            "followup_business_query",
            "chat",
            "schema_request",
            "metadata_request",
            "unsafe_request",
            "out_of_scope"
        }
        if value not in allowed_intents:
            raise ValueError(f"Intent '{value}' is not supported. Must be one of {allowed_intents}")
        return value

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, value: float) -> float:
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"Confidence score '{value}' must be strictly between 0.0 and 1.0")
        return value
