-- Keep public observations useful on a map without publishing precise
-- household-level locations or free-text notes that may contain personal data.
create or replace view public.approved_citizen_observations
with (security_barrier = true)
as
select
  id,
  category,
  reading_value,
  reading_unit,
  condition,
  null::text as note,
  round(latitude::numeric, 3)::double precision as latitude,
  round(longitude::numeric, 3)::double precision as longitude,
  null::double precision as location_accuracy_m,
  station_code,
  observed_at,
  created_at
from public.citizen_reports
where moderation_status = 'approved';

create or replace view public.approved_wastewater_observations
with (security_barrier = true)
as
select
  id,
  category,
  condition,
  note,
  latitude,
  longitude,
  location_accuracy_m,
  observed_at,
  created_at
from public.approved_citizen_observations
where category = 'wastewater';

revoke all on table public.approved_citizen_observations from public;
grant select on table public.approved_citizen_observations to anon, authenticated;
revoke all on table public.approved_wastewater_observations from public;
grant select on table public.approved_wastewater_observations to anon, authenticated;

-- This sample-level view applies influent-based equations to effluent samples.
-- Keep it unavailable until valid influent data can support the calculation.
revoke all on table public.ghg_sample_emissions from public, anon, authenticated;
revoke all on table public.ghg_station_year from public, anon, authenticated;
