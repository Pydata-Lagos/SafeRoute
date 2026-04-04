from datetime import datetime, timezone

from app.models.enums import ReportStatus, SeverityLevel
from app.models.location import Location
from app.models.report import Report
from app.repositories import ReportRepository


class TestReportCreation:
    async def test_create_anonymous_report(
        self, report_repo: ReportRepository, sample_location: Location
    ):
        """Anonymous reports have no reporter_id and auto-generate a reference_no."""
        report = await report_repo.create(
            location_id=sample_location.id,
            description="Test incident",
            incident_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
        )

        assert report.id is not None
        assert report.reporter_id is None
        assert report.reference_no is not None
        assert report.reference_no.startswith("SR-")
        assert report.status == ReportStatus.PENDING
        assert report.severity == SeverityLevel.LOW
        assert report.is_deleted is False

    async def test_create_authenticated_report(
        self,
        report_repo: ReportRepository,
        sample_location: Location,
        sample_user,
    ):
        """Authenticated reports are linked to a user."""
        report = await report_repo.create(
            reporter_id=sample_user.id,
            location_id=sample_location.id,
            description="Test incident",
            incident_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
        )

        assert report.reporter_id == sample_user.id

    async def test_reference_no_is_unique(
        self, report_repo: ReportRepository, sample_location: Location
    ):
        """Each report gets a unique reference number."""
        report_a = await report_repo.create(
            location_id=sample_location.id,
            description="Incident A",
            incident_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
        )
        report_b = await report_repo.create(
            location_id=sample_location.id,
            description="Incident B",
            incident_at=datetime(2026, 3, 16, tzinfo=timezone.utc),
        )

        assert report_a.reference_no != report_b.reference_no


class TestReportLookup:
    async def test_get_by_reference_no(
        self, report_repo: ReportRepository, sample_report: Report
    ):
        """Lookup by reference_no returns the correct report."""
        found = await report_repo.get_by_reference_no(sample_report.reference_no)

        assert found is not None
        assert found.id == sample_report.id

    async def test_get_by_reference_no_not_found(self, report_repo: ReportRepository):
        """Non-existent reference_no returns None."""
        found = await report_repo.get_by_reference_no("SR-nonexistent")

        assert found is None

    async def test_get_by_reference_no_excludes_deleted(
        self, report_repo: ReportRepository, sample_report: Report
    ):
        """Soft-deleted reports are not returned by reference_no lookup."""
        await report_repo.soft_delete(sample_report)

        found = await report_repo.get_by_reference_no(sample_report.reference_no)

        assert found is None

    async def test_get_by_id(
        self, report_repo: ReportRepository, sample_report: Report
    ):
        """Lookup by primary key returns the correct report."""
        found = await report_repo.get_by_id(sample_report.id)

        assert found is not None
        assert found.reference_no == sample_report.reference_no


class TestReportFiltering:
    async def test_get_active_reports_excludes_deleted(
        self,
        report_repo: ReportRepository,
        sample_location: Location,
    ):
        """get_active_reports never returns soft-deleted reports."""
        report = await report_repo.create(
            location_id=sample_location.id,
            description="Will be deleted",
            incident_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
        )
        await report_repo.soft_delete(report)

        active = await report_repo.get_active_reports()

        assert all(r.id != report.id for r in active)

    async def test_filter_by_status(
        self,
        report_repo: ReportRepository,
        sample_location: Location,
    ):
        """Active reports can be filtered by status."""
        report = await report_repo.create(
            location_id=sample_location.id,
            description="Under review",
            incident_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
        )
        await report_repo.update(report, status=ReportStatus.UNDER_REVIEW)

        results = await report_repo.get_active_reports(status=ReportStatus.UNDER_REVIEW)

        assert any(r.id == report.id for r in results)

    async def test_filter_by_severity(
        self,
        report_repo: ReportRepository,
        sample_location: Location,
    ):
        """Active reports can be filtered by severity."""
        report = await report_repo.create(
            location_id=sample_location.id,
            description="High severity incident",
            incident_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
        )
        await report_repo.update(report, severity=SeverityLevel.HIGH)

        results = await report_repo.get_active_reports(severity=SeverityLevel.HIGH)

        assert any(r.id == report.id for r in results)

    async def test_filter_excludes_non_matching(
        self,
        report_repo: ReportRepository,
        sample_location: Location,
    ):
        """Filters exclude reports that don't match."""
        await report_repo.create(
            location_id=sample_location.id,
            description="Pending report",
            incident_at=datetime(2026, 3, 15, tzinfo=timezone.utc),
        )

        results = await report_repo.get_active_reports(status=ReportStatus.RESOLVED)

        assert len(results) == 0


class TestSoftDelete:
    async def test_soft_delete_sets_flag(
        self, report_repo: ReportRepository, sample_report: Report
    ):
        """Soft delete sets is_deleted to True but preserves the row."""
        await report_repo.soft_delete(sample_report)

        # Direct ID lookup still finds it (no is_deleted filter)
        found = await report_repo.get_by_id(sample_report.id)

        assert found is not None
        assert found.is_deleted is True

    async def test_soft_deleted_excluded_from_active(
        self, report_repo: ReportRepository, sample_report: Report
    ):
        """Soft-deleted reports don't appear in active queries."""
        await report_repo.soft_delete(sample_report)

        active = await report_repo.get_active_reports()

        assert all(r.id != sample_report.id for r in active)
