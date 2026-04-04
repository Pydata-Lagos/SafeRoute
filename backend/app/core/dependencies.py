from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_session
from app.repositories import (
    AppUserRepository,
    LocationRepository,
    MediaRepository,
    ReportRepository,
    ReportAuditLogRepository,
)


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_report_repository(session: SessionDep) -> ReportRepository:
    return ReportRepository(session)


def get_audit_log_repository(session: SessionDep) -> ReportAuditLogRepository:
    return ReportAuditLogRepository(session)


def get_location_repository(session: SessionDep) -> LocationRepository:
    return LocationRepository(session)


def get_media_repository(session: SessionDep) -> MediaRepository:
    return MediaRepository(session)


def get_app_user_repository(session: SessionDep) -> AppUserRepository:
    return AppUserRepository(session)


ReportRepoDep = Annotated[ReportRepository, Depends(get_report_repository)]
AuditLogRepoDep = Annotated[ReportAuditLogRepository, Depends(get_audit_log_repository)]
LocationRepoDep = Annotated[LocationRepository, Depends(get_location_repository)]
MediaRepoDep = Annotated[MediaRepository, Depends(get_media_repository)]
AppUserRepoDep = Annotated[AppUserRepository, Depends(get_app_user_repository)]
