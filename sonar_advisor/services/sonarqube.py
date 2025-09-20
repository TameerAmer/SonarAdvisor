import httpx
import json
import base64
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from sonar_advisor.core.config import settings
from sonar_advisor.schemas.analysis import SonarQubeData, SonarQubeIssue
from sonar_advisor.models.analysis_request import AnalysisRequest


class SonarQubeService:
    """
    Service to interact with SonarQube Web API
    """
    
    def __init__(self):
        self.base_url = settings.sonarqube_url.rstrip('/')
        self.token = settings.sonarqube_token
        self.username = settings.sonarqube_username
        self.password = settings.sonarqube_password
        
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for SonarQube API
        """
        headers = {"Content-Type": "application/json"}
        
        if self.token:
            # Use token authentication (preferred)
            auth_string = f"{self.token}:"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_auth}"
        elif self.username and self.password:
            # Use username/password authentication
            auth_string = f"{self.username}:{self.password}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_auth}"
        
        return headers
    
    async def test_connection(self) -> bool:
        """
        Test connection to SonarQube server
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/system/status",
                    headers=self._get_auth_headers(),
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception:
            return False
    
    async def get_project_info(self, project_key: str) -> Optional[Dict[str, Any]]:
        """
        Get basic project information from SonarQube
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/projects/search",
                    params={"projects": project_key},
                    headers=self._get_auth_headers(),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("components"):
                        return data["components"][0]
                return None
        except Exception as e:
            print(f"Error fetching project info: {e}")
            return None
    
    async def fetch_project_issues(self, project_key: str) -> SonarQubeData:
        """
        Fetch all issues for a project from SonarQube
        """
        all_issues = []
        page = 1
        page_size = 500
        total_fetched = 0
        
        try:
            async with httpx.AsyncClient() as client:
                while True:
                    response = await client.get(
                        f"{self.base_url}/api/issues/search",
                        params={
                            "componentKeys": project_key,
                            "p": page,
                            "ps": page_size,
                            "resolved": "false"  # Only get unresolved issues
                        },
                        headers=self._get_auth_headers(),
                        timeout=60.0
                    )
                    
                    if response.status_code != 200:
                        break
                    
                    data = response.json()
                    issues = data.get("issues", [])
                    
                    if not issues:
                        break
                    
                    # Convert to our schema format
                    for issue in issues:
                        sonar_issue = SonarQubeIssue(
                            key=issue.get("key", ""),
                            rule=issue.get("rule", ""),
                            severity=issue.get("severity", ""),
                            component=issue.get("component", ""),
                            line=issue.get("line"),
                            message=issue.get("message", ""),
                            type=issue.get("type", ""),
                            status=issue.get("status", "OPEN")
                        )
                        all_issues.append(sonar_issue)
                    
                    total_fetched += len(issues)
                    
                    # Check if we've fetched all issues
                    total_issues = data.get("total", 0)
                    if total_fetched >= total_issues:
                        break
                    
                    page += 1
        
        except Exception as e:
            print(f"Error fetching issues: {e}")
        
        # Calculate statistics
        bugs = sum(1 for issue in all_issues if issue.type == "BUG")
        vulnerabilities = sum(1 for issue in all_issues if issue.type == "VULNERABILITY")
        code_smells = sum(1 for issue in all_issues if issue.type == "CODE_SMELL")
        
        return SonarQubeData(
            project_key=project_key,
            issues=all_issues,
            total_issues=len(all_issues),
            bugs=bugs,
            vulnerabilities=vulnerabilities,
            code_smells=code_smells
        )
    
    async def fetch_project_measures(self, project_key: str) -> Dict[str, Any]:
        """
        Fetch project quality measures from SonarQube
        """
        metrics = [
            "bugs", "vulnerabilities", "code_smells",
            "coverage", "duplicated_lines_density",
            "ncloc", "complexity", "violations"
        ]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/measures/component",
                    params={
                        "component": project_key,
                        "metricKeys": ",".join(metrics)
                    },
                    headers=self._get_auth_headers(),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    measures = {}
                    for measure in data.get("component", {}).get("measures", []):
                        measures[measure["metric"]] = measure.get("value")
                    return measures
                
        except Exception as e:
            print(f"Error fetching measures: {e}")
        
        return {}
    
    async def store_sonarqube_data(
        self, 
        db: Session, 
        analysis_request: AnalysisRequest, 
        sonarqube_data: SonarQubeData
    ) -> AnalysisRequest:
        """
        Store SonarQube data in the database using SQLAlchemy
        """
        try:
            # Convert SonarQubeData to JSON string for storage
            sonarqube_json = sonarqube_data.model_dump_json()
            
            # Update the analysis request with the fetched data
            analysis_request.sonarqube_data = sonarqube_json
            analysis_request.status = "data_fetched"
            
            db.commit()
            db.refresh(analysis_request)
            
            return analysis_request
            
        except Exception as e:
            db.rollback()
            print(f"Error storing SonarQube data: {e}")
            analysis_request.status = "failed"
            db.commit()
            raise e


# Create a singleton instance
sonarqube_service = SonarQubeService()