import json
import openai
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from sonar_advisor.core.config import settings
from sonar_advisor.models.analysis_request import AnalysisRequest
from sonar_advisor.models.ai_report import AIReport
from sonar_advisor.schemas.analysis import (
    SonarQubeData, SonarQubeIssue, TopProblem, 
    SuggestedImprovement, PrioritizedIssue
)

# Check if OpenAI is available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

import logging
logger = logging.getLogger(__name__)


class AIAnalysisService:
    """
    AI-powered analysis service for SonarQube data
    Enhanced with priority-based sorting and action-oriented recommendations
    """
    
    # Priority mapping: Security > Correctness > Maintainability
    RULE_PRIORITY_MAP = {
        # Security rules (highest priority)
        "security": {
            "python:S2092", "python:S5542", "python:S4426", "python:S5443", 
            "python:S2245", "python:S5445", "python:S4423", "python:S5659",
            "python:S2078", "python:S1313", "python:S5122"
        },
        # Correctness/Bug rules (medium-high priority)
        "correctness": {
            "python:S1764", "python:S1066", "python:S1862", "python:S1854",
            "python:S1481", "python:S1172", "python:S108", "python:S1871",
            "python:S5756", "python:S930", "python:S5727"
        },
        # Maintainability rules (lower priority)
        "maintainability": {
            "python:S1192", "python:S7503", "python:S1134", "python:S125",
            "python:S101", "python:S107", "python:S1542", "python:S1821",
            "python:S3776", "python:S3358", "python:S6903", "javascript:S2486"
        }
    }
    
    # Code fix templates for common rules
    CODE_FIX_TEMPLATES = {
        "python:S1192": {
            "name": "String Literal Duplication",
            "before": '''
def process_error():
    if condition1:
        return "Analysis request not found"
    elif condition2:
        return "Analysis request not found"
    else:
        return "Analysis request not found"
''',
            "after": '''
# Define constant at module level
ERROR_MESSAGE = "Analysis request not found"

def process_error():
    if condition1:
        return ERROR_MESSAGE
    elif condition2:
        return ERROR_MESSAGE
    else:
        return ERROR_MESSAGE
''',
            "steps": [
                "Identify all duplicate string literals",
                "Define a module-level constant",
                "Replace all occurrences with the constant",
                "Use UPPER_CASE naming for constants"
            ]
        },
        "python:S7503": {
            "name": "Unnecessary async keyword",
            "before": '''
async def get_data():
    # No await calls in function
    return process_sync_data()
''',
            "after": '''
def get_data():
    # Removed async since no await is used
    return process_sync_data()
''',
            "steps": [
                "Check if function uses 'await' anywhere",
                "If no 'await' found, remove 'async' keyword",
                "Update function callers to not use 'await'",
                "Consider if function should be async for consistency"
            ]
        },
        "python:S6903": {
            "name": "Replace datetime.utcnow()",
            "before": '''
from datetime import datetime

def create_timestamp():
    return datetime.utcnow()
''',
            "after": '''
from datetime import datetime, timezone

def create_timestamp():
    return datetime.now(timezone.utc)
''',
            "steps": [
                "Import timezone from datetime module",
                "Replace datetime.utcnow() with datetime.now(timezone.utc)",
                "Ensure timezone awareness in all datetime operations",
                "Test that timezone information is preserved"
            ]
        },
        "python:S3776": {
            "name": "Reduce Cognitive Complexity",
            "before": '''
def complex_function(data):
    if data:
        if len(data) > 0:
            for item in data:
                if item.valid:
                    if item.type == 'A':
                        # many nested conditions...
                        return process_type_a(item)
                    elif item.type == 'B':
                        return process_type_b(item)
    return None
''',
            "after": '''
def complex_function(data):
    if not data or len(data) == 0:
        return None
    
    for item in data:
        if not item.valid:
            continue
        return _process_item_by_type(item)
    
    return None

def _process_item_by_type(item):
    """Extract type processing into separate function"""
    if item.type == 'A':
        return process_type_a(item)
    elif item.type == 'B':
        return process_type_b(item)
    return None
''',
            "steps": [
                "Extract nested logic into separate functions",
                "Use early returns to reduce nesting",
                "Replace nested if-else with guard clauses",
                "Break down complex conditions into named variables"
            ]
        }
    }
    
    def __init__(self):
        self.model_type = settings.ai_model_type
    
    def _get_issue_priority_score(self, issue: SonarQubeIssue) -> int:
        """Calculate priority score: Security=100, Correctness=75, Maintainability=50, plus severity bonus"""
        base_score = 25  # Default for unknown rules
        
        if issue.rule in self.RULE_PRIORITY_MAP["security"]:
            base_score = 100
        elif issue.rule in self.RULE_PRIORITY_MAP["correctness"]:
            base_score = 75
        elif issue.rule in self.RULE_PRIORITY_MAP["maintainability"]:
            base_score = 50
        
        # Add severity bonus
        severity_bonus = {
            "CRITICAL": 25,
            "BLOCKER": 30,
            "MAJOR": 15,
            "MINOR": 5,
            "INFO": 0
        }.get(issue.severity, 0)
        
        return base_score + severity_bonus
    
    def _get_issue_category(self, issue: SonarQubeIssue) -> str:
        """Get issue category for prioritization"""
        if issue.rule in self.RULE_PRIORITY_MAP["security"]:
            return "security"
        elif issue.rule in self.RULE_PRIORITY_MAP["correctness"]:
            return "correctness"
        else:
            return "maintainability"

    def analyze_issues(self, sonarqube_data: SonarQubeData, project_key: str = None) -> Dict[str, Any]:
        """
        Main analysis method with priority-based sorting and enhanced recommendations
        """
        # Sort issues by priority score
        sorted_issues = sorted(sonarqube_data.issues, key=self._get_issue_priority_score, reverse=True)
        
        # Group issues by file and category
        file_groups = {}
        category_counts = {"security": 0, "correctness": 0, "maintainability": 0}
        
        for issue in sorted_issues:
            # Extract file path, handle cases with or without project key prefix
            file_path = issue.component
            if project_key and file_path.startswith(f"{project_key}:"):
                file_path = file_path.replace(f"{project_key}:", "")
            
            category = self._get_issue_category(issue)
            
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append({
                "issue": issue,
                "category": category,
                "priority_score": self._get_issue_priority_score(issue)
            })
            category_counts[category] += 1
        
        # Identify top priority files (most critical issues)
        file_priorities = {}
        for file_path, file_issues in file_groups.items():
            total_score = sum(item["priority_score"] for item in file_issues)
            critical_count = len([item for item in file_issues if item["priority_score"] >= 100])
            file_priorities[file_path] = {
                "total_score": total_score,
                "critical_count": critical_count,
                "issue_count": len(file_issues),
                "issues": file_issues
            }
        
        # Sort files by priority
        top_files = sorted(file_priorities.items(), 
                          key=lambda x: (x[1]["critical_count"], x[1]["total_score"]), 
                          reverse=True)[:5]  # Top 5 files
        
        if self.model_type == "rule_based":
            return self._rule_based_analysis_enhanced(sonarqube_data, sorted_issues, file_groups, top_files, category_counts, project_key)
        elif self.model_type == "openai":
            return self._openai_analysis_enhanced(sonarqube_data, sorted_issues, file_groups, top_files, category_counts, project_key)
        else:
            # Fallback to rule-based
            return self._rule_based_analysis_enhanced(sonarqube_data, sorted_issues, file_groups, top_files, category_counts, project_key)

    def _rule_based_analysis_enhanced(self, data: SonarQubeData, sorted_issues, file_groups, top_files, category_counts, project_key=None) -> Dict[str, Any]:
        """
        Enhanced rule-based analysis with priority-based sorting
        """
        # Analyze top recurring problems with priority
        top_problems = self._analyze_top_problems_enhanced(sorted_issues)
        
        # Generate improvement suggestions based on priority files
        improvements = self._generate_improvement_suggestions_enhanced(top_files)
        
        # Prioritize critical issues
        prioritized_issues = self._prioritize_issues_enhanced(sorted_issues)
        
        # Generate enhanced summary
        summary = self._generate_summary_enhanced(data, top_problems, improvements, category_counts, project_key)
        
        # Generate enhanced analysis structure
        enhanced_analysis = self._generate_rule_based_enhanced_analysis(sorted_issues, file_groups, top_files)
        
        # Calculate metrics
        critical_issues = sum(1 for issue in data.issues if issue.severity == "CRITICAL")
        major_issues = sum(1 for issue in data.issues if issue.severity == "MAJOR")
        minor_issues = sum(1 for issue in data.issues if issue.severity in ["MINOR", "INFO"])
        
        return {
            "summary": summary,
            "top_recurring_problems": top_problems,
            "suggested_improvements": improvements,
            "prioritized_issues": prioritized_issues,
            "priority_analysis": {
                "total_issues": len(data.issues),
                "security_issues": category_counts["security"],
                "correctness_issues": category_counts["correctness"],
                "maintainability_issues": category_counts["maintainability"],
                "top_files": [{"file": f[0], "score": f[1]["total_score"], "issues": f[1]["issue_count"]} for f in top_files]
            },
            "enhanced_analysis": enhanced_analysis,
            "metrics": {
                "total_issues": data.total_issues,
                "critical_issues": critical_issues,
                "major_issues": major_issues,
                "minor_issues": minor_issues,
                "code_smells": data.code_smells,
                "bugs": data.bugs,
                "vulnerabilities": data.vulnerabilities
            },
            "ai_model_used": "rule_based_enhanced_v2.0",
            "confidence_score": 0.90
        }

    def _openai_analysis_enhanced(self, data: SonarQubeData, sorted_issues, file_groups, top_files, category_counts, project_key=None):
        """Enhanced OpenAI analysis with priority-based context"""
        if not OPENAI_AVAILABLE:
            return self._rule_based_analysis_enhanced(data, sorted_issues, file_groups, top_files, category_counts, project_key)
        
        try:
            client = openai.OpenAI(api_key=settings.openai_api_key)
            
            # Prepare enhanced prompt with priority context
            issues_data = self._prepare_issues_for_ai_enhanced(sorted_issues, file_groups, top_files, category_counts)
            
            project_name = project_key or "Unknown Project"
            
            # Get code templates for common rules
            common_rules = set(issue.rule for issue in sorted_issues[:10])
            relevant_templates = {rule: template for rule, template in self.CODE_FIX_TEMPLATES.items() 
                                if rule in common_rules}
            
            prompt = f"""
            You are an expert code quality analyst. Analyze the following SonarQube issues for project {project_name}.

            **Priority Context:**
            - Security issues: {category_counts['security']} (CRITICAL PRIORITY)
            - Correctness issues: {category_counts['correctness']} (HIGH PRIORITY) 
            - Maintainability issues: {category_counts['maintainability']} (MEDIUM PRIORITY)

            **Top Priority Files:**
            {self._format_top_files_for_ai(top_files)}

            **Available Code Fix Templates:**
            {self._format_code_templates(relevant_templates)}

            **Issues Data:**
            {issues_data}

            Use the code fix templates when available. Provide concrete, actionable fix instructions with code examples.

            Please provide a JSON response with this structure:
            {{
                "file_analysis": [
                    {{
                        "file_path": "string",
                        "priority_score": number,
                        "issue_count": number,
                        "top_issues": ["issue descriptions"],
                        "fix_instructions": ["step by step instructions with code examples"],
                        "related_files": ["list of related files that might be affected"]
                    }}
                ],
                "top_priority_fixes": [
                    {{
                        "rule": "string", 
                        "category": "security|correctness|maintainability",
                        "description": "string",
                        "impact": "string",
                        "fix_steps": ["concrete steps with code examples"],
                        "code_example": "before/after code if available"
                    }}
                ],
                "quick_wins": [
                    {{
                        "description": "string",
                        "files_affected": number,
                        "effort": "LOW|MEDIUM|HIGH",
                        "template_available": boolean
                    }}
                ]
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000
            )
            
            # Parse AI response
            ai_content = response.choices[0].message.content
            if ai_content.startswith('```json'):
                ai_content = ai_content.replace('```json', '').replace('```', '').strip()
            
            enhanced_analysis = json.loads(ai_content)
            
            # Generate backwards-compatible summary and recommendations
            summary = self._generate_summary_from_ai_analysis(enhanced_analysis, category_counts, data, project_key)
            recommendations = self._generate_recommendations_from_ai_analysis(enhanced_analysis)
            prioritized_issues = self._prioritize_issues_enhanced(sorted_issues)
            
            return {
                "summary": summary,
                "top_recurring_problems": self._analyze_top_problems_enhanced(sorted_issues),
                "suggested_improvements": recommendations,
                "prioritized_issues": prioritized_issues,
                "priority_analysis": {
                    "total_issues": len(data.issues),
                    "security_issues": category_counts["security"],
                    "correctness_issues": category_counts["correctness"],
                    "maintainability_issues": category_counts["maintainability"],
                    "top_files": [{"file": f[0], "score": f[1]["total_score"], "issues": f[1]["issue_count"]} for f in top_files]
                },
                "enhanced_analysis": enhanced_analysis,
                "metrics": {
                    "total_issues": data.total_issues,
                    "critical_issues": sum(1 for issue in data.issues if issue.severity == "CRITICAL"),
                    "major_issues": sum(1 for issue in data.issues if issue.severity == "MAJOR"),
                    "minor_issues": sum(1 for issue in data.issues if issue.severity in ["MINOR", "INFO"]),
                    "code_smells": data.code_smells,
                    "bugs": data.bugs,
                    "vulnerabilities": data.vulnerabilities
                },
                "ai_model_used": "openai_gpt4o_enhanced_v2.0",
                "confidence_score": 0.95
            }
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return self._rule_based_analysis_enhanced(data, sorted_issues, file_groups, top_files, category_counts, project_key)

    # Enhanced analysis helper methods
    def _analyze_top_problems_enhanced(self, sorted_issues):
        """Analyze top problems with priority sorting"""
        problem_counts = {}
        for issue in sorted_issues:
            rule = issue.rule
            if rule not in problem_counts:
                problem_counts[rule] = {
                    "count": 0,
                    "priority_score": self._get_issue_priority_score(issue),
                    "category": self._get_issue_category(issue),
                    "message": issue.message,
                    "affected_files": set()
                }
            problem_counts[rule]["count"] += 1
            if hasattr(issue, 'component') and issue.component:
                problem_counts[rule]["affected_files"].add(issue.component)
        
        # Sort by priority score then by count
        sorted_problems = sorted(problem_counts.items(), 
                               key=lambda x: (x[1]["priority_score"], x[1]["count"]), 
                               reverse=True)
        
        return [
            TopProblem(
                rule=rule,
                description=data["message"],
                frequency=data["count"],
                impact=data["category"],  # Map category to impact
                affected_files=list(data["affected_files"])[:10]  # Limit to 10 files
            )
            for rule, data in sorted_problems[:10]
        ]
    
    def _generate_improvement_suggestions_enhanced(self, top_files):
        """Generate improvements based on priority files"""
        suggestions = []
        
        for file_path, file_data in top_files[:3]:  # Top 3 files
            if file_data["critical_count"] > 0:
                suggestions.append(SuggestedImprovement(
                    category="Security",
                    suggestion=f"Address {file_data['critical_count']} critical security issues in {file_path}",
                    priority="HIGH",
                    affected_files=[file_path]
                ))
            
            if file_data["issue_count"] >= 5:
                suggestions.append(SuggestedImprovement(
                    category="Maintainability",
                    suggestion=f"Refactor {file_path} for better maintainability ({file_data['issue_count']} issues)",
                    priority="MEDIUM",
                    affected_files=[file_path]
                ))
        
        return suggestions
    
    def _prioritize_issues_enhanced(self, sorted_issues):
        """Create prioritized issue list with enhanced scoring"""
        return [
            PrioritizedIssue(
                rule=issue.rule,
                message=issue.message,
                severity=issue.severity,
                files_affected=1,  # Simplified for now
                affected_files=[issue.component] if hasattr(issue, 'component') and issue.component else []
            )
            for issue in sorted_issues[:20]  # Top 20 prioritized issues
        ]
    
    def _generate_summary_enhanced(self, data, top_problems, improvements, category_counts, project_key=None):
        """Generate enhanced summary with priority analysis"""
        total_issues = len(data.issues)
        security_pct = round((category_counts["security"] / total_issues) * 100, 1) if total_issues > 0 else 0
        
        project_name = project_key or "Unknown Project"
        summary = f"Analysis of {project_name} found {total_issues} total issues.\n"
        summary += f"Priority breakdown: {category_counts['security']} security ({security_pct}%), "
        summary += f"{category_counts['correctness']} correctness, {category_counts['maintainability']} maintainability issues.\n"
        
        if category_counts["security"] > 0:
            summary += f"⚠️ CRITICAL: {category_counts['security']} security issues require immediate attention.\n"
        
        if top_problems:
            top_rule = top_problems[0].rule
            summary += f"Most frequent issue: {top_rule} ({top_problems[0].frequency} occurrences).\n"
        
        if improvements:
            summary += f"Recommended actions: {len(improvements)} high-impact improvements identified."
        
        return summary

    def _generate_rule_based_enhanced_analysis(self, sorted_issues, file_groups, top_files):
        """Generate enhanced analysis structure for rule-based analysis"""
        file_analysis = []
        for file_path, file_data in top_files[:5]:
            file_analysis.append({
                "file_path": file_path,
                "priority_score": file_data["total_score"],
                "issue_count": file_data["issue_count"],
                "top_issues": [item["issue"].message for item in file_data["issues"][:3]],
                "fix_instructions": [f"Fix {item['category']} issue: {item['issue'].rule}" for item in file_data["issues"][:3]]
            })
        
        top_priority_fixes = []
        for issue in sorted_issues[:5]:
            if self._get_issue_priority_score(issue) >= 100:
                top_priority_fixes.append({
                    "rule": issue.rule,
                    "category": self._get_issue_category(issue),
                    "description": issue.message,
                    "impact": "High security impact",
                    "fix_steps": [f"Review line {issue.line} in {issue.component}", "Apply security best practices"]
                })
        
        quick_wins = []
        rule_counts = Counter(issue.rule for issue in sorted_issues if self._get_issue_priority_score(issue) < 75)
        for rule, count in rule_counts.most_common(3):
            quick_wins.append({
                "description": f"Fix all {rule} issues",
                "files_affected": count,
                "effort": "LOW"
            })
        
        return {
            "file_analysis": file_analysis,
            "top_priority_fixes": top_priority_fixes,
            "quick_wins": quick_wins
        }

    def _prepare_issues_for_ai_enhanced(self, sorted_issues, file_groups, top_files, category_counts):
        """Prepare issues data for enhanced AI analysis"""
        # Limit to top 20 issues to avoid token limits
        limited_issues = sorted_issues[:20]
        
        issues_data = []
        for issue in limited_issues:
            issues_data.append({
                "rule": issue.rule,
                "severity": issue.severity,
                "message": issue.message,
                "file": issue.component,
                "line": issue.line,
                "category": self._get_issue_category(issue),
                "priority_score": self._get_issue_priority_score(issue)
            })
        
        return json.dumps(issues_data, indent=2)

    def _format_top_files_for_ai(self, top_files):
        """Format top files information for AI prompt"""
        file_info = []
        for file_path, file_data in top_files[:3]:
            file_info.append(f"- {file_path}: {file_data['issue_count']} issues, {file_data['critical_count']} critical")
        return "\n".join(file_info)

    def _format_code_templates(self, relevant_templates):
        """Format code fix templates for AI prompt"""
        if not relevant_templates:
            return "No specific templates available for current issues."
        
        templates_text = []
        for rule, template in relevant_templates.items():
            templates_text.append(f"""
