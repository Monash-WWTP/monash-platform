import { observationSummary } from "../api/observations"
import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import mapWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ChevronsLeft, ChevronsRight, X } from 'lucide-react'

import type { Plant } from '../api/types'
import { usePlants } from '../api/hooks'
import { useCommunityWastewaterObservations, useStations } from '@/api/monitoring'
import type { CommunityWastewaterObservation, Station } from '@/api/monitoring-types'
import { CHART } from '@/components/dashboard/chartPalette'
import OperatorHeader from '@/components/OperatorHeader'

// OpenFreeMap Liberty: free vector style with 3D building extrusions.
const MAP_STYLE = 'https://tiles.openfreemap.org/styles/liberty'
maplibregl.setWorkerUrl(mapWorkerUrl)
const StationDashboard = lazy(() => import('@/components/monitoring/StationDashboard'))

function observationPopupContent(observation: CommunityWastewaterObservation): HTMLElement {
  const content = document.createElement('div')
  content.style.maxWidth = '260px'

  const heading = document.createElement('strong')
  heading.textContent = observation.observation ? 'Community observation' : 'Legacy wastewater observation'
  content.append(heading)

  const condition = document.createElement('p')
  condition.style.margin = '8px 0 4px'
  condition.textContent = observation.observation ? observationSummary(observation.observation) : `Legacy reported condition: ${observation.condition}`
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
  provenance.style.color = CHART.axis
  provenance.textContent =
    'Approved for display by a moderator. This is a community report, not a laboratory result.'
  content.append(provenance)

  return content
}

