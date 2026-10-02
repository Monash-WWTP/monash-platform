"""Explicit synthetic development fixture. Never invoked during API startup."""

from .config import settings
from .db.models import ComplianceLimit, Plant, PlantUnit, Scenario
from .db.session import SessionLocal


def main() -> None:
    if settings.app_env == "production":
        raise RuntimeError("development fixtures are forbidden in production")
    with SessionLocal.begin() as db:
        if db.query(Plant).filter(Plant.code == "DEMO001").first():
            return
        plant = Plant(
            code="DEMO001",
            name="Synthetic Demonstration Plant",
            status="unknown",
            latitude=0.0,
            longitude=0.0,
            capacity_mld=10.0,
            description="Synthetic test data only; not a real plant or legal compliance basis.",
            stp_type="synthetic",
            ef_ch4=0.0121,
            ef_n2o=0.0093,
        )
        db.add(plant)
        db.flush()
        db.add_all(
            [
                PlantUnit(plant_id=plant.id, unit_type=t, name=f"Synthetic {t}")
                for t in ("pump", "aeration", "clarifier")
            ]
        )
        db.add_all(
            [
                ComplianceLimit(plant_id=plant.id, metric=m, limit_value=v, unit="mg/L")
                for m, v in (("bod", 50), ("cod", 200), ("tss", 100))
            ]
        )
        db.add(
            Scenario(
                plant_id=plant.id,
                name="Synthetic baseline",
                horizon="3_months",
                forecast={
                    "demand": "normal",
                    "weather": "normal",
                    "influent": {"flow": 6, "bod": 250, "cod": 520, "tss": 300, "ammonia": 30, "tkn": 40},
                },
                maintenance=[],
                operating_parameters={"capacity_mld": 10},
                is_baseline=True,
            )
        )


if __name__ == "__main__":
    main()
