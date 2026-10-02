import { useMemo } from 'react'
import DeckGL from '@deck.gl/react'
import { PolygonLayer, TextLayer } from '@deck.gl/layers'

import type { PlantDetail, Timeseries } from '../../api/types'
import { useWorkspaceStore } from '../../stores/scenarioStore'

/** Local site layout (metres, converted to degree offsets around the plant). */
const M = 0.00001 // ~1 m in degrees, close enough at these latitudes

interface UnitShape {
  name: string
  unitKey: 'pump' | 'aeration' | 'clarifier'
  polygon: [number, number][]
  height: number
}

function circle(cx: number, cy: number, r: number, n = 24): [number, number][] {
  return Array.from({ length: n }, (_, i) => {
    const a = (i / n) * Math.PI * 2
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)] as [number, number]
  })
}

function rect(x: number, y: number, w: number, h: number): [number, number][] {
  return [
    [x, y],
    [x + w, y],
    [x + w, y + h],
    [x, y + h],
  ]
}

const SITE: UnitShape[] = [
  { name: 'Inlet Pump Station', unitKey: 'pump', polygon: rect(-160, -40, 50, 80), height: 8 },
  { name: 'Aeration Basin 1', unitKey: 'aeration', polygon: rect(-80, 10, 120, 45), height: 5 },
  { name: 'Aeration Basin 2', unitKey: 'aeration', polygon: rect(-80, -55, 120, 45), height: 5 },
  { name: 'Secondary Clarifier', unitKey: 'clarifier', polygon: circle(110, 0, 45), height: 4 },
]

function availabilityColor(avail: number): [number, number, number, number] {
  if (avail >= 95) return [42, 157, 144, 220] // chart-2 teal
  if (avail >= 75) return [232, 196, 104, 230] // chart-4
  return [231, 110, 80, 230] // chart-1
}

function webglAvailable(): boolean {
  try {
    const canvas = document.createElement('canvas')
    return !!(canvas.getContext('webgl2') || canvas.getContext('webgl'))
  } catch {
    return false
  }
}

export default function DigitalTwin({ plant, ts }: { plant: PlantDetail; ts: Timeseries | null }) {
  const { timelineDay, setTimelineDay } = useWorkspaceStore()
  const hasWebgl = useMemo(() => webglAvailable(), [])
  const nDays = ts?.dates.length ?? 0
  const day = Math.min(timelineDay, Math.max(0, nDays - 1))

  const layers = useMemo(() => {
    const data = SITE.map((shape) => {
      const avail = ts ? (ts.series[`availability_${shape.unitKey}`]?.[day] ?? 100) : 100
      return {
        ...shape,
        avail,
        coords: shape.polygon.map(([x, y]) => [
          plant.longitude + x * M,
          plant.latitude + y * M,
        ]),
      }
    })
    return [
      new PolygonLayer({
        id: 'site-pad',
        data: [
          {
            coords: rect(-200, -110, 380, 220).map(([x, y]) => [
              plant.longitude + x * M,
              plant.latitude + y * M,
            ]),
          },
        ],
        getPolygon: (d: { coords: number[][] }) => d.coords,
        getFillColor: [244, 244, 245, 255],
        getLineColor: [212, 212, 216, 255],
        getLineWidth: 1,
        lineWidthUnits: 'pixels',
        extruded: false,
      }),
      new PolygonLayer({
        id: 'units',
        data,
        getPolygon: (d: { coords: number[][] }) => d.coords,
        getFillColor: (d: { avail: number }) => availabilityColor(d.avail),
        getElevation: (d: { height: number; avail: number }) => d.height * (0.4 + 0.6 * d.avail / 100),
        extruded: true,
        wireframe: true,
        getLineColor: [63, 63, 70, 70],
        pickable: true,
        updateTriggers: { getFillColor: [day, ts?.run_id], getElevation: [day, ts?.run_id] },
      }),
      new TextLayer({
        id: 'labels',
        data,
        getPosition: (d: { coords: number[][] }) => {
          const xs = d.coords.map((c) => c[0])
          const ys = d.coords.map((c) => c[1])
          return [
            (Math.min(...xs) + Math.max(...xs)) / 2,
            (Math.min(...ys) + Math.max(...ys)) / 2,
            14,
          ]
        },
        getText: (d: { name: string; avail: number }) => `${d.name}\n${Math.round(d.avail)}%`,
        getSize: 12,
        getColor: [24, 24, 27, 255],
        background: true,
        getBackgroundColor: [255, 255, 255, 210],
      }),
    ]
  }, [plant, ts, day])

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="relative min-h-[420px] flex-1 overflow-hidden rounded-lg border border-border bg-muted/40">
        {!hasWebgl && (
          <div className="flex h-full items-center justify-center p-6 text-center text-sm text-muted-foreground">
            3D digital twin requires WebGL, which is not available in this environment.
          </div>
        )}
        {hasWebgl && (
          <>
            <DeckGL
              initialViewState={{
                longitude: plant.longitude,
                latitude: plant.latitude,
                zoom: 17.2,
                pitch: 50,
                bearing: -20,
              }}
              controller
              layers={layers}
            />
            <div className="absolute top-3 left-3 rounded-md border border-border bg-card/90 px-3 py-2 text-xs text-muted-foreground">
              <div className="font-semibold text-foreground">{plant.name} — 3D Digital Twin</div>
              <div>Drag to rotate · scroll to zoom · units coloured by availability</div>
            </div>
          </>
        )}
      </div>

      <div className="rounded-lg border border-border bg-card px-4 py-3">
        {ts ? (
          <>
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Simulation timeline</span>
              <span className="font-mono text-foreground">
                Day {day + 1} / {nDays} — {ts.dates[day]}
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={nDays - 1}
              value={day}
              onChange={(e) => setTimelineDay(Number(e.target.value))}
              className="mt-1 w-full accent-(--primary)"
            />
          </>
        ) : (
          <p className="text-xs text-muted-foreground">
            Run a simulation to animate equipment availability over the horizon.
          </p>
        )}
      </div>
    </div>
  )
}
