# PROJECT.md

# Treatment Plant Scenario Simulation & Effluent Quality Prediction Platform

## Overview

Build a web-based platform that allows engineers and operators to simulate treatment plant performance under different operating scenarios and predict future effluent water quality.

The platform should help answer questions such as:

* What will effluent quality look like in 1 month?
* What will happen during the next 3 months of forecasted demand?
* How will maintenance activities affect performance?
* What operational changes should be made to maintain compliance?

The system is focused on planning and decision support rather than real-time control.

---

# Primary Goal

Provide a simple workflow:

```text
Scenario Input
    ↓
Configure Parameters
    ↓
Run Simulation
    ↓
Predict Effluent Quality
    ↓
Review Maintenance Impact
    ↓
Make Operational Decisions
```

---

# Core User Journey

## Step 1 - Select Treatment Plant

User opens the map.

Map displays:

* Treatment plants
* Plant status
* Plant location

User clicks a treatment plant.

---

## Step 2 - Open Plant Workspace

The selected treatment plant opens a simulation workspace.

Workspace contains:

### Left Panel

Scenario Configuration

### Center Panel

Simulation Dashboard

### Right Panel

Predicted Results

---

# Simulation Dashboard Layout

```text
┌───────────────────────────────────────────┐
│ Treatment Plant                           │
├───────────────────────────────────────────┤
│ Scenario Settings                         │
│                                           │
│ Forecast Inputs                           │
│                                           │
│ Maintenance Inputs                        │
├───────────────────────────────────────────┤
│ Model Execution                           │
├───────────────────────────────────────────┤
│ Effluent Quality Prediction               │
├───────────────────────────────────────────┤
│ KPI Summary                               │
└───────────────────────────────────────────┘
```

---

# Scenario Configuration

Users create simulation scenarios.

Example:

Scenario Name:

Heavy Rainfall + Planned Maintenance

Simulation Horizon:

* 1 Month
* 3 Months
* 6 Months

---

# Forecast Inputs

Users can input forecast assumptions.

Examples:

### Demand Forecast

* Low
* Normal
* High

or

Custom values

### Weather Forecast

* Dry
* Normal
* Wet

or

Imported forecast data

### Influent Conditions

* Flow
* BOD
* COD
* TSS
* Ammonia

---

# Maintenance Inputs

Users can configure upcoming maintenance events.

Examples:

### Pump Maintenance

Start Date

Duration

### Aeration Maintenance

Start Date

Duration

### Clarifier Maintenance

Start Date

Duration

### Equipment Availability

Example:

```text
Aeration System
Availability = 80%

Pump Station
Availability = 90%
```

The simulation should account for maintenance impacts when generating predictions.

---

# Simulation Engine

The simulation engine is the core of the platform.

It receives:

```json
{
  "forecast": {},
  "maintenance": {},
  "operating_parameters": {},
  "simulation_horizon": "3_months"
}
```

And returns:

```json
{
  "predicted_effluent": {},
  "kpis": {},
  "risks": {}
}
```

---

# Configurable Model Architecture

The platform must support replacing or upgrading models in the future.

Version 1:

Single prediction model.

Future:

Multiple models.

Example:

```text
Effluent Quality Model v1
Effluent Quality Model v2
Machine Learning Model
Process Model
Hybrid Model
```

Frontend should not depend on model implementation.

Models should follow a common interface.

```python
class SimulationModel:

    def run(
        forecast,
        maintenance,
        operating_parameters,
        horizon
    ):
        pass
```

---

# Simulation Horizons

Supported prediction periods:

### 1 Month

Short-term operational planning

### 3 Months

Quarterly planning

### 6 Months

Medium-term planning

Future support:

### 12 Months

Annual planning

---

# Effluent Quality Prediction

The primary output of the system.

Metrics:

* BOD
* COD
* TSS
* Ammonia
* Nitrate
* Phosphorus
* Turbidity
* pH

Users should immediately understand:

* Expected quality
* Expected trends
* Compliance status

---

# Result Dashboard

Simulation results should display:

### Effluent Quality Trends

Charts showing projected values over time.

### KPI Summary

* Compliance %
* Average Quality Score
* Treatment Capacity
* Risk Level

### Maintenance Impact

Show how maintenance events affect performance.

Example:

```text
Aeration Maintenance

Expected Impact:

+12% Ammonia
+5% COD

```

---

# Scenario Comparison

Users can compare:

Baseline

vs

Scenario A

vs

Scenario B

Example:

```text
Current Operations

vs

Reduced Aeration

vs

Planned Maintenance
```

Comparison should focus on:

* Effluent quality
* Compliance
* Risk

---

# Technology Stack

Frontend

* React
* TypeScript
* Vite
* Tailwind
* shadcn/ui
* ECharts
* MapLibre
* deckGL for visualation and prediction
* React Query 
* Zustand

Backend

* FastAPI

Database

* PostgreSQL
* PostGIS

Simulation Service

* Python

Storage

* Parquet

---

# Phase 1 Scope

Build:

✅ Treatment plant map

✅ Plant simulation workspace

✅ Scenario configuration

✅ Forecast input

✅ Maintenance planning input

✅ Simulation execution

✅ Effluent quality prediction

✅ KPI dashboard

✅ Scenario comparison

✅ 3D Digital Twin

Do Not Build Yet:

❌ AI Agent

❌ SCADA Integration

❌ Real-Time Control

❌ BIM Models

❌ Enterprise Planning

---

# Success Criteria

A user should be able to:

1. Select a treatment plant.
2. Configure a future scenario.
3. Add forecast assumptions.
4. Add planned maintenance activities.
5. Run a simulation.
6. Predict effluent quality for 1–6 months.
7. Understand operational risks.
8. Compare alternative scenarios.
9. Plan maintenance with confidence.

The platform's primary purpose is to support treatment plant planning through scenario simulation and effluent quality prediction.
