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
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/tabulator-tables@5.5.2/dist/js/tabulator.min.js"></script>
    <link href="https://unpkg.com/tabulator-tables@5.5.2/dist/css/tabulator.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
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
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
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
        .security { border-left-color: #dc3545; }
        .correctness { border-left-color: #fd7e14; }
        .maintainability { border-left-color: #28a745; }
        
        .charts-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 30px 0;
        }
        .chart-container {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            height: 400px;
        }
        .chart-title {
            text-align: center;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
        }
        
        .heatmap-container {
            margin: 30px 0;
            background: #f8f9fa;
            border-radius: 12px;
            padding: 25px;
        }
        .heatmap-legend {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
            padding: 8px 12px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 50%;
        }
        .file-heatmap {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .file-item {
            padding: 18px;
            border-radius: 12px;
            color: white;
            font-weight: bold;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border: 2px solid transparent;
        }
        .file-item:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.2);
            border-color: rgba(255,255,255,0.3);
        }
        .file-item .file-name {
            display: block;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            margin-bottom: 8px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .file-item .issue-summary {
            font-size: 0.8em;
            opacity: 0.9;
            font-weight: normal;
        }
        .file-critical { background: linear-gradient(135deg, #dc3545, #c82333); }
        .file-high { background: linear-gradient(135deg, #fd7e14, #e06310); }
        .file-medium { background: linear-gradient(135deg, #ffc107, #e0a800); color: #212529; }
        .file-low { background: linear-gradient(135deg, #28a745, #1e7e34); }
        .file-clean { background: linear-gradient(135deg, #6c757d, #545b62); }
        .file-tooltip {
            position: absolute;
            background: #343a40;
            color: white;
            padding: 12px;
            border-radius: 8px;
            font-size: 0.85em;
            z-index: 1000;
            max-width: 350px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s ease;
            left: 50%;
            transform: translateX(-50%);
            bottom: 100%;
            margin-bottom: 8px;
        }
        .file-tooltip::after {
            content: '';
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border: 6px solid transparent;
            border-top-color: #343a40;
        }
        .file-item:hover .file-tooltip {
            opacity: 1;
        }
        
        /* Enhanced Tabulator table styles for File Analysis */
        #fileAnalysisTable {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        #fileAnalysisTable .tabulator-table {
            font-size: 14px;
        }
        #fileAnalysisTable .tabulator-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: bold;
            font-size: 13px;
        }
        #fileAnalysisTable .tabulator-header .tabulator-col {
            border-right: 1px solid rgba(255,255,255,0.2);
        }
        #fileAnalysisTable .tabulator-row {
            border-bottom: 1px solid #f0f0f0;
        }
        #fileAnalysisTable .tabulator-row:hover {
            background: #f8f9fa;
        }
        #fileAnalysisTable .tabulator-cell {
            padding: 12px 8px;
            vertical-align: top;
            line-height: 1.4;
        }
        #fileAnalysisTable .tabulator-row:nth-child(even) {
            background: #fafafa;
        }
        #fileAnalysisTable .tabulator-row:nth-child(even):hover {
            background: #f0f0f0;
        }
        
        .section {
            margin: 40px 0;
        }
        .section h2 {
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section-icon {
            font-size: 1.2em;
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
        
        /* Affected Files Styling */
        .affected-files {
            margin-top: 10px;
            padding: 8px 0;
        }
        .affected-files strong {
            color: #495057;
            font-size: 0.9em;
        }
        .file-list {
            margin-top: 5px;
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        .file-tag {
            background: #e9ecef;
            color: #495057;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-family: 'Courier New', monospace;
            font-weight: 500;
            border: 1px solid #dee2e6;
            display: inline-block;
        }
        .file-tag:hover {
            background: #dee2e6;
            border-color: #adb5bd;
        }
        .more-files {
            color: #6c757d;
            font-size: 0.8em;
            font-style: italic;
            align-self: center;
            padding: 3px 8px;
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
            .file-list {
                flex-direction: column;
                gap: 3px;
            }
            .file-tag {
                align-self: flex-start;
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
                {% if priority_analysis %}
                <div class="metric-card security">
                    <div class="metric-number">{{ priority_analysis.security_issues }}</div>
                    <div class="metric-label">Security Issues</div>
                </div>
                <div class="metric-card correctness">
                    <div class="metric-number">{{ priority_analysis.correctness_issues }}</div>
                    <div class="metric-label">Correctness Issues</div>
                </div>
                <div class="metric-card maintainability">
                    <div class="metric-number">{{ priority_analysis.maintainability_issues }}</div>
                    <div class="metric-label">Maintainability Issues</div>
                </div>
                {% endif %}
            </div>
            
            <!-- Charts Section -->
            <div class="section">
                <h2><span class="section-icon">📊</span>Visual Analysis</h2>
                <div class="charts-grid">
                    <div class="chart-container">
                        <div class="chart-title">Issue Distribution by Severity</div>
                        <canvas id="severityChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <div class="chart-title">Issue Categories by Priority</div>
                        <canvas id="categoryChart"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- File Heatmap -->
            {% if priority_analysis and priority_analysis.top_files %}
            <div class="section">
                <h2><span class="section-icon">🗂️</span>File Priority Heatmap</h2>
                <p>Files colored by issue severity and count. Hover for detailed information.</p>
                <div class="heatmap-container">
                    <div class="heatmap-legend">
                        <div class="legend-item">
                            <div class="legend-color" style="background: linear-gradient(135deg, #dc3545, #c82333);"></div>
                            <span>Critical (200+ score)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: linear-gradient(135deg, #fd7e14, #e06310);"></div>
                            <span>High (100-199 score)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: linear-gradient(135deg, #ffc107, #e0a800);"></div>
                            <span>Medium (50-99 score)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: linear-gradient(135deg, #28a745, #1e7e34);"></div>
                            <span>Low (1-49 score)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background: linear-gradient(135deg, #6c757d, #545b62);"></div>
                            <span>Clean (0 issues)</span>
                        </div>
                    </div>
                    <div class="file-heatmap">
                        {% for file in priority_analysis.top_files %}
                        <div class="file-item {% if file.score >= 200 %}file-critical{% elif file.score >= 100 %}file-high{% elif file.score >= 50 %}file-medium{% elif file.score > 0 %}file-low{% else %}file-clean{% endif %}" 
                             data-file="{{ file.file }}" data-issues="{{ file.issues }}" data-score="{{ file.score }}">
                            <div class="file-name">{{ file.file | basename }}</div>
                            <div class="issue-summary">{{ file.issues }} issues • Score: {{ file.score }}</div>
                            <div class="file-tooltip">
                                <strong>{{ file.file }}</strong><br>
                                Issues: {{ file.issues }}<br>
                                Priority Score: {{ file.score }}<br>
                                <em>Click to see detailed analysis</em>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            {% endif %}
            
            <!-- AI Summary -->
            <div class="section">
                <h2><span class="section-icon">📋</span>Executive Summary</h2>
                <div class="summary-text">{{ summary }}</div>
            </div>
            
            <!-- Top Problems -->
            <div class="section">
                <h2><span class="section-icon">🔍</span>Top Recurring Problems</h2>
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
                    {% if problem.get('affected_files') %}
                    <div class="affected-files">
                        <strong>Affected files:</strong>
                        <div class="file-list">
                            {% for file in problem.get('affected_files', [])[:5] %}
                            <span class="file-tag">{{ file | basename }}</span>
                            {% endfor %}
                            {% if problem.get('affected_files') | length > 5 %}
                            <span class="more-files">... and {{ (problem.get('affected_files') | length) - 5 }} more</span>
                            {% endif %}
                        </div>
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            
            <!-- Enhanced File Analysis (if available) -->
            {% if enhanced_analysis and enhanced_analysis.file_analysis %}
            <div class="section">
                <h2><span class="section-icon">📁</span>File-Focused Analysis</h2>
                <div id="fileAnalysisTable"></div>
            </div>
            {% endif %}
            
            <!-- Top Priority Fixes (if available) -->
            {% if enhanced_analysis and enhanced_analysis.top_priority_fixes %}
            <div class="section">
                <h2><span class="section-icon">⚡</span>Critical Fixes Required</h2>
                {% for fix in enhanced_analysis.top_priority_fixes %}
                <div class="improvement-item">
                    <div class="improvement-header">
                        <div class="improvement-title">{{ fix.rule }} - {{ fix.category | title }}</div>
                        <span class="priority-{{ fix.category }} priority-badge">{{ fix.category | upper }}</span>
                    </div>
                    <div class="description">{{ fix.description }}</div>
                    <div class="description"><strong>Impact:</strong> {{ fix.impact }}</div>
                    {% if fix.fix_steps %}
                    <div class="description">
                        <strong>Fix Steps:</strong>
                        <ul>
                        {% for step in fix.fix_steps %}
                            <li>{{ step }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                    {% if fix.get('affected_files') %}
                    <div class="affected-files">
                        <strong>Affected files:</strong>
                        <div class="file-list">
                            {% for file in fix.get('affected_files', [])[:5] %}
                            <span class="file-tag">{{ file | basename }}</span>
                            {% endfor %}
                            {% if fix.get('affected_files') | length > 5 %}
                            <span class="more-files">... and {{ (fix.get('affected_files') | length) - 5 }} more</span>
                            {% endif %}
                        </div>
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <!-- Quick Wins (if available) -->
            {% if enhanced_analysis and enhanced_analysis.quick_wins %}
            <div class="section">
                <h2><span class="section-icon">🚀</span>Quick Wins</h2>
                {% for win in enhanced_analysis.quick_wins %}
                <div class="improvement-item">
                    <div class="improvement-header">
                        <div class="improvement-title">{{ win.description }}</div>
                        <span class="priority-{{ win.effort.lower() }} priority-badge">{{ win.effort }} EFFORT</span>
                    </div>
                    <div class="description">Affects {{ win.files_affected }} files - Easy to implement!</div>
                    {% if win.get('affected_files') %}
                    <div class="affected-files">
                        <strong>Affected files:</strong>
                        <div class="file-list">
                            {% for file in win.get('affected_files', [])[:5] %}
                            <span class="file-tag">{{ file | basename }}</span>
                            {% endfor %}
                            {% if win.get('affected_files') | length > 5 %}
                            <span class="more-files">... and {{ (win.get('affected_files') | length) - 5 }} more</span>
                            {% endif %}
                        </div>
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <!-- Improvement Suggestions -->
            <div class="section">
                <h2><span class="section-icon">💡</span>Suggested Improvements</h2>
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
                    {% if problem.get('affected_files') %}
                    <div class="affected-files">
                        <strong>Affected files:</strong>
                        <div class="file-list">
                            {% for file in problem.get('affected_files', [])[:5] %}
                            <span class="file-tag">{{ file | basename }}</span>
                            {% endfor %}
                            {% if problem.get('affected_files') | length > 5 %}
                            <span class="more-files">... and {{ (problem.get('affected_files') | length) - 5 }} more</span>
                            {% endif %}
                        </div>
                    </div>
                    {% endif %}
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
                    {% if improvement.get('affected_files') %}
                    <div class="affected-files">
                        <strong>Affected files:</strong>
                        <div class="file-list">
                            {% for file in improvement.get('affected_files', [])[:5] %}
                            <span class="file-tag">{{ file | basename }}</span>
                            {% endfor %}
                            {% if improvement.get('affected_files') | length > 5 %}
                            <span class="more-files">... and {{ (improvement.get('affected_files') | length) - 5 }} more</span>
                            {% endif %}
                        </div>
                    </div>
                    {% endif %}
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
    
    <!-- Chart.js Scripts -->
    <script>
        // Severity Distribution Chart
        const severityCtx = document.getElementById('severityChart').getContext('2d');
        new Chart(severityCtx, {
            type: 'doughnut',
            data: {
                labels: ['Critical', 'Major', 'Minor'],
                datasets: [{
                    data: [{{ metrics.critical_issues }}, {{ metrics.major_issues }}, {{ metrics.minor_issues }}],
                    backgroundColor: ['#dc3545', '#fd7e14', '#ffc107'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
        
        // Category Distribution Chart
        {% if priority_analysis %}
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        new Chart(categoryCtx, {
            type: 'bar',
            data: {
                labels: ['Security', 'Correctness', 'Maintainability'],
                datasets: [{
                    label: 'Issues by Category',
                    data: [{{ priority_analysis.security_issues }}, {{ priority_analysis.correctness_issues }}, {{ priority_analysis.maintainability_issues }}],
                    backgroundColor: ['#dc3545', '#fd7e14', '#28a745'],
                    borderColor: ['#c82333', '#e06310', '#1e7e34'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
        {% else %}
        // Fallback chart when no priority analysis available
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        new Chart(categoryCtx, {
            type: 'bar',
            data: {
                labels: ['Bugs', 'Vulnerabilities', 'Code Smells'],
                datasets: [{
                    label: 'Issues by Type',
                    data: [{{ metrics.bugs }}, {{ metrics.vulnerabilities }}, {{ metrics.code_smells }}],
                    backgroundColor: ['#e74c3c', '#8e44ad', '#3498db'],
                    borderColor: ['#c0392b', '#7d3c98', '#2980b9'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
        {% endif %}
        
        // Enhanced interactive file heatmap
        document.querySelectorAll('.file-item').forEach(item => {
            // Enhanced click handler with detailed information
            item.addEventListener('click', function() {
                const fileName = this.getAttribute('data-file');
                const issues = this.getAttribute('data-issues');
                const score = this.getAttribute('data-score');
                
                // Create a more informative modal
                const modalContent = `
File Analysis Details:
━━━━━━━━━━━━━━━━━━━━━
📁 File: ${fileName}
🔍 Total Issues: ${issues}
⚡ Priority Score: ${score}
━━━━━━━━━━━━━━━━━━━━━

Priority Level: ${score >= 200 ? '🔥 CRITICAL' : score >= 100 ? '⚠️ HIGH' : score >= 50 ? '📊 MEDIUM' : score > 0 ? '✅ LOW' : '🎉 CLEAN'}

💡 Focus areas for this file should be prioritized in your development workflow.
                `;
                
                alert(modalContent);
            });
            
            // Enhanced hover effects with position-aware tooltips
            item.addEventListener('mouseenter', function(e) {
                const tooltip = this.querySelector('.file-tooltip');
                if (tooltip) {
                    tooltip.style.opacity = '1';
                    
                    // Position tooltip to avoid viewport edges
                    const rect = this.getBoundingClientRect();
                    const tooltipRect = tooltip.getBoundingClientRect();
                    
                    if (rect.top - tooltipRect.height < 10) {
                        tooltip.style.bottom = 'auto';
                        tooltip.style.top = '100%';
                        tooltip.style.marginTop = '8px';
                        tooltip.style.marginBottom = '0';
                    }
                }
            });
            
            item.addEventListener('mouseleave', function() {
                const tooltip = this.querySelector('.file-tooltip');
                if (tooltip) {
                    tooltip.style.opacity = '0';
                    // Reset position
                    tooltip.style.bottom = '100%';
                    tooltip.style.top = 'auto';
                    tooltip.style.marginTop = '0';
                    tooltip.style.marginBottom = '8px';
                }
            });
        });
        
        // Add search/filter functionality for heatmap
        function createHeatmapFilter() {
            const heatmapContainer = document.querySelector('.heatmap-container');
            if (!heatmapContainer) return;
            
            const filterHtml = `
                <div style="margin-bottom: 15px; text-align: center;">
                    <input type="text" id="fileFilter" placeholder="🔍 Filter files..." 
                           style="padding: 8px 15px; border: 2px solid #dee2e6; border-radius: 20px; 
                                  width: 250px; font-size: 14px;">
                    <select id="severityFilter" style="margin-left: 10px; padding: 8px 15px; 
                                                       border: 2px solid #dee2e6; border-radius: 20px;">
                        <option value="">All Severity Levels</option>
                        <option value="file-critical">Critical</option>
                        <option value="file-high">High</option>
                        <option value="file-medium">Medium</option>
                        <option value="file-low">Low</option>
                        <option value="file-clean">Clean</option>
                    </select>
                </div>
            `;
            
            heatmapContainer.insertAdjacentHTML('afterbegin', filterHtml);
            
            // Filter functionality
            const fileFilter = document.getElementById('fileFilter');
            const severityFilter = document.getElementById('severityFilter');
            
            function applyFilters() {
                const fileText = fileFilter.value.toLowerCase();
                const severity = severityFilter.value;
                
                document.querySelectorAll('.file-item').forEach(item => {
                    const fileName = item.getAttribute('data-file').toLowerCase();
                    const matchesText = !fileText || fileName.includes(fileText);
                    const matchesSeverity = !severity || item.classList.contains(severity);
                    
                    item.style.display = (matchesText && matchesSeverity) ? 'block' : 'none';
                });
            }
            
            fileFilter.addEventListener('input', applyFilters);
            severityFilter.addEventListener('change', applyFilters);
        }
        
        // Initialize filter when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', createHeatmapFilter);
        } else {
            createHeatmapFilter();
        }
        
        // Interactive File Analysis Table
        {% if enhanced_analysis and enhanced_analysis.file_analysis %}
        const fileAnalysisData = {{ enhanced_analysis.file_analysis | tojson }};
        
        // Debug: Log the data structure
        console.log('File Analysis Data:', fileAnalysisData);
        if (fileAnalysisData && fileAnalysisData.length > 0) {
            console.log('First item structure:', fileAnalysisData[0]);
        }
        
        if (fileAnalysisData && fileAnalysisData.length > 0) {
            const table = new Tabulator("#fileAnalysisTable", {
                data: fileAnalysisData,
                layout: "fitColumns",
                responsiveLayout: "collapse",
                pagination: "local",
                paginationSize: 8,
                height: "500px",
                resizableColumns: true,
                movableColumns: true,
                columns: [
                    {title: "File", field: "file_path", minWidth: 150, widthGrow: 1, formatter: function(cell) {
                        const fullPath = cell.getValue();
                        const fileName = fullPath.split('/').pop();
                        return `<span title="${fullPath}" style="font-family: monospace; font-weight: bold;">${fileName}</span>`;
                    }},
                    {title: "Score", field: "priority_score", width: 80, minWidth: 60, formatter: function(cell) {
                        const score = cell.getValue();
                        const rowData = cell.getRow().getData();
                        
                        // Debug: Check what we got
                        console.log('Score cell data:', score, 'Row data:', rowData);
                        
                        // Try different field names if priority_score is not available
                        let actualScore = score || rowData.score || rowData.priority || rowData.total_score || 0;
                        
                        if (!actualScore || actualScore === 0) {
                            return '<span style="color: #999;">N/A</span>';
                        }
                        
                        // Color coding
                        let color = "#28a745"; // green
                        if (actualScore >= 200) color = "#dc3545"; // red
                        else if (actualScore >= 100) color = "#fd7e14"; // orange
                        else if (actualScore >= 50) color = "#ffc107"; // yellow
                        
                        return `<div style="background: ${color}; color: white; padding: 4px 8px; border-radius: 4px; text-align: center; font-weight: bold;">${actualScore}</div>`;
                    }},
                    {title: "Issues", field: "issue_count", width: 70, minWidth: 50, hozAlign: "center"},
                    {title: "Top Issues", field: "top_issues", minWidth: 200, widthGrow: 2, formatter: function(cell) {
                        const issues = cell.getValue();
                        if (Array.isArray(issues)) {
                            const issueList = issues.slice(0, 5).map((issue, index) => 
                                `<div style="margin-bottom: 6px;"><strong>•</strong> ${issue}</div>`
                            ).join('');
                            return `<div style="font-size: 0.85em; line-height: 1.4; max-height: 120px; overflow-y: auto;">${issueList}${issues.length > 5 ? '<div style="margin-top: 8px;"><em>...and ${issues.length - 5} more issues</em></div>' : ''}</div>`;
                        }
                        return "";
                    }},
                    {title: "Fix Instructions", field: "fix_instructions", minWidth: 300, widthGrow: 3, formatter: function(cell) {
                        const instructions = cell.getValue();
                        if (Array.isArray(instructions)) {
                            const instructionList = instructions.slice(0, 4).map((instruction, index) => 
                                `<div style="margin-bottom: 8px;"><strong>${index + 1}.</strong> ${instruction}</div>`
                            ).join('');
                            return `<div style="font-size: 0.85em; line-height: 1.5; max-height: 120px; overflow-y: auto;">${instructionList}${instructions.length > 4 ? '<div><em>...and more steps</em></div>' : ''}</div>`;
                        }
                        return "";
                    }}
                ],
                rowFormatter: function(row) {
                    const score = row.getData().priority_score;
                    if (score >= 200) {
                        row.getElement().style.borderLeft = "4px solid #dc3545";
                    } else if (score >= 100) {
                        row.getElement().style.borderLeft = "4px solid #fd7e14";
                    } else if (score >= 50) {
                        row.getElement().style.borderLeft = "4px solid #ffc107";
                    }
                }
            });
            
            // Add window resize handler for table responsiveness
            window.addEventListener('resize', function() {
                table.redraw();
            });
        }
        {% endif %}
    </script>
</body>
</html>
        """
    
    def format_html_report(self, analysis_data: Dict[str, Any]) -> str:
        """
        Generate a beautiful HTML report from analysis data
        """
        import os
        from jinja2 import Environment
        
        # Create Jinja2 environment with custom filters
        env = Environment()
        env.filters['basename'] = lambda x: os.path.basename(x) if x else ''
        
        template = env.from_string(self.html_template)
        
        # Extract data
        request_data = analysis_data.get('request', {})
        report_data = analysis_data.get('report', {})
        
        if not report_data:
            return "<html><body><h1>No report data available</h1></body></html>"
        
        # Parse JSON fields - handle both string and already-parsed data
        top_problems = report_data.get('top_recurring_problems', [])
        if isinstance(top_problems, str):
            top_problems = json.loads(top_problems)
        
        improvements = report_data.get('suggested_improvements', [])
        if isinstance(improvements, str):
            improvements = json.loads(improvements)
        
        prioritized_issues = report_data.get('prioritized_issues', [])
        if isinstance(prioritized_issues, str):
            prioritized_issues = json.loads(prioritized_issues)
        
        grouped_by_file = report_data.get('grouped_by_file', {})
        if isinstance(grouped_by_file, str):
            grouped_by_file = json.loads(grouped_by_file)
        
        issues_with_suggestions = report_data.get('issues_with_suggestions', [])
        if isinstance(issues_with_suggestions, str):
            issues_with_suggestions = json.loads(issues_with_suggestions)
        
        enhanced_analysis = report_data.get('enhanced_analysis', {})
        if isinstance(enhanced_analysis, str):
            enhanced_analysis = json.loads(enhanced_analysis)
        
        # Also get enhanced_analysis from root level if it exists there
        if not enhanced_analysis and 'enhanced_analysis' in analysis_data:
            enhanced_analysis = analysis_data.get('enhanced_analysis', {})
        
        # Parse priority analysis if available - get from root level
        priority_analysis = analysis_data.get('priority_analysis', {})
        
        # Prepare template data
        template_data = {
            'project_key': request_data.get('project_key', 'Unknown'),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ai_model': report_data.get('ai_model_used', 'Unknown'),
            'summary': report_data.get('summary', 'No summary available'),
            'priority_analysis': priority_analysis,
            'enhanced_analysis': enhanced_analysis,
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
        
        # Parse JSON fields - handle both string and already-parsed data
        top_problems = report_data.get('top_recurring_problems', [])
        if isinstance(top_problems, str):
            top_problems = json.loads(top_problems)
        
        improvements = report_data.get('suggested_improvements', [])
        if isinstance(improvements, str):
            improvements = json.loads(improvements)
        
        prioritized_issues = report_data.get('prioritized_issues', [])
        if isinstance(prioritized_issues, str):
            prioritized_issues = json.loads(prioritized_issues)
        
        grouped_by_file = report_data.get('grouped_by_file', {})
        if isinstance(grouped_by_file, str):
            grouped_by_file = json.loads(grouped_by_file)
        
        issues_with_suggestions = report_data.get('issues_with_suggestions', [])
        if isinstance(issues_with_suggestions, str):
            issues_with_suggestions = json.loads(issues_with_suggestions)
        
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