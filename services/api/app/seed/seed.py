"""Sync plants from Supabase stations + seed units/limits/baseline scenarios.

The Supabase `stations` table is the source of truth for plants. Effluent
compliance limits follow Malaysia EQA 2009 (Environmental Quality (Sewage)
Regulations) Standard A/B by station category.
"""
import json
import urllib.request

from ..config import settings
from ..db.models import ComplianceLimit, Plant, PlantUnit, Scenario
from ..db.session import SessionLocal

# Shared EQA 2009 limits that do not depend on receiving-water type (mg/L).
# Nitrogen and phosphorus limits are omitted because their legal values also
# depend on whether the receiving water is a river or enclosed water body.
EQA_LIMITS = {
    "A": {"bod": 20, "cod": 120, "tss": 50},
    "B": {"bod": 50, "cod": 200, "tss": 100},
}
LEGACY_EQA_LIMITS = {
    "A": {"bod": 20, "cod": 120, "tss": 50, "ammonia": 10, "nitrate": 20,
          "phosphorus": 5, "turbidity": 50},
    "B": {"bod": 50, "cod": 200, "tss": 100, "ammonia": 20, "nitrate": 50,
          "phosphorus": 10, "turbidity": 100},
}

# Typical Malaysian municipal influent assumptions for a small SBR plant
DEFAULT_INFLUENT = {
    "flow": 6.0,
    "bod": 250,
    "cod": 520,
    "tss": 300,
    "ammonia": 30,
    # Explicit influent Kjeldahl nitrogen input for Guideline Equation 5.28.
    "tkn": 40.0,
}
DEFAULT_CAPACITY_MLD = 10.0


def _mark_legacy_fixture_unverified(plant: Plant) -> None:
    if "EQA 2009 Standard" not in (plant.description or ""):
        return
    plant.status = "unknown"
    plant.description = (
        "Legacy seed values: plant capacity and operating status are unverified. "
        "Confirm both before using scenarios for operational decisions."
    )


def _fetch(table: str) -> list[dict]:
    req = urllib.request.Request(
        f"{settings.supabase_url}/rest/v1/{table}?select=*",
        headers={"apikey": settings.supabase_key, "User-Agent": "wwtp-backend"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def seed_if_empty() -> None:
    """Sync plants from Supabase. Falls back to existing rows if unreachable."""
    try:
        stations = _fetch("stations")
        efs = {row["process_type"].upper(): row for row in _fetch("emission_factors")}
    except Exception as exc:  # offline dev should still boot
        print(f"[seed] WARNING: could not reach Supabase ({exc}); keeping local plants")
        return
    general = efs.get("GENERAL", {"ef_ch4": 0.0121, "ef_n2o": 0.0093})

    db = SessionLocal()
    try:
        for st in stations:
            plant = db.query(Plant).filter(Plant.code == st["code"]).first()
            is_new_plant = plant is None
            was_seeded_fixture = bool(plant and "EQA 2009 Standard" in plant.description)
            if is_new_plant:
                plant = Plant(code=st["code"])
                db.add(plant)
                plant.status = "unknown"
            plant.name = st["name"]
            plant.latitude = st["latitude"]
            plant.longitude = st["longitude"]
            if is_new_plant:
                plant.capacity_mld = DEFAULT_CAPACITY_MLD
                plant.description = (
                    f"Illustrative defaults only: {DEFAULT_CAPACITY_MLD:g} MLD capacity; "
                    f"{st.get('stp_type') or 'STP'} process. Configure verified plant details "
                    "before using scenarios for operational decisions."
                )
            elif was_seeded_fixture:
                _mark_legacy_fixture_unverified(plant)
            plant.stp_type = st.get("stp_type") or ""
            ef = efs.get(plant.stp_type.upper(), general)
            plant.ef_ch4 = float(ef["ef_ch4"])
            plant.ef_n2o = float(ef["ef_n2o"])
            db.flush()

            if not plant.units:
                db.add_all(
                    [
                        PlantUnit(plant_id=plant.id, unit_type="pump", name="Inlet Pump Station"),
                        PlantUnit(plant_id=plant.id, unit_type="aeration", name="SBR Basin 1"),
                        PlantUnit(plant_id=plant.id, unit_type="aeration", name="SBR Basin 2"),
                        PlantUnit(plant_id=plant.id, unit_type="clarifier", name="Decanter / Settling"),
                    ]
                )
            category = (st.get("category") or "B").upper()
            existing_limits = {row.metric: row.limit_value for row in plant.compliance_limits}
            if existing_limits == LEGACY_EQA_LIMITS.get(category):
                plant.compliance_limits.clear()
            if not plant.compliance_limits:
                limits = EQA_LIMITS.get(category, EQA_LIMITS["B"])
                db.add_all(
                    [
                        ComplianceLimit(plant_id=plant.id, metric=m, limit_value=v)
                        for m, v in limits.items()
                    ]
                )
            if not plant.scenarios:
                db.add(
                    Scenario(
                        plant_id=plant.id,
                        name="Baseline — Current Operations",
                        horizon="3_months",
                        forecast={"demand": "normal", "weather": "normal",
                                  "influent": DEFAULT_INFLUENT},
                        maintenance=[],
                        operating_parameters={"capacity_mld": DEFAULT_CAPACITY_MLD},
                        is_baseline=True,
                    )
                )
        db.commit()
        print(f"[seed] synced {len(stations)} station(s) from Supabase")
    finally:
        db.close()
