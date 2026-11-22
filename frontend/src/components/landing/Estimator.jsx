import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { getHealth, estimateEvacuation } from "@/lib/api"

const FIELDS = [
  { name: "homes", label: "Homes", step: 1 },
  { name: "cars_per_home", label: "Cars per home", step: 0.1 },
  { name: "capacity_per_hour", label: "Road capacity (cars / hour)", step: 50 },
  { name: "exits", label: "Independent exits", step: 1 },
  { name: "prep_min", label: "Time to get ready (min)", step: 1 },
  { name: "travel_min", label: "Drive to the danger point (min)", step: 1 },
  { name: "road_cut_min", label: "Road cut after ignition (min)", step: 1 },
]

// Lofou test case from the notebook. Assumptions, not measurements.
const DEFAULTS = {
  homes: 187,
  cars_per_home: 1.5,
  capacity_per_hour: 700,
  exits: 1,
  prep_min: 30,
  travel_min: 28,
  road_cut_min: 60,
}

function BackendStatus({ state }) {
  const map = {
    checking: ["bg-muted-foreground/50", "checking backend…"],
    up: ["bg-emerald-500", "backend online"],
    down: ["bg-red-500", "backend offline"],
  }
  const [dot, text] = map[state]
  return (
    <span className="inline-flex items-center gap-2 font-mono text-xs text-muted-foreground">
      <span className={`h-2 w-2 rounded-full ${dot}`} />
      {text}
    </span>
  )
}

export default function Estimator() {
  const [values, setValues] = useState(
    Object.fromEntries(Object.entries(DEFAULTS).map(([k, v]) => [k, String(v)]))
  )
  const [health, setHealth] = useState("checking")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [exchange, setExchange] = useState(null) // { request, response }

  const checkBackend = () => {
    setHealth("checking")
    getHealth()
      .then(() => setHealth("up"))
      .catch(() => setHealth("down"))
  }

  useEffect(() => {
    getHealth()
      .then(() => setHealth("up"))
      .catch(() => setHealth("down"))
  }, [])

  const onSubmit = async (e) => {
    e.preventDefault()
    const request = Object.fromEntries(
      Object.entries(values).map(([k, v]) => [k, Number(v)])
    )
    setBusy(true)
    setError(null)
    try {
      const response = await estimateEvacuation(request)
      setExchange({ request, response })
      setHealth("up")
    } catch (err) {
      setExchange(null)
      setError(
        err instanceof TypeError
          ? "Could not reach the backend. Is it running?"
          : `The backend rejected the input: ${err.message}`
      )
      if (err instanceof TypeError) setHealth("down")
    } finally {
      setBusy(false)
    }
  }

  const r = exchange?.response

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <form onSubmit={onSubmit} className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
        <div className="flex items-center justify-between gap-3">
          <h3 className="font-mono text-sm font-semibold">one village, one road</h3>
          <button
            type="button"
            onClick={checkBackend}
            className="rounded-md hover:bg-muted px-2 py-1 transition-colors"
            title="Check the backend again"
          >
            <BackendStatus state={health} />
          </button>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {FIELDS.map((f) => (
            <label key={f.name} className="flex flex-col gap-1.5 text-xs text-muted-foreground">
              {f.label}
              <Input
                type="number"
                inputMode="decimal"
                min="0"
                step={f.step}
                required
                value={values[f.name]}
                onChange={(e) => setValues({ ...values, [f.name]: e.target.value })}
                className="font-mono text-foreground"
              />
            </label>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" disabled={busy}>
            {busy ? "Asking the backend…" : "Run the estimate"}
          </Button>
          <Button type="button" variant="ghost" onClick={() => setValues(Object.fromEntries(Object.entries(DEFAULTS).map(([k, v]) => [k, String(v)])))}>
            Reset to Lofou defaults
          </Button>
        </div>

        {health === "down" && (
          <p className="rounded-md bg-muted p-3 font-mono text-xs">
            Start the backend:<br />
            cd Backend &amp;&amp; uv run python main.py
          </p>
        )}
        {error && <p className="text-sm text-destructive">{error}</p>}
      </form>

      <div className="flex flex-col gap-4">
        {r ? (
          <div
            className={`rounded-xl border p-5 ${
              r.feasible
                ? "border-emerald-600/40 bg-emerald-500/10"
                : "border-red-600/40 bg-red-500/10"
            }`}
          >
            <p className="font-mono text-xs uppercase tracking-wide text-muted-foreground">result</p>
            <p className="mt-1 text-sm font-medium">{r.message}</p>
            <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-sm">
              <dt className="text-muted-foreground">cars to move</dt>
              <dd className="text-right">{r.cars}</dd>
              <dt className="text-muted-foreground">queue time</dt>
              <dd className="text-right">{r.queue_min} min</dd>
              <dt className="text-muted-foreground">evacuation time</dt>
              <dd className="text-right">{r.evac_min} min</dd>
              <dt className="text-muted-foreground">latest alert</dt>
              <dd className="text-right">{r.latest_alert_min} min after ignition</dd>
            </dl>
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-border p-5 text-sm text-muted-foreground">
            Press <span className="font-mono text-foreground">Run the estimate</span>. The page sends your numbers
            to the backend, which does the arithmetic and answers.
          </div>
        )}

        <div className="rounded-xl border border-border bg-card p-5">
          <p className="font-mono text-xs uppercase tracking-wide text-muted-foreground">
            what travelled between the page and the server
          </p>
          {exchange ? (
            <div className="mt-3 grid gap-3">
              <div>
                <p className="font-mono text-xs">POST /api/evacuation/estimate</p>
                <pre className="mt-1 overflow-x-auto rounded-md bg-muted p-3 font-mono text-xs">
                  {JSON.stringify(exchange.request, null, 2)}
                </pre>
              </div>
              <div>
                <p className="font-mono text-xs">200 OK</p>
                <pre className="mt-1 overflow-x-auto rounded-md bg-muted p-3 font-mono text-xs">
                  {JSON.stringify(exchange.response, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <p className="mt-2 text-sm text-muted-foreground">Nothing sent yet.</p>
          )}
        </div>
      </div>
    </div>
  )
}
