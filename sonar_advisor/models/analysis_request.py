from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sonar_advisor.core.database import Base


class AnalysisRequest(Base):
    __tablename__ = "analysis_requests"

    id = Column(Integer, primary_key=True, index=True)
    project_key = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    sonarqube_data = Column(Text)  # JSON string of fetched SonarQube data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="analysis_requests")
    ai_reports = relationship("AIReport", back_populates="analysis_request", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AnalysisRequest(id={self.id}, project_key='{self.project_key}', status='{self.status}')>"


# Add the back reference to User model
from sonar_advisor.models.user import User
User.analysis_requests = relationship("AnalysisRequest", back_populates="user")