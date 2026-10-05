"""Wastewater-treatment process GHG calculations.

Implements Equations 5.25 and 5.28 from *Guidelines for Carbon Accounting
and Emission Reduction in the Urban Water Sector* (2024).

Inputs use the units stated by the guideline:

- BOD5 and influent Kjeldahl nitrogen (TKN): mg/L
- emission factors: kg CH4/kg BOD5 and kg N2O-N/kg N
- recovered/removed gas: kg gas/m3
- result: kg CO2-eq/m3
"""
from __future__ import annotations

import numpy as np

GWP_CH4 = 28.0
GWP_N2O = 265.0
N2O_N_TO_N2O = 44.0 / 28.0
MG_L_TO_KG_M3 = 1e-3


def ch4_intensity_kgco2e_m3(
    bod5_in_mg_l,
    emission_factor: float,
    recovered_kg_ch4_m3: float = 0.0,
):
    """Return net CH4 process-emission intensity using Equation 5.25."""
    gross_kg_ch4_m3 = (
        np.asarray(bod5_in_mg_l, dtype=float)
        * float(emission_factor)
        * MG_L_TO_KG_M3
    )
    net_kg_ch4_m3 = gross_kg_ch4_m3 - recovered_kg_ch4_m3
    return net_kg_ch4_m3 * GWP_CH4


def n2o_intensity_kgco2e_m3(
    tkn_in_mg_l,
    emission_factor: float,
    recovered_kg_n2o_m3: float = 0.0,
):
    """Return net N2O process-emission intensity using Equation 5.28."""
    gross_kg_n2o_m3 = (
        np.asarray(tkn_in_mg_l, dtype=float)
        * float(emission_factor)
        * N2O_N_TO_N2O
        * MG_L_TO_KG_M3
    )
    net_kg_n2o_m3 = gross_kg_n2o_m3 - recovered_kg_n2o_m3
    return net_kg_n2o_m3 * GWP_N2O
