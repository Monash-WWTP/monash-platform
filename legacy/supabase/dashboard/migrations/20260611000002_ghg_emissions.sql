-- GHG emission modelling (CH4 & N2O) over effluent monitoring samples.
--
-- Emission intensities follow Eq. 5.25 / 5.28:
--   CES_CH4 [kg CO2-eq/m3] = BOD5_in [mg/L] * EF_CH4 [kg CH4/kg BOD5] * GWP_CH4 * 1e-3
--   CES_N2O [kg CO2-eq/m3] = TN_in  [mg N/L] * EF_N2O [kg N2O-N/kg N] * 44/28 * 1e-3 * GWP_N2O
-- with TN estimated as NH3-N + NO3-N, recovery terms assumed zero,
-- GWP_CH4 = 28 and GWP_N2O = 265 (IPCC AR5, 100-yr).
--
-- Emission factors are process-specific (Tables 5.6 / 5.8); the GENERAL row
-- is the integrated factor used when a station's process type is unmapped.

create table if not exists public.emission_factors (
  process_type text primary key,
  ef_ch4 numeric not null,  -- kg CH4 / kg BOD5
  ef_n2o numeric not null,  -- kg N2O-N / kg N
  source text
);

insert into public.emission_factors (process_type, ef_ch4, ef_n2o, source) values
  ('GENERAL',         0.0121, 0.0093,  'Integrated EF, centralized aerobic plant (Tables 5.6/5.8)'),
  ('SBR',             0.0100, 0.02020, 'Process-specific EF (Tables 5.6/5.8)'),
  ('AAO',             0.0142, 0.00466, 'Process-specific EF (Tables 5.6/5.8)'),
  ('AO',              0.0083, 0.00680, 'Process-specific EF (Tables 5.6/5.8)'),
  ('OXIDATION DITCH', 0.0096, 0.00641, 'Process-specific EF (Tables 5.6/5.8)'),
  ('AERATION TANK',   0.0152, 0.00166, 'Process-specific EF (Tables 5.6/5.8)'),
  ('ANAMMOX',         0.0200, 0.02000, 'Process-specific EF (Tables 5.6/5.8)'),
  ('AGS',             0.0033, 0.00330, 'Process-specific EF (Tables 5.6/5.8)')
on conflict (process_type) do update
  set ef_ch4 = excluded.ef_ch4, ef_n2o = excluded.ef_n2o, source = excluded.source;

alter table public.emission_factors enable row level security;
drop policy if exists "public read emission factors" on public.emission_factors;
create policy "public read emission factors" on public.emission_factors
  for select using (true);

-- Per-sample emission intensities. security_invoker so table RLS applies.
create or replace view public.ghg_sample_emissions
  with (security_invoker = on) as
select
  s.id,
  s.station_code,
  s.sample_date,
  s.source_year,
  s.bod as bod5,
  case
    when s.nh3n is null and s.no3n is null then null
    else coalesce(s.nh3n, 0) + coalesce(s.no3n, 0)
  end as tn_est,
  st.stp_type,
  coalesce(ef.ef_ch4, gen.ef_ch4) as ef_ch4,
  coalesce(ef.ef_n2o, gen.ef_n2o) as ef_n2o,
  s.bod * coalesce(ef.ef_ch4, gen.ef_ch4) * 28 * 1e-3 as ch4_kgco2e_m3,
  case
    when s.nh3n is null and s.no3n is null then null
    else (coalesce(s.nh3n, 0) + coalesce(s.no3n, 0))
         * coalesce(ef.ef_n2o, gen.ef_n2o) * (44.0 / 28.0) * 1e-3 * 265
  end as n2o_kgco2e_m3
from public.effluent_samples s
join public.stations st on st.code = s.station_code
left join public.emission_factors ef on upper(ef.process_type) = upper(st.stp_type)
left join public.emission_factors gen on gen.process_type = 'GENERAL';

-- Station x year summary (counts, means, medians).
create or replace view public.ghg_station_year
  with (security_invoker = on) as
select
  station_code,
  source_year,
  count(ch4_kgco2e_m3) as ch4_count,
  avg(ch4_kgco2e_m3) as ch4_mean,
  percentile_cont(0.5) within group (order by ch4_kgco2e_m3) as ch4_median,
  count(n2o_kgco2e_m3) as n2o_count,
  avg(n2o_kgco2e_m3) as n2o_mean,
  percentile_cont(0.5) within group (order by n2o_kgco2e_m3) as n2o_median
from public.ghg_sample_emissions
group by station_code, source_year;
