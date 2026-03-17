from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="required, non-empty")
    max_length: int = Field(default=100, gt=0, description="optional, default 100")


class SummarizeResponse(BaseModel):
    summary: str
    model: str
    truncated: bool


class SummaryRow(BaseModel):
    id: int
    input_text: str
    summary_text: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    created_at: str
