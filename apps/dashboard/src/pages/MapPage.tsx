import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import mapWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import { useNavigate } from 'react-router-dom'
import { ChevronsLeft, ChevronsRight, X } from 'lucide-react'

import { usePlants } from '../api/hooks'
import { useCommunityWastewaterObservations, useStations } from '@/api/monitoring'
import type { CommunityWastewaterObservation, Station } from '@/api/monitoring-types'
import StationDashboard from '@/components/monitoring/StationDashboard'

// OpenFreeMap Liberty: free vector style with 3D building extrusions.
const MAP_STYLE = 'https://tiles.openfreemap.org/styles/liberty'
maplibregl.setWorkerUrl(mapWorkerUrl)

function observationPopupContent(observation: CommunityWastewaterObservation): HTMLElement {
  const content = document.createElement('div')
  content.style.maxWidth = '260px'

  const heading = document.createElement('strong')
  heading.textContent = 'Community wastewater observation'
  content.append(heading)

  const condition = document.createElement('p')
  condition.style.margin = '8px 0 4px'
  condition.textContent = `Reported condition: ${observation.condition}`
  content.append(condition)

  const observed = document.createElement('p')
  observed.style.margin = '0 0 8px'
  observed.textContent = `Observed ${new Date(observation.observed_at).toLocaleString()}`
  content.append(observed)

  const privacy = document.createElement('p')
  privacy.textContent = 'Location rounded for public display.'
  content.append(privacy)

  const provenance = document.createElement('p')
  provenance.style.margin = '8px 0 0'
  provenance.style.fontSize = '12px'
  provenance.style.color = '#52525b'
  provenance.textContent =
    'Approved for display by a moderator. This is a community report, not a laboratory result.'
  content.append(provenance)

  return content
}

