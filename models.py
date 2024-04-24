from pydantic import BaseModel,field_validator
from typing import List, Optional

class Prompt(BaseModel):
    prompt: str
    poisoned: int | None = None
    @field_validator('prompt')
    @classmethod
    def check_length(cls, value :str) -> str:
        if len(value.split()) <= 3:
            raise ValueError("Prompt must contain at least 3 words.")
        return value

class PromptCheckResult(BaseModel):
    prompt: str
    is_injected: int
    confidence_score: str | None = None
    details: List[dict] | None = None
    time: str | None = None
