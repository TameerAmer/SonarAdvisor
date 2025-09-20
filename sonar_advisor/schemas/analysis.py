from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AnalysisRequestCreate(BaseModel):
    project_key: str


class AnalysisRequestResponse(BaseModel):
    id: int
    project_key: str
    user_id: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SonarQubeIssue(BaseModel):
    key: str
    rule: str
    severity: str
    component: str
    line: Optional[int] = None
    message: str
    type: str  # BUG, VULNERABILITY, CODE_SMELL


class SonarQubeData(BaseModel):
    total_issues: int
    issues: List[SonarQubeIssue]
    code_smells: int
    bugs: int
    vulnerabilities: int


class TopProblem(BaseModel):
    rule: str
    description: str
    frequency: int
    impact: str  # high, medium, low


class SuggestedImprovement(BaseModel):
    category: str
    suggestion: str
    priority: str  # high, medium, low


class PrioritizedIssue(BaseModel):
    rule: str
    message: str
    severity: str
    files_affected: int


class AIReportResponse(BaseModel):
    id: int
    analysis_request_id: int
    summary: str
    top_recurring_problems: List[TopProblem]
    suggested_improvements: List[SuggestedImprovement]
    prioritized_issues: List[PrioritizedIssue]
    total_issues: int
    critical_issues: int
    major_issues: int
    minor_issues: int
    code_smells: int
    bugs: int
    vulnerabilities: int
    ai_model_used: str
    confidence_score: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    request: AnalysisRequestResponse
    report: Optional[AIReportResponse] = None