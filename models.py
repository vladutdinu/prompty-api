from pydantic import BaseModel,field_validator
from typing import List, Optional

class PromptAccuracy(BaseModel):
    system_prompt: str
    user_prompt: str
    answer: str
    calculation_method: str

class Prompt(BaseModel):
    prompt: str
    poisoned: float | None = None
    @field_validator('prompt')
    @classmethod
    def check_length(cls, value: str) -> str:
        if len(value.split()) <= 3:
            raise ValueError("Prompt must contain at least 3 words.")
        return value

class PromptCheckResult(BaseModel):
    prompt: str
    is_injected: float
    injection_confidence_score: float | None = None
    time: str | None = None

class CleanPrompt(BaseModel):
    prompt: str
    cleaned_prompt: str

class UsageCounter(BaseModel):
    count: int