import json
import asyncio
from typing import List, Dict, Any
from collections import Counter
from sqlalchemy.orm import Session
from datetime import datetime

from sonar_advisor.core.config import settings
from sonar_advisor.schemas.analysis import SonarQubeData, SonarQubeIssue, TopProblem, SuggestedImprovement, PrioritizedIssue
from sonar_advisor.models.analysis_request import AnalysisRequest
from sonar_advisor.models.ai_report import AIReport

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class AIAnalysisService:
    """
    AI-powered analysis service for SonarQube data
    Currently implements rule-based analysis, but can be extended with LLM integration
    """
    
    def __init__(self):
        self.model_type = settings.ai_model_type
    
    def analyze_issues(self, sonarqube_data: SonarQubeData) -> Dict[str, Any]:
        """
        Main analysis method that coordinates all analysis tasks
        """
        if self.model_type == "rule_based":
            return self._rule_based_analysis(sonarqube_data)
        elif self.model_type == "openai":
            return self._openai_analysis(sonarqube_data)
        else:
            # Fallback to rule-based
            return self._rule_based_analysis(sonarqube_data)
    
    def _rule_based_analysis(self, data: SonarQubeData) -> Dict[str, Any]:
        """
        Rule-based analysis implementation
        """
        # Analyze top recurring problems
        top_problems = self._analyze_top_problems(data.issues)
        
        # Generate improvement suggestions
        improvements = self._generate_improvement_suggestions(data.issues)
        
        # Prioritize critical issues
        prioritized_issues = self._prioritize_issues(data.issues)
        
        # Generate summary
        summary = self._generate_summary(data, top_problems, improvements)
        
        # Calculate metrics
        critical_issues = sum(1 for issue in data.issues if issue.severity == "CRITICAL")
        major_issues = sum(1 for issue in data.issues if issue.severity == "MAJOR")
        minor_issues = sum(1 for issue in data.issues if issue.severity in ["MINOR", "INFO"])
        
        return {
            "summary": summary,
            "top_recurring_problems": top_problems,
            "suggested_improvements": improvements,
            "prioritized_issues": prioritized_issues,
            "metrics": {
                "total_issues": data.total_issues,
                "critical_issues": critical_issues,
                "major_issues": major_issues,
                "minor_issues": minor_issues,
                "code_smells": data.code_smells,
                "bugs": data.bugs,
                "vulnerabilities": data.vulnerabilities
            },
            "ai_model_used": "rule_based_v1.0",
            "confidence_score": 0.85
        }
    
    def _openai_analysis(self, data: SonarQubeData) -> Dict[str, Any]:
        """
        OpenAI GPT-powered analysis implementation
        """
        if not OPENAI_AVAILABLE:
            return self._rule_based_analysis(data)
        
        try:
            client = openai.OpenAI(api_key=settings.openai_api_key)
            
            # Prepare issues data for AI analysis
            issues_summary = self._prepare_issues_for_ai(data.issues)
            
            prompt = f"""
            You are a senior software engineer reviewing code quality issues from SonarQube.
            
            Project Overview:
            - Total Issues: {data.total_issues}
            - Code Smells: {data.code_smells}
            - Bugs: {data.bugs}
            - Vulnerabilities: {data.vulnerabilities}
            
            Top Issues by Type and Severity:
            {issues_summary}
            
            Please provide:
            1. A comprehensive summary of the code quality state
            2. Top 3 recurring problems that need immediate attention
            3. 3 specific improvement recommendations
            4. Priority ranking of the most critical issues
            
            Format your response as JSON with the following structure:
            {{
                "summary": "detailed analysis...",
                "top_problems": [
                    {{"rule": "rule_id", "description": "problem description", "frequency": number, "impact": "high/medium/low"}}
                ],
                "improvements": [
                    {{"category": "category", "suggestion": "suggestion text", "priority": "high/medium/low"}}
                ],
                "prioritized_issues": [
                    {{"rule": "rule_id", "message": "message", "severity": "severity", "files_affected": number}}
                ]
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a senior code quality analyst. Provide structured, actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            response_content = response.choices[0].message.content
            
            # Check if response is empty or None
            if not response_content or response_content.strip() == "":
                print("OpenAI returned empty response, falling back to rule-based analysis")
                return self._rule_based_analysis(data)
            
            # Handle markdown-wrapped JSON responses
            if response_content.strip().startswith("```json"):
                # Extract JSON from markdown code blocks
                start_idx = response_content.find("```json") + 7
                end_idx = response_content.rfind("```")
                if end_idx > start_idx:
                    response_content = response_content[start_idx:end_idx].strip()
            elif response_content.strip().startswith("```"):
                # Handle generic code blocks
                start_idx = response_content.find("```") + 3
                end_idx = response_content.rfind("```")
                if end_idx > start_idx:
                    response_content = response_content[start_idx:end_idx].strip()
            
            try:
                ai_response = json.loads(response_content)
            except json.JSONDecodeError as je:
                print(f"OpenAI response is not valid JSON: {je}")
                print(f"Response content: {response_content[:500]}...")
                return self._rule_based_analysis(data)
            
            # Convert AI response to our format
            top_problems = [
                TopProblem(
                    rule=p["rule"],
                    description=p["description"],
                    frequency=p["frequency"],
                    impact=p["impact"]
                ) for p in ai_response.get("top_problems", [])
            ]
            
            improvements = [
                SuggestedImprovement(
                    category=i["category"],
                    suggestion=i["suggestion"],
                    priority=i["priority"]
                ) for i in ai_response.get("improvements", [])
            ]
            
            prioritized_issues = [
                PrioritizedIssue(
                    rule=p["rule"],
                    message=p["message"],
                    severity=p["severity"],
                    files_affected=p["files_affected"]
                ) for p in ai_response.get("prioritized_issues", [])
            ]
            
            return {
                "summary": ai_response.get("summary", ""),
                "top_recurring_problems": top_problems,
                "suggested_improvements": improvements,
                "prioritized_issues": prioritized_issues,
                "metrics": {
                    "total_issues": data.total_issues,
                    "critical_issues": sum(1 for issue in data.issues if issue.severity == "CRITICAL"),
                    "major_issues": sum(1 for issue in data.issues if issue.severity == "MAJOR"),
                    "minor_issues": sum(1 for issue in data.issues if issue.severity in ["MINOR", "INFO"]),
                    "code_smells": data.code_smells,
                    "bugs": data.bugs,
                    "vulnerabilities": data.vulnerabilities
                },
                "ai_model_used": "gpt-4o",
                "confidence_score": 0.92
            }
            
        except Exception as e:
            print(f"OpenAI analysis failed: {e}")
            return self._rule_based_analysis(data)

    def _prepare_issues_for_ai(self, issues: List[SonarQubeIssue]) -> str:
        """
        Prepare a concise summary of issues for AI analysis
        """
        if not issues:
            return "No issues found in the project."
        
        # Group issues by severity, rule, and components
        severity_counts = Counter(issue.severity for issue in issues)
        rule_counts = Counter(issue.rule for issue in issues)
        component_counts = Counter(issue.component for issue in issues)
        
        summary = f"""
        ISSUE BREAKDOWN:
        Total Issues: {len(issues)}
        
        By Severity: {dict(severity_counts)}
        
        Most Frequent Rules:
        {dict(rule_counts.most_common(10))}
        
        Most Problematic Files:
        {dict(component_counts.most_common(5))}
        """
        
        return summary

    def _analyze_top_problems(self, issues: List[SonarQubeIssue]) -> List[TopProblem]:
        """
        Identify top recurring problems based on rule frequency and severity
        """
        rule_stats = {}
        
        for issue in issues:
            rule = issue.rule
            if rule not in rule_stats:
                rule_stats[rule] = {
                    'count': 0,
                    'severity_scores': [],
                    'sample_message': issue.message
                }
            
            rule_stats[rule]['count'] += 1
            
            # Assign severity scores for impact calculation
            severity_score = {
                'CRITICAL': 5,
                'MAJOR': 4,
                'MINOR': 3,
                'INFO': 2
            }.get(issue.severity, 1)
            
            rule_stats[rule]['severity_scores'].append(severity_score)
        
        # Calculate impact and sort by combined score
        problems = []
        for rule, stats in rule_stats.items():
            avg_severity = sum(stats['severity_scores']) / len(stats['severity_scores'])
            impact_score = stats['count'] * avg_severity
            
            impact_level = "high" if impact_score > 15 else "medium" if impact_score > 8 else "low"
            
            problems.append(TopProblem(
                rule=rule,
                description=stats['sample_message'],
                frequency=stats['count'],
                impact=impact_level
            ))
        
        # Return top 5 problems sorted by frequency
        return sorted(problems, key=lambda x: x.frequency, reverse=True)[:5]

    def _generate_improvement_suggestions(self, issues: List[SonarQubeIssue]) -> List[SuggestedImprovement]:
        """
        Generate improvement suggestions based on issue patterns
        """
        suggestions = []
        
        # Analyze issue patterns
        severity_counts = Counter(issue.severity for issue in issues)
        type_counts = Counter(issue.type for issue in issues)
        
        # Security suggestions
        if any(issue.type == "VULNERABILITY" for issue in issues):
            suggestions.append(SuggestedImprovement(
                category="Security",
                suggestion="Address security vulnerabilities immediately. Review authentication, input validation, and sensitive data handling.",
                priority="high"
            ))
        
        # Code quality suggestions
        if severity_counts.get("CRITICAL", 0) > 5:
            suggestions.append(SuggestedImprovement(
                category="Code Quality",
                suggestion="Focus on resolving critical issues first. These often indicate fundamental design problems.",
                priority="high"
            ))
        
        # Maintainability suggestions
        if type_counts.get("CODE_SMELL", 0) > 10:
            suggestions.append(SuggestedImprovement(
                category="Maintainability",
                suggestion="Refactor code to reduce technical debt. Focus on duplicated code, complex methods, and poor naming conventions.",
                priority="medium"
            ))
        
        return suggestions

    def _prioritize_issues(self, issues: List[SonarQubeIssue]) -> List[PrioritizedIssue]:
        """
        Prioritize issues based on severity and type
        """
        # Group issues by rule to count occurrences
        rule_groups = {}
        for issue in issues:
            if issue.rule not in rule_groups:
                rule_groups[issue.rule] = {
                    'issues': [],
                    'files': set()
                }
            rule_groups[issue.rule]['issues'].append(issue)
            rule_groups[issue.rule]['files'].add(issue.component)
        
        prioritized = []
        for rule, group in rule_groups.items():
            # Take the highest severity issue as representative
            representative = max(group['issues'], key=lambda x: {
                'CRITICAL': 4, 'MAJOR': 3, 'MINOR': 2, 'INFO': 1
            }.get(x.severity, 0))
            
            prioritized.append(PrioritizedIssue(
                rule=rule,
                message=representative.message,
                severity=representative.severity,
                files_affected=len(group['files'])
            ))
        
        # Sort by severity and number of affected files
        severity_order = {'CRITICAL': 4, 'MAJOR': 3, 'MINOR': 2, 'INFO': 1}
        return sorted(prioritized, 
                     key=lambda x: (severity_order.get(x.severity, 0), x.files_affected),
                     reverse=True)[:10]

    def _generate_summary(self, data: SonarQubeData, top_problems: List[TopProblem], improvements: List[SuggestedImprovement]) -> str:
        """
        Generate a comprehensive summary of the analysis
        """
        if not data.issues:
            return "No issues found in the project. The code quality appears to be excellent!"
        
        severity_counts = Counter(issue.severity for issue in data.issues)
        
        summary = f"""
        ## Code Quality Analysis Summary
        
        **Overall Health**: {self._calculate_health_score(data)}
        
        **Issue Distribution**:
        - Total Issues: {data.total_issues}
        - Critical: {severity_counts.get('CRITICAL', 0)}
        - Major: {severity_counts.get('MAJOR', 0)}
        - Minor: {severity_counts.get('MINOR', 0)}
        - Info: {severity_counts.get('INFO', 0)}
        
        **Issue Types**:
        - Bugs: {data.bugs}
        - Vulnerabilities: {data.vulnerabilities}
        - Code Smells: {data.code_smells}
        
        **Key Concerns**:
        """
        
        for problem in top_problems[:3]:
            summary += f"\n- {problem.rule}: {problem.description} (appears {problem.frequency} times)"
        
        summary += "\n\n**Recommended Actions**:"
        for improvement in improvements[:3]:
            summary += f"\n- [{improvement.priority.upper()}] {improvement.suggestion}"
        
        return summary

    def _calculate_health_score(self, data: SonarQubeData) -> str:
        """
        Calculate a simple health score based on issue distribution
        """
        if data.total_issues == 0:
            return "Excellent"
        
        critical_ratio = data.bugs + data.vulnerabilities
        if critical_ratio > data.total_issues * 0.1:  # More than 10% critical
            return "Poor"
        elif critical_ratio > data.total_issues * 0.05:  # More than 5% critical
            return "Fair"
        elif data.total_issues > 50:
            return "Good"
        else:
            return "Very Good"

    async def save_analysis_report(self, analysis_request_id: int, analysis_result: Dict[str, Any], db: Session):
        """
        Save the analysis report to the database
        """
        try:
            # Extract metrics
            metrics = analysis_result.get("metrics", {})
            
            # Create AI report record
            ai_report = AIReport(
                analysis_request_id=analysis_request_id,
                summary=analysis_result.get("summary", ""),
                top_recurring_problems=json.dumps([problem.__dict__ if hasattr(problem, '__dict__') 
                                                 else problem for problem in analysis_result.get("top_recurring_problems", [])]),
                suggested_improvements=json.dumps([improvement.__dict__ if hasattr(improvement, '__dict__')
                                                 else improvement for improvement in analysis_result.get("suggested_improvements", [])]),
                prioritized_issues=json.dumps([issue.__dict__ if hasattr(issue, '__dict__')
                                             else issue for issue in analysis_result.get("prioritized_issues", [])]),
                total_issues=metrics.get("total_issues", 0),
                critical_issues=metrics.get("critical_issues", 0),
                major_issues=metrics.get("major_issues", 0),
                minor_issues=metrics.get("minor_issues", 0),
                code_smells=metrics.get("code_smells", 0),
                bugs=metrics.get("bugs", 0),
                vulnerabilities=metrics.get("vulnerabilities", 0),
                ai_model_used=analysis_result.get("ai_model_used", "unknown"),
                confidence_score=analysis_result.get("confidence_score", 0.0),
                created_at=datetime.utcnow()
            )
            
            db.add(ai_report)
            db.commit()
            db.refresh(ai_report)
            
            # Update analysis request status
            analysis_request = db.query(AnalysisRequest).filter(
                AnalysisRequest.id == analysis_request_id
            ).first()
            
            if analysis_request:
                analysis_request.status = "completed"
                analysis_request.completed_at = datetime.utcnow()
                db.commit()
            
            return ai_report
            
        except Exception as e:
            db.rollback()
            print(f"Error saving analysis report: {e}")
            
            # Update analysis request status to failed
            analysis_request = db.query(AnalysisRequest).filter(
                AnalysisRequest.id == analysis_request_id
            ).first()
            
            if analysis_request:
                analysis_request.status = "failed"
                db.commit()
            
            raise e


# Create singleton instance
ai_analysis_service = AIAnalysisService()