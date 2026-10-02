-- Read-only contract for the WWTP dashboard. Upstream view already filters
-- moderation_status = 'approved' and omits reporter and private photo fields.

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

revoke all on table public.approved_wastewater_observations from public;
grant select on table public.approved_wastewater_observations to anon, authenticated;