Rule {rule} - {template['name']}:
Steps: {', '.join(template['steps'])}
Before: {template['before'].strip()}
After: {template['after'].strip()}
""")
        return "\n".join(templates_text)

    def _generate_summary_from_ai_analysis(self, enhanced_analysis, category_counts, data, project_key=None):
        """Generate backwards-compatible summary from AI analysis"""
        total_issues = len(data.issues)
        project_name = project_key or "Unknown Project"
        summary = f"AI analysis of {project_name} identified {total_issues} issues with action-oriented recommendations.\n"
        
        if enhanced_analysis.get("file_analysis"):
            top_file = enhanced_analysis["file_analysis"][0]
            summary += f"Priority focus: {top_file['file_path']} ({top_file['issue_count']} issues).\n"
        
        if enhanced_analysis.get("top_priority_fixes"):
            security_fixes = len([f for f in enhanced_analysis["top_priority_fixes"] if f.get("category") == "security"])
            if security_fixes > 0:
                summary += f"⚠️ {security_fixes} critical security fixes identified.\n"
        
        if enhanced_analysis.get("quick_wins"):
            summary += f"{len(enhanced_analysis['quick_wins'])} quick wins available for immediate improvement."
        
        return summary

    def _generate_recommendations_from_ai_analysis(self, enhanced_analysis):
        """Generate backwards-compatible recommendations from AI analysis"""
        recommendations = []
        
        # Convert top priority fixes to recommendations
        for fix in enhanced_analysis.get("top_priority_fixes", [])[:3]:
            recommendations.append(SuggestedImprovement(
                category=fix.get("category", "Security").title(),
                suggestion=fix.get("description", ""),
                priority="HIGH" if fix.get("category") == "security" else "MEDIUM"
            ))
        
        # Convert quick wins to recommendations
        for win in enhanced_analysis.get("quick_wins", [])[:2]:
            recommendations.append(SuggestedImprovement(
                category="Quick Win",
                suggestion=win.get("description", ""),
                priority="LOW"
            ))
        
        return recommendations

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
                enhanced_analysis=json.dumps(analysis_result.get("enhanced_analysis", {})),
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