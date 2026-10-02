-- Stations (sewage treatment plants) and real effluent monitoring samples.

create table if not exists public.stations (
  code text primary key,
  name text not null,
  stp_type text,           -- e.g. SBR
  category text,           -- EQA2009 category (A/B)
  latitude double precision not null,
  longitude double precision not null,
  created_at timestamptz default now()
);

create table if not exists public.effluent_samples (
  id bigint generated always as identity primary key,
  station_code text not null references public.stations(code) on delete cascade,
  sample_date date not null,
  sampling int,
  sample_point text,        -- FE = final effluent
  bod numeric,
  bod_bdl boolean default false,        -- below detection limit ("< x")
  cod numeric,
  cod_bdl boolean default false,
  nh3n numeric,
  nh3n_bdl boolean default false,
  no3n numeric,
  no3n_bdl boolean default false,
  ph numeric,
  ph_bdl boolean default false,
  oil_grease numeric,
  oil_grease_bdl boolean default false,
  tss numeric,
  tss_bdl boolean default false,
  temperature numeric,
  compliance text,          -- Comply / Not Comply
  source_year int not null,
  created_at timestamptz default now(),
  unique (station_code, sample_date, sampling)
);

create index if not exists idx_samples_station_date
  on public.effluent_samples (station_code, sample_date);

-- Public read-only access (frontend uses the publishable key).
alter table public.stations enable row level security;
alter table public.effluent_samples enable row level security;

create policy "public read stations" on public.stations
  for select using (true);

create policy "public read samples" on public.effluent_samples
  for select using (true);
