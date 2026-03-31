from app.models.location import Location
from app.repositories import LocationRepository


class TestLocationCreation:
    async def test_create_location(self, location_repo: LocationRepository):
        loc = await location_repo.create(state="Lagos", city="Lekki", town="Ajah")

        assert loc.id is not None
        assert loc.state == "Lagos"
        assert loc.city == "Lekki"
        assert loc.town == "Ajah"

    async def test_create_location_without_town(
        self, location_repo: LocationRepository
    ):
        """Town is optional."""
        loc = await location_repo.create(state="Abuja", city="Garki")

        assert loc.town is None


class TestFindOrCreate:
    async def test_find_existing_location(
        self, location_repo: LocationRepository, sample_location: Location
    ):
        """find_or_create returns an existing match instead of duplicating."""
        found = await location_repo.find_or_create(
            state="Lagos", city="Ikeja", town="Alausa"
        )

        assert found.id == sample_location.id

    async def test_create_new_location(self, location_repo: LocationRepository):
        """find_or_create creates a new record when no match exists."""
        loc = await location_repo.find_or_create(
            state="Ogun", city="Abeokuta", town="Oke-Ilewo"
        )

        assert loc.id is not None
        assert loc.state == "Ogun"

    async def test_town_null_distinction(self, location_repo: LocationRepository):
        """A location with town=None is distinct from one with a town."""
        with_town = await location_repo.find_or_create(
            state="Lagos", city="Lekki", town="Ajah"
        )
        without_town = await location_repo.find_or_create(state="Lagos", city="Lekki")

        assert with_town.id != without_town.id
