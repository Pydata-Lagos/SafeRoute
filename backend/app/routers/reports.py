from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import ReportRepoDep, AuditLogRepoDep
from app.models.enums import ActorType, AuditAction


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/track/{reference_no}")
async def track_report(reference_no: str, report_repo: ReportRepoDep):
    """Unauthenticated endpoint - returns only status and severity"""
    report = await report_repo.get_by_reference_no(reference_no)

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )
    return {
        "reference_no": report.reference_no,
        "status": report.status,
        "severity": report.severity,
    }
