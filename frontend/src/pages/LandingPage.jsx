import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowRight, BellRing, Flame, Route, Users } from "lucide-react"
import Estimator from "@/components/landing/Estimator"

const PARTS = [
  {
    icon: Flame,
    title: "Fire",
    text: "Where the fire spreads and how fast, depending on wind, terrain and vegetation.",
  },
  {
    icon: Route,
    title: "Roads",
    text: "The road network as a graph: how many cars pass per hour, where the bottlenecks are, which sections burn first.",
  },
  {
    icon: Users,
    title: "People",
    text: "How many residents and cars a village has, and how long it takes them to get out.",
  },
  {
    icon: BellRing,
    title: "Warnings",
    text: "When the alert goes out, and how many people leave early or late once it does.",
  },
]

const PROBLEMS = [
  "Fire or smoke blocks one of the roads down.",
  "Everyone decides to leave at once, and the remaining road jams.",
  "People without cars, the elderly and tourists are the most vulnerable.",
]

function Section({ id, label, title, children }) {
  return (
    <section id={id} className="scroll-mt-20 border-t border-border/60 py-12">
      <p className="font-mono text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <h2 className="mt-2 mb-6 text-2xl font-semibold tracking-tight">{title}</h2>
      {children}
    </section>
  )
}

export default function LandingPage() {
  return (
    <div className="w-full max-w-5xl">
      {/* Hero */}
      <section className="flex flex-col gap-6 py-12 sm:py-16">
        <Badge variant="secondary" className="w-fit font-mono">
          research prototype · Troodos mountains, Cyprus
        </Badge>
        <h1 className="font-mono text-5xl font-bold tracking-tight sm:text-6xl">EGRESS</h1>
        <p className="max-w-2xl text-xl text-foreground sm:text-2xl">
          Will people be able to get out in time, and how can we make sure they do?
        </p>
        <p className="max-w-2xl text-muted-foreground">
          Many small villages in the Troodos mountains have only one or two roads down. EGRESS simulates hundreds of
          wildfire scenarios against a village&apos;s roads and residents, and answers: when must the alert go out, and
          how should the village be evacuated?
        </p>
        <div className="flex flex-wrap gap-3 pt-2">
          <Button asChild size="lg" className="gap-2">
            <a href="#estimator">
              <span>Try the estimator</span>
              <ArrowRight className="h-4 w-4" />
            </a>
          </Button>
          <Button asChild size="lg" variant="outline">
            <a href="#how">How it works</a>
          </Button>
          <Button asChild size="lg" variant="ghost">
            <Link to="/app/dashboard">Open App</Link>
          </Button>
        </div>
      </section>

      {/* Problem */}
      <Section label="the problem" title="One road is not an evacuation plan">
        <ul className="grid gap-3 sm:grid-cols-3">
          {PROBLEMS.map((p, i) => (
            <li key={p} className="rounded-xl border border-border bg-card p-4 text-sm">
              <span className="font-mono text-xs text-muted-foreground">0{i + 1}</span>
              <p className="mt-2">{p}</p>
            </li>
          ))}
        </ul>
      </Section>

      {/* How it works */}
      <Section id="how" label="how it works" title="Four parts, one model">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PARTS.map(({ icon: Icon, title, text }) => (
            <Card key={title}>
              <CardHeader>
                <Icon className="mb-1 h-5 w-5 text-muted-foreground" />
                <CardTitle className="font-mono">{title}</CardTitle>
                <CardDescription>{text}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>

        <div className="mt-8 rounded-xl border border-border bg-card p-5">
          <p className="font-mono text-xs uppercase tracking-wide text-muted-foreground">the core idea: two clocks</p>
          <pre className="mt-3 overflow-x-auto font-mono text-sm leading-relaxed">
{`T_evac       = getting ready + queue + driving
latest alert = T_cut - T_evac - margin`}
          </pre>
          <p className="mt-3 text-sm text-muted-foreground">
            T_cut is when the escape road is lost to fire or smoke. If the latest alert comes out negative, even
            warning people at ignition is too late, and the plan has to change: stage the departures, open a second
            route, or help people leave earlier. Because wind and behaviour are uncertain, the model runs hundreds of
            scenarios and reports a probability, not a single number.
          </p>
        </div>
      </Section>

      {/* Live estimator */}
      <Section
        id="estimator"
        label="try it"
        title="Ask the backend: can this village get out in time?"
      >
        <p className="mb-6 max-w-2xl text-sm text-muted-foreground">
          This is the two-clocks check for a single road. The defaults describe our test village, Lofou. They are
          illustrative assumptions, not measurements or predictions.
        </p>
        <Estimator />
      </Section>

      {/* Status */}
      <Section label="status" title="Where the project is">
        <ul className="grid gap-3 text-sm sm:grid-cols-2">
          <li className="rounded-xl border border-border bg-card p-4">
            <span className="font-mono text-xs text-muted-foreground">working</span>
            <p className="mt-2">
              Road graph and exits for the Lofou test village, a toy fire model, and a first coupling of fire and roads.
            </p>
          </li>
          <li className="rounded-xl border border-border bg-card p-4">
            <span className="font-mono text-xs text-muted-foreground">next</span>
            <p className="mt-2">
              Real vegetation and terrain data, census population, and calibration against the 2025 Limassol fire.
            </p>
          </li>
        </ul>
        <p className="mt-8 rounded-xl bg-muted p-4 text-xs text-muted-foreground">
          EGRESS is a research and planning prototype. It is not an emergency tool and has not been validated for real
          decisions. In a wildfire, call 112.
        </p>
      </Section>
    </div>
  )
}
