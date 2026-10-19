---
name: Monash Water neutral interface
colors:
  ink: "#202020"
  muted: "#666666"
  rule: "#e5e5e5"
  primary: "#262626"
  primary-hover: "#111111"
  soft: "#f5f5f5"
  white: "#fff"
typography:
  family: "Manrope, sans-serif"
---

# Monash Water interface

The user requested a neutral palette and less clutter on 19 October 2026. This supersedes the former green interface accent. White, charcoal and true grey carry backgrounds, text, controls, selection and focus. Warning, danger and success colours retain their operational meaning; photographs, cartography and the immutable published APK screenshot retain their actual content.

Use the shared tokens in `apps/dashboard/src/index.css`; native Android uses `AppTheme` with the same neutral values and Material controls. Charts use charcoal/grey series and labelled red screening thresholds. Do not use colour alone to distinguish evidence or status. Typography, source labels, dates, missing values and below-detection notation remain explicit.

## Public pages

Keep one clear download action and a secondary dashboard route. The real Android 1.0.0 screenshot identifies that release. A separate generated river image accompanies documentation and is visibly labelled illustrative, never as a monitored location or scientific evidence. Flat surfaces, thin rules, self-hosted Manrope and restrained spacing maintain continuity. Preserve keyboard focus, readable links and 44px mobile targets.

## Monitoring and research

The latest available sample, observation date, selected parameter, trend and legal-screening caveat remain visible. Filters, statistics, sample rows, community layer settings and research explanations use native labelled disclosures. Filter summaries show active choices; community summaries show layer visibility. No data is deleted or transformed by disclosure state. Research stays secondary and visibly unvalidated. Maintenance, equipment and carbon inputs remain accessible with summaries of configured state.

## Android

The four reporting categories and Report/Map/Me navigation stay visible. Reading input, location/error status and Submit remain in the form. Photo and note controls share an optional native expansion tile with retained state. The map's recent-readings list expands on request; every existing marker, row, detail and refresh action remains. Observation detail sheets scroll on short screens.

## Documentation

The separate Fumadocs repository uses white/charcoal/grey light and dark themes. Primary navigation offers Platform and Manual; the Platform source shortcut is removed. Collapsed implementation citations remain in the manual so scientific and engineering claims stay traceable.
