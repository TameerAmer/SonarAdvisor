from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sonar_advisor.core.database import Base


class AIReport(Base):
    __tablename__ = "ai_reports"

    id = Column(Integer, primary_key=True, index=True)
    analysis_request_id = Column(Integer, ForeignKey("analysis_requests.id"), nullable=False)
    
    # AI Analysis Results
    summary = Column(Text)  # Overall summary
    top_problems = Column(Text)  # JSON string of top problems
    suggested_improvements = Column(Text)  # JSON string of suggestions
    prioritized_issues = Column(Text)  # JSON string of prioritized critical issues
    metrics = Column(Text)  # JSON string of metrics
    
    # AI Model Info
    ai_model_used = Column(String(100))
    confidence_score = Column(Float)  # 0.0 to 1.0
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    analysis_request = relationship("AnalysisRequest", back_populates="ai_reports")

    def __repr__(self):
        return f"<AIReport(id={self.id}, analysis_request_id={self.analysis_request_id}, ai_model='{self.ai_model_used}')>"