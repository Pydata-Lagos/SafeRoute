from app.models.enums import MediaType
from app.models.report import Report
from app.repositories import MediaRepository


class TestMediaCreation:
    async def test_create_media(
        self, media_repo: MediaRepository, sample_report: Report
    ):
        media = await media_repo.create(
            report_id=sample_report.id,
            type=MediaType.IMAGE,
            media_link="https://storage.example.com/evidence/photo1.jpg",
        )

        assert media.id is not None
        assert media.report_id == sample_report.id
        assert media.type == MediaType.IMAGE

    async def test_get_by_report_id(
        self, media_repo: MediaRepository, sample_report: Report
    ):
        await media_repo.create(
            report_id=sample_report.id,
            type=MediaType.IMAGE,
            media_link="https://storage.example.com/photo1.jpg",
        )
        await media_repo.create(
            report_id=sample_report.id,
            type=MediaType.VIDEO,
            media_link="https://storage.example.com/video1.mp4",
        )

        results = await media_repo.get_by_report_id(sample_report.id)

        assert len(results) == 2

    async def test_get_by_report_id_empty(
        self, media_repo: MediaRepository, sample_report: Report
    ):
        """Report with no media returns an empty list."""
        results = await media_repo.get_by_report_id(sample_report.id)

        assert len(results) == 0
