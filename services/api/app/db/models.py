from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Plant(Base):
    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=True)  # supabase station code
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="operational")
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_mld: Mapped[float] = mapped_column(Float, default=60.0)
    description: Mapped[str] = mapped_column(String, default="")
    stp_type: Mapped[str] = mapped_column(String, default="")
    # GHG emission factors synced from the supabase emission_factors table
    ef_ch4: Mapped[float] = mapped_column(Float, default=0.0121)
    ef_n2o: Mapped[float] = mapped_column(Float, default=0.0093)

    units: Mapped[list[PlantUnit]] = relationship(back_populates="plant", cascade="all, delete-orphan")
    scenarios: Mapped[list[Scenario]] = relationship(back_populates="plant", cascade="all, delete-orphan")
    compliance_limits: Mapped[list[ComplianceLimit]] = relationship(
        back_populates="plant", cascade="all, delete-orphan"
    )


class PlantUnit(Base):
    __tablename__ = "plant_units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"), nullable=False)
    unit_type: Mapped[str] = mapped_column(String, nullable=False)  # pump|aeration|clarifier
    name: Mapped[str] = mapped_column(String, nullable=False)
    baseline_availability: Mapped[float] = mapped_column(Float, default=100.0)

    plant: Mapped[Plant] = relationship(back_populates="units")


class ComplianceLimit(Base):
    __tablename__ = "compliance_limits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"), nullable=False)
    metric: Mapped[str] = mapped_column(String, nullable=False)
    limit_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String, default="mg/L")

    plant: Mapped[Plant] = relationship(back_populates="compliance_limits")


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    horizon: Mapped[str] = mapped_column(String, default="3_months")
    forecast: Mapped[dict] = mapped_column(JSON, default=dict)
    maintenance: Mapped[list] = mapped_column(JSON, default=list)
    operating_parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    is_baseline: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    plant: Mapped[Plant] = relationship(back_populates="scenarios")
    runs: Mapped[list[SimulationRun]] = relationship(back_populates="scenario", cascade="all, delete-orphan")


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id"), nullable=False)
    model_id: Mapped[str] = mapped_column(String, nullable=False)
    model_version: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="completed")
    kpis: Mapped[dict] = mapped_column(JSON, default=dict)
    exceedances: Mapped[list] = mapped_column(JSON, default=list)
    # {"dates": [...], "series": {metric: [...]}} — stored in-DB so the
    # backend stays stateless (no local parquet; works on ephemeral hosts)
    timeseries: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    scenario: Mapped[Scenario] = relationship(back_populates="runs")
