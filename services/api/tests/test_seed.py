from types import SimpleNamespace

from app.seed.seed import _mark_legacy_fixture_unverified


def test_legacy_seed_fixture_is_not_left_marked_operational():
    plant = SimpleNamespace(
        status="operational",
        description="Legacy fixture — EQA 2009 Standard B",
    )

    _mark_legacy_fixture_unverified(plant)

    assert plant.status == "unknown"
    assert "unverified" in plant.description


def test_verified_plant_status_is_not_overwritten():
    plant = SimpleNamespace(
        status="operational",
        description="Verified plant details supplied by the operator",
    )

    _mark_legacy_fixture_unverified(plant)

    assert plant.status == "operational"
    assert plant.description == "Verified plant details supplied by the operator"
