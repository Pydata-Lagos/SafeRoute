import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MediaType
from app.repositories import (
    AppUserRepository,
    MediaRepository,
    ReportRepository,
)


class TestUniqueConstraints:
    async def test_duplicate_email_rejected(self, app_user_repo: AppUserRepository):
        """The email unique constraint prevents duplicate users."""
        await app_user_repo.create(
            first_name="Ada",
            last_name="Lovelace",
            email="duplicate@saferoute.test",
            hashed_password="hashed_pw",
        )

        with pytest.raises(IntegrityError):
            await app_user_repo.create(
                first_name="Another",
                last_name="Person",
                email="duplicate@saferoute.test",
                hashed_password="hashed_pw",
            )

    async def test_duplicate_reference_no_rejected(
        self,
        session: AsyncSession,
        report_repo: ReportRepository,
        sample_location,
    ):
        """The reference_no unique constraint prevents collisions."""
        report = await report_repo.create(
            location_id=sample_location.id,
            description="First report",
            incident_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
        )

        # Force a duplicate reference_no
        with pytest.raises(IntegrityError):
            await report_repo.create(
                location_id=sample_location.id,
                description="Second report",
                incident_at=datetime(2026, 3, 16, tzinfo=timezone.utc),
                reference_no=report.reference_no,  # deliberately duplicate
            )


class TestForeignKeyConstraints:
    async def test_report_requires_valid_location(self, report_repo: ReportRepository):
        """A report cannot reference a non-existent location."""
        fake_location_id = uuid.uuid4()

        with pytest.raises(IntegrityError):
            await report_repo.create(
                location_id=fake_location_id,
                description="Orphaned report",
                incident_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
            )

    async def test_media_requires_valid_report(self, media_repo: MediaRepository):
        """Media cannot reference a non-existent report."""
        fake_report_id = uuid.uuid4()

        with pytest.raises(IntegrityError):
            await media_repo.create(
                report_id=fake_report_id,
                type=MediaType.IMAGE,
                media_link="https://storage.example.com/orphan.jpg",
            )


class TestNotNullConstraints:
    async def test_user_requires_email(self, app_user_repo: AppUserRepository):
        with pytest.raises(IntegrityError):
            await app_user_repo.create(
                first_name="No",
                last_name="Email",
                email=None,
                hashed_password="hashed_pw",
            )

    async def test_report_requires_description(
        self, report_repo: ReportRepository, sample_location
    ):
        with pytest.raises(IntegrityError):
            await report_repo.create(
                location_id=sample_location.id,
                description=None,
                incident_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
            )

    async def test_report_requires_location(self, report_repo: ReportRepository):
        with pytest.raises(IntegrityError):
            await report_repo.create(
                location_id=None,
                description="No location",
                incident_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
            )
