"use client";

import { FormEvent, useState } from "react";

import { AnalyzeVehicleResult, analyzeVehicle } from "@/lib/api";

type VehicleDraft = {
  vin: string;
  make: string;
  model: string;
  year: string;
};

const initialVehicleDraft: VehicleDraft = {
  vin: "",
  make: "",
  model: "",
  year: "",
};

function riskLevelClass(level: string): string {
  const normalized = level.toLowerCase();
  if (normalized.includes("high")) return "border-red-200 bg-red-100 text-red-700";
  if (normalized.includes("medium")) return "border-amber-200 bg-amber-100 text-amber-700";
  return "border-emerald-200 bg-emerald-100 text-emerald-700";
}

function recallSeverityClass(level: string): string {
  const normalized = level.toLowerCase();
  if (normalized.includes("critical")) return "bg-red-600 text-white";
  if (normalized.includes("high")) return "bg-orange-500 text-white";
  if (normalized.includes("medium")) return "bg-amber-400 text-zinc-900";
  return "bg-emerald-500 text-white";
}

export default function Home() {
  const [error, setError] = useState("");
  const [vehicleDraft, setVehicleDraft] = useState<VehicleDraft>(initialVehicleDraft);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<AnalyzeVehicleResult | null>(null);

  async function onAnalyzeVehicle(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setAnalyzing(true);
    setAnalysis(null);
    try {
      const vin = vehicleDraft.vin.trim();
      const payload = vin
        ? { vin }
        : {
            make: vehicleDraft.make.trim(),
            model: vehicleDraft.model.trim(),
            year: Number(vehicleDraft.year),
          };
      setAnalysis(await analyzeVehicle(payload));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze vehicle");
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6">
      <header className="sticky top-0 z-20 -mx-4 rounded-2xl border border-indigo-700 bg-gradient-to-r from-indigo-900 via-blue-800 to-blue-700 px-5 py-3 text-white shadow-lg sm:-mx-6 sm:px-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-200">
              Vehicle Insights
            </p>
            <h1 className="text-2xl font-extrabold tracking-tight">Car Cloud</h1>
          </div>
          <span className="rounded-full bg-white/15 px-3 py-1 text-xs font-medium text-blue-100">
            Smart Risk Dashboard
          </span>
        </div>
      </header>

      <header className="rounded-2xl border border-blue-100 bg-gradient-to-br from-white via-blue-50 to-indigo-50 p-6 shadow-sm">
        <p className="mb-2 inline-block rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700">
          Vehicle Reliability Intelligence
        </p>
        <h2 className="text-3xl font-bold tracking-tight text-zinc-900">Car Cloud Dashboard</h2>
        <p className="mt-2 max-w-3xl text-zinc-600">
          Search by VIN or make/model/year and get an organized dashboard of recalls,
          risk score, common failures, and AI health insights.
        </p>
      </header>

      <section className="rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-zinc-900">Vehicle Analysis</h2>
        <p className="mt-1 text-sm text-zinc-600">
          Enter a VIN, or provide year/make/model. After search, you will see a dashboard
          with risk score, active recalls, and common failures by mileage.
        </p>
        <form className="mt-4 grid gap-3 sm:grid-cols-2" onSubmit={onAnalyzeVehicle}>
          <input
            className="rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 placeholder:text-zinc-500 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 sm:col-span-2"
            placeholder="VIN (optional, 17 chars)"
            value={vehicleDraft.vin}
            onChange={(e) => setVehicleDraft({ ...vehicleDraft, vin: e.target.value })}
          />
          <input
            className="rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 placeholder:text-zinc-500 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            placeholder="Make (required if VIN is empty)"
            value={vehicleDraft.make}
            onChange={(e) => setVehicleDraft({ ...vehicleDraft, make: e.target.value })}
          />
          <input
            className="rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 placeholder:text-zinc-500 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            placeholder="Model (required if VIN is empty)"
            value={vehicleDraft.model}
            onChange={(e) => setVehicleDraft({ ...vehicleDraft, model: e.target.value })}
          />
          <input
            className="rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 placeholder:text-zinc-500 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 sm:col-span-2"
            placeholder="Year (required if VIN is empty)"
            type="number"
            value={vehicleDraft.year}
            onChange={(e) => setVehicleDraft({ ...vehicleDraft, year: e.target.value })}
          />
          <button
            className="rounded-lg bg-blue-700 px-4 py-2 font-medium text-white shadow-sm transition hover:bg-blue-600 sm:col-span-2 disabled:opacity-60"
            disabled={analyzing}
            type="submit"
          >
            {analyzing ? "Analyzing..." : "Analyze Vehicle"}
          </button>
        </form>

        {error ? (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        ) : null}

        {analysis ? (
          <div className="mt-6 grid gap-4">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-xl border border-zinc-200 bg-white p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Confirmed Vehicle
                </p>
                <p className="mt-1 text-sm font-semibold text-zinc-900">
                  {String(analysis.resolved_vehicle.year ?? "-")}{" "}
                  {String(analysis.resolved_vehicle.make ?? "")}{" "}
                  {String(analysis.resolved_vehicle.model ?? "")}
                </p>
              </div>
              <div className="rounded-xl border border-zinc-200 bg-white p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">VIN</p>
                <p className="mt-1 truncate text-sm font-mono text-zinc-800">
                  {String(analysis.resolved_vehicle.vin || "Not provided")}
                </p>
              </div>
              <div className="rounded-xl border border-zinc-200 bg-white p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Recalls Found
                </p>
                <p className="mt-1 text-2xl font-bold text-zinc-900">{analysis.recalls.length}</p>
              </div>
              <div className="rounded-xl border border-zinc-200 bg-white p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Failure Trends
                </p>
                <p className="mt-1 text-2xl font-bold text-zinc-900">
                  {analysis.common_failures.length}
                </p>
              </div>
            </div>

            <div className="grid gap-4 xl:grid-cols-12">
              <div className="rounded-xl border border-blue-100 bg-gradient-to-b from-white to-blue-50 p-4 xl:col-span-3">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-zinc-500">
                  Risk Score
                </h3>
                <p className="mt-1 text-3xl font-bold text-zinc-900">
                  {analysis.risk_score.score}
                  <span className="text-base font-medium text-zinc-500"> / 100</span>
                </p>
                <span
                  className={`mt-2 inline-block rounded-full border px-2.5 py-1 text-xs font-semibold ${riskLevelClass(
                    analysis.risk_score.level,
                  )}`}
                >
                  {analysis.risk_score.level}
                </span>
                <p className="mt-2 text-sm text-zinc-600">{analysis.risk_score.rationale}</p>
              </div>

              <div className="rounded-xl border border-zinc-200 p-4 xl:col-span-5">
                <h3 className="font-semibold text-zinc-900">AI Vehicle Health Summary</h3>
                <p className="mt-2 max-h-56 overflow-auto whitespace-pre-wrap text-sm leading-6 text-zinc-700">
                  {analysis.ai_summary}
                </p>
              </div>

              <div className="rounded-xl border border-zinc-200 p-4 xl:col-span-4">
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="font-semibold text-zinc-900">Recall Alerts</h3>
                  <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-600">
                    {analysis.recalls.length} total
                  </span>
                </div>
                {analysis.recalls.length === 0 ? (
                  <p className="mt-2 text-sm text-zinc-600">No active recalls returned.</p>
                ) : (
                  <ul className="mt-2 max-h-56 space-y-2 overflow-auto pr-1">
                    {analysis.recalls.slice(0, 10).map((r) => (
                      <li
                        className="rounded-lg border border-zinc-200 bg-zinc-50 p-3"
                        key={r.nhtsa_id + r.component}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div className="text-sm font-medium text-zinc-900">{r.component}</div>
                          <span
                            className={`rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase ${recallSeverityClass(
                              r.severity,
                            )}`}
                          >
                            {r.severity}
                          </span>
                        </div>
                        <p className="mt-1 text-xs leading-5 text-zinc-600">
                          {r.summary || "No summary"}
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            <div className="rounded-xl border border-zinc-200 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="font-semibold text-zinc-900">Common Failures by Mileage</h3>
                  <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-600">
                    {analysis.common_failures.length} trends
                  </span>
                </div>
                {analysis.common_failures.length === 0 ? (
                  <p className="mt-2 text-sm text-zinc-600">No failure trends yet.</p>
                ) : (
                  <ul className="mt-2 grid gap-2 md:grid-cols-2">
                    {analysis.common_failures.map((f) => (
                      <li
                        className="rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-700"
                        key={`${f.mileage_range}-${f.issue}`}
                      >
                        <span className="font-semibold text-zinc-900">{f.mileage_range}</span>
                        <span className="mx-2 text-zinc-400">•</span>
                        {f.issue}
                        <span className="ml-2 text-xs text-zinc-500">({f.mentions} mentions)</span>
                      </li>
                    ))}
                  </ul>
                )}
            </div>
          </div>
        ) : null}
      </section>
    </main>
  );
}
