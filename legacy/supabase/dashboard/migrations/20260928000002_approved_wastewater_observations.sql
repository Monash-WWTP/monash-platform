-- Dashboard read contract for wastewater reports that CitizenFlood operators
-- have approved. This deliberately excludes reporter identity, photo paths,
-- moderation notes, and every non-wastewater category.

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
