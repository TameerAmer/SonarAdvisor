import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session

from sonar_advisor.core.database import get_db
from sonar_advisor.core.auth import get_current_active_user
from sonar_advisor.models.user import User
from sonar_advisor.models.analysis_request import AnalysisRequest
from sonar_advisor.models.ai_report import AIReport
from sonar_advisor.schemas.analysis import (
    AnalysisRequestCreate, AnalysisRequestResponse, 
    AnalysisResponse, AIReportResponse, SonarQubeData,
    TopProblem, SuggestedImprovement, PrioritizedIssue
)
from sonar_advisor.services.sonarqube import sonarqube_service
from sonar_advisor.services.ai_analysis import ai_analysis_service
from sonar_advisor.services.report_formatter import report_formatter

router = APIRouter()


async def process_analysis_background(
    analysis_request_id: int,
    project_key: str,
    db: Session
):
    """
    Background task to process SonarQube analysis
    """
    try:
        # Get the analysis request using SQLAlchemy
        analysis_request = db.query(AnalysisRequest).filter(
            AnalysisRequest.id == analysis_request_id
        ).first()
        
        if not analysis_request:
            return
        
        # Update status to processing
        analysis_request.status = "processing"
        db.commit()
        
        # Fetch SonarQube data
        sonarqube_data = await sonarqube_service.fetch_project_issues(project_key)
        
        # Store SonarQube data
        analysis_request = await sonarqube_service.store_sonarqube_data(
            db, analysis_request, sonarqube_data
        )
        
        # Perform AI analysis
        analysis_results = ai_analysis_service.analyze_issues(sonarqube_data)
        
        # Store AI report
        await ai_analysis_service.save_analysis_report(
            analysis_request.id, analysis_results, db
        )
        
    except Exception as e:
        print(f"Background analysis failed: {e}")
        if analysis_request:
            analysis_request.status = "failed"
            db.commit()


@router.post("/analyze", response_model=AnalysisRequestResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_project_analysis(
    request_data: AnalysisRequestCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Start analysis of a SonarQube project (protected endpoint)
    """
    # Test SonarQube connection first
    connection_ok = await sonarqube_service.test_connection()
    if not connection_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot connect to SonarQube server. Please check configuration."
        )
    
    # Verify project exists in SonarQube
    project_info = await sonarqube_service.get_project_info(request_data.project_key)
    if not project_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{request_data.project_key}' not found in SonarQube"
        )
    
    try:
        # Create analysis request using SQLAlchemy
        analysis_request = AnalysisRequest(
            project_key=request_data.project_key,
            user_id=current_user.id,
            status="pending"
        )
        
        db.add(analysis_request)
        db.commit()
        db.refresh(analysis_request)
        
        # Start background processing
        background_tasks.add_task(
            process_analysis_background,
            analysis_request.id,
            request_data.project_key,
            db
        )
        
        return analysis_request
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create analysis request: {str(e)}"
        )


@router.get("/requests", response_model=List[AnalysisRequestResponse])
async def get_user_analysis_requests(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all analysis requests for the current user
    """
    # Query using SQLAlchemy with pagination
    requests = db.query(AnalysisRequest).filter(
        AnalysisRequest.user_id == current_user.id
    ).order_by(AnalysisRequest.created_at.desc()).offset(skip).limit(limit).all()
    
    return requests


@router.get("/requests/{request_id}", response_model=AnalysisResponse)
async def get_analysis_result(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get analysis result by request ID
    """
    # Query analysis request using SQLAlchemy
    analysis_request = db.query(AnalysisRequest).filter(
        AnalysisRequest.id == request_id,
        AnalysisRequest.user_id == current_user.id
    ).first()
    
    if not analysis_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis request not found"
        )
    
    # Get the AI report if analysis is completed
    ai_report = None
    if analysis_request.status == "completed":
        ai_report_db = db.query(AIReport).filter(
            AIReport.analysis_request_id == request_id
        ).first()
        
        if ai_report_db:
            # Parse JSON fields back to objects
            top_problems = [TopProblem(**p) for p in json.loads(ai_report_db.top_recurring_problems)]
            improvements = [SuggestedImprovement(**i) for i in json.loads(ai_report_db.suggested_improvements)]
            prioritized = [PrioritizedIssue(**i) for i in json.loads(ai_report_db.prioritized_issues)]
            
            ai_report = AIReportResponse(
                id=ai_report_db.id,
                analysis_request_id=ai_report_db.analysis_request_id,
                summary=ai_report_db.summary,
                top_recurring_problems=top_problems,
                suggested_improvements=improvements,
                prioritized_issues=prioritized,
                total_issues=ai_report_db.total_issues,
                critical_issues=ai_report_db.critical_issues,
                major_issues=ai_report_db.major_issues,
                minor_issues=ai_report_db.minor_issues,
                code_smells=ai_report_db.code_smells,
                bugs=ai_report_db.bugs,
                vulnerabilities=ai_report_db.vulnerabilities,
                ai_model_used=ai_report_db.ai_model_used,
                confidence_score=ai_report_db.confidence_score,
                created_at=ai_report_db.created_at
            )
    
    return AnalysisResponse(
        request=AnalysisRequestResponse.model_validate(analysis_request),
        report=ai_report
    )


@router.get("/status/{request_id}")
async def get_analysis_status(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current status of an analysis request
    """
    analysis_request = db.query(AnalysisRequest).filter(
        AnalysisRequest.id == request_id,
        AnalysisRequest.user_id == current_user.id
    ).first()
    
    if not analysis_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis request not found"
        )
    
    return {
        "request_id": request_id,
        "status": analysis_request.status,
        "project_key": analysis_request.project_key,
        "created_at": analysis_request.created_at,
        "completed_at": analysis_request.completed_at
    }


@router.delete("/requests/{request_id}")
async def delete_analysis_request(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an analysis request and its associated reports
    """
    analysis_request = db.query(AnalysisRequest).filter(
        AnalysisRequest.id == request_id,
        AnalysisRequest.user_id == current_user.id
    ).first()
    
    if not analysis_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis request not found"
        )
    
    try:
        # SQLAlchemy will handle cascade deletion of related AI reports
        db.delete(analysis_request)
        db.commit()
        
        return {"message": "Analysis request deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete analysis request: {str(e)}"
        )


@router.get("/sonarqube/projects")
async def list_sonarqube_projects(
    current_user: User = Depends(get_current_active_user)
):
    """
    List available projects from SonarQube (helper endpoint)
    """
    # This is a helper endpoint to see available projects
    # You might want to implement caching for this
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{sonarqube_service.base_url}/api/projects/search",
                headers=sonarqube_service._get_auth_headers(),
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                projects = []
                for component in data.get("components", []):
                    projects.append({
                        "key": component.get("key"),
                        "name": component.get("name"),
                        "qualifier": component.get("qualifier")
                    })
                return {"projects": projects}
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch projects from SonarQube"
                )
                
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot connect to SonarQube: {str(e)}"
        )


@router.get("/requests/{request_id}/report/html", response_class=HTMLResponse)
async def get_analysis_html_report(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get analysis result as a beautiful HTML report
    """
    # Get the analysis data using the existing endpoint logic
    analysis_request = db.query(AnalysisRequest).filter(
        AnalysisRequest.id == request_id,
        AnalysisRequest.user_id == current_user.id
    ).first()
    
    if not analysis_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis request not found"
        )
    
    if analysis_request.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis is not completed yet"
        )
    
    # Get the AI report
    ai_report_db = db.query(AIReport).filter(
        AIReport.analysis_request_id == request_id
    ).first()
    
    if not ai_report_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI report not found"
        )
    
    # Prepare data for the formatter
    analysis_data = {
        "request": {
            "id": analysis_request.id,
            "project_key": analysis_request.project_key,
            "user_id": analysis_request.user_id,
            "status": analysis_request.status,
            "created_at": analysis_request.created_at.isoformat(),
            "completed_at": analysis_request.completed_at.isoformat() if analysis_request.completed_at else None
        },
        "report": {
            "id": ai_report_db.id,
            "analysis_request_id": ai_report_db.analysis_request_id,
            "summary": ai_report_db.summary,
            "top_recurring_problems": ai_report_db.top_recurring_problems,
            "suggested_improvements": ai_report_db.suggested_improvements,
            "prioritized_issues": ai_report_db.prioritized_issues,
            "total_issues": ai_report_db.total_issues,
            "critical_issues": ai_report_db.critical_issues,
            "major_issues": ai_report_db.major_issues,
            "minor_issues": ai_report_db.minor_issues,
            "code_smells": ai_report_db.code_smells,
            "bugs": ai_report_db.bugs,
            "vulnerabilities": ai_report_db.vulnerabilities,
            "ai_model_used": ai_report_db.ai_model_used,
            "confidence_score": ai_report_db.confidence_score,
            "created_at": ai_report_db.created_at.isoformat()
        }
    }
    
    # Generate HTML report
    html_content = report_formatter.format_html_report(analysis_data)
    return HTMLResponse(content=html_content)


