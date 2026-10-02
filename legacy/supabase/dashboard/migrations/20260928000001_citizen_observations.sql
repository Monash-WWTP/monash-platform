-- Shared CitizenFlood schema. This mirrors the app's standalone migration;
-- production shared-platform migrations are applied from wwtp-dashboard.

create table if not exists public.citizen_reports (
  id                  uuid primary key default gen_random_uuid(),
  category            text not null
    check (category in ('rainfall', 'water_level', 'temperature', 'wastewater')),
  reading_value       double precision,
  reading_unit        text,
  condition           text
    check (condition in ('normal', 'warning', 'critical')),
  note                text check (note is null or char_length(note) <= 2000),
  latitude            double precision not null check (latitude between -90 and 90),
  longitude           double precision not null check (longitude between -180 and 180),
  location_accuracy_m double precision
    check (location_accuracy_m is null or location_accuracy_m between 0 and 10000),
  station_code        text
    check (station_code is null or station_code ~ '^[A-Z0-9_-]{2,32}$'),
  photo_path          text,
  observed_at         timestamptz not null default now(),
  moderation_status   text not null default 'pending'
    check (moderation_status in ('pending', 'approved', 'rejected')),
  moderation_note     text,
  reporter_id         uuid not null default auth.uid(),
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now(),
  constraint citizen_reports_reading_shape check (
    (
      category = 'rainfall'
      and reading_value is not null
      and reading_value >= 0
      and reading_unit = 'mm'
      and condition is null
    )
    or (
      category = 'water_level'
      and reading_value is not null
      and reading_unit = 'm'
      and condition is null
    )
    or (
      category = 'temperature'
      and reading_value is not null
      and reading_unit = '°C'
      and condition is null
    )
    or (
      category = 'wastewater'
      and reading_value is null
      and reading_unit is null
      and condition is not null
    )
  )
);

create index if not exists citizen_reports_reporter_created_idx
  on public.citizen_reports (reporter_id, created_at desc);

create index if not exists citizen_reports_category_observed_idx
  on public.citizen_reports (category, observed_at desc, id desc);

create index if not exists citizen_reports_approved_observed_idx
  on public.citizen_reports (observed_at desc, id desc)
  where moderation_status = 'approved';

create or replace function public.set_citizen_report_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists citizen_reports_set_updated_at
  on public.citizen_reports;
create trigger citizen_reports_set_updated_at
before update on public.citizen_reports
for each row execute function public.set_citizen_report_updated_at();

alter table public.citizen_reports enable row level security;

revoke all on table public.citizen_reports from anon, authenticated;
grant select, insert on table public.citizen_reports to authenticated;

drop policy if exists "citizens insert own pending reports"
  on public.citizen_reports;
create policy "citizens insert own pending reports"
  on public.citizen_reports
  for insert
  to authenticated
  with check (
    reporter_id = (select auth.uid())
    and moderation_status = 'pending'
  );

drop policy if exists "citizens read own reports"
  on public.citizen_reports;
create policy "citizens read own reports"
  on public.citizen_reports
  for select
  to authenticated
  using (reporter_id = (select auth.uid()));

create or replace view public.approved_citizen_observations
with (security_barrier = true)
as
select
  id,
  category,
  reading_value,
  reading_unit,
  condition,
  note,
  latitude,
  longitude,
  location_accuracy_m,
  station_code,
  observed_at,
  created_at
from public.citizen_reports
where moderation_status = 'approved';

revoke all on table public.approved_citizen_observations from public;
grant select on table public.approved_citizen_observations to anon, authenticated;

insert into storage.buckets (
  id,
  name,
  public,
  file_size_limit,
  allowed_mime_types
)
values (
  'citizen-report-photos',
  'citizen-report-photos',
  false,
  10485760,
  array['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif']
)
on conflict (id) do update
set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "citizens upload own report photos"
  on storage.objects;
create policy "citizens upload own report photos"
  on storage.objects
  for insert
  to authenticated
  with check (
    bucket_id = 'citizen-report-photos'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

drop policy if exists "citizens read own report photos"
  on storage.objects;
create policy "citizens read own report photos"
  on storage.objects
  for select
  to authenticated
  using (
    bucket_id = 'citizen-report-photos'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );
