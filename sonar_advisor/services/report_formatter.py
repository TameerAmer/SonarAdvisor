import json
from typing import Dict, Any
from datetime import datetime
from jinja2 import Template

class ReportFormatter:
    """
    Service to format analysis reports in user-friendly formats
    """
    
    def __init__(self):
        self.html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SonarQube AI Analysis Report - {{ project_key }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .content {
            padding: 30px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #667eea;
        }
        .metric-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            margin: 0;
        }
        .metric-label {
            color: #666;
            margin: 5px 0 0 0;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 1px;
        }
        .critical { border-left-color: #dc3545; }
        .major { border-left-color: #fd7e14; }
        .minor { border-left-color: #ffc107; }
        .bugs { border-left-color: #e74c3c; }
        .vulnerabilities { border-left-color: #8e44ad; }
        .code-smells { border-left-color: #3498db; }
        
        .section {
            margin: 40px 0;
        }
        .section h2 {
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .priority-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        .priority-critical { background: #dc3545; color: white; }
        .priority-high { background: #fd7e14; color: white; }
        .priority-medium { background: #ffc107; color: black; }
        .severity-critical { background: #dc3545; color: white; }
        .severity-major { background: #fd7e14; color: white; }
        .severity-minor { background: #28a745; color: white; }
        
        .problem-item, .improvement-item, .issue-item {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }
        .problem-header, .improvement-header, .issue-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 10px;
        }
        .problem-title, .improvement-title, .issue-title {
            font-weight: bold;
            font-size: 1.1em;
            margin: 0;
        }
        .count-badge {
            background: #667eea;
            color: white;
            padding: 4px 8px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-left: 10px;
        }
        .description {
            color: #666;
            margin: 10px 0;
        }
        .file-location {
            font-family: 'Courier New', monospace;
            background: #e9ecef;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.9em;
            color: #495057;
        }
        .affected-files {
            margin-top: 10px;
        }
        .affected-files span {
            display: inline-block;
            background: #e9ecef;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin: 2px;
        }
        .summary-text {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            white-space: pre-line;
            line-height: 1.8;
        }
        .ai-info {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            margin-top: 30px;
        }
        .score {
            font-size: 1.2em;
            font-weight: bold;
        }
        
        /* New styles for file grouping and AI suggestions */
        .file-group {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #6c757d;
        }
        .file-group h4 {
            margin: 0 0 10px 0;
            color: #333;
            font-family: 'Courier New', monospace;
        }
        .severity-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }
        .severity-count {
            text-align: center;
            padding: 8px;
            border-radius: 4px;
            font-size: 0.9em;
        }
        .ai-suggestion {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 12px;
            margin: 8px 0;
            border-radius: 4px;
        }
        .ai-suggestion strong {
            color: #1976d2;
        }
        .issue-with-suggestion {
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .issue-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .issue-rule {
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            color: #666;
        }
        .issue-location {
            font-size: 0.8em;
            color: #888;
        }
        
        @media (max-width: 768px) {
            .summary-grid {
                grid-template-columns: 1fr;
            }
            .problem-header, .improvement-header, .issue-header {
                flex-direction: column;
                align-items: flex-start;
            }
            .count-badge {
                margin-left: 0;
                margin-top: 5px;
            }
            .severity-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Code Quality Analysis Report</h1>
            <p>Project: <strong>{{ project_key }}</strong> | Generated: {{ generated_at }} | AI Model: {{ ai_model }}</p>
        </div>
        
        <div class="content">
            <!-- Summary Metrics -->
            <div class="summary-grid">
                <div class="metric-card critical">
                    <div class="metric-number">{{ metrics.critical_issues }}</div>
                    <div class="metric-label">Critical Issues</div>
                </div>
                <div class="metric-card major">
                    <div class="metric-number">{{ metrics.major_issues }}</div>
                    <div class="metric-label">Major Issues</div>
                </div>
                <div class="metric-card minor">
                    <div class="metric-number">{{ metrics.minor_issues }}</div>
                    <div class="metric-label">Minor Issues</div>
                </div>
                <div class="metric-card bugs">
                    <div class="metric-number">{{ metrics.bugs }}</div>
                    <div class="metric-label">Bugs</div>
                </div>
                <div class="metric-card vulnerabilities">
                    <div class="metric-number">{{ metrics.vulnerabilities }}</div>
                    <div class="metric-label">Vulnerabilities</div>
                </div>
                <div class="metric-card code-smells">
                    <div class="metric-number">{{ metrics.code_smells }}</div>
                    <div class="metric-label">Code Smells</div>
                </div>
            </div>
            
            <!-- AI Summary -->
            <div class="section">
                <h2>📋 Executive Summary</h2>
                <div class="summary-text">{{ summary }}</div>
            </div>
            
            <!-- Top Problems -->
            <div class="section">
                <h2>🔍 Top Recurring Problems</h2>
                {% for problem in top_problems %}
                <div class="problem-item">
                    <div class="problem-header">
                        <div class="problem-title">{{ problem.get('rule', problem.get('rule_name', 'Unknown Rule')) }}</div>
                        <div>
                            <span class="severity-{{ problem.get('impact', 'unknown').lower() }} priority-badge">{{ problem.get('impact', 'Unknown') }}</span>
                            <span class="count-badge">{{ problem.get('frequency', 0) }} occurrences</span>
                        </div>
                    </div>
                    <div class="description">{{ problem.get('description', 'No description available') }}</div>
                    <div class="file-location">Rule: {{ problem.get('rule', 'Unknown') }}</div>
                </div>
                {% endfor %}
            </div>
            
            <!-- Improvement Suggestions -->
            <div class="section">
                <h2>💡 Suggested Improvements</h2>
                {% for improvement in improvements %}
                <div class="improvement-item">
                    <div class="improvement-header">
                        <div class="improvement-title">{{ improvement.get('category', 'General') }}</div>
                        <span class="priority-{{ improvement.get('priority', 'medium').lower() }} priority-badge">{{ improvement.get('priority', 'Medium') }}</span>
                    </div>
                    <div class="description">{{ improvement.get('suggestion', 'No suggestion available') }}</div>
                    <div class="affected-files">
                        <strong>Priority:</strong> {{ improvement.get('priority', 'Medium') }}
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <!-- Prioritized Issues -->
            <div class="section">
                <h2>⚡ Top Priority Issues</h2>
                {% for issue in prioritized_issues[:10] %}
                <div class="issue-item">
                    <div class="issue-header">
                        <div class="issue-title">{{ issue.get('rule', 'Unknown Rule') }} - {{ issue.get('severity', 'Unknown') }}</div>
                        <span class="score">Files affected: {{ issue.get('files_affected', 0) }}</span>
                    </div>
                    <div class="description">{{ issue.get('message', 'No message available') }}</div>
                    <div class="file-location">Rule: {{ issue.get('rule', 'Unknown') }}</div>
                </div>
                {% endfor %}
            </div>
            
            <!-- AI Information -->
            <div class="ai-info">
                <div>Analysis powered by AI Model: <span class="score">{{ ai_model }}</span></div>
                <div>Confidence Score: <span class="score">{{ confidence_score }}%</span></div>
            </div>
            
            <!-- File Grouping Section -->
            {% if grouped_by_file %}
            <div class="section">
                <h2>📁 Issues by File</h2>
                <p>Issues organized by file location with severity breakdown:</p>
                {% for file_path, file_data in grouped_by_file.items() %}
                <div class="file-group">
                    <h4>{{ file_data.file_name }}</h4>
                    <p style="font-size: 0.9em; color: #666; margin: 5px 0;">{{ file_path }}</p>
                    <div><strong>Total Issues:</strong> {{ file_data.total_issues }}</div>
                    <div class="severity-grid">
                        {% if file_data.critical > 0 %}
                        <div class="severity-count critical">
                            <strong>{{ file_data.critical }}</strong><br>Critical
                        </div>
                        {% endif %}
                        {% if file_data.major > 0 %}
                        <div class="severity-count major">
                            <strong>{{ file_data.major }}</strong><br>Major
                        </div>
                        {% endif %}
                        {% if file_data.minor > 0 %}
                        <div class="severity-count minor">
                            <strong>{{ file_data.minor }}</strong><br>Minor
                        </div>
                        {% endif %}
                        {% if file_data.info > 0 %}
                        <div class="severity-count">
                            <strong>{{ file_data.info }}</strong><br>Info
                        </div>
                        {% endif %}
                    </div>
                    {% if file_data.bugs > 0 or file_data.vulnerabilities > 0 or file_data.code_smells > 0 %}
                    <div style="margin-top: 10px; font-size: 0.9em;">
                        <span style="color: #e74c3c;">🐛 {{ file_data.bugs }} Bugs</span> | 
                        <span style="color: #8e44ad;">🔒 {{ file_data.vulnerabilities }} Vulnerabilities</span> | 
                        <span style="color: #3498db;">🏠 {{ file_data.code_smells }} Code Smells</span>
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <!-- AI Fix Suggestions Section -->
            {% if issues_with_suggestions %}
            <div class="section">
                <h2>🤖 AI-Powered Fix Suggestions</h2>
                <p>Specific, actionable fix recommendations for individual issues:</p>
                {% for issue in issues_with_suggestions[:10] %}
                <div class="issue-with-suggestion">
                    <div class="issue-header">
                        <div>
                            <span class="priority-badge severity-{{ issue.get('severity', 'unknown').lower() }}">{{ issue.get('severity', 'Unknown') }}</span>
                            <span class="issue-rule">{{ issue.get('rule', 'Unknown Rule') }}</span>
                        </div>
                        <div class="issue-location">{{ issue.get('component', 'Unknown file') }}{% if issue.get('line') %}:{{ issue.get('line') }}{% endif %}</div>
                    </div>
                    <div><strong>Issue:</strong> {{ issue.get('message', 'No message available') }}</div>
                    <div class="ai-suggestion">
                        <strong>💡 AI Fix Suggestion:</strong><br>
                        {{ issue.get('ai_fix_suggestion', 'No AI suggestion available') }}
                    </div>
                </div>
                {% endfor %}
                {% if issues_with_suggestions|length > 10 %}
                <div style="text-align: center; margin-top: 20px; color: #666;">
                    ... and {{ issues_with_suggestions|length - 10 }} more issues with AI suggestions
                </div>
                {% endif %}
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
        """
    
    def format_html_report(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate a beautiful HTML report from analysis data
        """
        template = Template(self.html_template)
        
        # Extract data
        request_data = analysis_data.get('request', {})
        report_data = analysis_data.get('report', {})
        
        if not report_data:
            return "<html><body><h1>No report data available</h1></body></html>"
        
        # Parse JSON fields
        top_problems = json.loads(report_data.get('top_recurring_problems', '[]'))
        improvements = json.loads(report_data.get('suggested_improvements', '[]'))
        prioritized_issues = json.loads(report_data.get('prioritized_issues', '[]'))
        grouped_by_file = json.loads(report_data.get('grouped_by_file', '{}'))
        issues_with_suggestions = json.loads(report_data.get('issues_with_suggestions', '[]'))
        
        # Prepare template data
        template_data = {
            'project_key': request_data.get('project_key', 'Unknown'),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ai_model': report_data.get('ai_model_used', 'Unknown'),
            'summary': report_data.get('summary', 'No summary available'),
            'metrics': {
                'critical_issues': report_data.get('critical_issues', 0),
                'major_issues': report_data.get('major_issues', 0),
                'minor_issues': report_data.get('minor_issues', 0),
                'bugs': report_data.get('bugs', 0),
                'vulnerabilities': report_data.get('vulnerabilities', 0),
                'code_smells': report_data.get('code_smells', 0),
            },
            'top_problems': top_problems,
            'improvements': improvements,
            'prioritized_issues': prioritized_issues,
            'grouped_by_file': grouped_by_file,
            'issues_with_suggestions': issues_with_suggestions,
            'confidence_score': int((report_data.get('confidence_score', 0) * 100))
        }
        
        return template.render(**template_data)
    
    def format_markdown_report(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate a markdown report from analysis data
        """
        request_data = analysis_data.get('request', {})
        report_data = analysis_data.get('report', {})
        
        if not report_data:
            return "# No report data available"
        
        # Parse JSON fields
        top_problems = json.loads(report_data.get('top_recurring_problems', '[]'))
        improvements = json.loads(report_data.get('suggested_improvements', '[]'))
        prioritized_issues = json.loads(report_data.get('prioritized_issues', '[]'))
        grouped_by_file = json.loads(report_data.get('grouped_by_file', '{}'))
        issues_with_suggestions = json.loads(report_data.get('issues_with_suggestions', '[]'))
        
        md_content = f"""# 🎯 Code Quality Analysis Report
        
**Project:** {request_data.get('project_key', 'Unknown')}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**AI Model:** {report_data.get('ai_model_used', 'Unknown')}  
**Confidence:** {int(report_data.get('confidence_score', 0) * 100)}%

## 📊 Summary Metrics

| Metric | Count |
|--------|-------|
| Critical Issues | **{report_data.get('critical_issues', 0)}** |
| Major Issues | {report_data.get('major_issues', 0)} |
| Minor Issues | {report_data.get('minor_issues', 0)} |
| Bugs | {report_data.get('bugs', 0)} |
| Vulnerabilities | {report_data.get('vulnerabilities', 0)} |
| Code Smells | {report_data.get('code_smells', 0)} |

## 📋 Executive Summary

{report_data.get('summary', 'No summary available')}

## 🔍 Top Recurring Problems

"""
        
        for i, problem in enumerate(top_problems, 1):
            md_content += f"""### {i}. {problem.get('rule_name', 'Unknown')} 
- **Severity:** {problem.get('severity', 'Unknown')}
- **Occurrences:** {problem.get('count', 0)}
- **Rule:** `{problem.get('rule_key', 'Unknown')}`
- **Description:** {problem.get('description', 'No description')}

"""
        
        md_content += "## 💡 Suggested Improvements\n\n"
        
        for i, improvement in enumerate(improvements, 1):
            files_list = ', '.join(improvement.get('affected_files', [])[:3])
            if len(improvement.get('affected_files', [])) > 3:
                files_list += "..."
                
            md_content += f"""### {i}. {improvement.get('category', 'Unknown')} ({improvement.get('priority', 'Unknown')} Priority)
{improvement.get('description', 'No description')}

**Affected Files:** {files_list}

"""
        
        md_content += "## ⚡ Top Priority Issues\n\n"
        
        for i, issue in enumerate(prioritized_issues[:10], 1):
            md_content += f"""### {i}. {issue.get('type', 'Unknown')} - {issue.get('severity', 'Unknown')}
- **Priority Score:** {issue.get('priority_score', 0):.1f}
- **File:** `{issue.get('component', 'Unknown')}`{f":{issue.get('line')}" if issue.get('line') else ""}
- **Message:** {issue.get('message', 'No message')}
- **Reasoning:** {issue.get('reasoning', 'No reasoning')}

"""
        
        # Add file grouping section
        if grouped_by_file:
            md_content += "## 📁 Issues by File\n\n"
            for file_path, file_data in grouped_by_file.items():
                md_content += f"### {file_data['file_name']}\n"
                md_content += f"**Path:** `{file_path}`\n\n"
                md_content += f"**Total Issues:** {file_data['total_issues']}\n\n"
                
                # Severity breakdown
                severity_parts = []
                if file_data.get('critical', 0) > 0:
                    severity_parts.append(f"🔴 {file_data['critical']} Critical")
                if file_data.get('major', 0) > 0:
                    severity_parts.append(f"🟠 {file_data['major']} Major")
                if file_data.get('minor', 0) > 0:
                    severity_parts.append(f"🟡 {file_data['minor']} Minor")
                if file_data.get('info', 0) > 0:
                    severity_parts.append(f"ℹ️ {file_data['info']} Info")
                
                if severity_parts:
                    md_content += f"**Severity Breakdown:** {' | '.join(severity_parts)}\n\n"
                
                # Type breakdown
                type_parts = []
                if file_data.get('bugs', 0) > 0:
                    type_parts.append(f"🐛 {file_data['bugs']} Bugs")
                if file_data.get('vulnerabilities', 0) > 0:
                    type_parts.append(f"🔒 {file_data['vulnerabilities']} Vulnerabilities")
                if file_data.get('code_smells', 0) > 0:
                    type_parts.append(f"🏠 {file_data['code_smells']} Code Smells")
                
                if type_parts:
                    md_content += f"**Type Breakdown:** {' | '.join(type_parts)}\n\n"
                
                md_content += "---\n\n"
        
        # Add AI suggestions section
        if issues_with_suggestions:
            md_content += "## 🤖 AI-Powered Fix Suggestions\n\n"
            for i, issue in enumerate(issues_with_suggestions[:10], 1):
                md_content += f"### {i}. {issue['severity']} - {issue['rule']}\n"
                file_location = f":{issue['line']}" if issue.get('line') else ""
                md_content += f"**File:** `{issue['component']}{file_location}`\n\n"
                md_content += f"**Issue:** {issue['message']}\n\n"
                md_content += f"**💡 AI Fix Suggestion:**\n{issue['ai_fix_suggestion']}\n\n"
                md_content += "---\n\n"
            
            if len(issues_with_suggestions) > 10:
                md_content += f"*... and {len(issues_with_suggestions) - 10} more issues with AI suggestions*\n\n"
        
        return md_content


# Create singleton instance
report_formatter = ReportFormatter()