export default function MapPage() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const { data: plants, isLoading, error, refetch: refetchPlants } = usePlants()
  const { data: stations } = useStations()
  const {
    data: communityObservations,
    isLoading: communityObservationsLoading,
    isError: communityObservationsError,
    refetch: refetchCommunityObservations,
  } = useCommunityWastewaterObservations()
  const [mapUnavailable, setMapUnavailable] = useState(false)
  const [selectedStation, setSelected] = useState<Station | null>(null)
  const [params] = useSearchParams()
  const [returnSelectionDismissed, setReturnSelectionDismissed] = useState(false)
  const selected = selectedStation ?? (!returnSelectionDismissed ? stations?.find(station => station.code === params.get('station')) ?? null : null)
  const [expanded, setExpanded] = useState(false)
  const [showCommunityObservations, setShowCommunityObservations] = useState(true)
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [narrow, setNarrow] = useState(() => window.matchMedia('(max-width: 639px)').matches)
  const closeButton = useRef<HTMLButtonElement>(null)
  const trigger = useRef<HTMLElement | null>(null)
  const selectPlant = useCallback((plant: Plant, source: HTMLElement) => {
    trigger.current = source
    const station = stations?.find(s => s.code === plant.code)
    setSelected(station ?? { code: plant.code ?? String(plant.id), name: plant.name,
      stp_type: null, category: null, latitude: plant.latitude, longitude: plant.longitude })
    mapRef.current?.flyTo({ center: [plant.longitude, plant.latitude], zoom: 14,
      pitch: 0, bearing: 0, duration: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 500 })
  }, [stations])
  const dismissPanel = useCallback(() => {
    setSelected(null)
    setReturnSelectionDismissed(true)
    setExpanded(false)
  }, [])
  useEffect(() => {
    if (selected) closeButton.current?.focus()
    else if (trigger.current?.isConnected) trigger.current.focus()
    else if (trigger.current) document.querySelector<HTMLInputElement>('#plant-search')?.focus()
  }, [selected, narrow])
  useEffect(() => {
    const query = window.matchMedia('(max-width: 639px)')
    const update = () => setNarrow(query.matches)
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [])
  const visiblePlants = plants?.filter(plant =>
    `${plant.name} ${plant.code ?? ''}`.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase())) ?? []

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
                'fill-extrusion-color': '#9aac9f',
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
      const el = document.createElement('button')
      el.type = 'button'
      el.className = 'plant-map-marker cursor-pointer rounded border border-border bg-background px-3 py-2 text-sm font-semibold text-foreground'
      el.textContent = plant.name
      el.setAttribute('aria-label', `View ${plant.name}`)
      el.addEventListener('click', () => selectPlant(plant, el))

      markers.push(
        new maplibregl.Marker({ element: el })
          .setLngLat([plant.longitude, plant.latitude])
          .addTo(map),
      )
    }
    return () => markers.forEach((m) => m.remove())
  }, [plants, selectPlant, mapUnavailable])

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
      marker.setAttribute('aria-label', observation.observation ? observationSummary(observation.observation) : 'Approved community wastewater observation')
      marker.title = 'Approved community wastewater observation — not a lab result'
      marker.textContent = observation.observation ? '•' : 'W'
      marker.style.width = '26px'
      marker.style.height = '26px'
      marker.style.border = '2px solid white'
      marker.style.borderRadius = '50%'
      marker.style.backgroundColor = CHART.series
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
    <main className="relative h-full overflow-hidden" aria-label="Water monitoring">
      <div inert={selected !== null && narrow}>
      <div className="absolute inset-x-0 top-0 z-10"><OperatorHeader context="Monitoring" monitoring /></div>
      <div ref={mapContainer} style={{ position: 'absolute', inset: '56px 0 0' }} aria-label="Plant locations" />
      <section className={`absolute left-3 top-[68px] z-10 max-h-[calc(100%-80px)] w-[min(320px,calc(100%-24px))] overflow-y-auto rounded-lg border border-border bg-background p-4 ${mapUnavailable ? 'shadow-none' : 'shadow-sm'}`} aria-label="Find a plant">
        <h1 className="text-lg font-semibold">Water monitoring</h1>
        <p className="mt-1 text-xs text-muted-foreground">Select a plant to explore its laboratory record.</p>
        {mapUnavailable && <p role="status" className="mt-3 text-sm text-warning">Interactive map unavailable. All plants remain available below.</p>}
        <label className="mt-4 block text-sm font-medium" htmlFor="plant-search">Search plants</label>
        <input id="plant-search" type="search" value={search} onChange={event => setSearch(event.target.value)}
          className="mt-2 min-h-11 w-full rounded border bg-background px-3 text-sm" placeholder="Plant name or code" />
        {isLoading && <p role="status" className="mt-3 text-sm">Loading plants…</p>}
        <p className="mt-2 text-xs text-muted-foreground">Design capacity is measured in MLD (million litres per day); it is not current measured flow.</p>
        {error ? <div role="alert" className="mt-3 text-sm">
          <p>Plant records could not be loaded. The data service may be unavailable.</p>
          <p className="mt-2 text-xs text-muted-foreground">{error.message} No plant records are being displayed.</p>
          <button className="min-h-11 text-primary underline" onClick={() => void refetchPlants()}>Retry plants</button>
        </div> : !isLoading && <>
          <p role="status" className="mt-3 text-xs text-muted-foreground">{visiblePlants.length} {visiblePlants.length === 1 ? 'plant' : 'plants'}</p>
          <ul className="mt-2 max-h-[32vh] overflow-y-auto divide-y" aria-label="Plants">
            {visiblePlants.map(plant => <li key={plant.id}>
              <button className="min-h-11 w-full rounded p-3 text-left hover:bg-muted"
                onClick={event => selectPlant(plant, event.currentTarget)}>
                <span className="block text-sm font-semibold">{plant.name}</span>
                <span className="text-xs text-muted-foreground">{plant.code} · Design capacity {plant.capacity_mld} MLD</span>
              </button>
            </li>)}
          </ul>
          {visiblePlants.length === 0 && <p className="mt-3 text-sm">{search.trim() ? 'No plants match your search. Try another name or code.' : 'No plants are available yet.'}</p>}
        </>}
        <details className="mt-4 border-t pt-3">
          <summary className="cursor-pointer py-2 text-sm font-medium">Community layer · {communityObservationsError ? 'Unavailable' : !showCommunityObservations ? 'Off' : communityObservationsLoading ? 'Loading' : 'On'}</summary>
        <section className="pt-2" aria-label="Community observations">
          <label className="flex min-h-11 cursor-pointer items-center gap-2 text-sm font-medium">
            <input type="checkbox" checked={showCommunityObservations} onChange={event => setShowCommunityObservations(event.target.checked)} className="size-4 accent-primary" />
            Approved community wastewater
          </label>
          <p className="mt-1 text-xs text-muted-foreground">Citizen reports · not laboratory measurements. Locations are rounded.</p>
          {communityObservationsLoading && <p role="status" className="mt-2 text-xs">Loading observations…</p>}
          {communityObservationsError && <button className="mt-2 min-h-11 text-sm text-primary underline" onClick={() => void refetchCommunityObservations()}>Retry community observations</button>}
          {!communityObservationsLoading && !communityObservationsError && !communityObservations?.length && <p className="mt-2 text-xs text-muted-foreground">No approved observations yet.</p>}
          {mapUnavailable && showCommunityObservations && !!communityObservations?.length && <ul className="mt-3 max-h-40 overflow-y-auto divide-y">
            {communityObservations.map(observation => <li key={observation.id} className="py-2 text-sm">
              <span className="capitalize">{observation.observation ? observationSummary(observation.observation) : observation.condition}</span> · <time dateTime={observation.observed_at}>{new Date(observation.observed_at).toLocaleDateString()}</time>
            </li>)}
          </ul>}
        </section>
        </details>
      </section>
      </div>
      {selected && <aside className={`absolute inset-y-0 right-0 z-20 flex max-w-full flex-col border-l border-border bg-background ${expanded ? 'w-[min(880px,100%)]' : 'w-full sm:w-[380px]'}`}
        role={narrow ? 'dialog' : undefined} aria-modal={narrow ? true : undefined}
        aria-label={`${selected.name} laboratory record`} data-testid="station-dashboard"
        onKeyDown={event => {
          if (event.defaultPrevented) return
          if (event.key === 'Escape') { event.stopPropagation(); dismissPanel() }
          if (event.key === 'Tab' && narrow && event.currentTarget.contains(document.activeElement)) {
            // Radix's portaled select manages its own focus outside this panel.
            const controls = Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button, a[href], input, select, textarea, [tabindex]'))
              .filter(element => element.tabIndex >= 0 && !element.hasAttribute('disabled') && element.getClientRects().length > 0)
            const first = controls[0], last = controls.at(-1)
            if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
            else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
          }
        }}>
        <div className="flex shrink-0 items-center justify-between border-b px-3 py-2">
          <button className="flex size-11 items-center justify-center rounded hover:bg-muted" onClick={() => setExpanded(value => !value)}
            aria-label={expanded ? 'Collapse panel' : 'Expand panel'} aria-expanded={expanded}>
            {expanded ? <ChevronsRight className="size-5" /> : <ChevronsLeft className="size-5" />}
          </button>
          <button ref={closeButton} className="flex size-11 items-center justify-center rounded hover:bg-muted" onClick={dismissPanel} aria-label="Close station panel"><X className="size-5" /></button>
        </div>
        <div className="min-h-0 flex-1">
          <Suspense fallback={<p role="status" className="p-4 text-sm">Loading laboratory view…</p>}>
          <StationDashboard key={selected.code} station={selected} onOpenWorkspace={plants?.some(plant => plant.code === selected.code) ? () => openWorkspace(selected) : undefined} />
          </Suspense>
        </div>
      </aside>}
    </main>
  )
}