@router.get("/requests/{request_id}/report/markdown", response_class=PlainTextResponse)
async def get_analysis_markdown_report(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get analysis result as a markdown report
    """
    # Get the analysis data (same logic as HTML endpoint)
    analysis_request = db.query(AnalysisRequest).filter(
        AnalysisRequest.id == request_id,
        AnalysisRequest.user_id == current_user.id
    ).first()
    
    if not analysis_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis request not found"
        )
    
    if analysis_request.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis is not completed yet"
        )
    
    # Get the AI report
    ai_report_db = db.query(AIReport).filter(
        AIReport.analysis_request_id == request_id
    ).first()
    
    if not ai_report_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI report not found"
        )
    
    # Prepare data for the formatter
    analysis_data = {
        "request": {
            "id": analysis_request.id,
            "project_key": analysis_request.project_key,
            "user_id": analysis_request.user_id,
            "status": analysis_request.status,
            "created_at": analysis_request.created_at.isoformat(),
            "completed_at": analysis_request.completed_at.isoformat() if analysis_request.completed_at else None
        },
        "report": {
            "id": ai_report_db.id,
            "analysis_request_id": ai_report_db.analysis_request_id,
            "summary": ai_report_db.summary,
            "top_recurring_problems": ai_report_db.top_recurring_problems,
            "suggested_improvements": ai_report_db.suggested_improvements,
            "prioritized_issues": ai_report_db.prioritized_issues,
            "total_issues": ai_report_db.total_issues,
            "critical_issues": ai_report_db.critical_issues,
            "major_issues": ai_report_db.major_issues,
            "minor_issues": ai_report_db.minor_issues,
            "code_smells": ai_report_db.code_smells,
            "bugs": ai_report_db.bugs,
            "vulnerabilities": ai_report_db.vulnerabilities,
            "ai_model_used": ai_report_db.ai_model_used,
            "confidence_score": ai_report_db.confidence_score,
            "created_at": ai_report_db.created_at.isoformat()
        }
    }
    
    # Generate Markdown report
    markdown_content = report_formatter.format_markdown_report(analysis_data)
    return PlainTextResponse(content=markdown_content, media_type="text/markdown")