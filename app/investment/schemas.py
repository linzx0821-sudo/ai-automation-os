from pydantic import BaseModel, Field


class InvestmentResearchRequest(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    ticker: str | None = Field(default=None, max_length=40)
    exchange: str | None = Field(default=None, max_length=80)
    focus: str | None = Field(default=None, max_length=1000)


class InvestmentResearchPlan(BaseModel):
    company: str
    workspace: str
    task_goal: str
