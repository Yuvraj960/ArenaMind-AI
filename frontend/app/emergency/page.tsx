"use client";

import { useState } from "react";
import Link from "next/link";
import { emergencyRespond } from "@/lib/api";
import type { EmergencyScenario } from "@/lib/api";

const SCENARIO_TYPES = [
  { value: "medical", label: "Medical emergency", emoji: "🚑" },
  { value: "fire", label: "Fire", emoji: "🔥" },
  { value: "security", label: "Security threat", emoji: "🚨" },
  { value: "evacuation", label: "Evacuation", emoji: "🏃" },
];

const SEVERITIES = [
  { value: "high", label: "High", color: "border-red-500 bg-red-50 text-red-700" },
  { value: "critical", label: "Critical", color: "border-red-600 bg-red-600 text-white" },
  { value: "medium", label: "Medium", color: "border-amber-500 bg-amber-50 text-amber-700" },
  { value: "low", label: "Low", color: "border-emerald-500 bg-emerald-50 text-emerald-700" },
];

export default function EmergencyPage() {
  const [scenario, setScenario] = useState<EmergencyScenario>({
    type: "medical",
    location: { lat: 40.7130, lng: -74.0055 },
    severity: "high",
    details: "Fan collapsed near Section 103",
    reported_by: "Volunteer",
  });
  const [result, setResult] = useState<Awaited<ReturnType<typeof emergencyRespond>> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await emergencyRespond(scenario);
      setResult(data);
    } catch (err) {
      setError("Failed to get response — is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-red-700 text-white px-6 py-4 flex items-center gap-4 shadow">
        <Link href="/" className="text-red-200 hover:text-white text-sm">← Home</Link>
        <span className="text-xl font-bold">🚨 Emergency AI</span>
        <span className="ml-auto text-xs text-red-300">Response plan generator</span>
      </header>

      <div className="flex-1 p-6 max-w-5xl mx-auto w-full space-y-6">
        {!result ? (
          <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-red-200 shadow-lg p-6 space-y-5">
            <h2 className="text-lg font-bold text-slate-800 border-b border-slate-200 pb-3">
              Report an Incident
            </h2>

            {/* Type */}
            <div>
              <label className="text-sm font-semibold text-slate-600 block mb-2">Incident type</label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {SCENARIO_TYPES.map((t) => (
                  <button
                    key={t.value}
                    type="button"
                    onClick={() => setScenario({ ...scenario, type: t.value as EmergencyScenario["type"] })}
                    className={`px-3 py-2 rounded-xl text-sm border-2 transition-colors ${
                      scenario.type === t.value
                        ? "border-red-500 bg-red-50 text-red-700 font-semibold"
                        : "border-slate-200 hover:border-red-300 text-slate-600"
                    }`}
                  >
                    {t.emoji} {t.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Severity */}
            <div>
              <label className="text-sm font-semibold text-slate-600 block mb-2">Severity</label>
              <div className="flex gap-2">
                {SEVERITIES.map((sv) => (
                  <button
                    key={sv.value}
                    type="button"
                    onClick={() => setScenario({ ...scenario, severity: sv.value as EmergencyScenario["severity"] })}
                    className={`px-3 py-1.5 rounded-lg text-sm border-2 ${
                      scenario.severity === sv.value ? sv.color : "border-slate-200 text-slate-500"
                    }`}
                  >
                    {sv.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Details */}
            <div>
              <label className="text-sm font-semibold text-slate-600 block mb-2">Details</label>
              <textarea
                value={scenario.details}
                onChange={(e) => setScenario({ ...scenario, details: e.target.value })}
                rows={2}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
                placeholder="Describe the incident..."
              />
            </div>

            {/* Reported by */}
            <div>
              <label className="text-sm font-semibold text-slate-600 block mb-2">Reported by</label>
              <input
                value={scenario.reported_by}
                onChange={(e) => setScenario({ ...scenario, reported_by: e.target.value })}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
              />
            </div>

            {error && <p className="text-red-600 text-sm">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl bg-red-600 text-white font-bold hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              {loading ? "Generating response plan..." : "⚡ Generate Emergency Response Plan"}
            </button>
          </form>
        ) : (
          <div className="space-y-4">
            {/* Success */}
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-sm text-emerald-800">
              ✅ Response plan generated — scenario ID: {result.scenario_id}
            </div>

            {/* Evacuation routes */}
            {result.evacuation_routes.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
                <h3 className="font-bold text-slate-800 mb-2">🚪 Evacuation Routes</h3>
                <ul className="space-y-1">
                  {result.evacuation_routes.map((r, i) => (
                    <li key={i} className="text-sm text-slate-700 flex gap-2">
                      <span className="text-emerald-500">→</span> {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Immediate actions */}
            {result.immediate_actions.length > 0 && (
              <div className="bg-red-50 rounded-2xl border border-red-200 p-5 shadow-sm">
                <h3 className="font-bold text-red-800 mb-2">⚡ Immediate Actions</h3>
                <ul className="space-y-1">
                  {result.immediate_actions.map((a, i) => (
                    <li key={i} className="text-sm text-red-700 flex gap-2">
                      <span className="font-bold text-red-500">{i + 1}.</span> {a}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Exits + Medical columns */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
                <h3 className="font-bold text-slate-800 mb-3">🚪 Nearest Exits</h3>
                {result.nearest_exits.map((ex) => (
                  <div key={ex.gate_id} className="flex justify-between text-sm py-1 border-b border-slate-100 last:border-0">
                    <span className="text-slate-700">{ex.name}</span>
                    <span className="text-slate-400">{ex.distance_m}m</span>
                  </div>
                ))}
              </div>

              <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
                <h3 className="font-bold text-slate-800 mb-3">🚑 Nearest Medical</h3>
                {result.nearest_medical.map((m, i) => (
                  <div key={i} className="flex justify-between text-sm py-1 border-b border-slate-100 last:border-0">
                    <span className="text-slate-700">{m.name}</span>
                    <span className="text-slate-400">{m.distance_m}m</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Multilingual announcements */}
            <div className="bg-arena-50 rounded-2xl border border-arena-200 p-5 shadow-sm">
              <h3 className="font-bold text-arena-800 mb-3">📢 Announcements ({result.announcements.length} languages)</h3>
              <div className="space-y-2">
                {result.announcements.map((ann, i) => (
                  <div key={i} className="bg-white rounded-lg px-4 py-2 text-sm">
                    <span className="font-bold text-arena-600 uppercase text-xs mr-2">{ann.language}</span>
                    <span className="text-slate-700">{ann.text}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Clearance time + coordination notes */}
            <div className="bg-slate-100 rounded-2xl p-5 space-y-2">
              <div className="text-sm">
                <span className="font-semibold text-slate-600">Est. clearance: </span>
                <span className="text-slate-800">~{result.estimated_clearance_time_min} min</span>
              </div>
              {result.coordination_notes && (
                <div className="text-sm">
                  <span className="font-semibold text-slate-600">Coordination: </span>
                  <span className="text-slate-700">{result.coordination_notes}</span>
                </div>
              )}
            </div>

            <button
              onClick={() => setResult(null)}
              className="px-6 py-2 rounded-xl border border-slate-300 text-slate-600 text-sm hover:bg-slate-100 transition-colors"
            >
              ← New incident
            </button>
          </div>
        )}
      </div>
    </div>
  );
}