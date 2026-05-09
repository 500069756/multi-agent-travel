import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

const VIDEO_SRC =
  "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260314_131748_f2ca2a28-fed7-44c8-b9a9-bd9acdd5ec31.mp4";

const SAMPLE_REQUEST =
  "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. Love food and temples, hate crowds.";

type CycleSummary = {
  cycle: number;
  overall: "PASS" | "FAIL";
  revision_target: string | null;
  failures: string[];
};

type PlanResponse = {
  document: string;
  cycles: CycleSummary[];
  converged: boolean;
  final_overall: "PASS" | "FAIL";
  total_estimated_cost_usd: number;
  budget_usd: number;
};

const NAV_LINKS = [
  { label: "Home", active: true },
  { label: "Studio" },
  { label: "About" },
  { label: "Journal" },
  { label: "Reach Us" },
];

export default function App() {
  const [open, setOpen] = useState(false);
  const [request, setRequest] = useState(SAMPLE_REQUEST);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PlanResponse | null>(null);

  async function planTrip() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Request failed");
      }
      setResult((await res.json()) as PlanResponse);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  function openPlanner() {
    setOpen(true);
    setResult(null);
    setError(null);
  }

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Fullscreen looping background video */}
      <video
        className="absolute inset-0 w-full h-full object-cover z-0"
        autoPlay
        loop
        muted
        playsInline
        preload="auto"
      >
        <source src={VIDEO_SRC} type="video/mp4" />
      </video>

      {/* Navigation */}
      <nav className="relative z-10 flex flex-row justify-between items-center px-8 py-6 max-w-7xl mx-auto">
        <a
          href="#"
          className="text-3xl tracking-tight text-foreground"
          style={{ fontFamily: "'Instrument Serif', serif" }}
        >
          Velorah<sup className="text-xs">®</sup>
        </a>

        <ul className="hidden md:flex items-center gap-8">
          {NAV_LINKS.map((link) => (
            <li key={link.label}>
              <a
                href="#"
                className={`text-sm transition-colors ${
                  link.active
                    ? "text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {link.label}
              </a>
            </li>
          ))}
        </ul>

        <button
          onClick={openPlanner}
          className="liquid-glass rounded-full px-6 py-2.5 text-sm text-foreground transition-transform hover:scale-[1.03] cursor-pointer"
        >
          Begin Journey
        </button>
      </nav>

      {/* Hero */}
      <section
        className="relative z-10 flex flex-col items-center text-center px-6 pt-32 pb-40 py-[90px]"
      >
        <h1
          className="animate-fade-rise text-5xl sm:text-7xl md:text-8xl leading-[0.95] tracking-[-2.46px] max-w-7xl font-normal text-foreground"
          style={{ fontFamily: "'Instrument Serif', serif" }}
        >
          Where{" "}
          <em className="not-italic text-muted-foreground">dreams</em> rise{" "}
          <em className="not-italic text-muted-foreground">through the silence.</em>
        </h1>

        <p className="animate-fade-rise-delay text-muted-foreground text-base sm:text-lg max-w-2xl mt-8 leading-relaxed">
          We're designing tools for deep thinkers, bold creators, and quiet
          rebels. Amid the chaos, we build digital spaces for sharp focus and
          inspired work.
        </p>

        <button
          onClick={openPlanner}
          className="animate-fade-rise-delay-2 liquid-glass rounded-full px-14 py-5 text-base text-foreground mt-12 transition-transform hover:scale-[1.03] cursor-pointer"
        >
          Begin Journey
        </button>
      </section>

      {/* Planning dialog */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Plan your journey</DialogTitle>
            <DialogDescription>
              Describe your trip in your own words — destination, days, budget,
              what you love, what you'd rather avoid.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4 flex flex-col gap-3">
            <textarea
              value={request}
              onChange={(e) => setRequest(e.target.value)}
              rows={4}
              className="w-full rounded-md bg-white/5 border border-white/10 px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-white/30 transition-colors resize-none"
              placeholder="Plan a 5-day trip to..."
              disabled={loading}
            />

            <button
              onClick={planTrip}
              disabled={loading || !request.trim()}
              className="liquid-glass self-start rounded-full px-8 py-3 text-sm text-foreground transition-transform hover:scale-[1.03] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              {loading ? "Planning…" : "Plan trip"}
            </button>

            {loading && (
              <p className="text-xs text-muted-foreground">
                Running pipeline (intake → research/logistics → budget →
                synthesis → review). This can take 30–60 seconds.
              </p>
            )}

            {error && (
              <div className="mt-2 rounded-md bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-300">
                {error}
              </div>
            )}

            {result && <PlanOutput data={result} />}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function PlanOutput({ data }: { data: PlanResponse }) {
  const overBudget = data.total_estimated_cost_usd > data.budget_usd;
  return (
    <div className="mt-6 flex flex-col gap-4">
      <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground border-y border-white/10 py-3">
        <span>
          Verdict:{" "}
          <span
            className={
              data.final_overall === "PASS" ? "text-emerald-400" : "text-red-400"
            }
          >
            {data.final_overall}
          </span>
        </span>
        <span>
          Cost:{" "}
          <span className={overBudget ? "text-red-400" : "text-emerald-400"}>
            ${Math.round(data.total_estimated_cost_usd).toLocaleString()}
          </span>{" "}
          / ${Math.round(data.budget_usd).toLocaleString()}
        </span>
        <span>
          Cycles: <span className="text-foreground">{data.cycles.length}</span>
        </span>
      </div>

      {data.cycles.length > 0 && (
        <div className="flex flex-col gap-1.5">
          {data.cycles.map((c) => (
            <div
              key={c.cycle}
              className={`text-xs rounded px-3 py-2 border-l-2 bg-white/[0.02] ${
                c.overall === "PASS"
                  ? "border-emerald-500/60"
                  : "border-red-500/60"
              }`}
            >
              <div className="text-foreground">
                Cycle {c.cycle}: {c.overall}
                {c.revision_target ? (
                  <>
                    {" "}
                    → revise{" "}
                    <span className="text-foreground/80">{c.revision_target}</span>
                  </>
                ) : null}
              </div>
              {c.failures.length > 0 && (
                <ul className="mt-1 text-muted-foreground">
                  {c.failures.map((f, i) => (
                    <li key={i}>• {f}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="prose-doc max-w-none">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{data.document}</ReactMarkdown>
      </div>
    </div>
  );
}
