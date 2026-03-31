from app.models.app_user import AppUser
from app.models.enums import UserRole
from app.repositories import AppUserRepository


class TestAppUserCreation:
    async def test_create_user(self, app_user_repo: AppUserRepository):
        user = await app_user_repo.create(
            first_name="Grace",
            last_name="Hopper",
            email="grace@saferoute.test",
            hashed_password="hashed_pw",
        )

        assert user.id is not None
        assert user.email == "grace@saferoute.test"
        assert user.role == UserRole.REPORTER  # default
        assert user.is_active is True

    async def test_create_admin_user(self, app_user_repo: AppUserRepository):
        user = await app_user_repo.create(
            first_name="Admin",
            last_name="User",
            email="admin@saferoute.test",
            role=UserRole.ADMIN,
            hashed_password="hashed_pw",
        )

        assert user.role == UserRole.ADMIN


class TestAppUserLookup:
    async def test_get_by_email(
        self, app_user_repo: AppUserRepository, sample_user: AppUser
    ):
        found = await app_user_repo.get_by_email("ada@saferoute.test")

        assert found is not None
        assert found.id == sample_user.id

    async def test_get_by_email_not_found(self, app_user_repo: AppUserRepository):
        found = await app_user_repo.get_by_email("nobody@saferoute.test")

        assert found is None


class TestAppUserDeactivation:
    async def test_deactivate_user(
        self, app_user_repo: AppUserRepository, sample_user: AppUser
    ):
        deactivated = await app_user_repo.deactivate(sample_user)

        assert deactivated.is_active is False

    async def test_deactivated_excluded_from_active_list(
        self, app_user_repo: AppUserRepository, sample_user: AppUser
    ):
        await app_user_repo.deactivate(sample_user)

        active = await app_user_repo.get_active_users()

        assert all(u.id != sample_user.id for u in active)
