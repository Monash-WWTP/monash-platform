# Inactive legacy references

Supabase histories under `supabase/` belong to the deployed legacy systems. They are not connected to the successor Alembic chain and must not be replayed against its database. Two source repositories contain overlapping migrations; preserve their provenance rather than combining them into a new chain.

`research/00_ghg_modelling.py` is historical: it infers GHG intensities from final-effluent inputs and is not scientifically approved. `scripts/dashboard/export_public_dataset.py` is a legacy live refresh helper using unrestricted table columns. It can overwrite a snapshot and is not an approved successor data release process. `upload_to_supabase.py` belongs to the legacy write path. None is called by app startup, onboarding or CI.