export default function MapPage() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const { data: plants, isLoading, error } = usePlants()
  const { data: stations } = useStations()
  const {
    data: communityObservations,
    isLoading: communityObservationsLoading,
    isError: communityObservationsError,
    refetch: refetchCommunityObservations,
  } = useCommunityWastewaterObservations()
  const [mapUnavailable, setMapUnavailable] = useState(false)
  const [selected, setSelected] = useState<Station | null>(null)
  const [expanded, setExpanded] = useState(false)
  const [showCommunityObservations, setShowCommunityObservations] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return
    let fallbackTimer: number | undefined
    try {
      const map = new maplibregl.Map({
        container: mapContainer.current,
        style: MAP_STYLE,
        center: [101.6394, 3.1012],
        zoom: 11.5,
        pitch: 45,
        bearing: -15,
      })
      map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right')
      map.on('style.load', () => {
        // emphasise 3D buildings once tiles arrive
        const buildings = map
          .getStyle()
          .layers?.find((l) => l.type === 'fill-extrusion' && l.id.includes('building'))
        if (!buildings) {
          // style without extrusions — add our own from the openmaptiles source
          try {
            map.addLayer({
              id: 'wwtp-3d-buildings',
              source: 'openmaptiles',
              'source-layer': 'building',
              type: 'fill-extrusion',
              minzoom: 14,
              paint: {
                'fill-extrusion-color': '#9aa7bd',
                'fill-extrusion-height': ['coalesce', ['get', 'render_height'], 8],
                'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0],
                'fill-extrusion-opacity': 0.75,
              },
            })
          } catch {
            /* source naming differs — skip extra extrusions */
          }
        }
      })
      mapRef.current = map
    } catch {
      // WebGL unavailable (remote desktop, headless, old GPU) — fall back to a list
      fallbackTimer = window.setTimeout(() => setMapUnavailable(true), 0)
    }
    return () => {
      if (fallbackTimer !== undefined) window.clearTimeout(fallbackTimer)
      mapRef.current?.remove()
      mapRef.current = null
    }
  }, [])

  // markers for plants (operational status from API; locations match stations)
  useEffect(() => {
    const map = mapRef.current
    if (!map || !plants || mapUnavailable) return

    const markers: maplibregl.Marker[] = []
    for (const plant of plants) {
      const el = document.createElement('div')
      el.className = 'cursor-pointer'
      el.innerHTML = `
        <div style="display:flex;flex-direction:column;align-items:center;gap:3px;">
          <div style="width:14px;height:14px;border-radius:50%;background:#18181b;
            border:2.5px solid #ffffff;box-shadow:0 1px 3px rgba(0,0,0,0.3);"></div>
          <div style="background:#ffffff;color:#18181b;font-size:11px;font-weight:600;
            padding:2px 7px;border-radius:6px;border:1px solid #e4e4e7;box-shadow:0 1px 2px rgba(0,0,0,0.08);white-space:nowrap;">${plant.name}</div>
        </div>`
      el.addEventListener('click', () => {
        // cinematic zoom into the station, then open its dashboard panel
        map.flyTo({
          center: [plant.longitude, plant.latitude],
          zoom: 16.8,
          pitch: 62,
          bearing: -30,
          duration: 2600,
          essential: true,
        })
        const station = stations?.find((s) => s.code === plant.code)
        setSelected(
          station ?? {
            code: plant.code ?? String(plant.id),
            name: plant.name,
            stp_type: null,
            category: null,
            latitude: plant.latitude,
            longitude: plant.longitude,
          },
        )
      })

      markers.push(
        new maplibregl.Marker({ element: el })
          .setLngLat([plant.longitude, plant.latitude])
          .addTo(map),
      )
    }
    return () => markers.forEach((m) => m.remove())
  }, [plants, stations, mapUnavailable])

  // Community observations use a separate, opt-out marker layer. They are not
  // joined to stations or shown in lab/compliance summaries.
  useEffect(() => {
    const map = mapRef.current
    if (
      !map ||
      mapUnavailable ||
      !showCommunityObservations ||
      !communityObservations?.length
    ) {
      return
    }

    const markers: maplibregl.Marker[] = []
    for (const observation of communityObservations) {
      const marker = document.createElement('button')
      marker.type = 'button'
      marker.className = 'community-wastewater-marker'
      marker.setAttribute('aria-label', 'Approved community wastewater observation')
      marker.title = 'Approved community wastewater observation — not a lab result'
      marker.textContent = 'W'
      marker.style.width = '26px'
      marker.style.height = '26px'
      marker.style.border = '2px solid white'
      marker.style.borderRadius = '50%'
      marker.style.backgroundColor = '#7c3aed'
      marker.style.color = 'white'
      marker.style.fontSize = '12px'
      marker.style.fontWeight = '700'
      marker.style.boxShadow = '0 1px 4px rgba(0,0,0,0.35)'
      marker.style.cursor = 'pointer'
      marker.addEventListener('click', (event) => {
        event.stopPropagation()
        new maplibregl.Popup({ closeButton: true, maxWidth: '300px' })
          .setLngLat([observation.longitude, observation.latitude])
          .setDOMContent(observationPopupContent(observation))
          .addTo(map)
      })

      markers.push(
        new maplibregl.Marker({ element: marker, anchor: 'center' })
          .setLngLat([observation.longitude, observation.latitude])
          .addTo(map),
      )
    }

    return () => markers.forEach((marker) => marker.remove())
  }, [communityObservations, mapUnavailable, showCommunityObservations])

  const openWorkspace = (station: Station) => {
    const plant = plants?.find((p) => p.code === station.code)
    if (plant) navigate(`/dashboard/plants/${plant.id}`)
  }

  return (
    <div className="relative h-full">
      <div ref={mapContainer} className="h-full" />

      {mapUnavailable && plants && (
        <div
          className="absolute inset-0 z-10 overflow-y-auto bg-background p-6 pt-32"
          data-testid="plant-list-fallback"
        >
          <p className="mx-auto mb-4 max-w-3xl text-xs text-amber-700">
            Interactive map unavailable (WebGL not supported here) — select a plant from the list.
          </p>
          <div className="mx-auto grid max-w-3xl gap-3 sm:grid-cols-2">
            {plants.map((plant) => (
              <button
                key={plant.id}
                onClick={() => {
                  const station = stations?.find((s) => s.code === plant.code)
                  if (station) setSelected(station)
                  else navigate(`/dashboard/plants/${plant.id}`)
                }}
                className="rounded-lg border border-border bg-card p-4 text-left hover:border-primary"
              >
                <span className="font-semibold">{plant.name}</span>
                <p className="mt-1 text-xs text-muted-foreground">
                  Design capacity {plant.capacity_mld} MLD
                </p>
              </button>
            ))}
          </div>
          <section className="mx-auto mt-8 max-w-3xl" aria-labelledby="community-observations-title">
            <h2 id="community-observations-title" className="font-semibold">
              Approved community wastewater observations
            </h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Citizen reports are shown separately from laboratory measurements and are not used for compliance or simulations.
            </p>
            {communityObservationsLoading ? (
              <p className="mt-3 text-sm text-muted-foreground">Loading observations…</p>
            ) : communityObservationsError ? (
              <button
                className="mt-3 text-sm text-destructive underline"
                onClick={() => void refetchCommunityObservations()}
              >
                Could not load observations. Retry
              </button>
            ) : !communityObservations?.length ? (
              <p className="mt-3 text-sm text-muted-foreground">No approved wastewater observations yet.</p>
            ) : (
              <ul className="mt-3 divide-y rounded-lg border border-border bg-card">
                {communityObservations.slice(0, 20).map((observation) => (
                  <li key={observation.id} className="flex items-start justify-between gap-3 p-3 text-sm">
                    <span>
                      <span className="font-medium capitalize">{observation.condition}</span>
                    </span>
                    <time className="shrink-0 text-xs text-muted-foreground" dateTime={observation.observed_at}>
                      {new Date(observation.observed_at).toLocaleDateString()}
                    </time>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}

      {!mapUnavailable && (
        <div className="absolute top-3 left-3 z-10 max-w-72 rounded-lg border border-border bg-background/95 p-3 shadow-sm backdrop-blur">
          <label className="flex cursor-pointer items-center gap-2 text-sm font-medium">
            <input
              type="checkbox"
              checked={showCommunityObservations}
              onChange={(event) => setShowCommunityObservations(event.target.checked)}
              className="size-4 accent-violet-600"
            />
            Approved community wastewater
          </label>
          <p className="mt-1 pl-6 text-xs text-muted-foreground">
            Latest 500 citizen reports · not laboratory measurements
          </p>
          {communityObservationsLoading && (
            <p className="mt-2 pl-6 text-xs text-muted-foreground">Loading…</p>
          )}
          {communityObservationsError && (
            <button
              className="mt-2 pl-6 text-xs text-destructive underline"
              onClick={() => void refetchCommunityObservations()}
            >
              Could not load. Retry
            </button>
          )}
          {!communityObservationsLoading &&
            !communityObservationsError &&
            !communityObservations?.length && (
              <p className="mt-2 pl-6 text-xs text-muted-foreground">No approved observations yet.</p>
            )}
        </div>
      )}

      {selected && (
        <aside
          className={`absolute top-0 right-0 z-20 h-full border-l border-border bg-background/95 backdrop-blur transition-[width] duration-300 ${
            expanded ? 'w-[min(880px,90vw)]' : 'w-[380px]'
          }`}
          data-testid="station-dashboard"
        >
          <div className="flex items-center justify-between border-b px-2 py-1.5">
            <button
              className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
              onClick={() => setExpanded((e) => !e)}
              title={expanded ? 'Collapse panel' : 'Expand panel'}
            >
              {expanded ? <ChevronsRight className="size-4" /> : <ChevronsLeft className="size-4" />}
            </button>
            <button
              className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
              onClick={() => {
                setSelected(null)
                setExpanded(false)
                mapRef.current?.flyTo({ zoom: 11.5, pitch: 45, bearing: -15, duration: 1800 })
              }}
            >
              <X className="size-4" />
            </button>
          </div>
          <div className="h-[calc(100%-34px)]">
            <StationDashboard station={selected} onOpenWorkspace={() => openWorkspace(selected)} />
          </div>
        </aside>
      )}

      {isLoading && (
        <div className="absolute inset-x-0 bottom-6 z-10 text-center text-sm text-muted-foreground">
          Loading plants…
        </div>
      )}
      {error && (
        <div className="absolute inset-x-0 bottom-6 z-10 text-center text-sm text-destructive">
          Failed to load plants — is the API running on :8000?
        </div>
      )}
    </div>
  )
}
