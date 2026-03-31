from datetime import datetime, timezone

import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base
from app.models.enums import (
    ActorType,
    AuditAction,
    MediaType,
    ReportStatus,
    SeverityLevel,
    UserRole,
)
from app.models.app_user import AppUser
from app.models.location import Location
from app.models.report import Report
from app.repositories import (
    AppUserRepository,
    LocationRepository,
    MediaRepository,
    ReportRepository,
    ReportAuditLogRepository,
)


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create a fresh in-memory SQLite engine for each test."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        echo=False,
    )

    # Enable foreign key enforcement for SQLite
    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    # Strip the safe_route schema from all tables so SQLite can create them
    for table in Base.metadata.tables.values():
        table.schema = None

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

    # Restore the schema for non-test usage
    for table in Base.metadata.tables.values():
        table.schema = "safe_route"


@pytest_asyncio.fixture(scope="function")
async def session(async_engine):
    """Provide an async session that rolls back after each test."""
    session_factory = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        yield session
        await session.rollback()


# ── Repository fixtures ─────────────────────


@pytest_asyncio.fixture
def app_user_repo(session: AsyncSession) -> AppUserRepository:
    return AppUserRepository(session)


@pytest_asyncio.fixture
def location_repo(session: AsyncSession) -> LocationRepository:
    return LocationRepository(session)


@pytest_asyncio.fixture
def report_repo(session: AsyncSession) -> ReportRepository:
    return ReportRepository(session)


@pytest_asyncio.fixture
def media_repo(session: AsyncSession) -> MediaRepository:
    return MediaRepository(session)


@pytest_asyncio.fixture
def audit_log_repo(session: AsyncSession) -> ReportAuditLogRepository:
    return ReportAuditLogRepository(session)


# ── Factory fixtures (shared test data) ─────


@pytest_asyncio.fixture
async def sample_user(app_user_repo: AppUserRepository) -> AppUser:
    """Create a reusable test user."""
    return await app_user_repo.create(
        first_name="Ada",
        last_name="Lovelace",
        email="ada@saferoute.test",
        role=UserRole.ADMIN,
        hashed_password="hashed_test_password",
    )


@pytest_asyncio.fixture
async def sample_location(location_repo: LocationRepository) -> Location:
    """Create a reusable test location."""
    return await location_repo.create(state="Lagos", city="Ikeja", town="Alausa")


@pytest_asyncio.fixture
async def sample_report(
    report_repo: ReportRepository,
    sample_location: Location,
) -> Report:
    """Create a reusable anonymous test report."""
    return await report_repo.create(
        location_id=sample_location.id,
        description="Suspicious activity near the market",
        incident_at=datetime(2026, 3, 15, 14, 30, tzinfo=timezone.utc),
    )
